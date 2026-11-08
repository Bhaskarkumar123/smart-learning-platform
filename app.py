
import os

from dotenv import load_dotenv
from flask import Flask, render_template, abort, redirect, url_for
from flask_mysqldb import MySQL
from flask import request
from flask import session

load_dotenv()

app = Flask(__name__)


# Flask configuration
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# MySQL configuration
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "localhost")
app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", "3306"))
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "smartlearn")
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/kids")
def kids():
    return render_template("kids.html")


@app.route("/kids/quiz/<quiz_type>")
def kids_quiz(quiz_type):
    allowed_quizzes = [
        "count-number",
        "count-things",
        "first-letter",
        "advanced-quiz",
        "add-number"
    ]

    if quiz_type not in allowed_quizzes:
        abort(404)

    return render_template("kids_quiz.html", quiz_type=quiz_type)


# All student hub part
@app.route("/students")
def students():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            "SELECT id, class_number FROM classes ORDER BY class_number"
        )
        classes = cursor.fetchall()
    finally:
        cursor.close()

    return render_template("students.html", classes=classes)

#-------------CLASS SUBJECT-------------------------
@app.route("/students/class/<int:class_id>")
def class_subjects(class_id):
    cursor = mysql.connection.cursor()

    try:
        # Check whether the selected class exists
        cursor.execute(
            "SELECT id, class_number FROM classes WHERE id = %s",
            (class_id,)
        )
        selected_class = cursor.fetchone()

        if not selected_class:
            abort(404)

        # Load subjects assigned to this class
        cursor.execute(
            """
            SELECT id, name
            FROM subjects
            WHERE class_id = %s
              AND NOT (
                  %s BETWEEN 6 AND 10
                  AND name IN ('English', 'Hindi', 'Social Science')
              )
            ORDER BY name
            """,
            (class_id, selected_class["class_number"])
        )
        subjects = cursor.fetchall()

    finally:
        cursor.close()

    return render_template(
        "class_subjects.html",
        selected_class=selected_class,
        subjects=subjects
    )

@app.route("/students/subject/<int:subject_id>")
def subject_options(subject_id):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            """
            SELECT s.id, s.name,
                s.class_id, c.class_number
            FROM subjects As s
            INNER JOIN classes As c ON s.class_id = c.id
            WHERE s.id = %s
            """,
            (subject_id,)
)
        subject = cursor.fetchone()
    finally:
        cursor.close()

    if not subject:
        abort(404)

    return render_template("subject_options.html", subject=subject)

#------------STUDY NOTES-------------------------------
@app.route("/students/subject/<int:subject_id>/notes")
def study_notes(subject_id):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            "SELECT id, name FROM subjects WHERE id = %s",
            (subject_id,)
        )
        subject = cursor.fetchone()

        if not subject:
            abort(404)

        cursor.execute(
            """
            SELECT chapter_name, chapter_order
            FROM chapters
            WHERE subject_id = %s
            ORDER BY chapter_order
            """,
            (subject_id,)
        )
        chapters = cursor.fetchall()

    finally:
        cursor.close()

    return render_template(
        "study_notes.html",
        subject=subject,
        chapters=chapters
    )


#----------------------NORMAL PRACTICE QUIZE----------------
@app.route("/students/subject/<int:subject_id>/quiz")
def practice_quiz(subject_id):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            "SELECT id, name FROM subjects WHERE id = %s",
            (subject_id,)
        )
        subject = cursor.fetchone()

        if not subject:
            abort(404)

        cursor.execute(
            """
            SELECT q.id, q.question_text,
                q.option_a, q.option_b,
                q.option_c, q.option_d,
                q.correct_option, q.explanation
            FROM questions As q
            INNER JOIN chapters As ch ON q.chapter_id = ch.id
            WHERE ch.subject_id = %s
            ORDER BY RAND()
            LIMIT 10
            """,
            (subject_id,)
        )

        questions = cursor.fetchall()
        

    finally:
        cursor.close()

    return render_template(
        "practice_quiz.html",
        subject=subject,
        questions=questions
    )

