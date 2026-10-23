import unittest
from starter import solve

class StarterTests(unittest.TestCase):
    @unittest.skip("Starter is intentionally incomplete; add tests after implementing solve().")
    def test_example_contract(self):
        self.assertEqual(solve(None), None)

if __name__ == "__main__":
    unittest.main()
