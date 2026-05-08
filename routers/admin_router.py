from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from auth import require_admin
from config import templates
from datetime import datetime

router = APIRouter()

IN_PROGRESS_STATUSES = ["approved", "scheduled", "schedule_confirmed", "collected", "priced"]


def _check(request: Request):
    user = require_admin(request)
    if not user:
        return None, RedirectResponse("/login", status_code=302)
    return user, None


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user, redir = _check(request)
    if redir:
        return redir

    total = db.query(models.Application).count()
    submitted = db.query(models.Application).filter(models.Application.status == "submitted").count()
    in_progress = db.query(models.Application).filter(models.Application.status.in_(IN_PROGRESS_STATUSES)).count()
    completed = db.query(models.Application).filter(
        models.Application.status.in_(["branch_confirmed", "completed"])
    ).count()
    recent = (
        db.query(models.Application)
        .order_by(models.Application.updated_at.desc())
        .limit(10)
        .all()
    )

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "session": request.session,
            "total": total,
            "submitted": submitted,
            "in_progress": in_progress,
            "completed": completed,
            "recent": recent,
        },
    )


@router.get("/applications", response_class=HTMLResponse)
def application_list(request: Request, status: str = "", db: Session = Depends(get_db)):
    user, redir = _check(request)
    if redir:
        return redir

    query = db.query(models.Application)
    if status:
        query = query.filter(models.Application.status == status)
    applications = query.order_by(models.Application.updated_at.desc()).all()

    return templates.TemplateResponse(
        "admin/application_list.html",
        {
            "request": request,
            "session": request.session,
            "applications": applications,
            "current_status": status,
        },
    )


@router.get("/applications/{app_id}", response_class=HTMLResponse)
def application_detail(request: Request, app_id: int, db: Session = Depends(get_db)):
    user, redir = _check(request)
    if redir:
        return redir

    app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app:
        return RedirectResponse("/admin/applications", status_code=302)

    return templates.TemplateResponse(
        "admin/application_detail.html",
        {"request": request, "session": request.session, "app": app},
    )


@router.post("/applications/{app_id}/approve")
def approve(request: Request, app_id: int, db: Session = Depends(get_db)):
    user, redir = _check(request)
    if redir:
        return redir
    if user["role"] != "coretail":
        return RedirectResponse(f"/admin/applications/{app_id}", status_code=302)

    app = db.query(models.Application).filter(
        models.Application.id == app_id,
        models.Application.status == "submitted",
    ).first()
    if app:
        app.status = "approved"
        app.approved_at = datetime.now()
        app.updated_at = datetime.now()
        db.commit()

    return RedirectResponse(f"/admin/applications/{app_id}", status_code=302)


@router.post("/applications/{app_id}/schedule")
async def set_schedule(request: Request, app_id: int, db: Session = Depends(get_db)):
    user, redir = _check(request)
    if redir:
        return redir
    if user["role"] != "coretail":
        return RedirectResponse(f"/admin/applications/{app_id}", status_code=302)

    form = await request.form()

    app = db.query(models.Application).filter(
        models.Application.id == app_id,
        models.Application.status == "approved",
    ).first()

    if app:
        if not app.schedule:
            sched = models.VisitSchedule(application_id=app_id)
            db.add(sched)
            db.flush()
            db.refresh(app)

        app.schedule.visit_date = form.get("visit_date", "")
        app.schedule.visit_time = form.get("visit_time", "")
        app.schedule.collector_name = form.get("collector_name", "")
        app.schedule.collector_phone = form.get("collector_phone", "")
        app.schedule.notes = form.get("notes", "")
        app.status = "scheduled"
        app.updated_at = datetime.now()
        db.commit()

    return RedirectResponse(f"/admin/applications/{app_id}", status_code=302)


@router.post("/applications/{app_id}/collect")
def mark_collected(request: Request, app_id: int, db: Session = Depends(get_db)):
    user, redir = _check(request)
    if redir:
        return redir
    if user["role"] != "coretail":
        return RedirectResponse(f"/admin/applications/{app_id}", status_code=302)

    app = db.query(models.Application).filter(
        models.Application.id == app_id,
        models.Application.status == "schedule_confirmed",
    ).first()
    if app:
        app.status = "collected"
        app.updated_at = datetime.now()
        db.commit()

    return RedirectResponse(f"/admin/applications/{app_id}", status_code=302)


@router.post("/applications/{app_id}/pricing")
async def set_pricing(request: Request, app_id: int, db: Session = Depends(get_db)):
    user, redir = _check(request)
    if redir:
        return redir
    if user["role"] != "coretail":
        return RedirectResponse(f"/admin/applications/{app_id}", status_code=302)

    form = await request.form()

    app = db.query(models.Application).filter(
        models.Application.id == app_id,
        models.Application.status == "collected",
    ).first()

    if app:
        total = 0.0
        for asset in app.assets:
            key = f"price_{asset.id}"
            try:
                price = float(form.get(key, 0) or 0)
            except ValueError:
                price = 0.0
            asset.unit_price = price
            total += price * asset.quantity

        if not app.settlement:
            settlement = models.Settlement(application_id=app_id)
            db.add(settlement)
            db.flush()
            db.refresh(app)

        app.settlement.total_amount = total
        app.settlement.pricing_notes = form.get("pricing_notes", "")
        app.status = "priced"
        app.updated_at = datetime.now()
        db.commit()

    return RedirectResponse(f"/admin/applications/{app_id}", status_code=302)


@router.post("/applications/{app_id}/complete")
def complete_payment(request: Request, app_id: int, db: Session = Depends(get_db)):
    user, redir = _check(request)
    if redir:
        return redir
    if user["role"] != "welfare":
        return RedirectResponse(f"/admin/applications/{app_id}", status_code=302)

    app = db.query(models.Application).filter(
        models.Application.id == app_id,
        models.Application.status == "branch_confirmed",
    ).first()

    if app and app.settlement:
        app.settlement.welfare_confirmed = True
        app.settlement.welfare_confirmed_at = datetime.now()
        app.settlement.payment_confirmed = True
        app.settlement.payment_date = datetime.now().strftime("%Y-%m-%d")
        app.status = "completed"
        app.updated_at = datetime.now()
        db.commit()

    return RedirectResponse(f"/admin/applications/{app_id}", status_code=302)
