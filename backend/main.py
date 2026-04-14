from fastapi import FastAPI
import uvicorn

from backend.api.main import app

@app.get("/")
def home() -> dict:
    return {"message": "Skill AI Platform Running"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)