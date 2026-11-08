import MySQLdb
from MySQLdb.cursors import DictCursor
from openpyxl import load_workbook
from pathlib import Path
from getpass import getpass
from collections import Counter

# Excel file location
EXCEL_FILE = Path("data/basic_computer_100_questions.xlsx")

# Database connection
password = getpass("Enter MySQL root password: ")

connection = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd=password,
    db="smartlearn",
    charset="utf8mb4",
    cursorclass=DictCursor
)

try:
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Excel file not found: {EXCEL_FILE}"
        )

    workbook = load_workbook(EXCEL_FILE, data_only=True)
    sheet = workbook["questions"]

    # Read and validate headers
    headers = [
        str(cell.value).strip().lower()
        if cell.value is not None else ""
        for cell in sheet[1]
    ]

    required_columns = [
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_option",
        "explanation",
        "difficulty"
    ]

    if headers != required_columns:
        raise ValueError(
            "Excel columns do not match the required format.\n"
            f"Expected: {required_columns}\n"
            f"Found: {headers}"
        )

    cursor = connection.cursor()

    # Find Basic Computer subject
    cursor.execute(
        "SELECT id FROM exam_subjects "
        "WHERE subject_name = %s",
        ("Basic Computer",)
    )

    subject = cursor.fetchone()

    if not subject:
        raise ValueError("GK / GS subject not found in database.")

    subject_id = subject["id"]

    # Existing questions: avoid duplicate imports
    cursor.execute(
        "SELECT question FROM exam_questions WHERE subject_id = %s",
        (subject_id,)
    )

    existing_questions = {
        row["question"].strip()
        for row in cursor.fetchall()
    }

    imported = 0
    duplicates = 0
    difficulty_count = Counter()

    insert_query = """
        INSERT INTO exam_questions (
            subject_id,
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_option,
            explanation,
            difficulty
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    for row_number in range(2, sheet.max_row + 1):

        values = [
            sheet.cell(row_number, col).value
            for col in range(1, 9)
        ]

        # Skip completely empty rows
        if all(value is None for value in values):
            continue

        if any(value is None or str(value).strip() == ""
               for value in values[:6]):
            raise ValueError(
                f"Missing required value at Excel row {row_number}"
            )

        question, a, b, c, d, correct, explanation, difficulty = values

        question = str(question).strip()
        correct = str(correct).strip().upper()
        difficulty = str(difficulty).strip().title()
        explanation = str(explanation).strip()

        if correct not in ("A", "B", "C", "D"):
            raise ValueError(
                f"Invalid correct_option at row {row_number}"
            )

        if difficulty not in ("Easy", "Medium", "Hard"):
            raise ValueError(
                f"Invalid difficulty at row {row_number}"
            )

        if question in existing_questions:
            duplicates += 1
            continue

        cursor.execute(
            insert_query,
            (
                subject_id,
                question,
                str(a).strip(),
                str(b).strip(),
                str(c).strip(),
                str(d).strip(),
                correct,
                explanation,
                difficulty
            )
        )

        existing_questions.add(question)
        imported += 1
        difficulty_count[difficulty] += 1

    connection.commit()

    print("\n========== EXAM ARENA IMPORT REPORT ==========")
    print(f"GK / GS Imported: {imported}")
    print(f"Duplicates Skipped: {duplicates}")
    print(f"Easy: {difficulty_count['Easy']}")
    print(f"Medium: {difficulty_count['Medium']}")
    print(f"Hard: {difficulty_count['Hard']}")
    print(f"Total Processed: {imported + duplicates}")
    print("==============================================")

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
