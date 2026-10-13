from fastapi import FastAPI

app = FastAPI(title="Aura Workforce API")

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
