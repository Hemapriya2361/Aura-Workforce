from fastapi import FastAPI

app = FastAPI(title="Aura Workforce API")

@app.get("/health")
def health():
    return {"status": "ok"}
