from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from api.api_router import api_router
from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Advanced Conversational Agentic RAG Chatbot API"
)

# CORS — always allow the Next.js dev server; extend via BACKEND_CORS_ORIGINS in .env
_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    *[str(o) for o in settings.BACKEND_CORS_ORIGINS],
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
