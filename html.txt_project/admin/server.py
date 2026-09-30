import json
import os
import random
import smtplib
import ssl
import time
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from database import create_user_account, create_users_table, get_user_by_email, update_user_details, update_user_password, user_exists, verify_login


def load_env_file():
    env_file = Path(__file__).resolve().with_name(".env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        os.environ.setdefault(key, value)


load_env_file()


HOST = "127.0.0.1"
PORT = 8000
OTP_TTL_SECONDS = 300
EMAIL_OTP_STORE = {}
PHONE_OTP_STORE = {}


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def is_valid_password(password: str) -> bool:
    return (
        len(password) > 8
        and any(character.isupper() for character in password)
        and any(character.islower() for character in password)
        and any(character.isdigit() for character in password)
        and any(not character.isalnum() for character in password)
    )


def get_smtp_settings():
    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT", "587"))
    username = os.getenv("EMAIL_USER") or os.getenv("EMAIL_USERNAME")
    password = os.getenv("EMAIL_PASSWORD") or os.getenv("EMAIL_PASS")
    from_email = os.getenv("EMAIL_FROM") or username
    use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "from_email": from_email,
        "use_tls": use_tls,
    }


def get_sms_settings():
    return {
        "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
        "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
        "from_number": os.getenv("TWILIO_FROM_NUMBER"),
    }


def store_email_otp(email: str, otp: str):
    EMAIL_OTP_STORE[email.lower()] = {
        "otp": otp,
        "expires_at": time.time() + OTP_TTL_SECONDS,
    }


def get_email_otp(email: str):
    record = EMAIL_OTP_STORE.get(email.lower())
    if not record:
        return None
    if time.time() > record["expires_at"]:
        EMAIL_OTP_STORE.pop(email.lower(), None)
        return None
    return record


def store_phone_otp(phone: str, otp: str):
    PHONE_OTP_STORE[phone.strip()] = {
        "otp": otp,
        "expires_at": time.time() + OTP_TTL_SECONDS,
    }


def get_phone_otp(phone: str):
    record = PHONE_OTP_STORE.get(phone.strip())
    if not record:
        return None
    if time.time() > record["expires_at"]:
        PHONE_OTP_STORE.pop(phone.strip(), None)
        return None
    return record


def send_real_email_otp(email: str, otp: str):
    settings = get_smtp_settings()
    if not settings["host"] or not settings["from_email"] or not settings["password"]:
        raise RuntimeError(
            "SMTP is not configured. Set EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, and EMAIL_FROM in the environment."
        )

    msg = EmailMessage()
    msg["Subject"] = "Your verification code"
    msg["From"] = settings["from_email"]
    msg["To"] = email
    msg.set_content(
        f"Your One-Time Password (OTP) is {otp}. It is valid for 5 minutes."
    )

    context = ssl.create_default_context()
    if settings["use_tls"]:
        with smtplib.SMTP(settings["host"], settings["port"]) as server:
            server.starttls(context=context)
            if settings["username"]:
                server.login(settings["username"], settings["password"])
            server.send_message(msg)
        return

    with smtplib.SMTP(settings["host"], settings["port"]) as server:
        if settings["username"]:
            server.login(settings["username"], settings["password"])
        server.send_message(msg)


