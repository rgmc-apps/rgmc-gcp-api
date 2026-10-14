"""Generic email-notification endpoint for internal services (e.g. Attribute Checker)."""
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

import src.services.send_mail as send_mail_service

notification_router = APIRouter(tags=["Notifications"])


class SendMailRequest(BaseModel):
    subject: str
    body: str
    recipients: Optional[List[str]] = None


@notification_router.post("/notifications/send-mail")
def send_mail(req: SendMailRequest):
    sent = send_mail_service.send_generic_mail(req.subject, req.body, req.recipients)
    return {"sent": sent}
