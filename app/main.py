
from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "env": os.getenv("ENVIRONMENT")}

@app.get("/")
async def root():
    return {"message": "Telegram Guardian Enterprise Running"}
