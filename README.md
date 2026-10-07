# LGU Socorro Web

A web-based prototype for the **Local Government Unit of Socorro**, built using Python and Flask.

The website provides public information about Socorro, LGU departments, tourism, services, transparency documents, news and events, while also allowing residents to submit service requests, contact messages, and department inquiries.

## Tech Stack

- Python
- Flask 3.0.3
- SQLite
- HTML
- CSS
- JavaScript
- Jinja2 Templates

## Features

- LGU homepage
- About Socorro
- News and events
- Tourism information
- Government services
- LGU department directory
- Department inquiry submission
- Inquiry reference tracking
- Transparency documents
- Contact form
- Site-wide search
- Staff login
- Staff submissions dashboard
- Service request management
- Department inquiry status management
- SQLite database
- CSRF protection for protected forms

---

# Running the Project Locally

## 1. Install Python

Make sure Python is installed on your computer.

Check by opening Command Prompt and running:

```bash
python --version
```

If Python is not installed, install a recent version of Python 3.

During installation on Windows, make sure:

```text
Add Python to PATH
```

is enabled.

---

## 2. Clone the Repository

Open Command Prompt, PowerShell, or Git Bash and run:

```bash
git clone https://github.com/edrianqt/LGU-Socorro-Web.git
```

Then enter the project directory:

```bash
cd LGU-Socorro-Web
```

---

## 3. Create a Virtual Environment

Creating a virtual environment is recommended so the project's Python packages remain isolated.

### Windows

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

After activation, your terminal should show something similar to:

```text
(.venv) C:\...\LGU-Socorro-Web>
```

---

## 4. Install Dependencies

Install the packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

The project currently requires:

```text
Flask==3.0.3
```

---

## 5. Run the Application

Run:

```bash
python app.py
```

The Flask development server should start and display an address similar to:

```text
http://127.0.0.1:5000
```

Open that address in your browser.

---

# Database Setup

No MySQL or external database server is required.

The project uses **SQLite**.

When the application starts, it automatically creates the required database and tables if they do not already exist.

The local database is stored at:

```text
instance/lgu_socorro.sqlite
```

The application creates tables for:

- Contact messages
- Service requests
- Department requests

The `instance/` directory is excluded from Git, so local database contents and generated credentials are not uploaded to the repository.

---

# Staff Login

The application includes a staff-only area for reviewing submissions.

Staff login page:

```text
http://127.0.0.1:5000/staff/login/
```

The default username is:

```text
staff
```

On the first run, the application automatically generates a secure random staff password.

The generated credentials are stored locally in:

```text
instance/staff-access.json
```

Open that file after starting the application to retrieve the generated password.

Example structure:

```json
{
  "username": "staff",
  "password": "generated-password"
}
```

Do not commit this file to GitHub.

After signing in, staff can access the submissions dashboard and review contact messages, service requests, and department inquiries.

---

# Optional Environment Variables

For deployment or a more permanent local configuration, the application supports environment variables.

### Staff Password

You can specify your own staff password using:

```text
SOCORRO_STAFF_PASSWORD
```

### Flask Session Secret

You can also specify the application's session secret using:

```text
SOCORRO_SECRET_KEY
```

If these are not provided, the application generates local values automatically.

---

# Project Structure

```text
LGU-Socorro-Web/
│
├── app.py
├── requirements.txt
├── .gitignore
├── DEPARTMENTS.md
│
├── data/
│   ├── site_data.json
│   └── departments.json
│
├── static/
│   └── CSS, JavaScript, images and other static assets
│
├── templates/
│   └── Flask/Jinja2 HTML templates
│
├── tests/
│   └── Application tests
│
├── _reference/
│   └── Reference resources
│
└── instance/
    ├── lgu_socorro.sqlite
    ├── staff-access.json
    └── session-secret.txt
```

The `instance/` directory is generated locally and ignored by Git.

---

# Running the Project After Initial Setup

After completing the installation once, you normally only need to run:

```bash
cd LGU-Socorro-Web
.venv\Scripts\activate
python app.py
```

Then visit:

```text
http://127.0.0.1:5000
```

---

# Getting the Latest Version

If the repository has already been cloned, retrieve the newest changes with:

```bash
git pull origin main
```

Then reinstall requirements if dependencies have changed:

```bash
pip install -r requirements.txt
```

Run the application again:

```bash
python app.py
```

---

# Troubleshooting

## `python` is not recognized

Python is either not installed or has not been added to your system PATH.

Install Python and enable **Add Python to PATH** during installation.

You can also try:

```bash
py --version
```

and use:

```bash
py app.py
```

instead.

## `No module named flask`

Activate the virtual environment:

```bash
.venv\Scripts\activate
```

Then install the requirements:

```bash
pip install -r requirements.txt
```

## Port 5000 is already in use

Another application may already be using Flask's default port.

Stop the other application and run the project again.

## Database problems

The local database is located at:

```text
instance/lgu_socorro.sqlite
```

For a fresh development database, stop the application, remove the local SQLite database, and start the application again.

The required tables will be recreated automatically.

---

# Repository

LGU Socorro Web

https://github.com/edrianqt/LGU-Socorro-Web

## Developer

Developed as an LGU website prototype for the **Municipality of Socorro**.
