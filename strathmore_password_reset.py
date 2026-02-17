import os
import time
import imaplib
import email
import smtplib
import re
import platform
import subprocess
import traceback
import secrets
import string
import tempfile # For cross-platform temporary directories
import ssl
from datetime import datetime
from pathlib import Path
from email.message import EmailMessage
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
try:
    from selenium.webdriver.common.selenium_manager import SeleniumManager
except ImportError:
    SeleniumManager = None
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# --- Configuration ---
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
STRATHMORE_USERNAME = os.getenv("STRATHMORE_USERNAME")  # Strathmore username (admission number)
FRONTEND_URL = "https://su-sso.strathmore.edu/student-pss/public/forgottenpassword"
PASSWORD_LENGTH = int(os.getenv("PASSWORD_LENGTH", "16"))
LOG_DIRECTORY = os.getenv("LOG_DIRECTORY", "passwords")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", EMAIL_ADDRESS)

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
            try:
                os.chmod(log_file, 0o600)
                os.chmod(master_log, 0o600)
                print("[+] File permissions set to owner-only (600)")
            except OSError as perm_err:
                 print(f"[!] Warning: Could not set file permissions: {perm_err}")


    except Exception as e:
        print(f"[-] CRITICAL: Failed to log password: {e}")
        print(f"[!] Password was: {password}")
        print("[!] SAVE THIS PASSWORD MANUALLY!")

