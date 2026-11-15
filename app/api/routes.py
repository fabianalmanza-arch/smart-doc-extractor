from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.schemas.document import ExtractionResponse
from app.services.ai_extractor import (
    AIExtractionError,
    DocumentExtractorService,
    extractor_service,
)

# Inicializamos el limitador basado en la IP del cliente
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/v1", tags=["Document Extraction"])


def get_extractor_service() -> DocumentExtractorService:
    """Dependencia inyectable que facilita reemplazar el servicio en los tests."""
    return extractor_service


@router.get(
    "/health",
    summary="Verificar estado del servicio",
    status_code=status.HTTP_200_OK,
)
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }


@router.post(
    "/extract/cv",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extraer datos estructurados de una Hoja de Vida (PDF)",
    description=(
        "Sube un archivo PDF (máx. 5 MB). El sistema valida la integridad del archivo, "
        "lo procesa en memoria con IA y devuelve un JSON validado con Pydantic v2."
    ),
)
@limiter.limit(settings.RATE_LIMIT)
async def extract_cv_endpoint(
    request: Request,  # Requerido por slowapi para leer la IP del cliente
    file: UploadFile = File(..., description="Archivo PDF de la Hoja de Vida"),
    service: DocumentExtractorService = Depends(get_extractor_service),
) -> ExtractionResponse:
    # 1. Validación inicial de cabecera Content-Type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido. Únicamente se aceptan archivos PDF (application/pdf).",
        )

    # 2. Lectura asíncrona en memoria y validación de tamaño máximo
    file_bytes = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo enviado está vacío.",
        )

    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el límite permitido de {settings.MAX_FILE_SIZE_MB} MB.",
        )

    # 3. Validación de Magic Bytes (firma real de todo archivo PDF válido)
    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo está corrupto o no es un documento PDF auténtico.",
        )

    # 4. Llamada al servicio de extracción y traducción de errores de dominio a HTTP
    try:
        candidate_data, elapsed_ms = await service.extract_candidate_profile(
            file_bytes=file_bytes,
            mime_type="application/pdf",
        )
    except AIExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        ) from e

    return ExtractionResponse(
        filename=file.filename or "documento.pdf",
        processing_time_ms=elapsed_ms,
        data=candidate_data,
    )