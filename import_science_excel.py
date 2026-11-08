
from pathlib import Path
import openpyxl

from app import app, mysql


EXCEL_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "class6_science_50_questions.xlsx"
)


def get_column_names(cursor, table_name):
    cursor.execute(f"DESCRIBE `{table_name}`")
    return {row["Field"] for row in cursor.fetchall()}


def import_questions():
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Excel file nahi mili: {EXCEL_FILE}"
        )

    workbook = openpyxl.load_workbook(
        EXCEL_FILE,
        read_only=True,
        data_only=True,
    )

    if "Questions" not in workbook.sheetnames:
        raise ValueError("Excel mein 'Questions' sheet nahi mili.")

    sheet = workbook["Questions"]
    rows = sheet.iter_rows(values_only=True)

    headers = [str(value).strip() if value is not None else "" 
               for value in next(rows)]
    records = [dict(zip(headers, row)) for row in rows]

    required_headers = {
        "Class", "Chapter", "Question",
        "Option A", "Option B", "Option C", "Option D",
        "Correct Answer", "Explanation",
    }

    if not required_headers.issubset(set(headers)):
        missing = required_headers - set(headers)
        raise ValueError(f"Excel ke columns missing hain: {missing}")

    with app.app_context():
        connection = mysql.connection
        cursor = connection.cursor()

        try:
            chapter_columns = get_column_names(cursor, "chapters")
            question_columns = get_column_names(cursor, "questions")

            # Database mein Class 6 ki Science subject ID dhoondo.
            cursor.execute("""
                SELECT s.id
                FROM subjects AS s
                INNER JOIN classes AS c ON c.id = s.class_id
                WHERE c.class_number = 6
                  AND LOWER(s.name) = 'science'
                LIMIT 1
            """)
            subject_row = cursor.fetchone()

            if not subject_row:
                raise ValueError(
                    "Class 6 Science subject database mein nahi mila."
                )

            subject_id = subject_row["id"]

            # Table ke actual chapter-name column ko identify karo.
            if "chapter_name" in chapter_columns:
                chapter_name_column = "chapter_name"
            elif "name" in chapter_columns:
                chapter_name_column = "name"
            else:
                raise ValueError(
                    "chapters table mein chapter_name ya name column nahi mila."
                )

            if "subject_id" not in chapter_columns:
                raise ValueError("chapters table mein subject_id column nahi mila.")

            if "chapter_id" not in question_columns:
                raise ValueError("questions table mein chapter_id column nahi mila.")

            inserted = 0
            skipped = 0
            created_chapters = 0
            chapter_cache = {}

            for excel_row, record in enumerate(records, start=2):
                if not record.get("Question") or not record.get("Chapter"):
                    raise ValueError(
                        f"Excel row {excel_row}: Question ya Chapter khaali hai."
                    )

                if int(record["Class"]) != 6:
                    raise ValueError(
                        f"Excel row {excel_row}: Class 6 ke alawa class mili."
                    )

                correct = str(record["Correct Answer"]).strip().upper()
                if correct not in {"A", "B", "C", "D"}:
                    raise ValueError(
                        f"Excel row {excel_row}: Correct Answer A/B/C/D hona chahiye."
                    )

                chapter_name = str(record["Chapter"]).strip()
                question_text = str(record["Question"]).strip()

                # Chapter pehle se hai toh use karo; warna create karo.
                if chapter_name not in chapter_cache:
                    cursor.execute(
                        f"""
                        SELECT id
                        FROM chapters
                        WHERE subject_id = %s
                          AND `{chapter_name_column}` = %s
                        LIMIT 1
                        """,
                        (subject_id, chapter_name),
                    )
                    chapter = cursor.fetchone()

                    if chapter:
                        chapter_id = chapter["id"]
                    else:
                        insert_columns = ["subject_id", chapter_name_column]
                        insert_values = [subject_id, chapter_name]
                        placeholders = ["%s", "%s"]

                        if "chapter_order" in chapter_columns:
                            cursor.execute("""
                                SELECT COALESCE(MAX(chapter_order), 0) AS max_order
                                FROM chapters
                                WHERE subject_id = %s
                            """, (subject_id,))
                            max_order = cursor.fetchone()["max_order"]

                            insert_columns.append("chapter_order")
                            insert_values.append(max_order + 1)
                            placeholders.append("%s")

                        sql = (
                            "INSERT INTO chapters "
                            f"({', '.join('`' + col + '`' for col in insert_columns)}) "
                            f"VALUES ({', '.join(placeholders)})"
                        )
                        cursor.execute(sql, tuple(insert_values))
                        chapter_id = cursor.lastrowid
                        created_chapters += 1

                    chapter_cache[chapter_name] = chapter_id

                chapter_id = chapter_cache[chapter_name]

                # Same chapter mein same question ho toh duplicate skip karo.
                cursor.execute("""
                    SELECT id
                    FROM questions
                    WHERE chapter_id = %s AND question_text = %s
                    LIMIT 1
                """, (chapter_id, question_text))

                if cursor.fetchone():
                    skipped += 1
                    continue

                cursor.execute("""
                    INSERT INTO questions (
                        chapter_id,
                        question_text,
                        option_a,
                        option_b,
                        option_c,
                        option_d,
                        correct_option,
                        explanation
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    chapter_id,
                    question_text,
                    str(record["Option A"]).strip(),
                    str(record["Option B"]).strip(),
                    str(record["Option C"]).strip(),
                    str(record["Option D"]).strip(),
                    correct,
                    str(record.get("Explanation") or "").strip(),
                ))

                inserted += 1

            connection.commit()

            print("\nExcel import complete!")
            print(f"Class 6 Science subject ID: {subject_id}")
            print(f"New chapters created: {created_chapters}")
            print(f"Questions imported: {inserted}")
            print(f"Duplicate questions skipped: {skipped}")

        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            workbook.close()


if __name__ == "__main__":
    import_questions()
