from fastapi import FastAPI

from app.api import departments, employees
from app.core.errors import register_error_handlers

app = FastAPI(title="Aura Workforce API", version="0.1.0")

register_error_handlers(app)
app.include_router(employees.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}