# Admin email OTP setup

## 1) Create a Gmail App Password

1. Open your Google Account.
2. Go to Security.
3. Turn on 2-Step Verification if it is not already enabled.
4. Go to App passwords.
5. Select Mail as the app and Windows Computer as the device.
6. Copy the 16-character app password.

## 2) Fill the environment file

Open `admin/.env` and replace the sample values:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=yourgmail@gmail.com
EMAIL_PASSWORD=your_16_character_app_password
EMAIL_FROM=yourgmail@gmail.com
EMAIL_USE_TLS=true
```

## 3) Start the server

From the `admin` folder:

```bash
python server.py
```

## 4) Use the login page

The login page sends a real OTP to the entered email and verifies it before registration is allowed.
