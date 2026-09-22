"""Verification module.

Full skill verification suite: RMSE, ETS, CSI, POD, FAR, multi-scale
FSS, and reliability diagrams -- comparing raw NWP vs. ensemble-blended
vs. corrected, split by regime and threshold.
"""


def run():
    """Run the full verification suite."""
    from src.verification.comparator import run_comparison

    print("  Running verification suite ...")
    run_comparison()