def send_password_email(username, password):
    """
    Sends the new password to the configured notification email address.

    Args:
        username: User's username
        password: The new password to send

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not NOTIFICATION_EMAIL:
        print("[!] Notification email is not configured. Skipping password email.")
        return False

    try:
        print("\n" + "=" * 60)
        print("PHASE 6: SENDING PASSWORD NOTIFICATION EMAIL")
        print("=" * 60)
        print(f"[*] Sending password email to: {NOTIFICATION_EMAIL}")

        message = EmailMessage()
        message["Subject"] = f"Strathmore Password Reset - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message["From"] = EMAIL_ADDRESS
        message["To"] = NOTIFICATION_EMAIL
        message.set_content(
            "Your Strathmore password reset completed successfully.\n\n"
            f"Username: {username}\n"
            f"New Password: {password}\n\n"
            "Store this password securely and delete this email after use."
        )

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(message)

        print("[+] Password notification email sent successfully.")
        return True
    except Exception as e:
        print(f"[!] Warning: Failed to send password notification email: {e}")
        return False

# --- Environment Detection ---

def is_running_in_wsl():
    """Checks if running inside Windows Subsystem for Linux."""
    return 'WSL_DISTRO_NAME' in os.environ or 'microsoft' in platform.uname().release.lower()

def install_chrome_wsl():
    """Installs Google Chrome in WSL if not already present."""
    try:
        # Check if Chrome is already installed
        result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
        if result.returncode == 0:
            print("[*] Chrome is already installed in WSL.")
            return True

        print("[*] Chrome not found. Attempting to install Chrome in WSL...")
        print("[*] This requires sudo privileges.")

        # Commands to install Chrome
        commands = [
            "wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O /tmp/chrome.deb",
            "sudo dpkg -i /tmp/chrome.deb",
            "sudo apt-get update && sudo apt-get install -f -y", # Fix potential dependency issues
            "rm /tmp/chrome.deb"
        ]

        for cmd in commands:
            print(f"[*] Running: {cmd}")
            # Run command, check=True will raise an exception if it fails
            process = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"[*] Output:\n{process.stdout}")
            if process.stderr:
                 print(f"[*] Stderr:\n{process.stderr}")


        print("[+] Chrome installation appears successful!")

        # Verify installation again
        result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
        if result.returncode != 0:
            print("[-] Verification failed: 'which google-chrome' still doesn't find it.")
            return False

        print("[+] Chrome verified.")
        return True

    except subprocess.CalledProcessError as cpe:
         print(f"[-] Command failed: {cpe.cmd}")
         print(f"[-] Stderr: {cpe.stderr}")
         print(f"[-] Stdout: {cpe.stdout}")
         print("[!] Ensure you have sudo privileges and internet connectivity.")
         return False
    except Exception as e:
        print(f"[-] An unexpected error occurred during Chrome installation: {e}")
        return False

# --- Chromedriver Resolution Helper (REMOVED - Selenium Manager handles this) ---

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

        wait = WebDriverWait(driver, 20) # Increased wait time

        # Wait for page to load - more robust wait for username field
        print("[*] Waiting for forgotten password page to load...")
        username_input = wait.until(EC.visibility_of_element_located((By.ID, "sAMAccountName")))
        print(f"[+] Page loaded: {driver.title}")

        # Enter username
        print(f"[*] Entering username: {username}")
        username_input.clear()
        username_input.send_keys(username)
        print("[+] Username entered")

        # Click Search button - wait for it to be clickable
        print("[*] Clicking Search button...")
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "submitBtn")))
        search_button.click()
        print("[+] Search button clicked")

        # Optional: Add a wait here if there's a specific message to confirm after search
        # Example: wait.until(EC.visibility_of_element_located((By.ID, "someConfirmationMessageId")))
        # print("[+] Confirmation message appeared.")

        time.sleep(3) # Keep a small delay for safety
        print(f"[+] Current page after search: {driver.current_url}")

        return True

    except TimeoutException:
         print("[-] Timed out waiting for elements on the password request page.")
         traceback.print_exc()
    except Exception as e:
        print(f"[-] Error during password reset request: {e}")
        traceback.print_exc()

    # Save screenshot on error
    try:
        screenshot_path = Path(tempfile.gettempdir()) / "selenium_error_request.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"[*] Screenshot saved: {screenshot_path}")
    except Exception as screenshot_err:
        print(f"[!] Failed to save screenshot: {screenshot_err}")

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
                # Flag email for deletion
                mail.store(mail_id, '+FLAGS', '\\Deleted')

            print("[*] Expunging deleted emails...")
            # Permanently remove flagged emails
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

def get_reset_link_from_email(retries=10, delay=15): # Increased delay
    """
    Retrieves the password reset link from email inbox.

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

            # Search for password reset email (unseen first, then any)
            search_queries = [
                '(UNSEEN FROM "student-pss-noreply@strathmore.edu" SUBJECT "Forgotten Password Verification")',
                '(FROM "student-pss-noreply@strathmore.edu" SUBJECT "Forgotten Password Verification")',
            ]

            email_id = None
            for query in search_queries:
                status, messages = mail.search(None, query)
                if status == "OK" and messages[0]:
                    email_id = messages[0].split()[-1] # Get the latest matching email
                    print(f"[+] Found email (ID: {email_id.decode()}) using query: {query}")
                    break

            if not email_id:
                print(f"[*] Email not found yet. Waiting {delay}s...")
                mail.logout()
                time.sleep(delay)
                continue

            # Fetch the full email content
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            mail.logout() # Logout after fetching

            reset_link = None
            for response_part in msg_data:
                if not isinstance(response_part, tuple):
                    continue

                msg = email.message_from_bytes(response_part[1])

                # Extract email body (HTML preferred)
                body = ""
                html_body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        charset = part.get_content_charset() or 'utf-8'
                        if content_type in ["text/plain", "text/html"] and part.get_payload(decode=True):
                            try:
                                payload_decoded = part.get_payload(decode=True).decode(charset, errors='replace')
                                if content_type == "text/html":
                                    html_body = payload_decoded
                                else:
                                    body = payload_decoded
                            except Exception as decode_err:
                                print(f"[!] Warning: Error decoding part ({content_type}): {decode_err}")
                else: # Not multipart
                    charset = msg.get_content_charset() or 'utf-8'
                    try:
                        payload = msg.get_payload(decode=True)
                        if payload:
                             body = payload.decode(charset, errors='replace')
                             # If content type is HTML, also store it in html_body
                             if "text/html" in msg.get_content_type():
                                 html_body = body
                    except Exception as decode_err:
                         print(f"[!] Warning: Error decoding single part body: {decode_err}")

                search_body = html_body if html_body else body
                if not search_body:
                    print("[!] Email body content seems empty.")
                    continue # Try next response part if any

                print(f"[*] Extracted email body length: {len(search_body)} characters")

                # Save for debugging
                debug_file = Path(tempfile.gettempdir()) / f"email_body_{email_id.decode()}.html"
                try:
                    debug_file.write_text(search_body, encoding='utf-8', errors='replace')
                    print(f"[*] Email content saved for debugging: {debug_file}")
                except Exception as save_err:
                    print(f"[!] Could not save email content: {save_err}")


                # --- Link Extraction Logic ---
                # Try BeautifulSoup first for HTML
                if html_body:
                    try:
                        soup = BeautifulSoup(html_body, 'html.parser')
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            # UPDATED: Look for the new pattern OR the old one just in case
                            if ('su-sso.strathmore.edu/student-pss/public/verifytoken' in href or
                                'su-sso.strathmore.edu/student-pss/public/forgottenpassword/' in href): # Added check for new pattern
                                reset_link = href
                                print(f"[+] Found reset link via BeautifulSoup: {reset_link[:80]}...")
                                break # Found the link
                    except Exception as soup_err:
                        print(f"[!] Error parsing HTML with BeautifulSoup: {soup_err}")

                # Fallback to Regex if BS fails or no link found
                if not reset_link:
                    # UPDATED: Add regex for the new pattern and keep old one
                    patterns = [
                         r'(https?://su-sso\.strathmore\.edu/student-pss/public/forgottenpassword/[^\s"\'<>]+)', # New pattern observed
                         r'(https?://su-sso\.strathmore\.edu/student-pss/public/verifytoken/[^\s"\'<>]+)'  # Original pattern
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, search_body, re.IGNORECASE)
                        if matches:
                            reset_link = matches[0].rstrip('.,;)\'">') # Get the first match and clean it
                            print(f"[+] Found reset link via Regex: {reset_link[:80]}...")
                            break # Exit pattern loop once found

                    if not reset_link:
                        print("[!] No reset link found using specific patterns.")
                        # Optional: Log all found URLs for deeper inspection if needed
                        all_urls = re.findall(r'https?://[^\s"\'<>]+', search_body)
                        if all_urls:
                             print("[!] All URLs found in body (for debugging):")
                             for i, url in enumerate(all_urls[:5]): # Show first 5
                                 print(f"    - {url[:100]}")


                if reset_link:
                    # Mark email as read (Connect again briefly)
                    try:
                        mail_marker = imaplib.IMAP4_SSL(IMAP_SERVER)
                        mail_marker.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                        mail_marker.select("inbox")
                        mail_marker.store(email_id, '+FLAGS', '\\Seen')
                        mail_marker.logout()
                        print("[+] Marked email as read.")
                    except Exception as mark_err:
                        print(f"[!] Warning: Could not mark email as read: {mark_err}")

                    return reset_link # Success!

            # If loop finishes without finding link in any part
            print("[-] Reset link not found in fetched email content.")

        except imaplib.IMAP4.error as imap_err:
             print(f"[-] IMAP Error: {imap_err}")
             print("[!] Check IMAP settings, credentials, and App Password status.")
             # No retry on critical IMAP errors
             return None
        except Exception as e:
            print(f"[-] Unexpected error checking email: {e}")
            traceback.print_exc()

        # If email was not found or link extraction failed, wait before retrying
        print(f"[*] Waiting {delay}s before next email check...")
        time.sleep(delay)

    print("[-] Failed to retrieve reset link after all attempts.")
    return None

