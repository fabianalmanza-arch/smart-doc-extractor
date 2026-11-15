from typing import Optional
from pydantic import BaseModel, Field


class WorkExperience(BaseModel):
    role: str = Field(..., description="Cargo o título del puesto desempeñado")
    company: str = Field(..., description="Nombre de la empresa u organización")
    duration: str = Field(
        ..., description="Periodo de tiempo (ej. 'Ene 2023 - Actualidad' o '2 años')"
    )
    key_achievements: list[str] = Field(
        default_factory=list,
        description="Lista corta de hasta 3 logros o responsabilidades principales",
    )


class CandidateProfile(BaseModel):
    full_name: str = Field(..., description="Nombre completo del candidato")
    email: Optional[str] = Field(
        None, description="Correo electrónico de contacto si aparece en el documento"
    )
    phone: Optional[str] = Field(
        None, description="Número de teléfono si aparece en el documento"
    )
    location: Optional[str] = Field(
        None, description="Ciudad y país de residencia del candidato"
    )
    professional_summary: str = Field(
        ...,
        description="Resumen ejecutivo de 2 líneas sobre el perfil profesional del candidato",
    )
    years_of_experience: float = Field(
        ...,
        ge=0,
        description="Años totales aproximados de experiencia laboral relevante",
    )
    hard_skills: list[str] = Field(
        ...,
        description="Lista de habilidades técnicas, lenguajes, frameworks y herramientas",
    )
    languages: list[str] = Field(
        default_factory=list,
        description="Idiomas que domina el candidato y su nivel si se menciona",
    )
    experience: list[WorkExperience] = Field(
        default_factory=list,
        description="Historial laboral ordenado del más reciente al más antiguo",
    )
    seniority_level: str = Field(
        ...,
        description="Nivel estimado del perfil: 'Junior', 'Mid-Level', 'Senior' o 'Lead'",
    )


class ExtractionResponse(BaseModel):
    filename: str = Field(..., description="Nombre original del archivo PDF procesado")
    processing_time_ms: int = Field(
        ..., description="Tiempo que tomó la extracción en milisegundos"
    )
    data: CandidateProfile = Field(
        ..., description="Datos estructurados extraídos del documento"
    )