#----------------MATHS LEVAL QUIZE SUBMIT------------------
@app.route(
    "/students/subject/<int:subject_id>/quiz/submit",
    methods=["POST"]
)
def submit_quiz(subject_id):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            "SELECT id, name FROM subjects WHERE id = %s",
            (subject_id,)
        )
        subject = cursor.fetchone()

        if not subject:
            abort(404)

        cursor.execute(
            """
            SELECT q.id, q.question_text,
                   q.option_a, q.option_b,
                   q.option_c, q.option_d,
                   q.correct_option, q.explanation
            FROM questions As q
            INNER JOIN chapters As ch ON q.chapter_id = ch.id
            WHERE ch.subject_id = %s
            """,
            (subject_id,)
        )
        all_questions = cursor.fetchall()

        question_ids = [
            int(key.replace("question_", ""))
            for key in request.form
            if key.startswith("question_")
            and key.replace("question_", "").isdigit()
        ]

        if not question_ids or len(question_ids) > 10:
            abort(400)

        questions_by_id = {
            q["id"]: q for q in all_questions
        }

        if any(qid not in questions_by_id for qid in question_ids):
            abort(400)

        selected_questions = [
            questions_by_id[qid] for qid in question_ids
        ]

        score = sum(
            request.form.get(f"question_{q['id']}") ==
            q["correct_option"]
            for q in selected_questions
        )

    finally:
        cursor.close()

    return render_template(
        "quiz_result.html",
        subject=subject,
        questions=selected_questions,
        score=score,
        total=len(selected_questions)
    )


#---------------MATHS LEVAL PAGE---------------------------
@app.route("/students/subject/<int:subject_id>/levels")
def maths_levels(subject_id):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT s.id, s.name,
                   s.class_id, c.class_number
            FROM subjects As s
            INNER JOIN classes As c ON s.class_id = c.id
            WHERE s.id = %s
        """, (subject_id,))
        subject = cursor.fetchone()
    finally:
        cursor.close()

    if not subject:
        abort(404)

    key = f"maths_unlocked_{subject_id}"
    unlocked_level = session.get(key, 1)

    return render_template(
        "maths_levels.html",
        subject=subject,
        unlocked_level=unlocked_level
    )


#-----------------------------MATHS LEVAL QUIZE-------------------
@app.route("/students/subject/<int:subject_id>/level/<int:level>")
def maths_level_quiz(subject_id, level):
    if level < 1:
        abort(404)

    key = f"maths_unlocked_{subject_id}"
    unlocked_level = session.get(key, 1)

    if level > unlocked_level:
        return redirect(
            url_for("maths_levels", subject_id=subject_id)
        )

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT s.id, s.name, s.class_id, c.class_number
            FROM subjects As s
            INNER JOIN classes As c ON s.class_id = c.id
            WHERE s.id = %s
        """, (subject_id,))
        subject = cursor.fetchone()

        if not subject:
            abort(404)

        cursor.execute("""
            SELECT q.id, q.question_text,
                q.option_a, q.option_b,
                q.option_c, q.option_d,
                q.correct_option, q.explanation
            FROM questions As q
            INNER JOIN chapters As ch ON q.chapter_id = ch.id
            WHERE ch.subject_id = %s
            ORDER BY RAND()
            LIMIT 10
        """, (subject_id,))

        questions = cursor.fetchall()
    finally:
        cursor.close()

    if not questions:
        return "We are preparing something amazing for you.", 404

    session["maths_current_questions"] = {
        str(subject_id): [q["id"] for q in questions]
    }

    return render_template(
        "practice_quiz.html",
        subject=subject,
        questions=questions,
        level=level,
        submit_endpoint="submit_maths_level"
    )