def complete_password_reset(driver, reset_link, new_password):
    """
    Navigates to the reset link and sets the new password.

    Args:
        driver: Selenium WebDriver instance
        reset_link: URL of the password reset page
        new_password: The new password to set

    Returns:
        bool: True if successful, False otherwise
    """
    screenshot_saved = False # Flag to avoid saving multiple screenshots for one error
    try:
        print("\n" + "=" * 60)
        print("PHASE 3: COMPLETING PASSWORD RESET")
        print("=" * 60)

        print(f"[*] Navigating to reset link: {reset_link[:80]}...")
        driver.get(reset_link)

        wait = WebDriverWait(driver, 25) # Slightly longer wait
        time.sleep(3)  # Allow page to fully render after navigation

        initial_url = driver.current_url
        print(f"[*] Landed on page: {initial_url}")
        print(f"[*] Page title: {driver.title}")

        # Check for immediate signs of invalid/expired token on the page
        page_source_lower = driver.page_source.lower()
        if "invalid token" in page_source_lower or "link has expired" in page_source_lower or "token is required" in page_source_lower:
             print("[-] Error message found on page: Link appears invalid, expired, or token missing.")
             return False

        print("[*] Looking for password input fields using confirmed names...")
        password1_field = None
        password2_field = None
        try:
            # Using the confirmed names from the HTML structure
            print("[*] Trying locators: name='password1', name='password2'")
            password1_field = wait.until(EC.visibility_of_element_located((By.NAME, "password1")))
            password2_field = wait.until(EC.visibility_of_element_located((By.NAME, "password2")))
            print("[+] Found fields by name='password1' and 'password2'.")

        except (TimeoutException, NoSuchElementException):
            print("[-] Could not find password input fields using names 'password1' and 'password2'.")
            return False


        # Ensure fields are interactable before sending keys
        print("[*] Ensuring fields are interactable...")
        wait.until(EC.element_to_be_clickable(password1_field))
        wait.until(EC.element_to_be_clickable(password2_field))

        print("[*] Entering new password...")
        password1_field.clear()
        password1_field.send_keys(new_password)
        print("[+] Password entered.")

        print("[*] Confirming password...")
        password2_field.clear()
        password2_field.send_keys(new_password)
        print("[+] Password confirmed.")

        print("[*] Submitting password reset...")
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "password_button")))
        submit_button.click()
        print("[+] Submit button clicked.")

        # --- ADDED DELAY ---
        print("[*] Waiting 2 seconds for server processing...")
        time.sleep(2)
        # --- END ADDED DELAY ---

        # --- UPDATED SUCCESS CONFIRMATION ---
        print("[*] Waiting up to 20s for success page URL and content...")
        try:
            # 1. Wait specifically for the URL to contain 'processAction=complete'
            wait.until(EC.url_contains("processAction=complete"))
            print("[+] Success URL detected.")

            # 2. Wait for the specific success text to be visible
            success_text = "The password has been changed successfully."
            success_element = wait.until(EC.visibility_of_element_located((By.XPATH, f"//*[contains(text(), '{success_text}')]")))
            print(f"[+] Success message confirmed: '{success_element.text}'")

            return True # Both conditions met

        except TimeoutException:
            # Timeout - check for specific error messages before failing
            print("[-] Timed out waiting for success URL or success message.")
            page_source_lower = driver.page_source.lower()
            error_keywords = ['error', 'fail', 'unable', 'invalid token', 'link has expired', 'did not match', 'problem', 'incorrect', 'requirement']
            found_errors = [kw for kw in error_keywords if kw in page_source_lower]

            if found_errors:
                print(f"[!] Found error keyword(s) on final page: {', '.join(found_errors)}")
                # Attempt to capture specific error message
                try:
                    error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .message, #message, [class*='error'], [id*='error']")
                    if error_elements:
                        for elem in error_elements:
                             if elem.is_displayed() and elem.text.strip():
                                 print(f"[!] Specific Error Message Found: '{elem.text.strip()}'")
                                 break
                    else:
                         print("[!] Could not find specific error message element, but keywords were present.")
                except Exception as find_err:
                     print(f"[!] Tried to find specific error message element but failed: {find_err}")

                screenshot_saved = True
                error_screenshot_path = Path(tempfile.gettempdir()) / "selenium_error_final_page.png"
                driver.save_screenshot(str(error_screenshot_path))
                print(f"[*] Screenshot of error page saved: {error_screenshot_path}")
                return False
            else:
                # No clear success, no clear error
                print("[!] Did not reach success page/message and no clear error message found after timeout. Please check the final screenshot.")
                screenshot_saved = True
                timeout_screenshot_path = Path(tempfile.gettempdir()) / "selenium_timeout_final_page.png"
                driver.save_screenshot(str(timeout_screenshot_path))
                print(f"[*] Screenshot of timeout page saved: {timeout_screenshot_path}")
                return False
        # --- END UPDATED SUCCESS CONFIRMATION ---

    except Exception as e:
        print(f"[-] An unexpected error occurred in Phase 3: {e}")
        traceback.print_exc()
        # Ensure screenshot is saved even on unexpected errors, if not already saved
        if not screenshot_saved and 'driver' in locals() and driver:
             try:
                 error_screenshot_path = Path(tempfile.gettempdir()) / "selenium_error_unexpected.png"
                 driver.save_screenshot(str(error_screenshot_path))
                 print(f"[*] Screenshot saved due to unexpected error: {error_screenshot_path}")
             except Exception as screenshot_err:
                 print(f"[!] Failed to save unexpected error screenshot: {screenshot_err}")
        return False # Return False if any exception occurred


