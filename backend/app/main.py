from fastapi import FastAPI

from app.health import check_services

app = FastAPI(title="AI Media Studio")


@app.get("/health")
def health():
    return check_services()
