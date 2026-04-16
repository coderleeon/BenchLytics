from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.session import engine, Base
from api import routes
import logging

logging.basicConfig(level=logging.INFO)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Benchlytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Benchlytics Backend Running"}
