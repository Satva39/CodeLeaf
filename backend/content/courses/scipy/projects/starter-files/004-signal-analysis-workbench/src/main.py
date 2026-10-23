"""Starter entry point for Signal Analysis Workbench.

Synthetic data only; implement the TODOs before relying on results.
"""
import numpy as np
import scipy

def analyze(values):
    """Validate numeric data and return a minimal summary."""
    data = np.asarray(values, dtype=float)
    if data.size == 0 or not np.isfinite(data).all():
        raise ValueError("values must be non-empty and finite")
    # TODO: implement the project-specific SciPy workflow and validation.
    return {"count": int(data.size), "mean": float(data.mean()), "scipy_version": scipy.__version__}

if __name__ == "__main__":
    sample = [1.0, 2.0, 3.0]
    print(analyze(sample))
