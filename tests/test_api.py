import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_extractor_service, limiter
from app.main import app
from app.schemas.document import CandidateProfile, WorkExperience
from app.services.ai_extractor import AIExtractionError

# Desactivamos el rate limiter durante los tests unitarios para no bloquear pruebas seguidas
limiter.enabled = False

client = TestClient(app)


# --- Mocks del Servicio de IA ---
class MockSuccessExtractorService:
    async def extract_candidate_profile(
        self, file_bytes: bytes, mime_type: str = "application/pdf"
    ) -> tuple[CandidateProfile, int]:
        fake_profile = CandidateProfile(
            full_name="Ana María Gómez",
            email="ana.gomez@ejemplo.com",
            phone="+57 300 123 4567",
            location="Bogotá, Colombia",
            professional_summary="Desarrolladora Backend especializada en Python y FastAPI con experiencia en microservicios.",
            years_of_experience=4.5,
            hard_skills=["Python", "FastAPI", "Docker", "PostgreSQL", "Pytest"],
            languages=["Español (Nativo)", "Inglés (B2)"],
            experience=[
                WorkExperience(
                    role="Backend Developer",
                    company="TechCorp",
                    duration="2022 - Actualidad",
                    key_achievements=[
                        "Redujo la latencia de la API en un 40% usando procesamiento asíncrono."
                    ],
                )
            ],
            seniority_level="Mid-Level",
        )
        return fake_profile, 120


class MockFailingExtractorService:
    async def extract_candidate_profile(
        self, file_bytes: bytes, mime_type: str = "application/pdf"
    ) -> tuple[CandidateProfile, int]:
        raise AIExtractionError("Simulación de caída del proveedor externo")


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    """Limpia las inyecciones de dependencias después de cada test."""
    yield
    app.dependency_overrides.clear()


# --- Casos de Prueba ---
def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_serves_frontend():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SmartDoc Extractor" in response.text


def test_extract_cv_success():
    app.dependency_overrides[get_extractor_service] = lambda: MockSuccessExtractorService()

    # Simulamos un PDF válido (debe comenzar con los magic bytes %PDF-)
    fake_pdf_content = b"%PDF-1.4\n%Contenido simulado de hoja de vida"
    files = {"file": ("cv_ana.pdf", fake_pdf_content, "application/pdf")}

    response = client.post("/api/v1/extract/cv", files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "cv_ana.pdf"
    assert body["processing_time_ms"] == 120
    assert body["data"]["full_name"] == "Ana María Gómez"
    assert "FastAPI" in body["data"]["hard_skills"]
    assert body["data"]["seniority_level"] == "Mid-Level"


def test_reject_non_pdf_mime_type():
    files = {"file": ("notas.txt", b"Hola mundo", "text/plain")}
    response = client.post("/api/v1/extract/cv", files=files)

    assert response.status_code == 400
    assert "Formato inválido" in response.json()["detail"]


def test_reject_fake_pdf_magic_bytes():
    # Archivo con extensión .pdf y MIME application/pdf, pero contenido falso
    files = {"file": ("virus.pdf", b"MZ\x90\x00EjecutableFalso", "application/pdf")}
    response = client.post("/api/v1/extract/cv", files=files)

    assert response.status_code == 422
    assert "no es un documento PDF auténtico" in response.json()["detail"]


def test_reject_empty_file():
    files = {"file": ("vacio.pdf", b"", "application/pdf")}
    response = client.post("/api/v1/extract/cv", files=files)

    assert response.status_code == 400
    assert "está vacío" in response.json()["detail"]


def test_handle_ai_provider_failure():
    app.dependency_overrides[get_extractor_service] = lambda: MockFailingExtractorService()

    fake_pdf_content = b"%PDF-1.4\n%Contenido valido"
    files = {"file": ("cv.pdf", fake_pdf_content, "application/pdf")}

    response = client.post("/api/v1/extract/cv", files=files)

    assert response.status_code == 502
    assert "Simulación de caída" in response.json()["detail"]