"""Alert dispatch: email (SMTP) + Telegram + Discord webhook + local file.

Reads credentials from environment variables. Degrades gracefully — if no
channel is configured, alerts are written to logs/alerts.log.

Env vars:
  WT_SMTP_HOST, WT_SMTP_PORT, WT_SMTP_USER, WT_SMTP_PASS,
  WT_ALERT_EMAIL_TO (comma-separated)
  WT_TELEGRAM_BOT_TOKEN, WT_TELEGRAM_CHAT_ID
  WT_DISCORD_WEBHOOK_URL
"""
from __future__ import annotations
import os, smtplib, json, urllib.request, ssl, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "alerts.log")

def _append_log(text: str):
    try:
        os.makedirs(os.path.abspath(os.path.join(LOG_PATH, "..")), exist_ok=True)
        with open(os.path.abspath(LOG_PATH), "a") as f:
            f.write(f"########## {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ##########\n{text}\n\n")
    except Exception:
        pass

def send_email(subject: str, body: str) -> tuple[bool, str]:
    host = os.environ.get("WT_SMTP_HOST")
    port = int(os.environ.get("WT_SMTP_PORT", "587"))
    user = os.environ.get("WT_SMTP_USER")
    pwd = os.environ.get("WT_SMTP_PASS")
    to = os.environ.get("WT_ALERT_EMAIL_TO")
    if not all([host, user, pwd, to]):
        return False, "email not configured"
    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.starttls(context=ctx)
            s.login(user, pwd)
            s.sendmail(user, [x.strip() for x in to.split(",") if x.strip()], msg.as_string())
        return True, "ok"
    except Exception as e:
        return False, f"email error: {e}"

def send_telegram(text: str) -> tuple[bool, str]:
    tok = os.environ.get("WT_TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("WT_TELEGRAM_CHAT_ID")
    if not tok or not chat:
        return False, "telegram not configured"
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    data = json.dumps({"chat_id": chat, "text": text, "parse_mode": "Markdown",
                       "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=15)
        return True, "ok"
    except Exception as e:
        return False, f"telegram error: {e}"

def send_discord(text: str) -> tuple[bool, str]:
    url = os.environ.get("WT_DISCORD_WEBHOOK_URL")
    if not url:
        return False, "discord not configured"
    data = json.dumps({"content": text[:1900]}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=15)
        return True, "ok"
    except Exception as e:
        return False, f"discord error: {e}"

def dispatch(subject: str, body: str) -> dict:
    """Send to all configured channels. Always logs locally."""
    _append_log(f"SUBJECT: {subject}\n{body}")
    out = {}
    out["email"] = send_email(subject, body)
    out["telegram"] = send_telegram(f"*{subject}*\n\n{body}")
    out["discord"] = send_discord(f"**{subject}**\n\n{body}")
    return out

if __name__ == "__main__":
    # smoke test — uses configured channels or just logs locally
    r = dispatch("world-trader alert smoke test",
                 "This is a test alert from wt/alerts.py.\nIf you see this, alerting works.")
    print(json.dumps(r, indent=2))
    print(f"Log written to {os.path.abspath(LOG_PATH)}")