# --- Main Workflow ---

def validate_environment():
    """Validates that all required environment variables are set."""
    required_vars = {
        "EMAIL_ADDRESS": EMAIL_ADDRESS,
        "EMAIL_PASSWORD": EMAIL_PASSWORD,
        "IMAP_SERVER": IMAP_SERVER,
        "STRATHMORE_USERNAME": STRATHMORE_USERNAME,
    }

    missing = [var for var, value in required_vars.items() if not value]

    if missing:
        print("[-] Missing required environment variables:")
        for var in missing:
            print(f"    - {var}")
        print("\n[*] Please set these in your .env file")
        return False

    # Basic email format check
    if not EMAIL_ADDRESS or "@" not in EMAIL_ADDRESS:
        print(f"[-] Invalid or missing EMAIL_ADDRESS: {EMAIL_ADDRESS}")
        return False
    if not STRATHMORE_USERNAME:
         print(f"[-] Missing STRATHMORE_USERNAME.")
         return False

    return True

def setup_chrome_driver():
    """Sets up Chrome WebDriver using Selenium Manager for local/WSL
       or explicit path for Docker."""
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
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    # Check if running in Docker
    is_docker = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"

    print("[*] Setting up ChromeDriver...")
    if is_docker:
        print("[*] Docker environment detected. Using explicit system ChromeDriver path.")
        try:
            # Explicitly point to the chromedriver installed by the Dockerfile
            driver_path_docker = "/usr/local/bin/chromedriver-linux64/chromedriver"
            if not Path(driver_path_docker).exists():
                 driver_path_docker = "/usr/local/bin/chromedriver" # Fallback

            if not Path(driver_path_docker).exists() or not os.access(driver_path_docker, os.X_OK):
                 raise FileNotFoundError("Chromedriver executable not found or not executable at expected Docker paths.")

            print(f"[*] Using driver path: {driver_path_docker}")
            service = ChromeService(executable_path=driver_path_docker)
            driver = webdriver.Chrome(service=service, options=options)
            print("[+] ChromeDriver initialized successfully from system path.")
            return driver
        except Exception as e:
            print(f"[-] CRITICAL: Failed to initialize ChromeDriver in Docker: {e}")
            traceback.print_exc()
            raise Exception("ChromeDriver setup failed in Docker container.")
    else:
        # For local/WSL runs, rely on Selenium Manager
        print("[*] Local/WSL/Windows environment detected. Using Selenium Manager.")

        # Optional: Check for Chrome in WSL and attempt install if missing
        if is_running_in_wsl():
             print("[*] WSL environment detected")
             # Check if chrome exists, but don't fail immediately if install fails
             try:
                 subprocess.run(['which', 'google-chrome'], check=True, capture_output=True)
                 print("[*] Chrome is already installed in WSL.")
             except (subprocess.CalledProcessError, FileNotFoundError):
                 print("[!] Google Chrome not found in WSL path.")
                 # Attempt install, but proceed even if it fails - Selenium Manager might still work
                 install_chrome_wsl()


        try:
            service = None

            # On Windows, explicitly resolve the driver path through Selenium Manager.
            # This avoids stale chromedriver binaries in PATH overriding the resolved version.
            if platform.system() == "Windows" and SeleniumManager is not None:
                print("[*] Windows detected. Resolving ChromeDriver path via Selenium Manager...")
                manager = SeleniumManager()
                resolved_paths = manager.binary_paths(["--browser", "chrome"])
                resolved_driver_path = resolved_paths.get("driver_path")
                resolved_browser_path = resolved_paths.get("browser_path")

                if resolved_browser_path and Path(resolved_browser_path).exists():
                    options.binary_location = resolved_browser_path

                if resolved_driver_path and Path(resolved_driver_path).exists():
                    print(f"[*] Using Selenium Manager driver path: {resolved_driver_path}")
                    service = ChromeService(executable_path=resolved_driver_path)
                else:
                    print("[!] Selenium Manager did not return a usable driver path. Falling back to default ChromeService.")
            elif platform.system() == "Windows":
                print("[!] SeleniumManager class not available in this Selenium version. Falling back to default ChromeService.")

            if service is None:
                # Initialize ChromeService WITHOUT executable_path.
                # Selenium Manager will automatically find/download the driver.
                print("[*] Initializing ChromeService (Selenium Manager will handle driver)...")
                service = ChromeService()

            driver = webdriver.Chrome(service=service, options=options)
            print("[+] ChromeDriver initialized successfully via Selenium Manager.")
            return driver
        except WebDriverException as wde:
             # Catch specific Selenium errors, often version mismatch or driver not found
             print(f"[-] Selenium WebDriverException during setup: {wde}")
             print("[!] This might indicate Selenium Manager failed to find/download the correct driver.")
             print("[!] Ensure Google Chrome is installed and accessible in your PATH.")
             print("[!] Or, try manually installing chromedriver and adding it to your PATH.")
             traceback.print_exc()
             raise Exception(f"Failed to initialize ChromeDriver using Selenium Manager: {wde}")
        except Exception as e:
            print(f"[-] Unexpected error during Selenium Manager setup: {e}")
            traceback.print_exc()
            raise Exception(f"Could not initialize ChromeDriver using Selenium Manager: {e}")


