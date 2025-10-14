**Strathmore Password Reset Automation**
========================================

A complete, automated solution for resetting passwords on the Strathmore University student AMS portal. This script handles the entire workflow—from initiating the request to securely logging the new password—with robust error handling, comprehensive documentation, and full cross-platform support for **Windows, macOS, WSL, and Docker**.

**Table of Contents**
---------------------

*   Why This Project?
    
*   Key Features
    
*   Documentation Hub
    
*   System Requirements
    
*   **Getting Started (Local Setup)**
    
    *   Step 1: Clone the Repository
        
    *   Step 2: Set Up the Virtual Environment
        
    *   Step 3: Install Dependencies
        
    *   Step 4: Configure Your Credentials
        
    *   Step 5: Test Your Configuration
        
*   **How to Run Locally**
    
*   **Alternative Method: Running with Docker**
    
    *   Docker Setup
        
    *   How to Run
        
*   How It Works: The 5 Phases of Automation
    
*   Project Structure
    
*   Security Best Practices
    
*   **Troubleshooting & FAQ**
    
*   Contributing
    
*   License
    

**Why This Project?**
---------------------

Manually resetting a Strathmore AMS password is a repetitive task. This project eliminates that manual effort by providing a reliable, "fire-and-forget" script that handles every step. It is designed for developers and students who value automation for routine tasks. By containerizing the application, it ensures consistent and flawless execution in any environment.

**Key Features**
----------------

*   ✅ **End-to-End Automation**: Manages the entire password reset workflow without any manual intervention.
    
*   ✅ **Cross-Platform**: Works flawlessly on **Windows, macOS, Linux (WSL), and in Docker**.
    
*   ✅ **Secure by Design**: Generates cryptographically strong passwords, uses a .env file for secrets, and includes a .gitignore to prevent accidental commits of sensitive data.
    
*   ✅ **Intelligent Email Handling**: Automatically cleans up old reset emails and robustly parses the new link from the email body.
    
*   ✅ **Pre-flight Configuration Tester**: A built-in script (test\_config.py) validates your setup before running the main application.
    
*   ✅ **Containerized & Portable**: Comes with a fine-tuned Dockerfile and docker-compose.yml for easy, consistent deployment.
    

**Documentation Hub**
---------------------

This repository contains multiple guides to help you get started and solve problems quickly.

*   **For the fastest setup**, see the **QUICKSTART.md** file.
    
*   **For a full list of commands and troubleshooting tips**, refer to the **CHEATSHEET.md** file.
    

**System Requirements**
-----------------------

*   **Python** (version 3.8 or higher)
    
*   **Git** (for cloning the repository)
    
*   **Docker** and **Docker Compose** (optional, for the containerized approach)
    

**Getting Started (Local Setup)**
---------------------------------

Follow these steps to get the project running on your local machine.

### **Step 1: Clone the Repository**
   ```
  git clone https://github.com/Karanei-Kimutai/strathmore-password-reset.git  
  cd strathmore-password-reset
  ```
### **Step 2: Set Up the Virtual Environment**

This isolates the project's dependencies from your system.
   ```
   # Create the environment
  python3 -m venv venv  

   # Activate it
  source venv/bin/activate  # Linux/Mac/WSL  
# OR 
     venv\Scripts\activate     # Windows   `
  ```
### **Step 3: Install Dependencies**
```
   pip install --upgrade pip  
   pip install -r requirements.txt   `
```
### **Step 4: Configure Your Credentials**

Create a .env file from the template to securely store your credentials.
```
 # Create the .env file
   cp .env.example .env  

 # Edit the file with your credentials
   nano .env # Or your preferred text editor   `
```
Fill in the required variables. For Gmail, you **must** use an "App Password."

### **Step 5: Test Your Configuration**

Before running the main script, verify that your setup is correct:
```
   python test_config.py   `
```
If all tests pass, you are ready to proceed!

**How to Run Locally**
----------------------

Ensure your virtual environment is activated, then run the main script:
```
   python strathmore_password_reset.py   `
```
**Alternative Method: Running with Docker**
-------------------------------------------

Using Docker is an excellent alternative that avoids local setup and guarantees the script works the same way every time.

### **Docker Setup (First Time Only)**

1.  **Clone the Repository** (if you haven't already).
    
2.  **Configure Credentials**: Create and edit the .env file as described in the local setup (Step 4).
    
3.   **Run:** ```  docker-compose build```
    

### **How to Run with Docker**

Run the password reset anytime with a single command:
```
  docker-compose up   `
```
The new password log will be saved in the passwords/ directory.

 **Note:** See the troubleshooting section below on how to view these files.

**How It Works: The 5 Phases of Automation**
--------------------------------------------

1.  **Phase 0: Cleanup**: Deletes old, unused password reset emails from your inbox.
    
2.  **Phase 1: Request Reset**: A headless browser initiates the reset process on the student portal.
    
3.  **Phase 2: Retrieve Link**: The script monitors your email and extracts the unique reset link.
    
4.  **Phase 3: Complete Reset**: It navigates to the link and submits a new, securely generated password.
    
5.  **Phase 4: Log Password**: The new password is logged to a secure text file.
    

**Project Structure**
---------------------
```
strathmore-password-reset/
├── strathmore_password_reset.py      # Main automation script
├── test_config.py                    # Configuration and dependency tester
├── requirements.txt                  # Python package dependencies
│
├── .env                              # Your credentials (create from .env.example)
├── .env.example                      # Template for credentials
├── .gitignore                        # Git ignore rules for security
│
├── README.md                         # Full documentation (this file)
├── QUICKSTART.md                     # Bare essentials to get started
├── CHEATSHEET.md                     # Detailed commands and troubleshooting
│
├── Dockerfile                        # Configuration for Docker image
├── docker-compose.yml                # Docker orchestration file
│
├── venv/                             # Virtual environment (created by you)
│
└── passwords/                        # Secure password logs (auto-created)
    ├── password_reset_YYYYMMDD_HHMMSS.txt
    └── password_log.txt
```
**Security Best Practices**
---------------------------

*   **Never Share Your .env File**: This file contains your credentials and should never be committed to Git.
    
*   **Use an App Password**: For your email account, do not use your main password. Generate and use an app-specific password.
    
*   **Manage Log Files**: After retrieving your password, store it in a password manager and **delete the plain text file**.
    

## **Troubleshooting & FAQ**

* **"Permission Denied" When Opening Password Files (Docker Users):**  
  * **Why it happens:** The Docker container runs as the root user, so any files it creates (like the password logs) are owned by root. Your user on your machine does not have permission to read them.  
  * **Solution:** Use the sudo cat command in your terminal to view the file's contents with root privileges.
  ```  
    # Example:  
    sudo cat passwords/password\_reset\_20251015\_001000.txt
  ```
  * **To edit or delete the file:** You will need to change its ownership back to your user with ```sudo chown```.
  ```  
    # Example:  
    sudo chown $(id \-u):$(id \-g) passwords/password\_reset\_20251015\_001000.txt
  ```

* Email Connection Fails:  
  Run ```python test_config.py```. This is almost always caused by using a regular email password instead of an App Password. 

* "No module named X" Error:  
  Your virtual environment is not activated. Activate it and run ```pip install -r requirements.txt```.

## **Contributing**

Contributions are welcome\! Please open an issue to discuss any changes you would like to make.

## **License**

This project is open-source and available for personal use.