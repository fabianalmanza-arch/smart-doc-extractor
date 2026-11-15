# 📄 SmartDoc AI Extractor API

Microservicio de extracción estructurada de datos desde documentos PDF (Hojas de Vida / CVs) construido con **FastAPI**, **Pydantic v2** y **Google Gemini Structured Outputs**, acompañado de una interfaz web minimalista para pruebas instantáneas.

🔗 **Demo en vivo:** [https://smart-doc-extractor.onrender.com](https://smart-doc-extractor.onrender.com) *(Actualizar con tu link de Render)*  
📘 **Documentación Interactiva (Swagger UI):** `/docs`

---

## 🎯 Propósito del Proyecto

Las aplicaciones que integran Modelos de Lenguaje (LLMs) suelen fallar en producción cuando reciben texto no estructurado o respuestas impredecibles. Este proyecto demuestra cómo construir un pipeline backend resiliente que:

1. **Valida la integridad real de los archivos** antes de procesarlos (MIME type, tamaño máximo en RAM y firma de *Magic Bytes* `%PDF-`).
2. **Fuerza contratos de datos estrictos** mediante **Pydantic v2** y *Structured Outputs*, eliminando el parseo frágil de texto plano o bloques Markdown.
3. **Opera de forma 100% asíncrona (`async/await`)** en memoria sin escribir archivos temporales en disco.
4. **Implementa resiliencia y protección de recursos** mediante reintentos asíncronos ante errores `429`/`503`, fallback automático de modelo y *Rate Limiting* por IP.

---

## 🏗️ Arquitectura del Sistema

```text
┌─────────────────────┐      POST /api/v1/extract/cv      ┌──────────────────────────────┐
│  Frontend / Client  │ ────────────────────────────────► │       FastAPI Router         │
│  (UI Web / Swagger) │      (multipart/form-data PDF)    │  • Rate Limiter (slowapi)    │
└─────────────────────┘                                   │  • Magic Bytes & Size Check  │
                                                          └──────────────┬───────────────┘
                                                                         │ bytes en RAM
                                                                         ▼
┌─────────────────────┐      JSON estrictamente tipado    ┌──────────────────────────────┐
│  CandidateProfile   │ ◄──────────────────────────────── │   DocumentExtractorService   │
│   (Pydantic v2)     │      Structured Output Schema     │  • Cliente Asíncrono (.aio)  │
└─────────────────────┘                                   │  • Retry + Model Fallback    │
                                                          └──────────────┬───────────────┘
                                                                         │
                                                                         ▼
                                                          ┌──────────────────────────────┐
                                                          │      Google Gemini API       │
                                                          │  (gemini-3.8-flash / lite)   │
                                                          └──────────────────────────────┘

Estructura de Carpetas

smart-doc-extractor/
├── app/
│   ├── api/
│   │   └── routes.py          # Endpoints HTTP, inyección de dependencias y validaciones
│   ├── schemas/
│   │   └── document.py        # Modelos Pydantic v2 (contratos de entrada/salida)
│   ├── services/
│   │   └── ai_extractor.py    # Lógica de negocio desacoplada, reintentos y llamadas async
│   ├── static/
│   │   └── index.html         # Interfaz web interactiva (Tailwind CSS + Vanilla JS)
│   ├── config.py              # Gestión centralizada de variables con pydantic-settings
│   └── main.py                # Configuración de la app, CORS y manejadores de error
├── tests/
│   └── test_api.py            # Suite de pruebas con Pytest, TestClient y Mocks
├── Dockerfile                 # Imagen optimizada lista para despliegue en la nube
├── requirements.txt           # Dependencias fijadas
└── .env.example               # Plantilla de variables de entorno

Stack Tecnológico
Backend: Python 3.11, FastAPI, Uvicorn

Validación y Configuración: Pydantic v2, Pydantic Settings

IA & Structured Outputs: SDK oficial google-genai (interfaz asíncrona)

Seguridad y Resiliencia: slowapi (Rate Limiting), validación de Magic Bytes, Exponential Backoff

Testing: pytest, httpx, FastAPI TestClient con dependency_overrides

Frontend Demo: HTML5, Tailwind CSS, JavaScript Fetch API (Zero-build)

Despliegue: Docker

🚀 Ejecución Local
1. Clonar el repositorio e instalar dependencias
Bash
git clone [https://github.com/TU_USUARIO/smart-doc-extractor.git](https://github.com/TU_USUARIO/smart-doc-extractor.git)
cd smart-doc-extractor

python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / Mac:
source venv/bin/activate

pip install -r requirements.txt
2. Configurar variables de entorno
Crea un archivo .env basado en .env.example:

Fragmento de código
GEMINI_API_KEY=tu_clave_de_google_ai_studio
ENVIRONMENT=development
3. Iniciar el servidor
Bash
uvicorn app.main:app --reload
Interfaz Web: http://127.0.0.1:8000

Swagger UI: http://127.0.0.1:8000/docs

🧪 Ejecutar Pruebas Automatizadas
La suite de pruebas utiliza inyección de dependencias (app.dependency_overrides) para simular respuestas exitosas y fallos del proveedor externo sin consumir cuota real de la API:

Bash
pytest -v
📡 Ejemplo de Respuesta (POST /api/v1/extract/cv)
JSON
{
  "filename": "cv_desarrollador.pdf",
  "processing_time_ms": 1420,
  "data": {
    "full_name": "Fabian Desarrollador",
    "email": "fabian@ejemplo.com",
    "phone": "+57 300 000 0000",
    "location": "Colombia",
    "professional_summary": "Desarrollador Backend enfocado en Python, FastAPI y arquitecturas SaaS escalables.",
    "years_of_experience": 3.0,
    "hard_skills": ["Python", "FastAPI", "Pydantic", "Docker", "PostgreSQL"],
    "languages": ["Español (Nativo)", "Inglés (Intermedio)"],
    "experience": [
      {
        "role": "Full Stack / Backend Developer",
        "company": "Proyectos SaaS",
        "duration": "2023 - Actualidad",
        "key_achievements": [
          "Diseño e implementación de plataformas SaaS end-to-end."
        ]
      }
    ],
    "seniority_level": "Mid-Level"
  }
}