
import MySQLdb
from MySQLdb.cursors import DictCursor
from openpyxl import load_workbook
from pathlib import Path
from getpass import getpass
from collections import Counter

EXCEL_FILE = Path("data/reasoning_questions.xlsx")
SUBJECT_ID = 4

if not EXCEL_FILE.exists():
    raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")

workbook = load_workbook(EXCEL_FILE, data_only=True)
sheet = workbook["questions"]

headers = [
    str(cell.value).strip().lower() if cell.value is not None else ""
    for cell in sheet[1]
]

required_headers = [
    "question", "option_a", "option_b", "option_c",
    "option_d", "correct_option", "explanation", "difficulty"
]

missing = [h for h in required_headers if h not in headers]
if missing:
    raise ValueError(f"Missing Excel columns: {missing}")

column_index = {name: headers.index(name) for name in required_headers}

connection = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd=getpass("MySQL password: "),
    db="smartlearn",
    charset="utf8mb4"
)

cursor = connection.cursor(DictCursor)

try:
    cursor.execute(
        "SELECT id FROM exam_subjects WHERE id = %s",
        (SUBJECT_ID,)
    )
    subject = cursor.fetchone()

    if not subject:
        raise ValueError("Reasoning subject ID 4 not found.")

    cursor.execute("""
        SELECT question
        FROM exam_questions
        WHERE subject_id = %s
    """, (SUBJECT_ID,))

    existing_questions = {
        row["question"].strip()
        for row in cursor.fetchall()
    }

    inserted = 0
    skipped = 0
    difficulty_count = Counter()

    for row_number, row in enumerate(
        sheet.iter_rows(min_row=2, values_only=True), start=2
    ):
        values = {
            name: row[index]
            for name, index in column_index.items()
        }

        question = values["question"]
        options = [
            values["option_a"],
            values["option_b"],
            values["option_c"],
            values["option_d"]
        ]

        if not question or any(v is None or str(v).strip() == "" for v in options):
            print(f"Skipped incomplete row: {row_number}")
            skipped += 1
            continue

        question = str(question).strip()
        correct_option = str(values["correct_option"]).strip().upper()
        difficulty = str(values["difficulty"]).strip().capitalize()

        if correct_option not in ("A", "B", "C", "D"):
            print(f"Invalid correct option at row {row_number}")
            skipped += 1
            continue

        if difficulty not in ("Easy", "Medium", "Hard"):
            print(f"Invalid difficulty at row {row_number}")
            skipped += 1
            continue

        if question in existing_questions:
            skipped += 1
            continue

        explanation = (
            str(values["explanation"]).strip()
            if values["explanation"] is not None
            and str(values["explanation"]).strip()
            else None
        )

        cursor.execute("""
            INSERT INTO exam_questions
            (subject_id, question, option_a, option_b,
             option_c, option_d, correct_option,
             explanation, difficulty)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            SUBJECT_ID,
            question,
            *[str(v).strip() for v in options],
            correct_option,
            explanation,
            difficulty
        ))

        existing_questions.add(question)
        inserted += 1
        difficulty_count[difficulty] += 1

    connection.commit()

    print("\nReasoning import completed!")
    print("Inserted:", inserted)
    print("Skipped:", skipped)
    print("Difficulty distribution:", dict(difficulty_count))

except Exception:
    connection.rollback()
    raise

finally:
    cursor.close()
    connection.close()
    workbook.close()
