"""Agent router: inventory, propose, approve, cancel, report, ask."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.paypal_client import get_client
from app.schemas import ApproveRequest
from app.security import get_current_user
from app.services import approvals, cancellations, qa, reports
from app.services.proposals import inventory, propose

router = APIRouter(tags=["agent"])


@router.get("/inventory")
def get_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client, _mode = get_client()
    return inventory(db, current_user, client)


@router.get("/propose")
def get_proposal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client, _mode = get_client()
    return propose(db, current_user, client)


@router.post("/approve")
def approve_subscriptions(
    payload: ApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    approved = approvals.approve(db, current_user, payload.subscription_ids)
    return {"approved": approved}


@router.post("/cancel")
def cancel_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client, _mode = get_client()
    return cancellations.cancel_approved(db, current_user, client)


@router.get("/report")
def get_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return reports.savings_report(db, current_user)


@router.get("/ask")
def ask_question(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client, _mode = get_client()
    return qa.ask(db, current_user, q, client=client)
