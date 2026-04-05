import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes.auth_routes import router as auth_router
from app.routes.patient_routes import router as patient_router
from app.routes.explain_routes import router as explain_router, set_rag_service
from app.services.rag_service import RAGService
from app.models.schemas import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rag_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs on startup
    global rag_service
    logger.info("starting backend")

    rag_service = RAGService()
    set_rag_service(rag_service)

    mode = "rag active" if rag_service.ready else "fallback mode"
    logger.info(f"backend ready ({mode})")
    yield
    # runs on shutdown
    logger.info("shutting down")


app = FastAPI(
    title="Health Literacy Assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

# let the frontend talk to us
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(patient_router)
app.include_router(explain_router)


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        backend=True,
        database=True,
        rag_ready=rag_service.ready if rag_service else False,
    )


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
