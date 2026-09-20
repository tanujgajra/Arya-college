# ============================================================
# COLLEGE ATTENDANCE & ACADEMIC MANAGEMENT SYSTEM
# Main Flask Application
# ============================================================

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from pathlib import Path
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash


# ============================================================
# APPLICATION SETTINGS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "attendance.db"

app = Flask(__name__)
app.secret_key = "arya-college-demo-secret-key"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ============================================================
# DATABASE SETUP
# ============================================================

def init_db():
    conn = get_db()

    conn.executescript(
        """
        -- ====================================================
        -- STATES
        -- ====================================================
        CREATE TABLE IF NOT EXISTS states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- ====================================================
        -- COLLEGES
        -- ====================================================
        CREATE TABLE IF NOT EXISTS colleges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            state_id INTEGER NOT NULL,
            UNIQUE(name, state_id),
            FOREIGN KEY(state_id) REFERENCES states(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- ADMINS
        -- ====================================================
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            FOREIGN KEY(college_id) REFERENCES colleges(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- DEPARTMENTS / BRANCHES
        -- ====================================================
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            UNIQUE(college_id, code),
            FOREIGN KEY(college_id) REFERENCES colleges(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- SECTIONS
        -- ====================================================
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
            FOREIGN KEY(college_id) REFERENCES colleges(id)
                ON DELETE CASCADE,
            FOREIGN KEY(department_id) REFERENCES departments(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- STUDENTS
        -- ====================================================
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
            FOREIGN KEY(college_id) REFERENCES colleges(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- SUBJECTS
        -- ====================================================
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER NOT NULL,
            subject_name TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            UNIQUE(college_id, subject_code),
            FOREIGN KEY(college_id) REFERENCES colleges(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- EMPLOYEES
        -- ====================================================
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
            FOREIGN KEY(college_id) REFERENCES colleges(id)
                ON DELETE CASCADE,
            FOREIGN KEY(department_id) REFERENCES departments(id)
                ON DELETE SET NULL
        );

        -- ====================================================
        -- EMPLOYEE RESPONSIBILITIES
        -- ====================================================
        CREATE TABLE IF NOT EXISTS employee_responsibilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            responsibility TEXT NOT NULL,
            UNIQUE(employee_id, responsibility),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- TEACHER ASSIGNMENTS
        -- ====================================================
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
            FOREIGN KEY(employee_id) REFERENCES employees(id)
                ON DELETE CASCADE,
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
                ON DELETE CASCADE,
            FOREIGN KEY(section_id) REFERENCES sections(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- MENTOR ASSIGNMENTS
        -- ====================================================
        CREATE TABLE IF NOT EXISTS mentor_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            section_id INTEGER NOT NULL,
            academic_session TEXT NOT NULL,
            UNIQUE(employee_id, section_id, academic_session),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
                ON DELETE CASCADE,
            FOREIGN KEY(section_id) REFERENCES sections(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- ATTENDANCE
        -- ====================================================
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
            UNIQUE(student_id, subject_id, date),
            FOREIGN KEY(student_id) REFERENCES students(id)
                ON DELETE CASCADE,
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- EXAM TYPES
        -- ====================================================
        CREATE TABLE IF NOT EXISTS exam_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(college_id, name),
            FOREIGN KEY(college_id) REFERENCES colleges(id)
                ON DELETE CASCADE
        );

        -- ====================================================
        -- MARKS
        -- ====================================================
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            exam_type_id INTEGER NOT NULL,
            marks REAL NOT NULL,
            max_marks REAL NOT NULL,
            updated_at TEXT,
            UNIQUE(student_id, subject_id, exam_type_id),
            FOREIGN KEY(student_id) REFERENCES students(id)
                ON DELETE CASCADE,
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
                ON DELETE CASCADE,
            FOREIGN KEY(exam_type_id) REFERENCES exam_types(id)
                ON DELETE CASCADE
        );
        """
    )

    # ========================================================
    # SAMPLE STATES + COLLEGES
    # ========================================================
    if conn.execute("SELECT COUNT(*) AS total FROM states").fetchone()["total"] == 0:
        sample_data = {
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

        for state_name, college_list in sample_data.items():
            state_cursor = conn.execute(
                "INSERT INTO states (name) VALUES (?)",
                (state_name,),
            )
            state_id = state_cursor.lastrowid

            for college_name in college_list:
                conn.execute(
                    "INSERT INTO colleges (name, state_id) VALUES (?, ?)",
                    (college_name, state_id),
                )

    # ========================================================
    # DEMO COLLEGE
    # ========================================================
    college = conn.execute(
        """
        SELECT c.id, c.name
        FROM colleges c
        JOIN states s ON c.state_id = s.id
        WHERE s.name = ? AND c.name = ?
        """,
        ("Rajasthan", "Arya College of Engineering & IT"),
    ).fetchone()

    if college:
        college_id = college["id"]

        # ----------------------------------------------------
        # DEMO ADMIN
        # ----------------------------------------------------
        if not conn.execute(
            "SELECT id FROM admins WHERE college_id = ? AND email = ?",
            (college_id, "admin@demo-college.com"),
        ).fetchone():
            conn.execute(
                """
                INSERT INTO admins
                (college_id, name, email, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (
                    college_id,
                    "Demo Admin",
                    "admin@demo-college.com",
                    generate_password_hash("Admin@123"),
                ),
            )

        # ----------------------------------------------------
        # DEMO STUDENT
        # ----------------------------------------------------
        if not conn.execute(
            "SELECT id FROM students WHERE college_id = ? AND roll_no = ?",
            (college_id, "23CSE101"),
        ).fetchone():
            conn.execute(
                """
                INSERT INTO students
                (college_id, name, roll_no, email, password_hash,
                 course, year, section, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
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

        # ----------------------------------------------------
        # DEMO SUBJECTS
        # ----------------------------------------------------
        for subject_name, subject_code in [
            ("Data Structures & Algorithms", "DSA"),
            ("Python Programming", "PY"),
        ]:
            conn.execute(
                """
                INSERT OR IGNORE INTO subjects
                (college_id, subject_name, subject_code)
                VALUES (?, ?, ?)
                """,
                (college_id, subject_name, subject_code),
            )

        # ----------------------------------------------------
        # DEMO DEPARTMENT
        # ----------------------------------------------------
        conn.execute(
            """
            INSERT OR IGNORE INTO departments
            (college_id, name, code)
            VALUES (?, ?, ?)
            """,
            (college_id, "Computer Science & Engineering", "CSE"),
        )

        department = conn.execute(
            """
            SELECT id FROM departments
            WHERE college_id = ? AND code = ?
            """,
            (college_id, "CSE"),
        ).fetchone()

        if department:
            department_id = department["id"]

            # ------------------------------------------------
            # DEMO SECTIONS
            # ------------------------------------------------
            for section_name in ["A", "B"]:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO sections
                    (college_id, department_id, name, year,
                     semester, academic_session)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        college_id,
                        department_id,
                        section_name,
                        "2nd Year",
                        "3rd Semester",
                        "2026-27",
                    ),
                )

            # ------------------------------------------------
            # DEMO TEACHER
            # ------------------------------------------------
            if not conn.execute(
                "SELECT id FROM employees WHERE college_id = ? AND employee_code = ?",
                (college_id, "EMP1001"),
            ).fetchone():
                employee_cursor = conn.execute(
                    """
                    INSERT INTO employees
                    (college_id, department_id, employee_code, name,
                     email, password_hash, phone, designation,
                     joining_date, qualification, experience,
                     salary, employment_type, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        college_id,
                        department_id,
                        "EMP1001",
                        "Demo Teacher",
                        "teacher@demo-college.com",
                        generate_password_hash("Teacher@123"),
                        "8888888888",
                        "Assistant Professor",
                        "2024-07-01",
                        "M.Tech",
                        "5 Years",
                        55000,
                        "Full Time",
                        "Active",
                    ),
                )
                employee_id = employee_cursor.lastrowid

                for responsibility in ["Subject Teacher", "Mentor"]:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO employee_responsibilities
                        (employee_id, responsibility)
                        VALUES (?, ?)
                        """,
                        (employee_id, responsibility),
                    )

        # ----------------------------------------------------
        # DEMO TEACHER ASSIGNMENT
        # ----------------------------------------------------
        teacher = conn.execute(
            """
            SELECT id FROM employees
            WHERE college_id = ? AND employee_code = ?
            """,
            (college_id, "EMP1001"),
        ).fetchone()

        dsa_subject = conn.execute(
            """
            SELECT id FROM subjects
            WHERE college_id = ? AND subject_code = ?
            """,
            (college_id, "DSA"),
        ).fetchone()

        section_a = conn.execute(
            """
            SELECT id FROM sections
            WHERE college_id = ? AND name = ?
              AND academic_session = ?
            LIMIT 1
            """,
            (college_id, "A", "2026-27"),
        ).fetchone()

        if teacher and dsa_subject and section_a:
            conn.execute(
                """
                INSERT OR IGNORE INTO teacher_assignments
                (employee_id, subject_id, section_id, academic_session)
                VALUES (?, ?, ?, ?)
                """,
                (
                    teacher["id"],
                    dsa_subject["id"],
                    section_a["id"],
                    "2026-27",
                ),
            )

        # ----------------------------------------------------
        # DEMO EXAM TYPES
        # ----------------------------------------------------
        for exam_name in [
            "Midterm 1",
            "Midterm 2",
            "Assignment",
            "Quiz",
            "Practical",
            "External",
        ]:
            conn.execute(
                """
                INSERT OR IGNORE INTO exam_types
                (college_id, name)
                VALUES (?, ?)
                """,
                (college_id, exam_name),
            )

    conn.commit()
    conn.close()


# ============================================================
# ROLE CHECK
# ============================================================

def require_role(role):
    return session.get("role") == role


@app.context_processor
def inject_site_context():
    """Expose the current college name/state to every template."""
    college = None

    if session.get("college_id"):
        conn = get_db()
        college = conn.execute(
            """
            SELECT c.id, c.name AS college_name, s.name AS state_name
            FROM colleges c
            JOIN states s ON c.state_id = s.id
            WHERE c.id = ?
            """,
            (session["college_id"],),
        ).fetchone()
        conn.close()

    return {"current_college": college}


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():
    return redirect(url_for("login"))


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        college_id = request.form.get("college_id", type=int)
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        if (
            role not in {"admin", "student"}
            or not college_id
            or not identifier
            or not password
        ):
            return render_template(
                "login.html",
                error="Please fill all login fields.",
            )

        conn = get_db()

        if role == "admin":
            user = conn.execute(
                """
                SELECT * FROM admins
                WHERE college_id = ? AND email = ?
                """,
                (college_id, identifier),
            ).fetchone()
        else:
            login_method = request.form.get("login_method", "roll")

            if login_method == "email":
                user = conn.execute(
                    """
                    SELECT * FROM students
                    WHERE college_id = ? AND email = ?
                    """,
                    (college_id, identifier),
                ).fetchone()
            else:
                user = conn.execute(
                    """
                    SELECT * FROM students
                    WHERE college_id = ? AND roll_no = ?
                    """,
                    (college_id, identifier),
                ).fetchone()

        conn.close()

        if not user or not check_password_hash(
            user["password_hash"],
            password,
        ):
            return render_template(
                "login.html",
                error="Invalid login details.",
            )

        session.clear()
        session["role"] = role
        session["college_id"] = college_id
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["user_name"] = user["name"]

        college_conn = get_db()
        college_row = college_conn.execute(
            "SELECT name FROM colleges WHERE id = ?",
            (college_id,),
        ).fetchone()
        college_conn.close()

        if college_row:
            session["college_name"] = college_row["name"]

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ============================================================
# STATES API
# ============================================================

@app.get("/api/states")
def api_states():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name FROM states ORDER BY name"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


# ============================================================
# COLLEGES API
# ============================================================

@app.get("/api/colleges/<int:state_id>")
def api_colleges(state_id):
    conn = get_db()
    rows = conn.execute(
        """
        SELECT id, name FROM colleges
        WHERE state_id = ?
        ORDER BY name
        """,
        (state_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    college = conn.execute(
        """
        SELECT c.name AS college_name, s.name AS state_name
        FROM colleges c
        JOIN states s ON c.state_id = s.id
        WHERE c.id = ?
        """,
        (session["college_id"],),
    ).fetchone()

    if session["role"] == "admin":
        student_count = conn.execute(
            "SELECT COUNT(*) AS total FROM students WHERE college_id = ?",
            (session["college_id"],),
        ).fetchone()["total"]

        subject_count = conn.execute(
            "SELECT COUNT(*) AS total FROM subjects WHERE college_id = ?",
            (session["college_id"],),
        ).fetchone()["total"]

        employee_count = conn.execute(
            "SELECT COUNT(*) AS total FROM employees WHERE college_id = ?",
            (session["college_id"],),
        ).fetchone()["total"]

        department_count = conn.execute(
            "SELECT COUNT(*) AS total FROM departments WHERE college_id = ?",
            (session["college_id"],),
        ).fetchone()["total"]

        section_count = conn.execute(
            "SELECT COUNT(*) AS total FROM sections WHERE college_id = ?",
            (session["college_id"],),
        ).fetchone()["total"]

        conn.close()

        return render_template(
            "admin_dashboard.html",
            college=college,
            student_count=student_count,
            subject_count=subject_count,
            employee_count=employee_count,
            department_count=department_count,
            section_count=section_count,
        )

    student = conn.execute(
        """
        SELECT name, roll_no, email, course, year, section, phone
        FROM students WHERE id = ?
        """,
        (session["user_id"],),
    ).fetchone()

    conn.close()

    return render_template(
        "student_dashboard.html",
        college=college,
        student=student,
    )


# ============================================================
# STUDENT MANAGEMENT
# ============================================================

@app.route("/admin/students")
def students():
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    rows = conn.execute(
        """
        SELECT id, name, roll_no, email, course, year, section
        FROM students
        WHERE college_id = ?
        ORDER BY roll_no
        """,
        (session["college_id"],),
    ).fetchall()
    conn.close()

    return render_template("students.html", students=rows)


@app.route("/admin/students/add", methods=["GET", "POST"])
def add_student():
    if not require_role("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"].strip()
        roll_no = request.form["roll_no"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        course = request.form["course"].strip()
        year = request.form["year"].strip()
        section = request.form["section"].strip()
        phone = request.form.get("phone", "").strip()

        conn = get_db()

        try:
            conn.execute(
                """
                INSERT INTO students
                (college_id, name, roll_no, email, password_hash,
                 course, year, section, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["college_id"],
                    name,
                    roll_no,
                    email,
                    generate_password_hash(password),
                    course,
                    year,
                    section,
                    phone,
                ),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("students"))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template(
                "add_student.html",
                error="Roll number or email already exists.",
            )

    return render_template("add_student.html")


@app.route("/admin/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    student = conn.execute(
        """
        SELECT * FROM students
        WHERE id = ? AND college_id = ?
        """,
        (student_id, session["college_id"]),
    ).fetchone()

    if not student:
        conn.close()
        return redirect(url_for("students"))

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
            if new_password:
                conn.execute(
                    """
                    UPDATE students SET
                        name = ?, roll_no = ?, email = ?,
                        password_hash = ?, course = ?, year = ?,
                        section = ?, phone = ?
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
            else:
                conn.execute(
                    """
                    UPDATE students SET
                        name = ?, roll_no = ?, email = ?,
                        course = ?, year = ?, section = ?, phone = ?
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
    return render_template("edit_student.html", student=student)


@app.post("/admin/students/delete/<int:student_id>")
def delete_student(student_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "DELETE FROM students WHERE id = ? AND college_id = ?",
        (student_id, session["college_id"]),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("students"))


# ============================================================
# SUBJECT MANAGEMENT
# ============================================================

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
                """
                INSERT INTO subjects
                (college_id, subject_name, subject_code)
                VALUES (?, ?, ?)
                """,
                (session["college_id"], name, code),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass

    rows = conn.execute(
        """
        SELECT id, subject_name, subject_code
        FROM subjects
        WHERE college_id = ?
        ORDER BY subject_code
        """,
        (session["college_id"],),
    ).fetchall()

    conn.close()
    return render_template("subjects.html", subjects=rows)


# ============================================================
# SUBJECT EDIT / DELETE
# ============================================================

@app.route("/admin/subjects/edit/<int:subject_id>", methods=["GET", "POST"])
def edit_subject(subject_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    subject = conn.execute(
        """
        SELECT id, subject_name, subject_code
        FROM subjects
        WHERE id = ? AND college_id = ?
        """,
        (subject_id, session["college_id"]),
    ).fetchone()

    if not subject:
        conn.close()
        return redirect(url_for("subjects"))

    if request.method == "POST":
        name = request.form["subject_name"].strip()
        code = request.form["subject_code"].strip().upper()

        try:
            conn.execute(
                """
                UPDATE subjects
                SET subject_name = ?, subject_code = ?
                WHERE id = ? AND college_id = ?
                """,
                (name, code, subject_id, session["college_id"]),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("subjects"))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template(
                "edit_subject.html",
                subject=subject,
                error="Subject code already exists.",
            )

    conn.close()
    return render_template("edit_subject.html", subject=subject)


@app.post("/admin/subjects/delete/<int:subject_id>")
def delete_subject(subject_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "DELETE FROM subjects WHERE id = ? AND college_id = ?",
        (subject_id, session["college_id"]),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("subjects"))


# ============================================================
# EMPLOYEE MANAGEMENT
# ============================================================

@app.route("/admin/employees")
def employees():
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    rows = conn.execute(
        """
        SELECT
            e.id, e.employee_code, e.name, e.email, e.phone,
            e.designation, e.joining_date, e.salary,
            e.employment_type, e.status,
            d.name AS department_name
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        WHERE e.college_id = ?
        ORDER BY e.name
        """,
        (session["college_id"],),
    ).fetchall()
    conn.close()

    return render_template("employees.html", employees=rows)


@app.route("/admin/employees/add", methods=["GET", "POST"])
def add_employee():
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    departments = conn.execute(
        """
        SELECT id, name, code FROM departments
        WHERE college_id = ? ORDER BY name
        """,
        (session["college_id"],),
    ).fetchall()

    if request.method == "POST":
        employee_code = request.form["employee_code"].strip()
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        phone = request.form.get("phone", "").strip()
        designation = request.form["designation"].strip()
        department_id = request.form.get("department_id", type=int)
        joining_date = request.form.get("joining_date", "")
        qualification = request.form.get("qualification", "").strip()
        experience = request.form.get("experience", "").strip()
        salary_text = request.form.get("salary", "").strip()
        employment_type = request.form.get("employment_type", "")
        status = request.form.get("status", "Active")

        try:
            salary = float(salary_text) if salary_text else None

            cursor = conn.execute(
                """
                INSERT INTO employees
                (college_id, department_id, employee_code, name,
                 email, password_hash, phone, designation, joining_date,
                 qualification, experience, salary, employment_type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["college_id"],
                    department_id,
                    employee_code,
                    name,
                    email,
                    generate_password_hash(password),
                    phone,
                    designation,
                    joining_date,
                    qualification,
                    experience,
                    salary,
                    employment_type,
                    status,
                ),
            )

            employee_id = cursor.lastrowid

            for responsibility in request.form.getlist("responsibilities"):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO employee_responsibilities
                    (employee_id, responsibility)
                    VALUES (?, ?)
                    """,
                    (employee_id, responsibility),
                )

            conn.commit()
            conn.close()
            return redirect(url_for("employees"))

        except (sqlite3.IntegrityError, ValueError):
            conn.close()
            return render_template(
                "add_employee.html",
                departments=departments,
                error="Employee ID or email already exists, or salary is invalid.",
            )

    conn.close()
    return render_template("add_employee.html", departments=departments)


@app.route("/admin/employees/edit/<int:employee_id>", methods=["GET", "POST"])
def edit_employee(employee_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    employee = conn.execute(
        """
        SELECT * FROM employees
        WHERE id = ? AND college_id = ?
        """,
        (employee_id, session["college_id"]),
    ).fetchone()

    if not employee:
        conn.close()
        return redirect(url_for("employees"))

    departments = conn.execute(
        """
        SELECT id, name, code FROM departments
        WHERE college_id = ? ORDER BY name
        """,
        (session["college_id"],),
    ).fetchall()

    responsibility_rows = conn.execute(
        """
        SELECT responsibility FROM employee_responsibilities
        WHERE employee_id = ?
        """,
        (employee_id,),
    ).fetchall()

    selected_responsibilities = {
        row["responsibility"] for row in responsibility_rows
    }

    if request.method == "POST":
        employee_code = request.form["employee_code"].strip()
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form.get("phone", "").strip()
        designation = request.form["designation"].strip()
        department_id = request.form.get("department_id", type=int)
        joining_date = request.form.get("joining_date", "")
        qualification = request.form.get("qualification", "").strip()
        experience = request.form.get("experience", "").strip()
        salary_text = request.form.get("salary", "").strip()
        employment_type = request.form.get("employment_type", "")
        status = request.form.get("status", "Active")
        new_password = request.form.get("password", "")

        try:
            salary = float(salary_text) if salary_text else None

            if new_password:
                conn.execute(
                    """
                    UPDATE employees SET
                        department_id = ?, employee_code = ?, name = ?,
                        email = ?, password_hash = ?, phone = ?,
                        designation = ?, joining_date = ?, qualification = ?,
                        experience = ?, salary = ?, employment_type = ?, status = ?
                    WHERE id = ? AND college_id = ?
                    """,
                    (
                        department_id,
                        employee_code,
                        name,
                        email,
                        generate_password_hash(new_password),
                        phone,
                        designation,
                        joining_date,
                        qualification,
                        experience,
                        salary,
                        employment_type,
                        status,
                        employee_id,
                        session["college_id"],
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE employees SET
                        department_id = ?, employee_code = ?, name = ?,
                        email = ?, phone = ?, designation = ?,
                        joining_date = ?, qualification = ?, experience = ?,
                        salary = ?, employment_type = ?, status = ?
                    WHERE id = ? AND college_id = ?
                    """,
                    (
                        department_id,
                        employee_code,
                        name,
                        email,
                        phone,
                        designation,
                        joining_date,
                        qualification,
                        experience,
                        salary,
                        employment_type,
                        status,
                        employee_id,
                        session["college_id"],
                    ),
                )

            conn.execute(
                "DELETE FROM employee_responsibilities WHERE employee_id = ?",
                (employee_id,),
            )

            for responsibility in request.form.getlist("responsibilities"):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO employee_responsibilities
                    (employee_id, responsibility)
                    VALUES (?, ?)
                    """,
                    (employee_id, responsibility),
                )

            conn.commit()
            conn.close()
            return redirect(url_for("employees"))

        except (sqlite3.IntegrityError, ValueError):
            conn.close()
            return render_template(
                "edit_employee.html",
                employee=employee,
                departments=departments,
                selected_responsibilities=selected_responsibilities,
                error="Employee ID or email already exists, or salary is invalid.",
            )

    conn.close()
    return render_template(
        "edit_employee.html",
        employee=employee,
        departments=departments,
        selected_responsibilities=selected_responsibilities,
    )


@app.post("/admin/employees/delete/<int:employee_id>")
def delete_employee(employee_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "DELETE FROM employees WHERE id = ? AND college_id = ?",
        (employee_id, session["college_id"]),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("employees"))


# ============================================================
# DEPARTMENT MANAGEMENT
# ============================================================

@app.route("/admin/departments")
def departments():
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    rows = conn.execute(
        """
        SELECT
            d.id,
            d.name,
            d.code,
            COUNT(DISTINCT s.id) AS section_count,
            COUNT(DISTINCT e.id) AS employee_count
        FROM departments d
        LEFT JOIN sections s ON s.department_id = d.id
        LEFT JOIN employees e ON e.department_id = d.id
        WHERE d.college_id = ?
        GROUP BY d.id, d.name, d.code
        ORDER BY d.name
        """,
        (session["college_id"],),
    ).fetchall()
    conn.close()

    return render_template("departments.html", departments=rows)


@app.route("/admin/departments/add", methods=["GET", "POST"])
def add_department():
    if not require_role("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"].strip()
        code = request.form["code"].strip().upper()

        conn = get_db()

        try:
            conn.execute(
                """
                INSERT INTO departments
                (college_id, name, code)
                VALUES (?, ?, ?)
                """,
                (session["college_id"], name, code),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("departments"))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template(
                "add_department.html",
                error="Department code already exists.",
            )

    return render_template("add_department.html")


@app.route(
    "/admin/departments/edit/<int:department_id>",
    methods=["GET", "POST"],
)
def edit_department(department_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    department = conn.execute(
        """
        SELECT id, name, code
        FROM departments
        WHERE id = ? AND college_id = ?
        """,
        (department_id, session["college_id"]),
    ).fetchone()

    if not department:
        conn.close()
        return redirect(url_for("departments"))

    if request.method == "POST":
        name = request.form["name"].strip()
        code = request.form["code"].strip().upper()

        try:
            conn.execute(
                """
                UPDATE departments
                SET name = ?, code = ?
                WHERE id = ? AND college_id = ?
                """,
                (
                    name,
                    code,
                    department_id,
                    session["college_id"],
                ),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("departments"))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template(
                "edit_department.html",
                department=department,
                error="Department code already exists.",
            )

    conn.close()
    return render_template(
        "edit_department.html",
        department=department,
    )


@app.post("/admin/departments/delete/<int:department_id>")
def delete_department(department_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    # Do not delete a department if it still has employees or sections.
    section_count = conn.execute(
        "SELECT COUNT(*) AS total FROM sections WHERE department_id = ?",
        (department_id,),
    ).fetchone()["total"]

    employee_count = conn.execute(
        "SELECT COUNT(*) AS total FROM employees WHERE department_id = ?",
        (department_id,),
    ).fetchone()["total"]

    if section_count == 0 and employee_count == 0:
        conn.execute(
            "DELETE FROM departments WHERE id = ? AND college_id = ?",
            (department_id, session["college_id"]),
        )
        conn.commit()

    conn.close()
    return redirect(url_for("departments"))


# ============================================================
# SECTION MANAGEMENT
# ============================================================

@app.route("/admin/sections")
def sections():
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    rows = conn.execute(
        """
        SELECT
            s.id,
            s.name,
            s.year,
            s.semester,
            s.academic_session,
            d.name AS department_name,
            d.code AS department_code
        FROM sections s
        JOIN departments d ON s.department_id = d.id
        WHERE s.college_id = ?
        ORDER BY d.name, s.year, s.name
        """,
        (session["college_id"],),
    ).fetchall()
    conn.close()

    return render_template("sections.html", sections=rows)


@app.route("/admin/sections/add", methods=["GET", "POST"])
def add_section():
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()
    departments = conn.execute(
        """
        SELECT id, name, code
        FROM departments
        WHERE college_id = ?
        ORDER BY name
        """,
        (session["college_id"],),
    ).fetchall()

    if request.method == "POST":
        department_id = request.form.get("department_id", type=int)
        name = request.form["name"].strip().upper()
        year = request.form["year"].strip()
        semester = request.form["semester"].strip()
        academic_session = request.form["academic_session"].strip()

        try:
            conn.execute(
                """
                INSERT INTO sections
                (college_id, department_id, name, year, semester, academic_session)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session["college_id"],
                    department_id,
                    name,
                    year,
                    semester,
                    academic_session,
                ),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("sections"))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template(
                "add_section.html",
                departments=departments,
                error="This section already exists for the selected academic session.",
            )

    conn.close()
    return render_template("add_section.html", departments=departments)


@app.route(
    "/admin/sections/edit/<int:section_id>",
    methods=["GET", "POST"],
)
def edit_section(section_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    section = conn.execute(
        """
        SELECT *
        FROM sections
        WHERE id = ? AND college_id = ?
        """,
        (section_id, session["college_id"]),
    ).fetchone()

    if not section:
        conn.close()
        return redirect(url_for("sections"))

    departments = conn.execute(
        """
        SELECT id, name, code
        FROM departments
        WHERE college_id = ?
        ORDER BY name
        """,
        (session["college_id"],),
    ).fetchall()

    if request.method == "POST":
        department_id = request.form.get("department_id", type=int)
        name = request.form["name"].strip().upper()
        year = request.form["year"].strip()
        semester = request.form["semester"].strip()
        academic_session = request.form["academic_session"].strip()

        try:
            conn.execute(
                """
                UPDATE sections
                SET department_id = ?, name = ?, year = ?,
                    semester = ?, academic_session = ?
                WHERE id = ? AND college_id = ?
                """,
                (
                    department_id,
                    name,
                    year,
                    semester,
                    academic_session,
                    section_id,
                    session["college_id"],
                ),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("sections"))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template(
                "edit_section.html",
                section=section,
                departments=departments,
                error="This section already exists for the selected academic session.",
            )

    conn.close()
    return render_template(
        "edit_section.html",
        section=section,
        departments=departments,
    )


@app.post("/admin/sections/delete/<int:section_id>")
def delete_section(section_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    # Teacher and mentor assignments must be removed first.
    conn.execute(
        "DELETE FROM teacher_assignments WHERE section_id = ?",
        (section_id,),
    )
    conn.execute(
        "DELETE FROM mentor_assignments WHERE section_id = ?",
        (section_id,),
    )

    conn.execute(
        """
        DELETE FROM sections
        WHERE id = ? AND college_id = ?
        """,
        (section_id, session["college_id"]),
    )

    conn.commit()
    conn.close()
    return redirect(url_for("sections"))


# ============================================================
# TEACHER ASSIGNMENT MANAGEMENT
# ============================================================

@app.route("/admin/teacher-assignments")
def teacher_assignments():
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    rows = conn.execute(
        """
        SELECT
            ta.id,
            ta.academic_session,
            e.employee_code,
            e.name AS teacher_name,
            e.designation,
            sub.subject_name,
            sub.subject_code,
            d.name AS department_name,
            d.code AS department_code,
            s.name AS section_name,
            s.year,
            s.semester
        FROM teacher_assignments ta
        JOIN employees e ON ta.employee_id = e.id
        JOIN subjects sub ON ta.subject_id = sub.id
        JOIN sections s ON ta.section_id = s.id
        JOIN departments d ON s.department_id = d.id
        WHERE e.college_id = ?
        ORDER BY ta.academic_session DESC,
                 d.name,
                 s.year,
                 s.name,
                 e.name
        """,
        (session["college_id"],),
    ).fetchall()

    conn.close()

    return render_template(
        "teacher_assignments.html",
        assignments=rows,
    )


@app.route("/admin/teacher-assignments/add", methods=["GET", "POST"])
def add_teacher_assignment():
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    teachers = conn.execute(
        """
        SELECT id, employee_code, name, designation
        FROM employees
        WHERE college_id = ? AND status = 'Active'
        ORDER BY name
        """,
        (session["college_id"],),
    ).fetchall()

    subjects = conn.execute(
        """
        SELECT id, subject_name, subject_code
        FROM subjects
        WHERE college_id = ?
        ORDER BY subject_code, subject_name
        """,
        (session["college_id"],),
    ).fetchall()

    departments = conn.execute(
        """
        SELECT id, name, code
        FROM departments
        WHERE college_id = ?
        ORDER BY name
        """,
        (session["college_id"],),
    ).fetchall()

    sections = conn.execute(
        """
        SELECT
            s.id,
            s.department_id,
            s.name,
            s.year,
            s.semester,
            s.academic_session,
            d.code AS department_code
        FROM sections s
        JOIN departments d ON s.department_id = d.id
        WHERE s.college_id = ?
        ORDER BY d.name, s.year, s.semester, s.name
        """,
        (session["college_id"],),
    ).fetchall()

    if request.method == "POST":
        employee_id = request.form.get("employee_id", type=int)
        subject_id = request.form.get("subject_id", type=int)
        section_id = request.form.get("section_id", type=int)
        academic_session = request.form.get("academic_session", "").strip()

        if not all([employee_id, subject_id, section_id, academic_session]):
            conn.close()
            return render_template(
                "add_teacher_assignment.html",
                teachers=teachers,
                subjects=subjects,
                departments=departments,
                sections=sections,
                error="Please fill all assignment fields.",
            )

        # Confirm every selected record belongs to the logged-in college.
        valid = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM employees
                 WHERE id = ? AND college_id = ? AND status = 'Active') AS teacher_ok,
                (SELECT COUNT(*) FROM subjects
                 WHERE id = ? AND college_id = ?) AS subject_ok,
                (SELECT COUNT(*) FROM sections
                 WHERE id = ? AND college_id = ?) AS section_ok
            """,
            (
                employee_id,
                session["college_id"],
                subject_id,
                session["college_id"],
                section_id,
                session["college_id"],
            ),
        ).fetchone()

        if not (valid["teacher_ok"] and valid["subject_ok"] and valid["section_ok"]):
            conn.close()
            return render_template(
                "add_teacher_assignment.html",
                teachers=teachers,
                subjects=subjects,
                departments=departments,
                sections=sections,
                error="Invalid teacher, subject or section selection.",
            )

        try:
            conn.execute(
                """
                INSERT INTO teacher_assignments
                (employee_id, subject_id, section_id, academic_session)
                VALUES (?, ?, ?, ?)
                """,
                (
                    employee_id,
                    subject_id,
                    section_id,
                    academic_session,
                ),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("teacher_assignments"))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template(
                "add_teacher_assignment.html",
                teachers=teachers,
                subjects=subjects,
                departments=departments,
                sections=sections,
                error="This teacher is already assigned to this subject and section for this session.",
            )

    conn.close()

    return render_template(
        "add_teacher_assignment.html",
        teachers=teachers,
        subjects=subjects,
        departments=departments,
        sections=sections,
    )


@app.route(
    "/admin/teacher-assignments/edit/<int:assignment_id>",
    methods=["GET", "POST"],
)
def edit_teacher_assignment(assignment_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    assignment = conn.execute(
        """
        SELECT *
        FROM teacher_assignments
        WHERE id = ?
        AND employee_id IN (
            SELECT id FROM employees WHERE college_id = ?
        )
        """,
        (assignment_id, session["college_id"]),
    ).fetchone()

    if not assignment:
        conn.close()
        return redirect(url_for("teacher_assignments"))

    teachers = conn.execute(
        """
        SELECT id, employee_code, name, designation
        FROM employees
        WHERE college_id = ? AND status = 'Active'
        ORDER BY name
        """,
        (session["college_id"],),
    ).fetchall()

    subjects = conn.execute(
        """
        SELECT id, subject_name, subject_code
        FROM subjects
        WHERE college_id = ?
        ORDER BY subject_code, subject_name
        """,
        (session["college_id"],),
    ).fetchall()

    departments = conn.execute(
        """
        SELECT id, name, code
        FROM departments
        WHERE college_id = ?
        ORDER BY name
        """,
        (session["college_id"],),
    ).fetchall()

    sections = conn.execute(
        """
        SELECT
            s.id,
            s.department_id,
            s.name,
            s.year,
            s.semester,
            s.academic_session,
            d.code AS department_code
        FROM sections s
        JOIN departments d ON s.department_id = d.id
        WHERE s.college_id = ?
        ORDER BY d.name, s.year, s.semester, s.name
        """,
        (session["college_id"],),
    ).fetchall()

    if request.method == "POST":
        employee_id = request.form.get("employee_id", type=int)
        subject_id = request.form.get("subject_id", type=int)
        section_id = request.form.get("section_id", type=int)
        academic_session = request.form.get("academic_session", "").strip()

        try:
            conn.execute(
                """
                UPDATE teacher_assignments
                SET employee_id = ?,
                    subject_id = ?,
                    section_id = ?,
                    academic_session = ?
                WHERE id = ?
                """,
                (
                    employee_id,
                    subject_id,
                    section_id,
                    academic_session,
                    assignment_id,
                ),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("teacher_assignments"))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template(
                "edit_teacher_assignment.html",
                assignment=assignment,
                teachers=teachers,
                subjects=subjects,
                departments=departments,
                sections=sections,
                error="This teacher is already assigned to this subject and section for this session.",
            )

    conn.close()

    return render_template(
        "edit_teacher_assignment.html",
        assignment=assignment,
        teachers=teachers,
        subjects=subjects,
        departments=departments,
        sections=sections,
    )


@app.post("/admin/teacher-assignments/delete/<int:assignment_id>")
def delete_teacher_assignment(assignment_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM teacher_assignments
        WHERE id = ?
        AND employee_id IN (
            SELECT id FROM employees WHERE college_id = ?
        )
        """,
        (assignment_id, session["college_id"]),
    )

    conn.commit()
    conn.close()

    return redirect(url_for("teacher_assignments"))


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()


# ============================================================
# START FLASK SERVER
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