#-------------------SUBMIT MATHS LEVAL------------------------
@app.route(
    "/students/subject/<int:subject_id>/level/<int:level>/submit",
    methods=["POST"]
)
def submit_maths_level(subject_id, level):
    key = f"maths_unlocked_{subject_id}"
    unlocked_level = session.get(key, 1)

    if level < 1 or level > unlocked_level:
        abort(400)

    question_ids = session.get(
        "maths_current_questions", {}
    ).get(str(subject_id), [])

    if not question_ids:
        return redirect(
            url_for("maths_level_quiz",
                    subject_id=subject_id, level=level)
        )

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id, name FROM subjects WHERE id = %s
        """, (subject_id,))
        subject = cursor.fetchone()

        if not subject:
            abort(404)

        placeholders = ",".join(["%s"] * len(question_ids))
        cursor.execute(f"""
            SELECT q.id, q.question_text,
                   q.option_a, q.option_b,
                   q.option_c, q.option_d,
                   q.correct_option, q.explanation
            FROM questions As q
            INNER JOIN chapters As ch ON q.chapter_id = ch.id
            WHERE ch.subject_id = %s
              AND q.id IN ({placeholders})
        """, tuple([subject_id] + question_ids))

        questions = cursor.fetchall()
    finally:
        cursor.close()

    if len(questions) != len(question_ids):
        abort(400)

    answers = request.form
    score = sum(
        1 for q in questions
        if answers.get(f"question_{q['id']}") == q["correct_option"]
    )

    passed = score >= 7

    if passed and level == unlocked_level:
        session[key] = unlocked_level + 1

    return render_template(
        "quiz_result.html",
        subject=subject,
        questions=questions,
        score=score,
        total=len(questions),
        form_answers=answers,
        level=level,
        passed=passed,
        next_level=level + 1,
        quiz_type="maths"
    )



# ============================================================
# SCIENCE LEVELS PAGE
# ============================================================

@app.route("/students/subject/<int:subject_id>/science-levels")
def science_levels(subject_id):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT s.id, s.name, s.class_id, c.class_number
            FROM subjects AS s
            INNER JOIN classes AS c ON s.class_id = c.id
            WHERE s.id = %s
              AND s.name = 'Science'
        """, (subject_id,))

        subject = cursor.fetchone()
    finally:
        cursor.close()

    if not subject:
        abort(404)

    key = f"science_unlocked_{subject_id}"
    unlocked_level = session.get(key, 1)

    return render_template(
        "science_levels.html",
        subject=subject,
        unlocked_level=unlocked_level
    )


# ============================================================
# START SCIENCE LEVEL QUIZ
# ============================================================

