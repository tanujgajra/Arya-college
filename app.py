from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from pathlib import Path
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "attendance.db"

app = Flask(__name__)
app.secret_key = "change-this-secret-key-before-deployment"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS colleges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            state_id INTEGER NOT NULL,
            UNIQUE(name, state_id),
            FOREIGN KEY(state_id) REFERENCES states(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            FOREIGN KEY(college_id) REFERENCES colleges(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            roll_no TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            course TEXT NOT NULL,
            year TEXT NOT NULL,
            section TEXT NOT NULL,
            phone TEXT,
            UNIQUE(college_id, roll_no),
            UNIQUE(college_id, email),
            FOREIGN KEY(college_id) REFERENCES colleges(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER NOT NULL,
            subject_name TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            UNIQUE(college_id, subject_code),
            FOREIGN KEY(college_id) REFERENCES colleges(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
            UNIQUE(student_id, subject_id, date),
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        );
        
                # ============================================================
        # DEPARTMENTS / BRANCHES
        # ============================================================
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            UNIQUE(college_id, code),
            FOREIGN KEY(college_id) REFERENCES colleges(id) ON DELETE CASCADE
        );


        # ============================================================
        # SECTIONS
        # ============================================================
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            year TEXT NOT NULL,
            semester TEXT NOT NULL,
            academic_session TEXT NOT NULL,

            UNIQUE(
                college_id,
                department_id,
                name,
                year,
                semester,
                academic_session
            ),

            FOREIGN KEY(college_id)
                REFERENCES colleges(id)
                ON DELETE CASCADE,

            FOREIGN KEY(department_id)
                REFERENCES departments(id)
                ON DELETE CASCADE
        );


        # ============================================================
        # EMPLOYEES
        # Teachers, HOD, Accountant, Librarian, IT Staff, etc.
        # ============================================================
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            college_id INTEGER NOT NULL,
            department_id INTEGER,

            employee_code TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,

            phone TEXT,
            designation TEXT NOT NULL,

            joining_date TEXT,
            qualification TEXT,
            experience TEXT,

            salary REAL,
            employment_type TEXT,

            status TEXT NOT NULL DEFAULT 'Active',

            UNIQUE(college_id, employee_code),
            UNIQUE(college_id, email),

            FOREIGN KEY(college_id)
                REFERENCES colleges(id)
                ON DELETE CASCADE,

            FOREIGN KEY(department_id)
                REFERENCES departments(id)
                ON DELETE SET NULL
        );


        # ============================================================
        # EMPLOYEE RESPONSIBILITIES
        # Example:
        # Teacher
        # Mentor
        # Class Coordinator
        # Lab Incharge
        # Exam Coordinator
        # ============================================================
        CREATE TABLE IF NOT EXISTS employee_responsibilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            employee_id INTEGER NOT NULL,
            responsibility TEXT NOT NULL,

            UNIQUE(employee_id, responsibility),

            FOREIGN KEY(employee_id)
                REFERENCES employees(id)
                ON DELETE CASCADE
        );


        # ============================================================
        # TEACHER SUBJECT / SECTION ASSIGNMENTS
        # ============================================================
        CREATE TABLE IF NOT EXISTS teacher_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            employee_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            section_id INTEGER NOT NULL,

            academic_session TEXT NOT NULL,

            UNIQUE(
                employee_id,
                subject_id,
                section_id,
                academic_session
            ),

            FOREIGN KEY(employee_id)
                REFERENCES employees(id)
                ON DELETE CASCADE,

            FOREIGN KEY(subject_id)
                REFERENCES subjects(id)
                ON DELETE CASCADE,

            FOREIGN KEY(section_id)
                REFERENCES sections(id)
                ON DELETE CASCADE
        );


        # ============================================================
        # MENTOR ASSIGNMENTS
        # One teacher can mentor a section.
        # ============================================================
        CREATE TABLE IF NOT EXISTS mentor_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            employee_id INTEGER NOT NULL,
            section_id INTEGER NOT NULL,

            academic_session TEXT NOT NULL,

            UNIQUE(
                employee_id,
                section_id,
                academic_session
            ),

            FOREIGN KEY(employee_id)
                REFERENCES employees(id)
                ON DELETE CASCADE,

            FOREIGN KEY(section_id)
                REFERENCES sections(id)
                ON DELETE CASCADE
        );


        # ============================================================
        # EXAM TYPES
        # Admin/Teacher can later add:
        # Midterm 1, Midterm 2, Quiz, Assignment, External, etc.
        # ============================================================
        CREATE TABLE IF NOT EXISTS exam_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            college_id INTEGER NOT NULL,
            name TEXT NOT NULL,

            UNIQUE(college_id, name),

            FOREIGN KEY(college_id)
                REFERENCES colleges(id)
                ON DELETE CASCADE
        );


        # ============================================================
        # MARKS
        # ============================================================
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            exam_type_id INTEGER NOT NULL,

            marks REAL NOT NULL,
            max_marks REAL NOT NULL,

            updated_at TEXT,

            UNIQUE(
                student_id,
                subject_id,
                exam_type_id
            ),

            FOREIGN KEY(student_id)
                REFERENCES students(id)
                ON DELETE CASCADE,

            FOREIGN KEY(subject_id)
                REFERENCES subjects(id)
                ON DELETE CASCADE,

            FOREIGN KEY(exam_type_id)
                REFERENCES exam_types(id)
                ON DELETE CASCADE
        );
        """
    )

    # Seed states and sample colleges once.
    if conn.execute("SELECT COUNT(*) AS c FROM states").fetchone()["c"] == 0:
        seed_data = {
            "Rajasthan": [
                "Arya College of Engineering & IT",
                "JECRC University",
                "Poornima College of Engineering",
            ],
            "Maharashtra": [
                "Indian Institute of Technology Bombay",
                "Veermata Jijabai Technological Institute",
            ],
            "Gujarat": [
                "Nirma University",
                "Dhirubhai Ambani Institute of Information and Communication Technology",
            ],
            "Delhi": [
                "Delhi Technological University",
                "Netaji Subhas University of Technology",
            ],
            "Karnataka": [
                "Indian Institute of Science",
                "RV College of Engineering",
            ],
            "Uttar Pradesh": [
                "Indian Institute of Technology Kanpur",
                "Amity University Uttar Pradesh",
            ],
        }
        for state_name, colleges_list in seed_data.items():
            cur = conn.execute("INSERT INTO states (name) VALUES (?)", (state_name,))
            state_id = cur.lastrowid
            for college_name in colleges_list:
                conn.execute(
                    "INSERT INTO colleges (name, state_id) VALUES (?, ?)",
                    (college_name, state_id),
                )

    # Seed demo accounts once.
    college = conn.execute(
        "SELECT c.id FROM colleges c JOIN states s ON c.state_id = s.id "
        "WHERE s.name = ? AND c.name = ?",
        ("Rajasthan", "Arya College of Engineering & IT"),
    ).fetchone()

    if college:
        college_id = college["id"]
        if conn.execute("SELECT COUNT(*) AS c FROM admins").fetchone()["c"] == 0:
            conn.execute(
                "INSERT INTO admins (college_id, name, email, password_hash) VALUES (?, ?, ?, ?)",
                (
                    college_id,
                    "Demo Admin",
                    "admin@demo-college.com",
                    generate_password_hash("Admin@123"),
                ),
            )

        if conn.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"] == 0:
            conn.execute(
                "INSERT INTO students "
                "(college_id, name, roll_no, email, password_hash, course, year, section, phone) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    college_id,
                    "Tanuj Gajra",
                    "23CSE101",
                    "23cse101@demo-college.com",
                    generate_password_hash("Student@123"),
                    "B.Tech CSE",
                    "2nd Year",
                    "A",
                    "9999999999",
                ),
            )
            conn.execute(
                "INSERT OR IGNORE INTO subjects (college_id, subject_name, subject_code) VALUES (?, ?, ?)",
                (college_id, "Data Structures & Algorithms", "DSA"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO subjects (college_id, subject_name, subject_code) VALUES (?, ?, ?)",
                (college_id, "Python Programming", "PY"),
            )

    conn.commit()
    conn.close()


def require_role(role):
    return session.get("role") == role


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        college_id = request.form.get("college_id", type=int)
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        if role not in {"admin", "student"} or not college_id or not identifier or not password:
            return render_template("login.html", error="Please fill all login fields.")

        conn = get_db()
        if role == "admin":
            user = conn.execute(
                "SELECT * FROM admins WHERE college_id = ? AND email = ?",
                (college_id, identifier),
            ).fetchone()
        else:
            method = request.form.get("login_method")
            if method == "email":
                user = conn.execute(
                    "SELECT * FROM students WHERE college_id = ? AND email = ?",
                    (college_id, identifier),
                ).fetchone()
            else:
                user = conn.execute(
                    "SELECT * FROM students WHERE college_id = ? AND roll_no = ?",
                    (college_id, identifier),
                ).fetchone()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid login details.")

        session.clear()
        session["role"] = role
        session["college_id"] = college_id
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.get("/api/states")
def api_states():
    conn = get_db()
    states = conn.execute("SELECT id, name FROM states ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(row) for row in states])


@app.get("/api/colleges/<int:state_id>")
def api_colleges(state_id):
    conn = get_db()
    colleges = conn.execute(
        "SELECT id, name FROM colleges WHERE state_id = ? ORDER BY name",
        (state_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in colleges])


@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    college = conn.execute(
        "SELECT c.name AS college_name, s.name AS state_name "
        "FROM colleges c JOIN states s ON c.state_id = s.id WHERE c.id = ?",
        (session["college_id"],),
    ).fetchone()

    if session["role"] == "admin":
        student_count = conn.execute(
            "SELECT COUNT(*) AS c FROM students WHERE college_id = ?",
            (session["college_id"],),
        ).fetchone()["c"]
        subject_count = conn.execute(
            "SELECT COUNT(*) AS c FROM subjects WHERE college_id = ?",
            (session["college_id"],),
        ).fetchone()["c"]
        return render_template(
            "admin_dashboard.html",
            college=college,
            student_count=student_count,
            subject_count=subject_count,
        )

    student = conn.execute(
        "SELECT name, roll_no, email, course, year, section, phone "
        "FROM students WHERE id = ?",
        (session["user_id"],),
    ).fetchone()
    conn.close()
    return render_template("student_dashboard.html", college=college, student=student)


@app.route("/admin/students")
def students():
    if not require_role("admin"):
        return redirect(url_for("login"))
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, roll_no, email, course, year, section "
        "FROM students WHERE college_id = ? ORDER BY roll_no",
        (session["college_id"],),
    ).fetchall()
    conn.close()
    return render_template("students.html", students=rows)


@app.route("/admin/students/add", methods=["GET", "POST"])
def add_student():
    if not require_role("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        data = (
            request.form["name"].strip(),
            request.form["roll_no"].strip(),
            request.form["email"].strip().lower(),
            request.form["password"],
            request.form["course"].strip(),
            request.form["year"].strip(),
            request.form["section"].strip(),
            request.form.get("phone", "").strip(),
        )
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO students "
                "(college_id, name, roll_no, email, password_hash, course, year, section, phone) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (session["college_id"], data[0], data[1], data[2], generate_password_hash(data[3]), *data[4:]),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("students"))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("add_student.html", error="Roll number or email already exists.")

    return render_template("add_student.html")

# ============================================================
# EDIT STUDENT
# ============================================================
@app.route("/admin/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    # Only admin can edit students
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    # Find only the student belonging to the logged-in college
    student = conn.execute(
        """
        SELECT *
        FROM students
        WHERE id = ? AND college_id = ?
        """,
        (student_id, session["college_id"]),
    ).fetchone()

    # Student not found
    if not student:
        conn.close()
        return redirect(url_for("students"))

    # Update student
    if request.method == "POST":
        name = request.form["name"].strip()
        roll_no = request.form["roll_no"].strip()
        email = request.form["email"].strip().lower()
        course = request.form["course"].strip()
        year = request.form["year"].strip()
        section = request.form["section"].strip()
        phone = request.form.get("phone", "").strip()
        new_password = request.form.get("password", "")

        try:
            # If password is changed
            if new_password:
                conn.execute(
                    """
                    UPDATE students
                    SET name = ?,
                        roll_no = ?,
                        email = ?,
                        password_hash = ?,
                        course = ?,
                        year = ?,
                        section = ?,
                        phone = ?
                    WHERE id = ? AND college_id = ?
                    """,
                    (
                        name,
                        roll_no,
                        email,
                        generate_password_hash(new_password),
                        course,
                        year,
                        section,
                        phone,
                        student_id,
                        session["college_id"],
                    ),
                )

            # If password is left empty, keep old password
            else:
                conn.execute(
                    """
                    UPDATE students
                    SET name = ?,
                        roll_no = ?,
                        email = ?,
                        course = ?,
                        year = ?,
                        section = ?,
                        phone = ?
                    WHERE id = ? AND college_id = ?
                    """,
                    (
                        name,
                        roll_no,
                        email,
                        course,
                        year,
                        section,
                        phone,
                        student_id,
                        session["college_id"],
                    ),
                )

            conn.commit()
            conn.close()

            return redirect(url_for("students"))

        except sqlite3.IntegrityError:
            conn.close()

            return render_template(
                "edit_student.html",
                student=student,
                error="Roll number or email already exists.",
            )

    conn.close()

    return render_template(
        "edit_student.html",
        student=student,
    )


# ============================================================
# DELETE STUDENT
# ============================================================
@app.post("/admin/students/delete/<int:student_id>")
def delete_student(student_id):
    # Only admin can delete students
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    # Delete only from the logged-in college
    conn.execute(
        """
        DELETE FROM students
        WHERE id = ? AND college_id = ?
        """,
        (student_id, session["college_id"]),
    )

    conn.commit()
    conn.close()

    return redirect(url_for("students"))


@app.route("/admin/subjects", methods=["GET", "POST"])
def subjects():
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    if request.method == "POST":
        name = request.form["subject_name"].strip()
        code = request.form["subject_code"].strip().upper()
        try:
            conn.execute(
                "INSERT INTO subjects (college_id, subject_name, subject_code) VALUES (?, ?, ?)",
                (session["college_id"], name, code),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass

    rows = conn.execute(
        "SELECT id, subject_name, subject_code FROM subjects WHERE college_id = ? ORDER BY subject_code",
        (session["college_id"],),
    ).fetchall()
    conn.close()
    return render_template("subjects.html", subjects=rows)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
