import smtplib
from email.message import EmailMessage
import os

def send_reset_email(dest_email: str, reset_link: str):
    EMAIL_FROM = os.getenv("EMAIL_FROM")
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")

    msg = EmailMessage()
    msg["Subject"] = "Recuperação de senha - Wondercom"
    msg["From"] = EMAIL_FROM
    msg["To"] = dest_email
    msg.set_content(f"""
Olá!

Recebemos uma solicitação para redefinir sua senha.

Clique no link abaixo para criar uma nova senha (válido por 1 hora):

{reset_link}

Se você não solicitou, ignore este e-mail.

ZincoApp
""")

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
