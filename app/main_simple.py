from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Mulajna Minimal Diagnostic")

@app.get("/")
async def root():
    return {"status": "minimal_online", "message": "The system is reachable at the hardware level.", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health():
    return {"status": "healthy"}
