# College Attendance Management System - Version 1

## Tech stack
- Python
- Flask
- SQLite
- HTML/CSS/JavaScript

## Features in Version 1
- State -> College cascading dropdown on login
- Student login by college email or roll number
- Admin login by college email
- Admin dashboard
- Student dashboard and profile
- Add/view students
- Add/view subjects
- Password hashing

## Run

1. Open a terminal in this folder.
2. Create a virtual environment:

```bash
python -m venv .venv
```

3. Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Install Flask:

```bash
pip install -r requirements.txt
```

5. Start the app:

```bash
python app.py
```

6. Open `http://127.0.0.1:5000`

## Demo credentials

### Student
- College: Arya College of Engineering & IT
- State: Rajasthan
- Roll No: `23CSE101`
- Email: `23cse101@demo-college.com`
- Password: `Student@123`

### Admin
- College: Arya College of Engineering & IT
- State: Rajasthan
- Email: `admin@demo-college.com`
- Password: `Admin@123`

## Important
The seeded college list is only a starter dataset for development. Before real deployment, replace/expand it with a verified official institution dataset and change the Flask secret key and demo passwords.
