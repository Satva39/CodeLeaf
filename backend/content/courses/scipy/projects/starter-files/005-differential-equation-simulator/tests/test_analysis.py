import numpy as np
import pytest
from src.main import analyze

def test_summary_for_synthetic_values():
    result = analyze([1.0, 2.0, 3.0])
    assert result["count"] == 3
    assert np.isclose(result["mean"], 2.0)
    assert result["scipy_version"]

@pytest.mark.parametrize("values", [[], [float("nan")], [float("inf")]])
def test_rejects_empty_or_nonfinite_values(values):
    with pytest.raises(ValueError):
        analyze(values)