def main():
    """Main workflow orchestration."""
    print("\n" + "=" * 60)
    print("STRATHMORE AUTOMATED PASSWORD RESET")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"OS: {platform.system()}")
    print("=" * 60 + "\n")

    # Validate environment first
    if not validate_environment():
        return 1 # Indicate failure

    # Phase 0: Clean up emails
    if not delete_previous_reset_emails():
        # Log a warning but continue? Or halt? Let's halt for safety.
        print("[-] Halting process due to email cleanup failure. Old links might interfere.")
        return 1 # Indicate failure

    driver = None
    exit_code = 0 # Assume success unless an error occurs

    try:
        # Setup browser
        driver = setup_chrome_driver()

        # Phase 1: Request password reset
        if not request_password_reset(driver, STRATHMORE_USERNAME):
            raise Exception("Failed to request password reset")

        # Phase 2: Retrieve reset link from email
        reset_link = get_reset_link_from_email()
        if not reset_link:
            raise Exception("Failed to retrieve reset link from email")

        # Phase 3: Generate secure password
        print("\n[*] Generating secure password...")
        new_password = generate_secure_password()
        print(f"[+] Generated password (length: {len(new_password)})")

        # Phase 4: Complete password reset using the retrieved link
        if not complete_password_reset(driver, reset_link, new_password):
            raise Exception("Failed to complete password reset")

        # Phase 5: Log the new password securely
        log_new_password(STRATHMORE_USERNAME, new_password)

        # Phase 6: Send password notification email
        email_sent = send_password_email(STRATHMORE_USERNAME, new_password)

        # Success summary
        print("\n" + "=" * 60)
        print("✓ PASSWORD RESET COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Username: {STRATHMORE_USERNAME}")
        print(f"Password: {new_password}")
        print(f"Logged to files in: {LOG_DIRECTORY}/")
        print(f"Email sent to: {NOTIFICATION_EMAIL if email_sent else 'FAILED'}")
        print("=" * 60)
        print("\n[!] IMPORTANT: Retrieve password from log, store securely, and delete log file.")

    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ WORKFLOW FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        # Only print traceback if it's not a simple Exception we raised
        if not isinstance(e, Exception) or traceback.format_exc().strip() != f"Exception: {e}":
             traceback.print_exc()
        exit_code = 1 # Indicate failure

    finally:
        if driver:
            try:
                driver.quit()
                print("\n[*] Browser closed")
            except Exception as quit_err:
                 print(f"[!] Error closing browser: {quit_err}")


        print(f"[*] Script finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # Exit with the determined code
        return exit_code

if __name__ == "__main__":
    status = main()
    exit(status)
