import uvicorn
import os
from app.main import app
from app.core.logging import setup_logging

if __name__ == "__main__":
    setup_logging()
    port = int(os.getenv("PORT", 8000))
    # API only requires 1 worker in many cloud envs, but can scale vertically
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False, workers=1)