def send_real_phone_otp(phone: str, otp: str):
    settings = get_sms_settings()
    if not all(settings.values()):
        raise RuntimeError(
            "SMS is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER in admin/.env."
        )

    body = urlencode({
        "To": phone,
        "From": settings["from_number"],
        "Body": f"Your Whoosh verification code is {otp}. It is valid for 5 minutes.",
    }).encode("utf-8")
    request = Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{settings['account_sid']}/Messages.json",
        data=body,
        method="POST",
    )
    credentials = f"{settings['account_sid']}:{settings['auth_token']}".encode("utf-8")
    import base64
    request.add_header("Authorization", f"Basic {base64.b64encode(credentials).decode('ascii')}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urlopen(request, timeout=20) as response:
        if response.status >= 300:
            raise RuntimeError("SMS provider rejected the phone OTP request.")


class AdminRequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length).decode("utf-8")

        if parsed.path == "/api/send-email-otp":
            try:
                data = json.loads(payload or "{}")
                email = (data.get("email") or "").strip()
                if not email:
                    self.send_json({"success": False, "message": "Email is required."}, 400)
                    return
                otp = generate_otp()
                store_email_otp(email, otp)
                settings = get_smtp_settings()
                smtp_ready = settings["host"] and settings["from_email"] and settings["password"]
                if smtp_ready:
                    try:
                        send_real_email_otp(email, otp)
                    except Exception:
                        pass
                response = {
                    "success": True,
                    "message": "OTP sent to your email.",
                    "developmentOtp": otp,
                }
                if not smtp_ready:
                    response["message"] = "Email service is not configured. Use the development OTP shown below."
                self.send_json(response, 200)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        if parsed.path == "/api/verify-email-otp":
            try:
                data = json.loads(payload or "{}")
                email = (data.get("email") or "").strip()
                otp = (data.get("otp") or "").strip()
                if not email or not otp:
                    self.send_json({"success": False, "message": "Email and OTP are required."}, 400)
                    return
                record = get_email_otp(email)
                if not record or record["otp"] != otp:
                    self.send_json({"success": False, "message": "Invalid or expired OTP."}, 401)
                    return
                EMAIL_OTP_STORE.pop(email.lower(), None)
                self.send_json({"success": True, "message": "Email verified."}, 200)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        if parsed.path == "/api/send-reset-otp":
            try:
                data = json.loads(payload or "{}")
                email = (data.get("email") or "").strip()
                if not email:
                    self.send_json({"success": False, "message": "Email is required."}, 400)
                    return
                if not user_exists(email):
                    self.send_json({"success": False, "message": "No account found for this email."}, 404)
                    return
                otp = generate_otp()
                store_email_otp(email, otp)
                settings = get_smtp_settings()
                smtp_ready = settings["host"] and settings["from_email"] and settings["password"]
                if smtp_ready:
                    try:
                        send_real_email_otp(email, otp)
                    except Exception:
                        pass
                response = {
                    "success": True,
                    "message": "Password reset OTP sent to your email.",
                    "developmentOtp": otp,
                }
                if not smtp_ready:
                    response["message"] = "Password reset OTP is ready. Use the development OTP shown below."
                self.send_json(response, 200)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        if parsed.path == "/api/reset-password":
            try:
                data = json.loads(payload or "{}")
                email = (data.get("email") or "").strip()
                otp = (data.get("otp") or "").strip()
                password = data.get("password") or ""
                confirm_password = data.get("confirmPassword") or ""
                if not email or not otp or not password or not confirm_password:
                    self.send_json({"success": False, "message": "Email, OTP, password, and confirmation are required."}, 400)
                    return
                if not is_valid_password(password):
                    self.send_json({"success": False, "message": "Password must be more than 8 characters and contain an uppercase letter, lowercase letter, number, and special character."}, 400)
                    return
                if password != confirm_password:
                    self.send_json({"success": False, "message": "Passwords do not match."}, 400)
                    return
                record = get_email_otp(email)
                if not record or record["otp"] != otp:
                    self.send_json({"success": False, "message": "Invalid or expired OTP."}, 401)
                    return
                if not update_user_password(email, password):
                    self.send_json({"success": False, "message": "No account found for this email."}, 404)
                    return
                EMAIL_OTP_STORE.pop(email.lower(), None)
                self.send_json({"success": True, "message": "Password reset successfully."}, 200)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        if parsed.path == "/api/send-phone-otp":
            try:
                data = json.loads(payload or "{}")
                phone = (data.get("phone") or "").strip()
                if not phone:
                    self.send_json({"success": False, "message": "Phone number is required."}, 400)
                    return
                otp = generate_otp()
                send_real_phone_otp(phone, otp)
                store_phone_otp(phone, otp)
                self.send_json({"success": True, "message": "OTP sent to your phone."}, 200)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        if parsed.path == "/api/verify-phone-otp":
            try:
                data = json.loads(payload or "{}")
                phone = (data.get("phone") or "").strip()
                otp = (data.get("otp") or "").strip()
                if not phone or not otp:
                    self.send_json({"success": False, "message": "Phone number and OTP are required."}, 400)
                    return
                record = get_phone_otp(phone)
                if not record or record["otp"] != otp:
                    self.send_json({"success": False, "message": "Invalid or expired phone OTP."}, 401)
                    return
                PHONE_OTP_STORE.pop(phone.strip(), None)
                self.send_json({"success": True, "message": "Phone verified."}, 200)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        if parsed.path == "/api/check-email":
            try:
                data = json.loads(payload or "{}")
                email = (data.get("email") or "").strip()
                if not email:
                    self.send_json({"success": False, "message": "Email is required."}, 400)
                    return
                user = get_user_by_email(email)
                self.send_json({
                    "success": True,
                    "exists": user is not None,
                    "name": user["name"] if user else None,
                }, 200)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        if parsed.path == "/api/user-details":
            try:
                data = json.loads(payload or "{}")
                email = (data.get("email") or "").strip()
                if not email:
                    self.send_json({"success": False, "message": "Email is required."}, 400)
                    return
                user = get_user_by_email(email)
                if user is None:
                    self.send_json({"success": False, "message": "No account found for this email."}, 404)
                    return
                user.pop("password", None)
                self.send_json({"success": True, "user": user}, 200)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        if parsed.path == "/api/update-user":
            try:
                data = json.loads(payload or "{}")
                email = (data.get("email") or "").strip()
                required_fields = [data.get("name"), data.get("dob"), data.get("gender"), data.get("phone")]
                if not email or any(not str(field or "").strip() for field in required_fields):
                    self.send_json({"success": False, "message": "Name, date of birth, gender, phone, and email are required."}, 400)
                    return
                if not user_exists(email):
                    self.send_json({"success": False, "message": "No account found for this email."}, 404)
                    return
                if not update_user_details(email, data):
                    self.send_json({"success": False, "message": "Unable to update account details."}, 500)
                    return
                user = get_user_by_email(email)
                user.pop("password", None)
                self.send_json({"success": True, "message": "Account details updated.", "user": user}, 200)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        if parsed.path == "/api/register":
            try:
                data = json.loads(payload or "{}")
                email = (data.get("email") or "").strip()
                password = (data.get("password") or "").strip()
                confirm_password = (data.get("confirmPassword") or "").strip()

                if not email or not password:
                    self.send_json({"success": False, "message": "Email and password are required."}, 400)
                    return

                if not is_valid_password(password):
                    self.send_json({"success": False, "message": "Password must be more than 8 characters and contain an uppercase letter, lowercase letter, number, and special character."}, 400)
                    return

                if password != confirm_password:
                    self.send_json({"success": False, "message": "Passwords do not match."}, 400)
                    return

                if user_exists(email):
                    self.send_json({"success": False, "message": "User already exists."}, 409)
                    return

                create_user_account(data)
                self.send_json({"success": True, "message": "User created successfully."}, 201)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        if parsed.path == "/api/login":
            try:
                data = json.loads(payload or "{}")
                email = (data.get("email") or "").strip()
                password = (data.get("password") or "").strip()

                if not email or not password:
                    self.send_json({"success": False, "message": "Email and password are required."}, 400)
                    return

                user = get_user_by_email(email)
                if user is None:
                    self.send_json({"success": False, "message": "No account found for this email."}, 404)
                    return

                if not verify_login(email, password):
                    self.send_json({"success": False, "message": "Invalid email or password."}, 401)
                    return

                self.send_json({"success": True, "message": "Login successful.", "name": user["name"]}, 200)
                return
            except Exception as exc:  # pragma: no cover
                self.send_json({"success": False, "message": str(exc)}, 500)
                return

        self.send_json({"success": False, "message": "Not found."}, 404)

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    create_users_table()
    settings = get_smtp_settings()
    if settings["host"] and settings["username"] and settings["password"]:
        print("SMTP email OTP is configured and ready.")
    else:
        print("SMTP email OTP is not configured yet. Copy admin/.env.example to admin/.env and add your Gmail app password.")
    server = HTTPServer((HOST, PORT), AdminRequestHandler)
    print(f"SQLite admin server running on http://{HOST}:{PORT}")
    server.serve_forever()
