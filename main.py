from fastapi import FastAPI
from database import engine, Base
from routers import analyze

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(analyze.router)

@app.get("/")
def home():
    return {"message": "ClearHire V2 backend is running"}