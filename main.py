import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from pathlib import Path
from database import engine
import models
from routers import auth_router, branch_router, admin_router, user_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="대신증권 IT자산 매각 플랫폼")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "daishin-securities-2024-secret"))

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(auth_router.router)
app.include_router(branch_router.router, prefix="/branch")
app.include_router(admin_router.router, prefix="/admin")
app.include_router(user_router.router, prefix="/admin")


@app.get("/")
def root(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse("/login")
    role = request.session.get("role")
    if role == "branch":
        return RedirectResponse("/branch/dashboard")
    return RedirectResponse("/admin/dashboard")
