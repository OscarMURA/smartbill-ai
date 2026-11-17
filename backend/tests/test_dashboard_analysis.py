from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base
from app.database.seed import seed_synthetic_invoices
from app.database.session import get_db
from app.main import app


def test_demo_dashboard_and_analysis_agree() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db:
        rows = seed_synthetic_invoices(db)
        november_id = rows[-1].id

    def override_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            dashboard_response = client.get("/api/dashboard")
            analysis_response = client.get(f"/api/invoices/{november_id}/analysis")
        assert dashboard_response.status_code == 200
        assert analysis_response.status_code == 200
        dashboard = dashboard_response.json()
        assert len(dashboard["invoices"]) == 6
        assert dashboard["series"][-1]["consumption_m3"] == 32
        assert dashboard["series"][-1]["total_cop"] == 88000
        assert analysis_response.json()["variation_percentage"] == 45.45
        assert dashboard["latest_analysis"] == analysis_response.json()
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
