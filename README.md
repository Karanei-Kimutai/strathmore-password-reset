# Strathmore Password Reset Automation

Automates the password reset process for Strathmore University student portal.

## Features

- ✅ Automated form submission on forgotten password page
- ✅ Email monitoring for reset link (with "click here" link extraction)
- ✅ Secure password generation (cryptographically random)
- ✅ Automatic password reset completion
- ✅ Comprehensive logging with timestamps
- ✅ WSL and Docker support

## Prerequisites

### For WSL/Linux:
```bash
# The script will auto-install Chrome in WSL if not present
# You just need Python 3.8+
python3 --version
```

### For Email Access:
- If using Gmail: Enable "App Passwords" in your Google Account settings
- If using another provider: Ensure IMAP is enabled

## Installation

### 1. Clone and Setup

```bash
# Create project directory
mkdir strathmore-password-reset
cd strathmore-password-reset

# Download all files to this directory
# (strathmore_password_reset.py, requirements.txt, setup.sh, etc.)

# Make scripts executable
chmod +x setup.sh run.sh activate.sh

# Run automated setup (creates venv, installs dependencies)
bash setup.sh
```

This will:
- ✅ Create a virtual environment in `venv/`
- ✅ Activate the virtual environment
- ✅ Install all Python dependencies
- ✅ Create `.env` file from template
- ✅ Create `passwords/` directory

### 2. Configure Environment

```bash
# Edit with your credentials
nano .env
```

**Required variables in `.env`:**
```env
EMAIL_ADDRESS=your.email@strathmore.edu
EMAIL_PASSWORD=your_app_password_here
IMAP_SERVER=imap.gmail.com
USERNAME=your_strathmore_username
PASSWORD_LENGTH=16
LOG_DIRECTORY=passwords
```

### 3. Run the Script

**Option 1: Using the convenience script (recommended)**
```bash
bash run.sh
```

**Option 2: Manual activation**
```bash
# Activate virtual environment
source venv/bin/activate

# Run the script
python strathmore_password_reset.py

# Deactivate when done
deactivate
```

**Option 3: Quick activation helper**
```bash
# Activate venv quickly
source activate.sh

# Then run
python strathmore_password_reset.py
```

## Docker Setup (For Later)

### Build Image
```bash
docker build -t strathmore-pwd-reset .
```

### Run Container
```bash
docker run --rm \
  -v $(pwd)/passwords:/app/passwords \
  strathmore-pwd-reset
```

## How It Works

1. **Phase 1**: Navigates to forgotten password page, enters username, clicks Search
2. **Phase 2**: Monitors email inbox for "Forgotten Password Verification" from student-pss-noreply@strathmore.edu
3. **Phase 3**: Extracts the "click here" link from the email
4. **Phase 4**: Follows link, enters new secure password twice
5. **Phase 5**: Logs password with timestamp to `passwords/` directory

## Security Notes

⚠️ **IMPORTANT**:
- Password logs are stored in `passwords/` directory with restricted permissions (600 on Linux)
- **Delete log files after saving passwords securely**
- Never commit `.env` or `passwords/` directory to version control
- Use app-specific passwords for email access (never your main password)

## Troubleshooting

### Virtual Environment Issues

**"venv not found" error**
```bash
# Create it manually
python3 -m venv venv

# Or run setup again
bash setup.sh
```

**"No module named X" error**
```bash
# Make sure venv is activated
source venv/bin/activate  # Linux/Mac/WSL
# OR
venv\Scripts\activate.bat  # Windows

# Then reinstall dependencies
pip install -r requirements.txt
```

**Check if venv is activated**
```bash
# You should see (venv) in your prompt
(venv) user@computer:~/project$

# Or check which python
which python
# Should show: /path/to/project/venv/bin/python
```

**Deactivate venv when done**
```bash
deactivate
```

### Email Not Found
- Check IMAP server settings in `.env`
- Verify email credentials are correct
- Ensure email isn't in spam folder
- Check if IMAP is enabled for your email account

### Chrome Issues in WSL
```bash
# Manually install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f -y
```

### Debugging
- Check `/tmp/email_body.html` for extracted email content
- Check `/tmp/selenium_error_*.png` for browser screenshots on errors
- Check `/tmp/page_source_*.html` for page HTML on errors

## File Structure

```
strathmore-password-reset/
├── strathmore_password_reset.py   # Main script
├── requirements.txt                # Python dependencies
├── .env                            # Your credentials (create from .env.example)
├── .env.example                    # Template for credentials
├── setup.sh                        # Automated setup script
├── run.sh                          # Convenience script to run with venv
├── activate.sh                     # Quick venv activation
├── test_config.py                  # Configuration tester
├── Dockerfile                      # Docker configuration
├── docker-compose.yml              # Docker orchestration
├── README.md                       # This file
├── .gitignore                      # Git ignore rules
├── venv/                           # Virtual environment (created by setup.sh)
└── passwords/                      # Generated password logs (gitignored)
    ├── password_reset_YYYYMMDD_HHMMSS.txt
    └── password_log.txt
```

## Logs Output

### Individual Reset Log (`password_reset_YYYYMMDD_HHMMSS.txt`)
```
============================================================
STRATHMORE PASSWORD RESET LOG
============================================================
Timestamp: 2025-10-13 14:23:45
Username: your_username
New Password: Xy9#mK2$pL4@qR7!
Password Length: 16
============================================================

IMPORTANT: Store this password securely and delete this file after use.
```

### Master Log (`password_log.txt`)
```
[2025-10-13 14:23:45] your_username: Xy9#mK2$pL4@qR7!
[2025-10-13 15:30:12] your_username: Zb8!nM3$vC6@wT9#
```

## Customization

### Change Password Length
Edit `.env`:
```env
PASSWORD_LENGTH=20  # Increase to 20 characters
```

### Change Log Directory
Edit `.env`:
```env
LOG_DIRECTORY=secure_logs
```

### Modify Retry Attempts
In `strathmore_password_reset.py`, edit the `get_reset_link_from_email()` call:
```python
reset_link = get_reset_link_from_email(retries=15, delay=15)  # 15 retries, 15s delay
```

## .gitignore Recommendations

Create a `.gitignore` file:
```gitignore
# Environment
.env
venv/
__pycache__/

# Logs
passwords/
*.txt

# Debug files
/tmp/
*.png
*.html

# OS
.DS_Store
Thumbs.db
```

## Scheduling (Optional)

### Using Cron (Linux/WSL)
```bash
# Edit crontab
crontab -e

# Run every week on Sunday at 2 AM (using absolute paths)
0 2 * * 0 cd /path/to/strathmore-password-reset && /path/to/strathmore-password-reset/venv/bin/python strathmore_password_reset.py

# Or use the run script
0 2 * * 0 cd /path/to/strathmore-password-reset && bash run.sh
```

### Using Docker Compose with Scheduler
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  password-reset:
    build: .
    volumes:
      - ./passwords:/app/passwords
    env_file:
      - .env
    restart: "no"
```

## Support

For issues specific to:
- **Strathmore portal**: Contact Strathmore IT support
- **Script errors**: Check logs in `/tmp/` directory
- **Email access**: Verify IMAP settings with your email provider

## License

This script is for personal use only. Use responsibly and in accordance with Strathmore University's acceptable use policies.

## Changelog

### v1.0.0 (2025-10-13)
- Initial release
- Automated password reset workflow
- Email link extraction with BeautifulSoup
- Secure password generation
- Comprehensive logging
- WSL support
- Docker support