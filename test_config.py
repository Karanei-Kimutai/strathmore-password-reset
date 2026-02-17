#!/usr/bin/env python3
"""
Configuration Tester for Strathmore Password Reset
Tests email connection and environment setup before running the main script.

Usage:
    source venv/bin/activate
    python test_config.py
    
Or:
    venv/bin/python test_config.py
"""

import os
import imaplib
import smtplib
import ssl
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

def test_env_variables():
    """Check if all required environment variables are set."""
    print("\n" + "=" * 60)
    print("Testing Environment Variables")
    print("=" * 60)
    
    required_vars = {
        "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
        "IMAP_SERVER": os.getenv("IMAP_SERVER"),
        "STRATHMORE_USERNAME": os.getenv("STRATHMORE_USERNAME"),
    }
    optional_vars = {
        "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "SMTP_PORT": os.getenv("SMTP_PORT", "587"),
        "NOTIFICATION_EMAIL": os.getenv("NOTIFICATION_EMAIL", os.getenv("EMAIL_ADDRESS")),
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Mask sensitive values
            if "PASSWORD" in var_name:
                display_value = "*" * 8
            else:
                display_value = var_value
            print(f"[+] {var_name}: {display_value}")
        else:
            print(f"[-] {var_name}: NOT SET")
            all_set = False

    print("\n[*] Optional notification settings:")
    for var_name, var_value in optional_vars.items():
        if var_value:
            print(f"[+] {var_name}: {var_value}")
        else:
            print(f"[!] {var_name}: NOT SET (will use script defaults where applicable)")
    
    return all_set

def test_email_connection():
    """Test IMAP connection to email server."""
    print("\n" + "=" * 60)
    print("Testing IMAP Email Connection")
    print("=" * 60)
    
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
    
    if not email_address or not email_password:
        print("[-] Email credentials not set in .env file")
        return False
    
    try:
        print(f"[*] Connecting to {imap_server}...")
        mail = imaplib.IMAP4_SSL(imap_server)
        
        print(f"[*] Logging in as {email_address}...")
        mail.login(email_address, email_password)
        
        print("[*] Selecting inbox...")
        mail.select("inbox")
        
        print("[*] Searching for emails...")
        status, messages = mail.search(None, "ALL")
        
        if status == "OK":
            email_count = len(messages[0].split())
            print(f"[+] Successfully connected! Found {email_count} emails in inbox")
        
        mail.logout()
        print("[+] Email connection test PASSED")
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"[-] IMAP Error: {e}")
        print("\n[!] Common issues:")
        print("    - Wrong email/password")
        print("    - IMAP not enabled")
        print("    - Need to use App Password (for Gmail)")
        print("    - Wrong IMAP server")
        return False
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return False

def test_notification_email_connection():
    """Test SMTP connection/login for password notification email."""
    print("\n" + "=" * 60)
    print("Testing SMTP Notification Connection")
    print("=" * 60)

    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    notification_email = os.getenv("NOTIFICATION_EMAIL", email_address)

    if not email_address or not email_password:
        print("[-] Email credentials not set in .env file")
        return False

    if not notification_email:
        print("[-] NOTIFICATION_EMAIL could not be resolved")
        return False

    try:
        print(f"[*] Connecting to SMTP server {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()

            print(f"[*] Logging in as {email_address}...")
            server.login(email_address, email_password)

        print(f"[+] SMTP login test PASSED (notification target: {notification_email})")
        print("[*] No email was sent during this test.")
        return True
    except smtplib.SMTPException as e:
        print(f"[-] SMTP Error: {e}")
        print("\n[!] Common issues:")
        print("    - Wrong email/app password")
        print("    - Wrong SMTP server/port")
        print("    - Account requires App Password (Gmail)")
        return False
    except Exception as e:
        print(f"[-] SMTP connection failed: {e}")
        return False

def test_directories():
    """Check if required directories exist and are writable."""
    print("\n" + "=" * 60)
    print("Testing Directories")
    print("=" * 60)
    
    log_dir = Path(os.getenv("LOG_DIRECTORY", "passwords"))
    
    try:
        # Create directory if it doesn't exist
        log_dir.mkdir(exist_ok=True)
        print(f"[+] Log directory exists: {log_dir.absolute()}")
        
        # Test write permissions
        test_file = log_dir / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        print("[+] Log directory is writable")
        
        return True
    except Exception as e:
        print(f"[-] Directory test failed: {e}")
        return False

def test_imports():
    """Check if all required Python packages are installed."""
    print("\n" + "=" * 60)
    print("Testing Python Dependencies")
    print("=" * 60)
    
    packages = [
        ("selenium", "selenium"),
        ("webdriver_manager", "webdriver-manager"),
        ("dotenv", "python-dotenv"),
        ("bs4", "beautifulsoup4"),
    ]
    
    all_installed = True
    for module_name, package_name in packages:
        try:
            __import__(module_name)
            print(f"[+] {package_name}: installed")
        except ImportError:
            print(f"[-] {package_name}: NOT installed")
            all_installed = False
    
    return all_installed

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("STRATHMORE PASSWORD RESET - CONFIGURATION TEST")
    print("=" * 60)
    
    results = {
        "Environment Variables": test_env_variables(),
        "Python Dependencies": test_imports(),
        "Directories": test_directories(),
        "IMAP Email Connection": test_email_connection(),
        "SMTP Notification Connection": test_notification_email_connection(),
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - Ready to run main script!")
        print("=" * 60)
        print("\nRun: python strathmore_password_reset.py")
    else:
        print("✗ SOME TESTS FAILED - Please fix issues above")
        print("=" * 60)
        print("\nCommon fixes:")
        print("  - Edit .env file with correct credentials")
        print("  - Run: pip install -r requirements.txt")
        print("  - Enable IMAP in your email settings")
        print("  - Use App Password for Gmail")
        print("  - Set SMTP_SERVER/SMTP_PORT correctly for notifications")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
