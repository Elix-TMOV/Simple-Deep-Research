from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ai_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_routes.router, prefix="/api/ai", tags=["AI"])