@app.route(
    "/students/subject/<int:subject_id>/science-level/<int:level>"
)
def science_level_quiz(subject_id, level):
    if level < 1:
        abort(404)

    key = f"science_unlocked_{subject_id}"
    unlocked_level = session.get(key, 1)

    if level > unlocked_level:
        return redirect(
            url_for("science_levels", subject_id=subject_id)
        )

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT s.id, s.name, s.class_id, c.class_number
            FROM subjects AS s
            INNER JOIN classes AS c ON s.class_id = c.id
            WHERE s.id = %s
              AND s.name = 'Science'
        """, (subject_id,))

        subject = cursor.fetchone()

        if not subject:
            abort(404)

        cursor.execute("""
            SELECT q.id, q.question_text,
                   q.option_a, q.option_b,
                   q.option_c, q.option_d,
                   q.correct_option, q.explanation
            FROM questions AS q
            INNER JOIN chapters AS ch ON q.chapter_id = ch.id
            WHERE ch.subject_id = %s
            ORDER BY RAND()
            LIMIT 10
        """, (subject_id,))

        questions = cursor.fetchall()

    finally:
        cursor.close()

    if not questions:
        return "We are preparing something amazing for you.", 404

    # Preserve question lists for other subjects in the session
    current_questions = session.get("science_current_questions", {})
    current_questions[str(subject_id)] = [q["id"] for q in questions]
    session["science_current_questions"] = current_questions

    return render_template(
        "practice_quiz.html",
        subject=subject,
        questions=questions,
        level=level,
        submit_endpoint="submit_science_level"
    )


# ============================================================
# SUBMIT SCIENCE LEVEL QUIZ
# ============================================================

@app.route(
    "/students/subject/<int:subject_id>/science-level/<int:level>/submit",
    methods=["POST"]
)
def submit_science_level(subject_id, level):
    key = f"science_unlocked_{subject_id}"
    unlocked_level = session.get(key, 1)

    if level < 1 or level > unlocked_level:
        abort(400)

    question_ids = session.get(
        "science_current_questions", {}
    ).get(str(subject_id), [])

    if not question_ids:
        return redirect(
            url_for(
                "science_level_quiz",
                subject_id=subject_id,
                level=level
            )
        )

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT s.id, s.name, s.class_id, c.class_number
            FROM subjects AS s
            INNER JOIN classes AS c ON s.class_id = c.id
            WHERE s.id = %s
              AND s.name = 'Science'
        """, (subject_id,))

        subject = cursor.fetchone()

        if not subject:
            abort(404)

        placeholders = ",".join(["%s"] * len(question_ids))

        cursor.execute(f"""
            SELECT q.id, q.question_text,
                   q.option_a, q.option_b,
                   q.option_c, q.option_d,
                   q.correct_option, q.explanation
            FROM questions AS q
            INNER JOIN chapters AS ch ON q.chapter_id = ch.id
            WHERE ch.subject_id = %s
              AND q.id IN ({placeholders})
        """, tuple([subject_id] + question_ids))

        questions = cursor.fetchall()

    finally:
        cursor.close()

    if len(questions) != len(question_ids):
        abort(400)

    answers = request.form

    score = sum(
        1 for q in questions
        if answers.get(f"question_{q['id']}") == q["correct_option"]
    )

    passed = score >= 7

    if passed and level == unlocked_level:
        session[key] = unlocked_level + 1

    return render_template(
        "quiz_result.html",
        subject=subject,
        questions=questions,
        score=score,
        total=len(questions),
        form_answers=answers,
        level=level,
        passed=passed,
        next_level=level + 1,
        quiz_type="science"
    )




@app.route("/test-db")
def test_db():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("SELECT DATABASE() AS db_name")
        result = cursor.fetchone()
        return f"Database connection successful: {result['db_name']}"
    finally:
        cursor.close()


@app.route("/exams")
def exams():
    return render_template("exams.html")

# ============================================================
# GK / GS QUIZ
# ============================================================

