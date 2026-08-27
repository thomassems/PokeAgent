from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="PokeAgent API")


class Health(BaseModel):
    status: str
    service: str


# Routes carry the /api prefix in the path itself rather than relying on a mount
# point. The same URL then resolves through the Next.js dev proxy and through the
# Vercel rewrite, whose post-rewrite path handling is not yet confirmed.
@app.get("/api/health")
def health() -> Health:
    return Health(status="ok", service="pokeagent-backend")
