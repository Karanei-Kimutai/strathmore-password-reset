# **Strathmore Password Reset Automation**

A complete, automated solution for resetting passwords on the Strathmore University student ams portal. This script handles the entire workflow—from initiating the request to securely logging the new password—with robust error handling, comprehensive documentation, and full containerization support.

## **Table of Contents**

* Why This Project?  
* Key Features  
* Documentation Hub  
* Getting Started  
  * Prerequisites  
  * Local Setup Instructions  
* Usage  
  * Running Locally  
  * Running with Docker  
* How It Works  
  * The 5 Phases of Automation  
* Project Structure  
* Security Best Practices  
* Troubleshooting  
* Contributing  
* License

## **Why This Project?**

Manually resetting a Strathmore AMS password can be a repetitive and time-consuming task. This project was created to eliminate that manual effort by providing a reliable, "fire-and-forget" script that handles every step of the process. It is designed for developers, students, and anyone who values automation for routine tasks. By containerizing the application, it ensures consistent and flawless execution in any environment.

## **Key Features**

* ✅ **End-to-End Automation**: Manages the entire password reset workflow without any manual intervention.  
* ✅ **Secure by Design**: Generates cryptographically strong passwords, uses .env for secrets, and includes a .gitignore to prevent accidental commits of sensitive data.  
* ✅ **Intelligent Email Handling**: Automatically cleans up old reset emails to prevent using stale links and robustly parses the new link from the email body.  
* ✅ **Pre-flight Configuration Tester**: A built-in script (test\_config.py) allows you to validate your setup (credentials, dependencies, etc.) before running the main application, saving time and preventing errors.  
* ✅ **Comprehensive Logging**: Securely logs newly created passwords to a timestamped file with restricted permissions for your records.  
* ✅ **Containerized & Portable**: Comes with a Dockerfile and docker-compose.yml for easy, consistent deployment on any machine with Docker installed .  
* ✅ **Excellent Documentation**: Includes a Quick Start guide for immediate setup and a detailed Cheatsheet for commands and troubleshooting.

## **Documentation Hub**

This repository contains multiple guides to help you get started and solve problems quickly.

* **For the fastest setup**, see the **QUICKSTART.md file**  
* **For a full list of commands and troubleshooting tips**, refer to the **CHEETSHEET.md file**

## **Getting Started**

### **Prerequisites**

* **Python** (version 3.8 or higher)  
* **Git** (for cloning the repository)  
* **Docker** and **Docker Compose** (for the containerized approach)

### **Local Setup Instructions**

**1\. Clone the Repository**
```
git clone https://github.com/karanei-kimutai/strathmore-password-reset.git
```
2\. Create and Activate a Virtual Environment  
This isolates the project's dependencies from your system.  

```
\# Create the environment  
python3 \-m venv venv

\# Activate it  
source venv/bin/activate  \# Linux/Mac/WSL  
\# OR  
venv\Scripts\activate     \# Windows
```
**3\. Install Dependencies**

```
pip install \--upgrade pip  
pip install \-r requirements.txt
```

4\. Configure Your Credentials  
Create a .env file to securely store your credentials. 
``` 
\# Create the .env file from the example template  
cp .env.example .env

\# Edit the file with your credentials  
nano .env \# Or your preferred text editor
```
Fill in the required variables as specified in the .env.example file. For Gmail, you **must** use an "App Password."

5\. Test Your Configuration  
Before running the main script, verify that your setup is correct:  
```
python test_config.py
```
If all tests pass, you are ready to proceed\!

## **Usage**

You can run this project either directly on your machine or within a Docker container.

### **Running Locally**

Ensure your virtual environment is activated, then run the main script:
```
python strathmore_password_reset.py
```
### **Running with Docker**

The recommended method for running this script is with Docker Compose, as it handles all the configuration for you.

**1\. Build the Docker Image**
```
docker-compose build
```
**2\. Run the Container**
```
docker-compose up
```
This command will start the container, run the script, and save the password log to your local passwords folder. The container will automatically stop when the script is finished.

## **How It Works**

The script is logically divided into a series of phases to ensure a reliable and transparent process.

### **The 5 Phases of Automation**

1. **Phase 0: Cleanup**: The script first connects to your email and deletes any old, unused password reset emails from Strathmore. This critical first step prevents the script from accidentally using an expired link.  
2. **Phase 1: Request Reset**: A headless Chrome browser is launched using Selenium. It navigates to the university's forgotten password page and submits your username to initiate the process.  
3. **Phase 2: Retrieve Link**: The script then monitors your email inbox in real-time, waiting for the new "Forgotten Password Verification" email. Once it arrives, it parses the HTML to extract the unique reset link.  
4. **Phase 3: Complete Reset**: The script navigates to the extracted reset link, generates a new, cryptographically secure password, fills out the new password and confirmation fields, and submits the form.  
5. **Phase 4: Log Password**: After a successful reset, the new password, username, and timestamp are logged to a secure text file in the passwords/ directory for your records.

## **Project Structure**
```
strathmore-password-reset/
├── strathmore_password_reset.py   # Main automation script
├── test_config.py                 # Configuration and dependency tester
├── requirements.txt               # Python package dependencies
│
├── .env                           # Your credentials (create from .env.example)
├── .env.example                   # Template for credentials
├── .gitignore                     # Git ignore rules for security
│
├── README.md                      # Full documentation (this file)
├── QUICKSTART.md                  # Bare essentials to get started
├── CHEATSHEET.md                  # Detailed commands and troubleshooting
│
├── Dockerfile                     # Configuration for Docker image
├── docker-compose.yml             # Docker orchestration file
│
├── venv/                          # Virtual environment (created by you)
└── passwords/
    ├── password_reset_YYYYMMDD_HHMMSS.txt
    └── password_log.txt
```


## **Security Best Practices**

⚠️ **Your security is paramount. Please follow these guidelines:**

* **Never Share Your .env File**: This file contains your credentials. The .gitignore file is already set up to prevent it from being committed to Git.  
* **Use an App Password**: For your email account (especially Gmail), do not use your main password. Generate and use an app-specific password for this script.  
* **Manage Log Files**: The script saves your new passwords in plain text. After retrieving your new password from the log file, store it in a secure password manager and **delete the log file**.  
* **Keep Dependencies Updated**: Periodically run ```pip install --upgrade -r requirements.txt``` to ensure you have the latest security patches for the project's dependencies.

## **Troubleshooting**

If you encounter any issues, your first step should be to run the configuration tester:
```
python test_config.py
```

For a comprehensive list of common errors and their solutions (e.g., email connection failures, Docker issues, dependency problems), please consult **CHEETSHEET.md**

## **Contributing**

Contributions are welcome\! If you have ideas for improvements, please open an issue to discuss what you would like to change. Pull requests are also welcome.