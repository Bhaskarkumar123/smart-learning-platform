
import os
from collections import OrderedDict

from openpyxl import load_workbook
from app import app, mysql

EXCEL_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "class7_science_100_questions.xlsx"
)

CLASS7_SCIENCE_SUBJECT_ID = 9


def main():
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(
            f"Excel file nahi mili: {EXCEL_FILE}"
        )

    workbook = load_workbook(EXCEL_FILE, data_only=True, read_only=True)
    sheet = workbook["Questions"]

    rows = sheet.iter_rows(values_only=True)
    headers = [str(value).strip() if value is not None else ""
               for value in next(rows)]
    column = {name: index for index, name in enumerate(headers)}

    required_columns = [
        "Class", "Chapter", "Question",
        "Option A", "Option B", "Option C", "Option D",
        "Correct Answer", "Explanation"
    ]

    missing = [name for name in required_columns if name not in column]
    if missing:
        workbook.close()
        raise ValueError(f"Excel mein columns missing hain: {missing}")

    questions = []
    for row in rows:
        if not row or all(value is None for value in row):
            continue

        if int(row[column["Class"]]) != 7:
            continue

        question = str(row[column["Question"]] or "").strip()
        chapter = str(row[column["Chapter"]] or "").strip()
        answer = str(row[column["Correct Answer"]] or "").strip().upper()

        if not question or not chapter:
            raise ValueError("Kisi row mein Question ya Chapter blank hai.")

        if answer not in {"A", "B", "C", "D"}:
            raise ValueError(
                f"Invalid correct answer '{answer}' for: {question}"
            )

        options = [
            str(row[column[f"Option {letter}"]] or "").strip()
            for letter in ["A", "B", "C", "D"]
        ]

        if any(not option for option in options):
            raise ValueError(f"Option blank hai: {question}")

        questions.append({
            "chapter": chapter,
            "question": question,
            "a": options[0],
            "b": options[1],
            "c": options[2],
            "d": options[3],
            "answer": answer,
            "explanation": str(
                row[column["Explanation"]] or ""
            ).strip()
        })

    workbook.close()

    if not questions:
        raise ValueError("Excel file mein Class 7 ke questions nahi mile.")

    chapters = list(OrderedDict.fromkeys(
        item["chapter"] for item in questions
    ))

    created_chapters = 0
    imported_questions = 0
    skipped_questions = 0

    with app.app_context():
        cursor = mysql.connection.cursor()

        try:
            # Confirm the subject belongs to Class 7.
            cursor.execute(
                """
                SELECT id
                FROM subjects
                WHERE id = %s AND class_id = 2
                """,
                (CLASS7_SCIENCE_SUBJECT_ID,)
            )

            if cursor.fetchone() is None:
                raise ValueError(
                    "Subject ID 9, Class 7 Science ke liye nahi mila."
                )

            # Reuse exact chapter names; create only missing ones.
            chapter_ids = {}

            cursor.execute(
                """
                SELECT COALESCE(MAX(chapter_order), 0)
                FROM chapters
                WHERE subject_id = %s
                """,
                (CLASS7_SCIENCE_SUBJECT_ID,)
            )
            next_order = list(cursor.fetchone().values())[0] or 0

            for chapter_name in chapters:
                cursor.execute(
                    """
                    SELECT id
                    FROM chapters
                    WHERE subject_id = %s AND chapter_name = %s
                    LIMIT 1
                    """,
                    (CLASS7_SCIENCE_SUBJECT_ID, chapter_name)
                )
                result = cursor.fetchone()

                if result:
                    chapter_ids[chapter_name] = result[0]
                else:
                    next_order += 1
                    cursor.execute(
                        """
                        INSERT INTO chapters
                            (chapter_name, subject_id, chapter_order)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            chapter_name,
                            CLASS7_SCIENCE_SUBJECT_ID,
                            next_order
                        )
                    )
                    chapter_ids[chapter_name] = cursor.lastrowid
                    created_chapters += 1

            # Import questions and skip exact duplicates in the same chapter.
            for item in questions:
                chapter_id = chapter_ids[item["chapter"]]

                cursor.execute(
                    """
                    SELECT id
                    FROM questions
                    WHERE chapter_id = %s AND question_text = %s
                    LIMIT 1
                    """,
                    (chapter_id, item["question"])
                )

                if cursor.fetchone():
                    skipped_questions += 1
                    continue

                cursor.execute(
                    """
                    INSERT INTO questions (
                        chapter_id, question_text,
                        option_a, option_b, option_c, option_d,
                        correct_option, explanation
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        chapter_id,
                        item["question"],
                        item["a"],
                        item["b"],
                        item["c"],
                        item["d"],
                        item["answer"],
                        item["explanation"]
                    )
                )
                imported_questions += 1

            mysql.connection.commit()

            print("\nExcel import complete!")
            print("Class 7 Science subject ID:", CLASS7_SCIENCE_SUBJECT_ID)
            print("Questions found in Excel:", len(questions))
            print("New chapters created:", created_chapters)
            print("Questions imported:", imported_questions)
            print("Duplicate questions skipped:", skipped_questions)

        except Exception:
            mysql.connection.rollback()
            raise

        finally:
            cursor.close()


if __name__ == "__main__":
    main()