@app.route("/exams/gk-gs")
def gk_gs():

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id, question, option_a, option_b,
                   option_c, option_d
            FROM exam_questions
            WHERE subject_id = (
                SELECT id
                FROM exam_subjects
                WHERE subject_name = 'GK / GS'
            )
            ORDER BY RAND()
            LIMIT 10
        """)

        questions = cursor.fetchall()

    finally:
        cursor.close()

    if not questions:
        return "GK / GS questions database mein nahi mile.", 404

    # Store question IDs for secure submission
    session["gk_gs_question_ids"] = [
        q["id"] for q in questions
    ]

    return render_template(
        "gk_gs_quiz.html",
        questions=questions
    )


# ============================================================
# GK / GS QUIZ SUBMIT
# ============================================================

@app.route("/exams/gk-gs/submit", methods=["POST"])
def submit_gk_gs():

    question_ids = session.get("gk_gs_question_ids", [])

    if not question_ids:
        return redirect(url_for("gk_gs"))

    placeholders = ",".join(["%s"] * len(question_ids))

    cursor = mysql.connection.cursor()

    try:
        cursor.execute(f"""
            SELECT id, question, option_a, option_b,
                   option_c, option_d, correct_option,
                   explanation
            FROM exam_questions
            WHERE id IN ({placeholders})
        """, tuple(question_ids))

        db_questions = cursor.fetchall()

    finally:
        cursor.close()

    # Restore the original quiz order
    question_map = {
        q["id"]: q for q in db_questions
    }

    if len(question_map) != len(question_ids):
        session.pop("gk_gs_question_ids", None)
        abort(400)

    questions = [
        question_map[qid] for qid in question_ids
    ]

    score = 0

    for q in questions:
        selected = request.form.get(
            f"question_{q['id']}", ""
        ).upper()

        q["selected_answer"] = selected
        q["is_correct"] = (
            selected == str(q["correct_option"]).upper()
        )

        if q["is_correct"]:
            score += 1

    total = len(questions)

    session.pop("gk_gs_question_ids", None)

    return render_template(
        "gk_gs_result.html",
        questions=questions,
        score=score,
        total=total
    )

# ============================================================
# COMMON EXAM SYSTEM FOR OTHER 7 SUBJECTS
# ============================================================

EXAM_SUBJECTS = {
    "basic-computer": "Basic Computer",
    "history": "History",
    "geography": "Geography",
    "polity": "Polity",
    "economics": "Economics",
    "general-science": "General Science",
    "reasoning": "Reasoning"
}

DIFFICULTY_LEVELS = {
    "easy": {"name": "Easy", "total_levels": 4},
    "medium": {"name": "Medium", "total_levels": 4},
    "hard": {"name": "Hard", "total_levels": 2}
}


def get_next_exam_level(difficulty, level):
    """Return the next difficulty and level, or None if complete."""

    if difficulty == "easy":
        if level < 4:
            return "easy", level + 1
        return "medium", 1

    if difficulty == "medium":
        if level < 4:
            return "medium", level + 1
        return "hard", 1

    if difficulty == "hard":
        if level < 2:
            return "hard", level + 1

    return None


# ============================================================
# START SUBJECT QUIZ
# ============================================================

@app.route("/exams/<subject_slug>/<difficulty>/<int:level>")
def start_subject_exam(subject_slug, difficulty, level):

    subject_name = EXAM_SUBJECTS.get(subject_slug)
    difficulty = difficulty.lower()

    if not subject_name or difficulty not in DIFFICULTY_LEVELS:
        abort(404)

    total_levels = DIFFICULTY_LEVELS[difficulty]["total_levels"]

    if level < 1 or level > total_levels:
        abort(404)

    offset = (level - 1) * 10

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id, question, option_a, option_b,
                   option_c, option_d
            FROM exam_questions
            WHERE subject_id = (
                SELECT id
                FROM exam_subjects
                WHERE subject_name = %s
            )
            AND difficulty = %s
            ORDER BY id ASC
            LIMIT 10 OFFSET %s
        """, (subject_name, DIFFICULTY_LEVELS[difficulty]["name"], offset))

        questions = cursor.fetchall()

    finally:
        cursor.close()

    if len(questions) != 10:
        return (
            f"{subject_name} ke {DIFFICULTY_LEVELS[difficulty]['name']} "
            f"Level {level} ke liye 10 questions available nahi hain.",
            404
        )

    session["common_exam_question_ids"] = [
        q["id"] for q in questions
    ]

    session["common_exam_subject"] = subject_slug
    session["common_exam_difficulty"] = difficulty
    session["common_exam_level"] = level

    return render_template(
        "gk_gs_quiz.html",
        questions=questions,
        subject_name=subject_name,
        difficulty=DIFFICULTY_LEVELS[difficulty]["name"],
        difficulty_slug=difficulty,
        subject_slug=subject_slug,
        level=level
    )


# ============================================================
# SUBMIT SUBJECT QUIZ
# ============================================================

