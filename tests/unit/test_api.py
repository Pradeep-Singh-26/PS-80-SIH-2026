"""Unit tests for the FastAPI service."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
os.environ["CONFIG_PATH"] = str(ROOT / "config.test.yaml")

from fastapi.testclient import TestClient  # noqa: E402
from api.main import app  # noqa: E402

client = TestClient(app)


class TestHealthEndpoint:
    def test_health(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestRegimeEndpoints:
    def test_get_regime_valid_date(self):
        resp = client.get("/api/v1/regime/2024-06-15")
        assert resp.status_code == 200
        data = resp.json()
        assert "dominant_label" in data
        assert "confidence" in data
        assert 0 <= data["confidence"] <= 1

    def test_get_regime_invalid_date(self):
        resp = client.get("/api/v1/regime/2099-01-01")
        assert resp.status_code == 404

    def test_list_regimes(self):
        resp = client.get("/api/v1/regime")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_regimes_date_filter(self):
        resp = client.get("/api/v1/regime?start_date=2024-06-10&end_date=2024-06-15")
        assert resp.status_code == 200
        data = resp.json()
        assert all("2024-06-10" <= d["date"] <= "2024-06-15" for d in data)


class TestDistrictEndpoints:
    def test_get_districts_valid(self):
        resp = client.get("/api/v1/districts/2024-06-15")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "district_name" in data[0]
        assert "corrected_rainfall_mm" in data[0]

    def test_get_districts_invalid_date(self):
        resp = client.get("/api/v1/districts/2099-01-01")
        assert resp.status_code == 404

    def test_list_districts_filter(self):
        resp = client.get("/api/v1/districts?district_name=Pune")
        assert resp.status_code == 200
        data = resp.json()
        assert all(d["district_name"] == "Pune" for d in data)


class TestStationEndpoints:
    def test_get_stations_valid(self):
        resp = client.get("/api/v1/stations/2024-06-15")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_stations(self):
        resp = client.get("/api/v1/stations")
        assert resp.status_code == 200


class TestVerificationEndpoints:
    def test_verification_summary(self):
        resp = client.get("/api/v1/verification/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_fss_scores(self):
        resp = client.get("/api/v1/verification/fss")
        assert resp.status_code == 200

    def test_reliability(self):
        resp = client.get("/api/v1/verification/reliability")
        assert resp.status_code == 200


class TestAlertEndpoints:
    def test_get_alerts(self):
        resp = client.get("/api/v1/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_filter_alerts_by_severity(self):
        resp = client.get("/api/v1/alerts?severity=WARNING")
        assert resp.status_code == 200
        data = resp.json()
        assert all(a["severity"] == "WARNING" for a in data)


class TestFeedbackEndpoint:
    def test_submit_feedback(self):
        resp = client.post(
            "/api/v1/feedback",
            json={
                "date": "2024-06-15",
                "feedback_type": "regime_correction",
                "original_value": "active",
                "corrected_value": "break",
                "comment": "Test feedback",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert "feedback_id" in data


class TestCacheEndpoint:
    def test_invalidate_cache(self):
        resp = client.post("/api/v1/cache/invalidate")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cache_cleared"
