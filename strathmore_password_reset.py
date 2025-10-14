import os
import time
import imaplib
import email
import re
import platform
import subprocess
import traceback
import secrets
import string
import tempfile
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# --- Configuration ---
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
USERNAME = os.getenv("USERNAME")  # Strathmore username
FRONTEND_URL = "https://su-sso.strathmore.edu/student-pss/public/forgottenpassword"
PASSWORD_LENGTH = int(os.getenv("PASSWORD_LENGTH", "16"))
LOG_DIRECTORY = os.getenv("LOG_DIRECTORY", "passwords")

# --- Password Generation and Logging ---

def generate_secure_password(length=PASSWORD_LENGTH):
    """
    Generates a cryptographically secure password with guaranteed character diversity.

    Args:
        length: Password length (minimum 12 characters recommended)

    Returns:
        str: A secure random password
    """
    if length < 12:
        print("[!] Warning: Password length less than 12 is not recommended. Using 12 instead.")
        length = 12

    # Character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    # Ensure at least one of each type
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]

    # Fill the rest randomly
    all_chars = lowercase + uppercase + digits + special
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)

def log_new_password(username, password):
    """
    Securely logs the new password to a timestamped file.

    Args:
        username: User's username
        password: The new password to log
    """
    try:
        log_dir = Path(LOG_DIRECTORY)
        log_dir.mkdir(exist_ok=True)

        # Create a unique log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"password_reset_{timestamp}.txt"

        # Log entry with metadata
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username": username,
            "password": password,
            "length": len(password)
        }

        with open(log_file, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("STRATHMORE PASSWORD RESET LOG\n")
            f.write("=" * 60 + "\n")
            f.write(f"Timestamp: {log_entry['timestamp']}\n")
            f.write(f"Username: {log_entry['username']}\n")
            f.write(f"New Password: {log_entry['password']}\n")
            f.write(f"Password Length: {log_entry['length']}\n")
            f.write("=" * 60 + "\n")
            f.write("\nIMPORTANT: Store this password securely and delete this file after use.\n")

        # Also append to master log
        master_log = log_dir / "password_log.txt"
        with open(master_log, "a") as f:
            f.write(f"[{log_entry['timestamp']}] {log_entry['username']}: {log_entry['password']}\n")

        print(f"[+] Password logged to: {log_file}")
        print(f"[+] Master log updated: {master_log}")

        # Set restrictive permissions (Unix-like systems)
        if platform.system() != "Windows":
            os.chmod(log_file, 0o600)
            os.chmod(master_log, 0o600)
            print("[+] File permissions set to owner-only (600)")

    except Exception as e:
        print(f"[-] CRITICAL: Failed to log password: {e}")
        print(f"[!] Password was: {password}")
        print("[!] SAVE THIS PASSWORD MANUALLY!")

# --- Environment Detection ---

def is_running_in_wsl():
    """Checks if running inside Windows Subsystem for Linux."""
    return 'WSL_DISTRO_NAME' in os.environ or 'microsoft' in platform.uname().release.lower()

def install_chrome_wsl():
    """Installs Google Chrome in WSL if not already present."""
    try:
        result = subprocess.run(['which', 'google-chrome'], capture_output=True)
        if result.returncode == 0:
            print("[*] Chrome is already installed in WSL.")
            return True

        print("[*] Chrome not found. Installing Chrome in WSL...")
        print("[*] This requires sudo access.")

        commands = [
            "wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O /tmp/chrome.deb",
            "sudo dpkg -i /tmp/chrome.deb",
            "sudo apt-get install -f -y",
            "rm /tmp/chrome.deb"
        ]

        for cmd in commands:
            print(f"[*] Running: {cmd}")
            result = subprocess.run(cmd, shell=True)
            if result.returncode != 0 and "dpkg" in cmd:
                print("[*] Installing dependencies...")
                continue

        print("[+] Chrome installation complete!")
        return True

    except Exception as e:
        print(f"[-] Error installing Chrome: {e}")
        return False

# --- Browser Automation Functions ---

def request_password_reset(driver, username):
    """
    Navigates to the Strathmore forgotten password page and submits username.

    Args:
        driver: Selenium WebDriver instance
        username: Strathmore username

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("\n" + "=" * 60)
        print("PHASE 1: REQUESTING PASSWORD RESET")
        print("=" * 60)

        print(f"[*] Navigating to: {FRONTEND_URL}")
        driver.get(FRONTEND_URL)

        wait = WebDriverWait(driver, 15)

        # Wait for page to load
        print("[*] Waiting for forgotten password page to load...")
        username_input = wait.until(EC.presence_of_element_located((By.ID, "sAMAccountName")))
        print(f"[+] Page loaded: {driver.title}")

        # Enter username
        print(f"[*] Entering username: {username}")
        username_input.clear()
        username_input.send_keys(username)
        print("[+] Username entered")

        # Click Search button
        print("[*] Clicking Search button...")
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "submitBtn")))
        search_button.click()
        print("[+] Search button clicked")

        # Wait for confirmation or next page
        time.sleep(3)
        print(f"[+] Current page: {driver.current_url}")
        
        return True

    except Exception as e:
        print(f"[-] Error during password reset request: {e}")
        traceback.print_exc()

        try:
            screenshot_path = Path(tempfile.gettempdir()) / "selenium_error_request.png"
            driver.save_screenshot(str(screenshot_path))
            print(f"[*] Screenshot saved: {screenshot_path}")
        except:
            pass

        return False

# --- Email Functions ---

def delete_previous_reset_emails():
    """
    Deletes previous password reset emails to avoid confusion.
    """
    print("\n" + "=" * 60)
    print("PHASE 0: CLEANING UP PREVIOUS RESET EMAILS")
    print("=" * 60)
    try:
        print(f"[*] Connecting to {IMAP_SERVER} to clean up old emails...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")
        print("[+] Connected to inbox.")

        # Search for emails from the specific sender with the specific subject
        search_query = '(FROM "student-pss-noreply@strathmore.edu" SUBJECT "Forgotten Password Verification")'
        print(f"[*] Searching for previous emails matching sender and subject...")
        
        status, messages = mail.search(None, search_query)
        if status != "OK":
            print("[-] Could not search for emails.")
            mail.logout()
            return False

        email_ids = messages[0].split()
        if not email_ids:
            print("[+] No previous password reset emails found.")
        else:
            print(f"[*] Found {len(email_ids)} old reset email(s) to delete.")
            for mail_id in email_ids:
                mail.store(mail_id, '+FLAGS', '\\Deleted')
            
            print("[*] Expunging deleted emails...")
            status, response = mail.expunge()
            if status == 'OK':
                print("[+] Old reset emails cleared successfully.")
            else:
                print(f"[-] Failed to expunge emails: {response}")

        mail.logout()
        return True

    except Exception as e:
        print(f"[-] Error during email cleanup: {e}")
        traceback.print_exc()
        return False

def get_reset_link_from_email(retries=10, delay=10):
    """
    Retrieves the password reset link from email inbox.
    Looks for "Forgotten Password Verification" email from student-pss-noreply@strathmore.edu

    Args:
        retries: Number of attempts to find the email
        delay: Seconds to wait between attempts

    Returns:
        str: Reset link URL or None if not found
    """
    print("\n" + "=" * 60)
    print("PHASE 2: RETRIEVING RESET LINK FROM EMAIL")
    print("=" * 60)

    for attempt in range(1, retries + 1):
        try:
            print(f"[*] Attempt {attempt}/{retries}: Connecting to {IMAP_SERVER}...")

            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            mail.select("inbox")
            print("[+] Connected to inbox")

            # Search for password reset email from Strathmore (preferably unseen)
            search_queries = [
                '(UNSEEN FROM "student-pss-noreply@strathmore.edu" SUBJECT "Forgotten Password Verification")',
                '(FROM "student-pss-noreply@strathmore.edu" SUBJECT "Forgotten Password Verification")',
            ]

            email_id = None
            for query in search_queries:
                status, messages = mail.search(None, query)
                if status == "OK" and messages[0]:
                    # Get the most recent email ID
                    email_id = messages[0].split()[-1]
                    print(f"[+] Found email (ID: {email_id.decode()}) using query: {query}")
                    break

            if not email_id:
                print(f"[*] Email not found yet. Waiting {delay}s...")
                mail.logout()
                time.sleep(delay)
                continue

            # Fetch and parse email
            _, msg_data = mail.fetch(email_id, "(RFC822)")

            for response_part in msg_data:
                if not isinstance(response_part, tuple):
                    continue

                msg = email.message_from_bytes(response_part[1])

                # Extract email body
                body = ""
                html_body = ""
                
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                decoded = payload.decode('utf-8', errors='ignore')
                                if content_type == "text/html":
                                    html_body = decoded
                                elif content_type == "text/plain":
                                    body = decoded
                        except:
                            continue
                else:
                    try:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                    except:
                        pass

                # Prefer HTML body for link extraction
                search_body = html_body if html_body else body

                if not search_body:
                    continue

                print(f"[*] Email body length: {len(search_body)} characters")

                # Save for debugging
                debug_file = Path(tempfile.gettempdir()) / "email_body.html"
                debug_file.write_text(search_body, encoding='utf-8')
                print(f"[*] Email saved to: {debug_file}")

                # Extract reset link - look for "click here" anchor tag
                reset_link = None

                # Try parsing HTML first
                if html_body:
                    try:
                        soup = BeautifulSoup(html_body, 'html.parser')
                        # Find all links
                        for link in soup.find_all('a', href=True):
                            link_text = link.get_text().strip().lower()
                            href = link['href']
                            
                            # Look for "click here" or password reset related links
                            if 'click here' in link_text or 'reset' in link_text.lower():
                                reset_link = href
                                print(f"[+] Found link via 'click here': {reset_link[:80]}...")
                                break
                            
                            # Also check if URL contains password reset patterns
                            if 'strathmore.edu' in href and ('password' in href.lower() or 'token' in href.lower()):
                                reset_link = href
                                print(f"[+] Found Strathmore password link: {reset_link[:80]}...")
                                break
                    except Exception as e:
                        print(f"[!] HTML parsing failed: {e}")

                # Fallback to regex patterns
                if not reset_link:
                    patterns = [
                        # Look for click here anchor pattern
                        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>.*?click here.*?</a>',
                        # Strathmore specific URLs
                        r'https?://su-sso\.strathmore\.edu[^\s"<>]+',
                        r'https?://[^\s"<>]*strathmore\.edu[^\s"<>]*password[^\s"<>]*',
                        # Generic password reset patterns
                        r'https?://[^\s"<>]+/student-pss[^\s"<>]+',
                    ]

                    for pattern_idx, pattern in enumerate(patterns, 1):
                        matches = re.findall(pattern, search_body, re.IGNORECASE)

                        if matches:
                            print(f"[*] Pattern {pattern_idx} found {len(matches)} link(s)")
                            for match in matches:
                                link = match.rstrip('.,;)\'">')
                                
                                # Validate it's a password reset link
                                if 'strathmore.edu' in link:
                                    reset_link = link
                                    print(f"[+] Extracted reset link: {reset_link[:80]}...")
                                    break
                            
                        if reset_link:
                            break

                if reset_link:
                    # Mark email as read
                    mail.store(email_id, '+FLAGS', '\\Seen')
                    mail.logout()
                    return reset_link

                # If we reach here, show all found URLs for debugging
                print("[!] No reset link found. All URLs in email:")
                all_urls = re.findall(r'https?://[^\s"<>]+', search_body)
                for idx, url in enumerate(all_urls[:10], 1):
                    print(f"    {idx}. {url[:100]}")

                # Mark as read to avoid reprocessing
                mail.store(email_id, '+FLAGS', '\\Seen')

            mail.logout()

        except Exception as e:
            print(f"[-] Error checking email: {e}")
            traceback.print_exc()

        print(f"[*] Waiting {delay}s before retry...")
        time.sleep(delay)

    print("[-] Failed to retrieve reset link after all attempts")
    return None

def complete_password_reset(driver, reset_link, new_password):
    """
    Navigates to the reset link and sets the new password.
    Detects success by monitoring page transitions and checking for errors.

    Args:
        driver: Selenium WebDriver instance
        reset_link: URL of the password reset page
        new_password: The new password to set

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("\n" + "=" * 60)
        print("PHASE 3: COMPLETING PASSWORD RESET")
        print("=" * 60)

        print(f"[*] Navigating to reset link...")
        driver.get(reset_link)

        wait = WebDriverWait(driver, 15)
        time.sleep(2)  # Allow page time for any redirects

        if driver.current_url == FRONTEND_URL:
            print("[-] CRITICAL: The reset link immediately redirected back to the start page.")
            print("[!] This likely means the token in the URL was invalid or expired.")
            return False

        initial_url = driver.current_url
        print(f"[*] Successfully landed on reset page: {initial_url}")
        print(f"[*] Page title: {driver.title}")

        print("[*] Looking for password input fields...")
        try:
            password1_field = wait.until(EC.presence_of_element_located((By.NAME, "password1")))
            print("[+] Found 'New Password' field.")
            password2_field = driver.find_element(By.NAME, "password2")
            print("[+] Found 'Confirm Password' field.")
        except (TimeoutException, NoSuchElementException):
            print("[-] Could not find password input fields on the page.")
            return False

        print("[*] Entering new password...")
        password1_field.clear()
        password1_field.send_keys(new_password)
        print("[+] Password entered in first field")

        print("[*] Confirming password...")
        password2_field.clear()
        password2_field.send_keys(new_password)
        print("[+] Password entered in confirmation field")

        print("[*] Submitting password reset...")
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "password_button")))
        submit_button.click()
        print("[+] Change Password button clicked")
        
        print("[*] Waiting for success confirmation page...")
        try:
            success_keywords = ['success', 'changed', 'updated', 'complete']
            xpath_conditions = [f"contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{kw}')" for kw in success_keywords]
            success_xpath = f"//*[{' or '.join(xpath_conditions)}]"

            wait.until(
                EC.any_of(
                    EC.url_changes(initial_url),
                    EC.presence_of_element_located((By.XPATH, success_xpath))
                )
            )
            
            time.sleep(2)
            print("[+] Confirmation detected! Password reset was successful.")
            return True

        except TimeoutException:
            print("[-] Timed out waiting for the success page or message.")
            
            screenshot_path = Path(tempfile.gettempdir()) / "final_page_state.png"
            driver.save_screenshot(str(screenshot_path))
            print(f"[!] A screenshot of the final page has been saved to: {screenshot_path}")
            
            final_page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            error_keywords = ['error', 'fail', 'unable', 'requirement', 'invalid']
            for keyword in error_keywords:
                if keyword in final_page_text:
                    print(f"[!] Found potential error keyword on final page: '{keyword}'")
            
            return False

    except Exception as e:
        print(f"[-] An unexpected error occurred in Phase 3: {e}")
        traceback.print_exc()
        try:
            error_screenshot_path = Path(tempfile.gettempdir()) / "selenium_error_reset.png"
            driver.save_screenshot(str(error_screenshot_path))
        except:
            pass
        return False

