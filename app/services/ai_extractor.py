import asyncio
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.schemas.document import CandidateProfile


class AIExtractionError(Exception):
    """Excepción personalizada para errores controlados durante la extracción con IA."""
    pass


class DocumentExtractorService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        # Lista ordenada de modelos: principal + respaldo por si hay alta demanda
        self.models = ["gemini-3.8-flash", "gemini-3.8-flash-lite"]

    async def extract_candidate_profile(
        self, file_bytes: bytes, mime_type: str = "application/pdf"
    ) -> tuple[CandidateProfile, int]:
        """
        Envía los bytes del PDF de forma asíncrona a Gemini con reintentos automáticos
        y fallback de modelo ante picos de demanda.
        """
        start_time = time.perf_counter()

        prompt = (
            "Analiza este documento (Hoja de Vida / Currículum Vitae) y extrae toda la "
            "información profesional estructurada según el esquema solicitado. "
            "Si algún dato opcional como teléfono o correo no está presente, déjalo como null. "
            "Calcula los años totales de experiencia sumando los periodos laborales relevantes."
        )

        last_error: str = ""

        for model_name in self.models:
            # Hasta 2 intentos por modelo antes de pasar al de respaldo
            for attempt in range(2):
                try:
                    response = await self.client.aio.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(
                                data=file_bytes,
                                mime_type=mime_type,
                            ),
                            prompt,
                        ],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=CandidateProfile,
                            temperature=0.1,
                        ),
                    )

                    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                    if response.parsed is None:
                        raise AIExtractionError(
                            "El modelo no pudo estructurar el contenido del documento."
                        )

                    return response.parsed, elapsed_ms

                except APIError as e:
                    last_error = e.message
                    # Si es saturación temporal (503) o rate limit (429), esperamos y reintentamos
                    if e.code in (429, 503) and attempt == 0:
                        await asyncio.sleep(1.5)
                        continue
                    # Si vuelve a fallar, rompemos el ciclo interno para probar el modelo fallback
                    break
                except Exception as e:
                    raise AIExtractionError(
                        f"Error inesperado al procesar el documento: {str(e)}"
                    ) from e

        raise AIExtractionError(
            f"Todos los modelos de IA están saturados temporalmente. Detalle: {last_error}"
        )


extractor_service = DocumentExtractorService()