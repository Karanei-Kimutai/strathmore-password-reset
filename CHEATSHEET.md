# Strathmore Password Reset - Cheat Sheet

## First Time Setup

```bash
# 1. Create virtual environment
python3 -m venv venv                    # Linux/Mac/WSL
python -m venv venv                     # Windows

# 2. Activate virtual environment
source venv/bin/activate                # Linux/Mac/WSL
venv\Scripts\activate                   # Windows

# 3. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env                    # Linux/Mac/WSL
copy .env.example .env                  # Windows

# 5. Edit credentials
nano .env                               # Linux/Mac/WSL
notepad .env                            # Windows

# 6. Create passwords directory
mkdir -p passwords                      # Linux/Mac/WSL
mkdir passwords                         # Windows

# 7. Test configuration
python test_config.py
```

## Daily Usage

```bash
# 1. Activate virtual environment
source venv/bin/activate                # Linux/Mac/WSL
venv\Scripts\activate                   # Windows

# 2. Run the script
python strathmore_password_reset.py

# 3. Deactivate when done
deactivate
```

## Virtual Environment Commands

### Create
```bash
python3 -m venv venv                    # Linux/Mac/WSL
python -m venv venv                     # Windows
```

### Activate
```bash
source venv/bin/activate                # Linux/Mac/WSL
venv\Scripts\activate                   # Windows
```

### Deactivate
```bash
deactivate                              # All platforms
```

### Check if Active
```bash
# Look for (venv) in your prompt
(venv) user@computer:~/project$

# Or check Python path
which python                            # Linux/Mac/WSL (shows venv/bin/python)
where python                            # Windows (shows venv\Scripts\python.exe)
```

### Install/Update Dependencies
```bash
# Make sure venv is activated first!
pip install -r requirements.txt

# Or install individually
pip install selenium webdriver-manager python-dotenv beautifulsoup4

# List installed packages
pip list

# Show package details
pip show selenium
```

### Recreate venv
```bash
# 1. Deactivate first
deactivate

# 2. Remove old venv
rm -rf venv                             # Linux/Mac/WSL
rmdir /s /q venv                        # Windows (Command Prompt)
Remove-Item -Recurse -Force venv        # Windows (PowerShell)

# 3. Create new venv
python3 -m venv venv                    # Linux/Mac/WSL
python -m venv venv                     # Windows

# 4. Activate and reinstall
source venv/bin/activate                # Linux/Mac/WSL
venv\Scripts\activate                   # Windows
pip install -r requirements.txt
```

## Configuration (.env file)

```env
# Email settings (for receiving reset emails)
EMAIL_ADDRESS=your.email@strathmore.edu
EMAIL_PASSWORD=your_app_password_here
IMAP_SERVER=imap.gmail.com

# Strathmore credentials
USERNAME=your_strathmore_username

# Password settings
PASSWORD_LENGTH=16
LOG_DIRECTORY=passwords
```

### Gmail App Password Setup
1. Visit: https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Visit: https://myaccount.google.com/apppasswords
4. Generate password for **Mail**
5. Copy generated password to `.env` file

## Common Commands

### Test Configuration
```bash
source venv/bin/activate
python test_config.py
```

### Run Password Reset
```bash
source venv/bin/activate
python strathmore_password_reset.py
```

### Check Logs
```bash
# List all password log files
ls -lh passwords/                       # Linux/Mac/WSL
dir passwords\                          # Windows

# View master log
cat passwords/password_log.txt          # Linux/Mac/WSL
type passwords\password_log.txt         # Windows

# View latest reset log
ls -t passwords/password_reset_*.txt | head -1 | xargs cat    # Linux/Mac/WSL
```

### View Debug Files (on errors)
```bash
# Email content
cat /tmp/email_body.html

# Screenshots
open /tmp/selenium_error_*.png          # Mac
xdg-open /tmp/selenium_error_*.png      # Linux

# Page source
cat /tmp/page_source_*.html
```

## Troubleshooting

### "Command not found: python3"
```bash
# Try python instead
python --version
python -m venv venv
```

### "No module named X"
```bash
# Check venv is activated
which python                            # Should show venv path

# If not activated
source venv/bin/activate                # Linux/Mac/WSL
venv\Scripts\activate                   # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### "venv/bin/activate: Permission denied"
```bash
# Wrong command - use 'source'
source venv/bin/activate                # Correct

# Not this:
./venv/bin/activate                     # Wrong
bash venv/bin/activate                  # Wrong
```

### Email Connection Fails
```bash
# Run diagnostic
python test_config.py

# Common fixes:
# 1. Use app password (not regular Gmail password)
# 2. Enable IMAP in Gmail settings
# 3. Check IMAP_SERVER is correct (imap.gmail.com for Gmail)
# 4. Verify EMAIL_ADDRESS and EMAIL_PASSWORD in .env
```

### Chrome Not Found (WSL)
```bash
# Script will auto-install, or manually:
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f -y
rm google-chrome-stable_current_amd64.deb
```

### ChromeDriver "Exec format error"
```bash
# This happens when webdriver-manager points to wrong file
# The script will auto-fix, but if it persists:

# Option 1: Clear webdriver-manager cache
rm -rf ~/.wdm

# Option 2: Manual chromedriver install
# Find your Chrome version
google-chrome --version

# Download matching chromedriver from:
# https://googlechromelabs.github.io/chrome-for-testing/