# --- Main Workflow ---

def validate_environment():
    """Validates that all required environment variables are set."""
    required_vars = {
        "EMAIL_ADDRESS": EMAIL_ADDRESS,
        "EMAIL_PASSWORD": EMAIL_PASSWORD,
        "IMAP_SERVER": IMAP_SERVER,
        "USERNAME": USERNAME,
    }

    missing = [var for var, value in required_vars.items() if not value]

    if missing:
        print("[-] Missing required environment variables:")
        for var in missing:
            print(f"    - {var}")
        print("\n[*] Please set these in your .env file")
        return False

    return True

def setup_chrome_driver():
    """Sets up Chrome WebDriver with appropriate options for Docker or local/WSL."""
    options = webdriver.ChromeOptions()

    # Standard options for headless operation
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Check if running in Docker
    is_docker = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"

    print("[*] Setting up ChromeDriver...")
    if is_docker:
        print("[*] Docker environment detected. Using system ChromeDriver.")
        try:
            # In Docker, chromedriver is in the system PATH, so no args are needed
            service = ChromeService()
            driver = webdriver.Chrome(service=service, options=options)
            print("[+] ChromeDriver initialized successfully from system path.")
            return driver
        except Exception as e:
            print(f"[-] CRITICAL: Failed to initialize ChromeDriver in Docker: {e}")
            raise Exception("ChromeDriver setup failed in Docker container.")
    else:
        # Fallback to WSL/local environment using webdriver-manager
        if is_running_in_wsl():
            print("[*] WSL environment detected")
            if not install_chrome_wsl():
                raise Exception("Chrome installation failed in WSL")

        print("[*] Local/WSL/Windows environment detected. Using webdriver-manager.")
        try:
            driver_path = ChromeDriverManager().install()
            print(f"[*] ChromeDriver path from manager: {driver_path}")
            
            # This logic correctly finds the actual executable
            driver_dir = Path(driver_path).parent
            actual_driver = driver_dir / "chromedriver"
            
            if actual_driver.exists() and os.access(actual_driver, os.X_OK):
                service = ChromeService(executable_path=str(actual_driver))
            else:
                service = ChromeService(executable_path=driver_path)
            
            driver = webdriver.Chrome(service=service, options=options)
            print("[+] ChromeDriver initialized successfully.")
            return driver
        except Exception as e:
            raise Exception(f"Could not find or initialize a valid ChromeDriver executable: {e}")

