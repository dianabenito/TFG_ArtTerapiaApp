import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure the backend folder (parent of tests) is on sys.path so `import app` works
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app.main as main
import app.database as database
import app.models as models
import app.dependencies as dependencies
import app.crud as crud
import app.schemas as schemas
from datetime import datetime, timedelta


TEST_DATABASE_URL = "sqlite:///:memory:"


# Use StaticPool so the in-memory SQLite DB is shared across connections/threads
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def initialized_app():
    # create tables
    models.Base.metadata.create_all(bind=engine)
    # override dependency
    main.app.dependency_overrides[dependencies.get_db] = override_get_db
    # ensure websocket module uses the testing sessionmaker as well
    try:
        import app.api.ws as ws_module
        ws_module.SessionLocal = TestingSessionLocal
    except Exception:
        pass
    client = TestClient(main.app)

    # create sample users and a session
    db = TestingSessionLocal()
    try:
        # create patient and therapist using CRUD directly (bypass password strength issues by valid password)
        patient_in = schemas.UserCreate(email="patient@example.com", full_name="Paciente Prueba", password="Password1!", type=schemas.UserType.patient)
        therapist_in = schemas.UserCreate(email="therapist@example.com", full_name="Terapeuta Prueba", password="Password1!", type=schemas.UserType.therapist)
        patient = crud.user.create_user(db, patient_in)
        therapist = crud.user.create_user(db, therapist_in)

        # Do not create a default session here; tests create sessions as needed to keep isolation
    finally:
        db.close()

    yield client


@pytest.fixture()
def client(initialized_app):
    return initialized_app
