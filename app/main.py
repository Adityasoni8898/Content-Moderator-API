from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import utils
from .routers import users, auth, moderate, analytics

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

app.include_router(users.router, prefix="/api/v1", tags=["User"])
app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(moderate.router, prefix="/api/v1", tags=["Moderate"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])

@app.get("/api")
def root():
    return {"message": "Welcome to the Content Moderation API!"}