def main():
    """Main workflow orchestration."""
    print("\n" + "=" * 60)
    print("STRATHMORE AUTOMATED PASSWORD RESET")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    # Validate environment
    if not validate_environment():
        return

    # Phase 0: Delete any old password reset emails to ensure we get the new one
    if not delete_previous_reset_emails():
        print("[-] Halting process due to email cleanup failure.")
        return

    driver = None

    try:
        # Setup browser
        driver = setup_chrome_driver()

        # Phase 1: Request password reset
        if not request_password_reset(driver, USERNAME):
            raise Exception("Failed to request password reset")

        # Phase 2: Retrieve reset link from email
        reset_link = get_reset_link_from_email()
        if not reset_link:
            raise Exception("Failed to retrieve reset link from email")

        # Phase 3: Generate secure password
        print("\n[*] Generating secure password...")
        new_password = generate_secure_password()
        print(f"[+] Generated password (length: {len(new_password)})")

        # Phase 4: Complete password reset
        if not complete_password_reset(driver, reset_link, new_password):
            raise Exception("Failed to complete password reset")

        # Phase 5: Log the new password
        log_new_password(USERNAME, new_password)

        # Success summary
        print("\n" + "=" * 60)
        print("✓ PASSWORD RESET COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Username: {USERNAME}")
        print(f"Password: {new_password}")
        print(f"Logged: {LOG_DIRECTORY}/")
        print("=" * 60)
        print("\n[!] IMPORTANT: Save this password securely!")

    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ WORKFLOW FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print("\n[*] Browser closed")

        print(f"[*] Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()