# Example for Chrome 120:
wget https://edgedl.me.gstatic.com/edgedl/chrome/chrome-for-testing/120.0.6099.109/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm -rf chromedriver-linux64 chromedriver-linux64.zip

# Then modify script to use system chromedriver
```

### "ModuleNotFoundError: No module named 'dotenv'"
```bash
# Wrong package name - it's python-dotenv
pip install python-dotenv

# Or install all dependencies
pip install -r requirements.txt
```

## File Locations

```
Project Structure:
├── venv/                               # Virtual environment (you create)
├── passwords/                          # Password logs (auto-created)
│   ├── password_reset_YYYYMMDD_HHMMSS.txt
│   └── password_log.txt
├── .env                                # Your credentials (NEVER commit!)
└── /tmp/                               # Debug files (on errors only)
    ├── email_body.html
    ├── selenium_error_*.png
    └── page_source_*.html
```

## Security Checklist

- [ ] `.env` has correct permissions (600 on Linux/Mac)
- [ ] Using app password (not main email password)
- [ ] `venv/` is in `.gitignore`
- [ ] `passwords/` is in `.gitignore`
- [ ] `.env` is in `.gitignore`
- [ ] Delete password logs after saving securely
- [ ] Never commit `.env` or `passwords/` to Git

## Quick Health Check

```bash
# 1. Check venv exists
ls -ld venv/                            # Linux/Mac/WSL
dir venv                                # Windows

# 2. Check .env exists
ls -lh .env                             # Linux/Mac/WSL
dir .env                                # Windows

# 3. Activate venv
source venv/bin/activate                # Linux/Mac/WSL
venv\Scripts\activate                   # Windows

# 4. Check dependencies installed
pip list | grep -E 'selenium|webdriver|dotenv|beautifulsoup'    # Linux/Mac/WSL
pip list | findstr "selenium webdriver dotenv beautifulsoup"     # Windows

# 5. Run configuration test
python test_config.py
```

## Fresh Start (Reset Everything)

```bash
# 1. Deactivate venv
deactivate

# 2. Remove venv and logs
rm -rf venv/ passwords/                 # Linux/Mac/WSL
rmdir /s /q venv passwords              # Windows

# 3. Recreate venv
python3 -m venv venv                    # Linux/Mac/WSL
python -m venv venv                     # Windows

# 4. Activate venv
source venv/bin/activate                # Linux/Mac/WSL
venv\Scripts\activate                   # Windows

# 5. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 6. Recreate directories
mkdir passwords

# 7. Test
python test_config.py
```

## Docker Quick Reference

```bash
# Build image
docker build -t strathmore-pwd-reset .

# Run once
docker run --rm \
  -v $(pwd)/passwords:/app/passwords \
  strathmore-pwd-reset

# Using docker-compose
docker-compose up                       # Run once
docker-compose up -d                    # Run in background
docker-compose logs -f                  # View logs
docker-compose down                     # Stop
```

## Scheduling with Cron (Linux/WSL)

```bash
# Edit crontab
crontab -e

# Examples (use FULL PATHS):

# Every Sunday at 2 AM
0 2 * * 0 cd /full/path/to/project && /full/path/to/project/venv/bin/python strathmore_password_reset.py

# Daily at midnight
0 0 * * * cd /full/path/to/project && /full/path/to/project/venv/bin/python strathmore_password_reset.py

# Every 6 hours
0 */6 * * * cd /full/path/to/project && /full/path/to/project/venv/bin/python strathmore_password_reset.py

# Every Monday at 3 AM
0 3 * * 1 cd /full/path/to/project && /full/path/to/project/venv/bin/python strathmore_password_reset.py
```

## Emergency Password Save

If script completes but logging fails:

```bash
# Password is printed in terminal output
# Look for:
✓ PASSWORD RESET COMPLETED SUCCESSFULLY
Password: Xy9#mK2$pL4@qR7!

# Save immediately
echo "Password: Xy9#mK2$pL4@qR7!" > emergency_password.txt
chmod 600 emergency_password.txt        # Linux/Mac/WSL
```

## Python Version Check

```bash
# Check Python version
python3 --version                       # Linux/Mac/WSL
python --version                        # Windows

# Script requires Python 3.8+
# If version is too old, install newer Python:
# - Linux: sudo apt install python3.11
# - Mac: brew install python@3.11
# - Windows: Download from python.org
```

## Useful pip Commands

```bash
# Activate venv first!
source venv/bin/activate

# Show outdated packages
pip list --outdated

# Upgrade a package
pip install --upgrade selenium

# Upgrade all packages
pip install --upgrade -r requirements.txt

# Uninstall a package
pip uninstall selenium

# Show dependency tree
pip show selenium

# Freeze current packages
pip freeze > requirements.txt

# Install specific version
pip install selenium==4.15.2
```

## Key Files You Need

**Essential:**
- `strathmore_password_reset.py` - Main script
- `requirements.txt` - Dependencies
- `.env` - Your credentials (create from .env.example)

**Helpful:**
- `test_config.py` - Configuration tester
- `QUICKSTART.md` - Simple setup guide
- `README.md` - Full documentation

**Optional:**
- `Dockerfile` - For Docker deployment
- `docker-compose.yml` - Docker orchestration
- `.gitignore` - Git safety

---

**Pro Tip:** Bookmark this cheat sheet for quick reference! 🚀
