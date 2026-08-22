import os
import tempfile

from fastapi.testclient import TestClient

_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"
os.environ["APP_ENV"] = "test"

from app.main import app


def test_health_check_returns_service_metadata() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api", "version": "0.1.0"}


def test_platform_metadata_declares_data_foundation_phase() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/platform")

    assert response.status_code == 200
    assert response.json()["phase"] == "data-foundation"


def test_ingest_and_retrieve_a_tokenized_transaction() -> None:
    payload = {
        "external_reference": "test-transaction-001",
        "customer_id": "cust_test_001",
        "payment_token": "tok_test_12345678",
        "amount_paise": 49900,
        "payment_method": "upi",
        "merchant_category": "grocery",
        "status": "captured",
        "occurred_at": "2026-08-21T10:00:00Z",
        "device_id": "device_test_01",
        "ip_hash": "test-hash-not-an-ip",
    }
    with TestClient(app) as client:
        created = client.post("/api/v1/transactions", json=payload)

        assert created.status_code == 201
        transaction_id = created.json()["id"]
        retrieved = client.get(f"/api/v1/transactions/{transaction_id}")

    assert retrieved.status_code == 200
    assert retrieved.json()["payment_token"] == payload["payment_token"]


def test_rejects_raw_card_number_fields() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/transactions",
            json={"card_number": "4111111111111111"},
        )

    assert response.status_code == 422


def test_risk_assessment_contains_explainable_components() -> None:
    payload = {
        "external_reference": "test-transaction-risk-001",
        "customer_id": "cust_risk_test_001",
        "payment_token": "tok_risk_test_12345678",
        "amount_paise": 999900,
        "payment_method": "card",
        "merchant_category": "electronics",
        "status": "captured",
        "occurred_at": "2026-08-21T11:00:00Z",
        "device_id": "device_risk_test_01",
        "ip_hash": "risk-test-hash",
    }
    with TestClient(app) as client:
        created = client.post("/api/v1/transactions", json=payload)
        assessment = client.post(f"/api/v1/transactions/{created.json()['id']}/assessments")

    assert assessment.status_code == 201
    result = assessment.json()
    assert 0 <= result["risk_score"] <= 100
    assert result["decision"] in {"allow", "manual_review", "block"}
    assert "ml_probability" in result
    assert result["reasons"]


def test_trains_a_synthetic_logistic_baseline() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/models/train", json={"sample_count": 200, "seed": 7})

    assert response.status_code == 201
    assert response.json()["algorithm"] == "logistic_regression_gradient_descent"


def test_analyst_review_captures_feedback_and_dashboard_metrics() -> None:
    payload = {
        "external_reference": "test-transaction-review-001",
        "customer_id": "cust_review_test_001",
        "payment_token": "tok_review_test_12345678",
        "amount_paise": 49900,
        "payment_method": "upi",
        "merchant_category": "grocery",
        "status": "captured",
        "occurred_at": "2026-08-21T12:00:00Z",
    }
    with TestClient(app) as client:
        transaction = client.post("/api/v1/transactions", json=payload).json()
        client.post(f"/api/v1/transactions/{transaction['id']}/assessments")
        review = client.post(
            f"/api/v1/transactions/{transaction['id']}/reviews",
            json={
                "decision": "allow",
                "outcome_label": "legitimate",
                "analyst_id": "analyst_demo",
                "notes": "Verified as a known returning customer.",
            },
        )
        summary = client.get("/api/v1/dashboard/summary")
        distribution = client.get("/api/v1/dashboard/risk-distribution")

    assert review.status_code == 201
    assert review.json()["outcome_label"] == "legitimate"
    assert summary.status_code == 200
    assert summary.json()["total_transactions"] >= 1
    assert distribution.status_code == 200
    assert len(distribution.json()["buckets"]) == 3


def test_mock_agent_returns_evidence_bounded_recommendation() -> None:
    payload = {
        "external_reference": "test-transaction-agent-001",
        "customer_id": "cust_agent_test_001",
        "payment_token": "tok_agent_test_12345678",
        "amount_paise": 999900,
        "payment_method": "card",
        "merchant_category": "electronics",
        "status": "captured",
        "occurred_at": "2026-08-21T13:00:00Z",
        "device_id": "device_agent_test_01",
    }
    with TestClient(app) as client:
        transaction = client.post("/api/v1/transactions", json=payload).json()
        client.post(f"/api/v1/transactions/{transaction['id']}/assessments")
        investigation = client.post(
            f"/api/v1/transactions/{transaction['id']}/investigations", json={"provider": "mock"}
        )

    assert investigation.status_code == 201
    result = investigation.json()
    assert result["provider"] == "mock"
    assert result["recommendation"] in {"allow", "manual_review", "block"}
    assert set(result["evidence"]) == {
        "transaction",
        "risk_assessment",
        "customer_history",
        "device_context",
        "policy",
    }
    assert result["limitations"]


def test_cors_allows_localhost_dev_ports() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/transactions",
            headers={
                "Origin": "http://localhost:5174",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5174"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_cors_rejects_non_localhost_origins() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/transactions",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_database_initialisation_does_not_drop_existing_tables(monkeypatch) -> None:
    from app.db import database as db_module

    def fail_drop(*args, **kwargs):
        raise AssertionError("drop_all should not run during initialise_database")

    monkeypatch.setattr(db_module.Base.metadata, "drop_all", fail_drop)
    called = {"create": False}

    def record_create(*args, **kwargs):
        called["create"] = True

    monkeypatch.setattr(db_module.Base.metadata, "create_all", record_create)
    db_module.initialise_database()

    assert called["create"] is True
