"""Shared email utilities for the application."""
from __future__ import annotations

import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

def send_email(subject: str, html_body: str, to_email: str = None) -> bool:
    """Send an HTML email using GMAIL_USER and GMAIL_PASSWORD environment variables."""
    smtp_user = os.getenv("GMAIL_USER")
    smtp_password = os.getenv("GMAIL_PASSWORD")
    if not to_email:
        to_email = os.getenv("GMAIL_RECIPIENT", "sergey.pochikovskiy@gmail.com")

    if not smtp_user or not smtp_password:
        logger.error("Missing GMAIL_USER or GMAIL_PASSWORD env vars.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [to_email], msg.as_string())

        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