@app.route(
    "/exams/<subject_slug>/<difficulty>/<int:level>/submit",
    methods=["POST"]
)
def submit_subject_exam(subject_slug, difficulty, level):

    difficulty = difficulty.lower()

    question_ids = session.get("common_exam_question_ids", [])

    if (
        not question_ids
        or session.get("common_exam_subject") != subject_slug
        or session.get("common_exam_difficulty") != difficulty
        or session.get("common_exam_level") != level
    ):
        return redirect(url_for("exams"))

    subject_name = EXAM_SUBJECTS.get(subject_slug)

    if not subject_name:
        abort(404)

    placeholders = ",".join(["%s"] * len(question_ids))

    cursor = mysql.connection.cursor()

    try:
        cursor.execute(f"""
            SELECT id, question, option_a, option_b,
                   option_c, option_d, correct_option,
                   explanation
            FROM exam_questions
            WHERE id IN ({placeholders})
        """, tuple(question_ids))

        db_questions = cursor.fetchall()

    finally:
        cursor.close()

    question_map = {
        q["id"]: q for q in db_questions
    }

    if len(question_map) != len(question_ids):
        abort(400)

    questions = [
        question_map[qid] for qid in question_ids
    ]

    score = 0

    for q in questions:
        selected = request.form.get(
            f"question_{q['id']}", ""
        ).upper()

        q["selected_answer"] = selected

        q["is_correct"] = (
            selected == str(q["correct_option"]).upper()
        )

        if q["is_correct"]:
            score += 1

    total = len(questions)

    next_level = get_next_exam_level(difficulty, level)

    next_level_url = None

    if next_level:
        next_difficulty, next_number = next_level

        next_level_url = url_for(
            "start_subject_exam",
            subject_slug=subject_slug,
            difficulty=next_difficulty,
            level=next_number
        )

    # Clear current quiz session
    session.pop("common_exam_question_ids", None)
    session.pop("common_exam_subject", None)
    session.pop("common_exam_difficulty", None)
    session.pop("common_exam_level", None)

    return render_template(
        "gk_gs_result.html",
        questions=questions,
        score=score,
        total=total,
        subject_name=subject_name,
        subject_slug=subject_slug,
        difficulty=DIFFICULTY_LEVELS[difficulty]["name"],
        difficulty_slug=difficulty,
        level=level,
        next_level_url=next_level_url
    )


# ============================================================
# for Basic computer QUIZ
# ============================================================

@app.route('/exams/basic-computer')
def basic_computer():

    return redirect(url_for(
        "start_subject_exam",
        subject_slug="basic-computer",
        difficulty="easy",
        level=1
    ))


# ============================================================
# for general science QUIZ
# ============================================================

@app.route('/exams/general-science')
def general_science():

    return redirect(url_for(
        "start_subject_exam",
        subject_slug="general-science",
        difficulty="easy",
        level=1
    ))

# ============================================================
# for reasoning QUIZ
# ============================================================
@app.route('/exams/reasoning')
def reasoning():

    return redirect(url_for(
        "start_subject_exam",
        subject_slug="reasoning",
        difficulty="easy",
        level=1
    ))

# ============================================================
# for history QUIZ
# ============================================================
@app.route('/exams/history')
def history():

    return redirect(url_for(
        "start_subject_exam",
        subject_slug="history",
        difficulty="easy",
        level=1
    ))

# ============================================================
# for polity QUIZ
# ============================================================
@app.route('/exams/polity')
def polity_coming_soon():
    return render_template('coming_soon.html')

# ============================================================
# for geography QUIZ
# ============================================================
@app.route('/exams/Geography')
def geography_coming_soon():
    return render_template('coming_soon.html')

# ============================================================
# for econimics QUIZ
# ============================================================
@app.route('/exams/Economics')
def economics_coming_soon():
    return render_template('coming_soon.html')

# ============================================================
# for about QUIZ
# ============================================================
@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
