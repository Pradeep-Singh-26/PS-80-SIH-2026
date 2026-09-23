"""Unit tests for verification metrics."""

import os
import sys
from pathlib import Path

import pytest
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
os.environ["CONFIG_PATH"] = str(ROOT / "config.test.yaml")

from src.verification.metrics import (
    rmse,
    bias,
    mae,
    contingency_table,
    pod,
    far,
    csi,
    ets,
    fss,
    reliability_data,
)


class TestContinuousMetrics:
    def test_rmse_perfect(self):
        obs = np.array([1.0, 2.0, 3.0])
        assert rmse(obs, obs) == pytest.approx(0.0)

    def test_rmse_known(self):
        obs = np.array([0.0, 0.0, 0.0])
        fcst = np.array([1.0, 1.0, 1.0])
        assert rmse(obs, fcst) == pytest.approx(1.0)

    def test_bias_positive(self):
        obs = np.array([10.0, 20.0])
        fcst = np.array([15.0, 25.0])
        assert bias(obs, fcst) == pytest.approx(5.0)

    def test_bias_zero(self):
        obs = np.array([10.0, 20.0])
        assert bias(obs, obs) == pytest.approx(0.0)

    def test_mae(self):
        obs = np.array([0.0, 0.0])
        fcst = np.array([3.0, -3.0])
        assert mae(obs, fcst) == pytest.approx(3.0)


class TestContingencyTable:
    def test_perfect_forecast(self):
        obs = np.array([100.0, 50.0, 10.0, 5.0])
        ct = contingency_table(obs, obs, threshold=64.5)
        assert ct["hits"] == 1
        assert ct["misses"] == 0
        assert ct["false_alarms"] == 0
        assert ct["correct_negatives"] == 3

    def test_pod_perfect(self):
        ct = {"hits": 10, "misses": 0, "false_alarms": 2, "correct_negatives": 5, "total": 17}
        assert pod(ct) == pytest.approx(1.0)

    def test_pod_zero(self):
        ct = {"hits": 0, "misses": 10, "false_alarms": 0, "correct_negatives": 5, "total": 15}
        assert pod(ct) == pytest.approx(0.0)

    def test_far_zero(self):
        ct = {"hits": 10, "misses": 0, "false_alarms": 0, "correct_negatives": 5, "total": 15}
        assert far(ct) == pytest.approx(0.0)

    def test_csi_perfect(self):
        ct = {"hits": 10, "misses": 0, "false_alarms": 0, "correct_negatives": 5, "total": 15}
        assert csi(ct) == pytest.approx(1.0)

    def test_ets_range(self):
        ct = {"hits": 5, "misses": 3, "false_alarms": 2, "correct_negatives": 10, "total": 20}
        score = ets(ct)
        assert -1.0 / 3 <= score <= 1.0


class TestFSS:
    def test_fss_perfect(self):
        obs = np.ones((10, 10)) * 100
        assert fss(obs, obs, threshold=50, neighborhood_radius=1) == pytest.approx(1.0)

    def test_fss_zero_fields(self):
        obs = np.zeros((10, 10))
        fcst = np.zeros((10, 10))
        # Both zero => FSS = 1.0 (no events, perfect match)
        assert fss(obs, fcst, threshold=50, neighborhood_radius=1) == pytest.approx(1.0)

    def test_fss_range(self):
        np.random.seed(42)
        obs = np.random.uniform(0, 100, (10, 10))
        fcst = np.random.uniform(0, 100, (10, 10))
        score = fss(obs, fcst, threshold=50, neighborhood_radius=2)
        assert 0.0 <= score <= 1.0


class TestReliability:
    def test_reliability_bins(self):
        obs = np.array([100.0, 50.0, 10.0, 80.0])
        prob = np.array([0.9, 0.3, 0.1, 0.7])
        rel = reliability_data(obs, prob, threshold=64.5, n_bins=5)
        assert len(rel["bin_centers"]) == 5
        assert len(rel["observed_frequency"]) == 5
        assert len(rel["counts"]) == 5
