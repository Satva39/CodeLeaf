"""Mocked battle-judge tests for hidden-test secrecy and fail-closed winner rules."""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException

from app import games_routes
from app.onlinecompiler_client import OnlineCompilerError


class OnlineCompilerBattleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = MagicMock()
        self.user = SimpleNamespace(id=uuid4())
        self.reservations = [SimpleNamespace(id=uuid4()) for _ in range(4)]
        self.patches = [
            patch.object(games_routes, "effective_plan_id", return_value="free"),
            patch.object(games_routes, "plan_limits", return_value={"code_executions_per_day": 100}),
            patch.object(games_routes, "reserve_daily_usage", side_effect=[(row, False) for row in self.reservations]),
            patch.object(games_routes, "finalize_daily_usage"),
        ]
        self.mocks = [item.start() for item in self.patches]
        for item in self.patches:
            self.addCleanup(item.stop)

    async def test_all_hidden_tests_must_be_accepted(self):
        with patch.object(games_routes, "run_onlinecompiler_tests", new_callable=AsyncMock) as run_tests:
            run_tests.return_value = {
                "verdict": "accepted", "passed": 2, "total": 2,
                "tests": [
                    {"verdict": "accepted", "hidden": True, "output": "MUST_NOT_BE_RETURNED"},
                    {"verdict": "accepted", "hidden": True, "input": "PRIVATE_INPUT"},
                ],
            }
            result = await games_routes._run_onlinecompiler_battle_tests(
                db=self.db, user=self.user, language="python", source_code="print('ok')",
                tests=[
                    {"input": "secret one", "output": "expected one", "hidden": True},
                    {"input": "secret two", "output": "expected two", "hidden": True},
                ],
                idempotency_key="battle-submit:test-id",
            )
        passed, message, provider_accepted, passed_count, total = result
        self.assertTrue(passed)
        self.assertTrue(provider_accepted)
        self.assertEqual((passed_count, total), (2, 2))
        self.assertNotIn("MUST_NOT_BE_RETURNED", message)
        self.assertNotIn("PRIVATE_INPUT", message)
        sent = run_tests.await_args.kwargs["tests"]
        self.assertTrue(all(item["hidden"] is True for item in sent))
        self.db.commit.assert_called()

    async def test_incomplete_provider_result_cannot_win(self):
        self.mocks[2].side_effect = [(row, False) for row in self.reservations]
        self.mocks[3].reset_mock()
        with patch.object(games_routes, "run_onlinecompiler_tests", new_callable=AsyncMock) as run_tests:
            run_tests.return_value = {
                "verdict": "incomplete", "passed": 1, "total": 2,
                "tests": [
                    {"verdict": "accepted", "hidden": True},
                    {"verdict": "skipped", "hidden": True},
                ],
            }
            result = await games_routes._run_onlinecompiler_battle_tests(
                db=self.db, user=self.user, language="javascript", source_code="console.log('ok')",
                tests=[
                    {"input": "private", "output": "expected", "hidden": True},
                    {"input": "private2", "output": "expected2", "hidden": True},
                ],
                idempotency_key="battle-submit:incomplete",
            )
        self.assertFalse(result[0])
        self.assertFalse(result[2])
        self.assertIn("not counted", result[1])
        calls = self.mocks[3].call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0].kwargs["success"], True)
        self.assertEqual(calls[1].kwargs["success"], False)

    async def test_wrong_answer_is_a_completed_rejection_not_a_provider_failure(self):
        with patch.object(games_routes, "run_onlinecompiler_tests", new_callable=AsyncMock) as run_tests:
            run_tests.return_value = {
                "verdict": "wrong_answer", "passed": 1, "total": 2,
                "tests": [
                    {"verdict": "accepted", "hidden": True},
                    {"verdict": "wrong_answer", "hidden": True},
                ],
            }
            result = await games_routes._run_onlinecompiler_battle_tests(
                db=self.db, user=self.user, language="python", source_code="print('wrong')",
                tests=[
                    {"input": "private", "output": "expected", "hidden": True},
                    {"input": "private2", "output": "expected2", "hidden": True},
                ],
                idempotency_key="battle-submit:wrong-answer",
            )
        self.assertFalse(result[0])
        self.assertTrue(result[2])
        self.assertIn("did not pass", result[1])

    async def test_rate_limit_never_becomes_a_win_and_releases_reservations(self):
        with patch.object(games_routes, "run_onlinecompiler_tests", new_callable=AsyncMock) as run_tests:
            run_tests.side_effect = OnlineCompilerError("safe rate-limit message", status_code=429)
            result = await games_routes._run_onlinecompiler_battle_tests(
                db=self.db, user=self.user, language="python", source_code="print('ok')",
                tests=[
                    {"input": "private", "output": "expected", "hidden": True},
                    {"input": "private2", "output": "expected2", "hidden": True},
                ],
                idempotency_key="battle-submit:rate-limit",
            )
        self.assertFalse(result[0])
        self.assertFalse(result[2])
        self.assertIn("usage limit", result[1])
        self.assertTrue(all(call.kwargs["success"] is False for call in self.mocks[3].call_args_list))

    async def test_daily_quota_error_releases_prior_test_reservations(self):
        self.mocks[2].side_effect = [
            (self.reservations[0], False),
            HTTPException(status_code=429, detail="quota"),
        ]
        with self.assertRaises(HTTPException):
            await games_routes._run_onlinecompiler_battle_tests(
                db=self.db, user=self.user, language="python", source_code="print('ok')",
                tests=[
                    {"input": "private", "output": "expected", "hidden": True},
                    {"input": "private2", "output": "expected2", "hidden": True},
                ],
                idempotency_key="battle-submit:daily-quota",
            )
        self.mocks[3].assert_called_once()
        self.assertFalse(self.mocks[3].call_args.kwargs["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
