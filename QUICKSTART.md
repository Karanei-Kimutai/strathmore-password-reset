# Quick Start Guide

## Setup (First Time Only)

### Step 1: Create Virtual Environment
```bash
python3 -m venv venv
```

### Step 2: Activate Virtual Environment
```bash
# Linux/Mac/WSL
source venv/bin/activate

# Windows
venv\Scripts\activate
```
You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Credentials
```bash
# Create .env file
cp .env.example .env

# Edit it with your info
nano .env  # or use any text editor
```

Add your credentials:
```env
EMAIL_ADDRESS=your.email@strathmore.edu
EMAIL_PASSWORD=your_app_password
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
NOTIFICATION_EMAIL=your.email@strathmore.edu
USERNAME=your_strathmore_username
PASSWORD_LENGTH=16
LOG_DIRECTORY=passwords
```

### Step 5: Create Passwords Directory
```bash
mkdir passwords
```

### Step 6: Test Setup
```bash
python test_config.py
```

If all tests pass, you're ready!

---

## Running the Script

### Every Time You Want to Reset Password:

```bash
# 1. Activate venv
source venv/bin/activate     # Linux/Mac/WSL
venv\Scripts\activate        # Windows

# 2. Run script
python strathmore_password_reset.py

# 3. Deactivate (optional)
deactivate
```

---

## Common Tasks

### Check if venv is active
Look for `(venv)` in your prompt:
```
(venv) user@computer:~/project$
```

### Reinstall dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Start fresh
```bash
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Gmail App Password Setup

If using Gmail:

1. Go to: https://myaccount.google.com/security
2. Enable "2-Step Verification"
3. Go to: https://myaccount.google.com/apppasswords
4. Create app password for "Mail"
5. Use that password in `.env` (not your regular Gmail password)
6. Keep `SMTP_SERVER=smtp.gmail.com` and `SMTP_PORT=587` for notifications

---

## Files You Need

**Required:**
- `strathmore_password_reset.py` - Main script
- `requirements.txt` - Dependencies list
- `.env` - Your credentials (you create this)
- `.env.example` - Template

**Optional but helpful:**
- `test_config.py` - Test your setup
- `README.md` - Full documentation
- `CHEATSHEET.md` - Quick reference
- `.gitignore` - Keep secrets safe

---

## Troubleshooting

**"No module named X"**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**"python3: command not found"**
```bash
# Try just 'python'
python -m venv venv
```

**Email connection fails**
```bash
python test_config.py
# Check the output for specific errors
```

**Password notification email fails**
- Check `SMTP_SERVER`, `SMTP_PORT`, and `NOTIFICATION_EMAIL` in `.env`
- Confirm `EMAIL_PASSWORD` is an app password (for Gmail)

**Need help?**
- Check `README.md` for detailed docs
- Check `CHEATSHEET.md` for quick commands
- Run `python test_config.py` to diagnose issues
