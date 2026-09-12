from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from api.api_router import api_router
from core.config import settings
import traceback

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Advanced Conversational Agentic RAG Chatbot API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()}
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
