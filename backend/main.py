from fastapi import FastAPI

from app.api import applications, jobs, sessions
from app.db.init_db import init_db

app = FastAPI(title="Indeed Auto-Apply Backend")

app.include_router(sessions.router)
app.include_router(jobs.router)
app.include_router(applications.router)


@app.on_event("startup")
def on_startup():
    init_db()
