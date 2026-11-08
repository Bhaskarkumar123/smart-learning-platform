
CREATE DATABASE IF NOT EXISTS smartlearn;
USE smartlearn;

-- 1. Classes: Class 6 to 12
CREATE TABLE IF NOT EXISTS classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_number INT NOT NULL UNIQUE
);

-- 2. Subjects available for each class
CREATE TABLE IF NOT EXISTS subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (class_id) REFERENCES classes(id),
    UNIQUE (class_id, name)
);

-- 3. Chapters belonging to subjects
CREATE TABLE IF NOT EXISTS chapters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    chapter_name VARCHAR(200) NOT NULL,
    chapter_order INT DEFAULT 1,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- 4. Formula library: Maths, Physics and Chemistry
CREATE TABLE IF NOT EXISTS formulas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chapter_id INT NOT NULL,
    formula_name VARCHAR(200) NOT NULL,
    formula_expression TEXT NOT NULL,
    explanation TEXT,
    unit VARCHAR(100),
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);

-- 5. Practice questions
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chapter_id INT NOT NULL,
    question_text TEXT NOT NULL,
    option_a VARCHAR(500) NOT NULL,
    option_b VARCHAR(500) NOT NULL,
    option_c VARCHAR(500) NOT NULL,
    option_d VARCHAR(500) NOT NULL,
    correct_option CHAR(1) NOT NULL,
    explanation TEXT,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);

-- 6. Quiz results
CREATE TABLE IF NOT EXISTS quiz_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(150),
    chapter_id INT NOT NULL,
    score INT NOT NULL DEFAULT 0,
    total_questions INT NOT NULL DEFAULT 0,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);

-- Insert classes 6 to 12
INSERT IGNORE INTO classes (class_number)
VALUES (6), (7), (8), (9), (10), (11), (12);


-- =========================================
-- SMARTLEARN: SUBJECT DATA FOR CLASSES 6–12
-- =========================================

-- Subjects for Classes 6–10
INSERT INTO subjects (class_id, name)
SELECT c.id, s.name
FROM classes c
CROSS JOIN (
    SELECT 'Mathematics' AS name
    UNION ALL SELECT 'Science'
) AS s
WHERE c.class_number BETWEEN 6 AND 10;

-- Subjects for Classes 11–12
INSERT INTO subjects (class_id, name)
SELECT c.id, s.name
FROM classes c
CROSS JOIN (
    SELECT 'Physics' AS name
    UNION ALL SELECT 'Chemistry'
    UNION ALL SELECT 'Mathematics'
    UNION ALL SELECT 'Biology'
) AS s
WHERE c.class_number BETWEEN 11 AND 12;



USE smartlearn;

-- =========================================
-- SMARTLEARN: STUDY NOTES
-- =========================================

CREATE TABLE IF NOT EXISTS study_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    note_type VARCHAR(50) NOT NULL DEFAULT 'Concept',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- =========================================
-- SMARTLEARN: SUBJECT FORMULAS
-- No chapter selection required
-- =========================================

CREATE TABLE IF NOT EXISTS subject_formulas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    formula_name VARCHAR(200) NOT NULL,
    formula_expression TEXT NOT NULL,
    explanation TEXT,
    unit VARCHAR(100),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- =========================================
-- SMARTLEARN: QUIZ PROGRESS
-- =========================================

CREATE TABLE IF NOT EXISTS quiz_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_key VARCHAR(100) NOT NULL,
    subject_id INT NOT NULL,
    highest_unlocked_level INT NOT NULL DEFAULT 1,
    best_score INT NOT NULL DEFAULT 0,
    UNIQUE KEY unique_student_subject (session_key, subject_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- =========================================
-- SMARTLEARN: QUIZ ATTEMPTS
-- =========================================

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_key VARCHAR(100) NOT NULL,
    subject_id INT NOT NULL,
    level_number INT NOT NULL,
    score INT NOT NULL,
    total_questions INT NOT NULL DEFAULT 10,
    passed BOOLEAN NOT NULL DEFAULT FALSE,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);


-- Class 6 Mathematics: Knowing Our Numbers
-- Add sample quiz questions only if they do not already exist.

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, 'What is the place value of 7 in 47,352?',
'7', '70', '700', '7000', 'D',
'The digit 7 is in the thousands place, so its place value is 7000.'
WHERE NOT EXISTS (
    SELECT 1 FROM questions
    WHERE chapter_id = 1
    AND question_text = 'What is the place value of 7 in 47,352?'
);

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, 'Which is the greatest number?',
'45,678', '45,786', '45,687', '45,768', 'B',
'45,786 is the greatest among the four numbers.';


-- Class 6 Mathematics: Remaining questions
-- Knowing Our Numbers (chapter_id = 1)

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, 'What is 3,456 + 2,789?',
'6,145', '6,245', '6,255', '6,345', 'B',
'3,456 + 2,789 = 6,245.'
WHERE NOT EXISTS (
    SELECT 1 FROM questions
    WHERE chapter_id = 1 AND question_text = 'What is 3,456 + 2,789?'
);

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, 'What is 8,000 - 3,475?',
'4,425', '4,525', '4,625', '4,725', 'B',
'8,000 - 3,475 = 4,525.'
WHERE NOT EXISTS (
    SELECT 1 FROM questions
    WHERE chapter_id = 1 AND question_text = 'What is 8,000 - 3,475?'
);

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, 'Which number is the smallest?',
'12,345', '12,354', '12,435', '12,543', 'A',
'12,345 is the smallest number.'
WHERE NOT EXISTS (
    SELECT 1 FROM questions
    WHERE chapter_id = 1 AND question_text = 'Which number is the smallest?'
);

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, 'What is the successor of 99,999?',
'99,998', '100,000', '100,001', '99,000', 'B',
'The successor is the next number: 99,999 + 1 = 100,000.'
WHERE NOT EXISTS (
    SELECT 1 FROM questions
    WHERE chapter_id = 1 AND question_text = 'What is the successor of 99,999?'
);

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, 'What is the predecessor of 50,000?',
'49,999', '50,001', '49,990', '50,010', 'A',
'The predecessor is one less: 50,000 - 1 = 49,999.'
WHERE NOT EXISTS (
    SELECT 1 FROM questions
    WHERE chapter_id = 1 AND question_text = 'What is the predecessor of 50,000?'
);

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, 'What is 125 multiplied by 8?',
'900', '950', '1,000', '1,100', 'C',
'125 multiplied by 8 equals 1,000.'
WHERE NOT EXISTS (
    SELECT 1 FROM questions
    WHERE chapter_id = 1 AND question_text = 'What is 125 multiplied by 8?'
);

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, 'Which digit is in the hundreds place in 63,482?',
'3', '4', '8', '2', 'B',
'In 63,482, the digit 4 is in the hundreds place.'
WHERE NOT EXISTS (
    SELECT 1 FROM questions
    WHERE chapter_id = 1 AND question_text = 'Which digit is in the hundreds place in 63,482?'
);

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, 'What is 7,200 divided by 8?',
'800', '850', '900', '950', 'C',
'7,200 divided by 8 equals 900.'
WHERE NOT EXISTS (
    SELECT 1 FROM questions
    WHERE chapter_id = 1 AND question_text = 'What is 7,200 divided by 8?'
);


INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
VALUES
(1, 'What is 348 + 276?', '614', '624', '634', '644', 'B', '348 + 276 = 624.'),
(1, 'What is 900 - 457?', '443', '453', '463', '543', 'A', '900 - 457 = 443.'),
(1, 'What is 24 x 15?', '340', '350', '360', '370', 'C', '24 x 15 = 360.'),
(1, 'What is 864 divided by 12?', '62', '68', '72', '82', 'C', '864 divided by 12 = 72.'),
(1, 'What is the place value of 7 in 57,326?', '7', '700', '7000', '70000', 'C', '7 is in the thousands place.'),
(1, 'Round 4768 to the nearest hundred.', '4700', '4760', '4800', '5000', 'C', '4768 rounds to 4800.'),
(1, 'What is (18 + 12) x 3?', '66', '78', '90', '96', 'C', '30 x 3 = 90.'),
(1, 'Which number is divisible by 5?', '132', '247', '365', '418', 'C', 'Numbers ending in 0 or 5 are divisible by 5.'),
(1, 'What is the HCF of 12 and 18?', '3', '6', '9', '12', 'B', 'The HCF is 6.'),
(1, 'What is the LCM of 4 and 6?', '8', '10', '12', '24', 'C', 'The LCM is 12.'),
(1, 'Which is a prime number?', '21', '27', '29', '33', 'C', '29 has exactly two factors.'),
(1, 'What is 3/8 + 2/8?', '5/16', '1/8', '5/8', '6/8', 'C', 'Add the numerators: 5/8.'),
(1, 'What is 7/10 - 3/10?', '4/10', '4/20', '3/10', '1/10', 'A', '7/10 - 3/10 = 4/10.'),
(1, 'Which fraction equals 1/2?', '2/3', '3/6', '4/6', '5/8', 'B', '3/6 simplifies to 1/2.'),
(1, 'What is 2/3 of 18?', '6', '9', '12', '15', 'C', '18 divided by 3, then multiplied by 2, equals 12.'),
(1, 'What is 2.5 + 1.75?', '3.25', '4.15', '4.25', '4.75', 'C', '2.50 + 1.75 = 4.25.'),
(1, 'What is 8.4 - 3.7?', '4.7', '5.3', '5.7', '4.3', 'A', '8.4 - 3.7 = 4.7.'),
(1, 'What is 0.6 x 10?', '0.06', '0.6', '6', '60', 'C', 'Multiplying by 10 gives 6.'),
(1, 'What is the perimeter of a square with side 7 cm?', '14 cm', '21 cm', '28 cm', '49 cm', 'C', '4 x 7 = 28 cm.'),
(1, 'What is the area of a rectangle 8 cm long and 5 cm wide?', '13 cm2', '26 cm2', '40 cm2', '80 cm2', 'C', 'Area = 8 x 5 = 40 cm2.'),
(1, 'How many sides does a hexagon have?', '5', '6', '7', '8', 'B', 'A hexagon has 6 sides.'),
(1, 'An angle of 90 degrees is called what?', 'Acute', 'Obtuse', 'Right', 'Straight', 'C', 'A right angle measures 90 degrees.'),
(1, 'How many lines of symmetry does a square have?', '2', '3', '4', '6', 'C', 'A square has 4 lines of symmetry.'),
(1, 'Convert 3 metres into centimetres.', '30 cm', '300 cm', '3000 cm', '3 cm', 'B', '3 metres = 300 centimetres.'),
(1, 'How many grams are in 2.5 kilograms?', '25 g', '250 g', '2050 g', '2500 g', 'D', '2.5 kg = 2500 g.'),
(1, 'How many minutes are in 2 hours 15 minutes?', '125', '130', '135', '145', 'C', '120 + 15 = 135 minutes.'),
(1, 'A book costs Rs 75. What do 4 books cost?', 'Rs 250', 'Rs 275', 'Rs 300', 'Rs 350', 'C', '75 x 4 = 300.'),
(1, 'What is 5 units to the left of 2 on a number line?', '-7', '-3', '3', '7', 'B', '2 - 5 = -3.'),
(1, 'What is -4 + 9?', '-13', '-5', '5', '13', 'C', '-4 + 9 = 5.'),
(1, 'What is the average of 4, 6 and 8?', '5', '6', '7', '18', 'B', '(4 + 6 + 8) divided by 3 = 6.');


WHERE NOT EXISTS (
    SELECT 1 FROM questions
    WHERE chapter_id = 1
    AND question_text = 'Which is the greatest number?'
);

INSERT INTO questions
(chapter_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
SELECT 1, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d,
       q.correct_option, q.explanation
FROM (
    SELECT
    'What is the place value of 7 in 57,321?' AS question_text,
    '7' AS option_a, '700' AS option_b, '7,000' AS option_c, '70,000' AS option_d,
    'C' AS correct_option,
    'The digit 7 is in the thousands place, so its place value is 7,000.' AS explanation

    UNION ALL SELECT
    'Which is the expanded form of 4,582?',
    '400 + 50 + 8 + 2', '4,000 + 500 + 80 + 2',
    '4,000 + 50 + 80 + 2', '400 + 5,000 + 80 + 2',
    'B', '4,582 = 4,000 + 500 + 80 + 2.'

    UNION ALL SELECT
    'What is the successor of 78,999?',
    '78,998', '79,000', '78,990', '79,999',
    'B', 'The successor is the number plus one.'

    UNION ALL SELECT
    'What is the predecessor of 1,000?',
    '999', '1,001', '990', '900',
    'A', 'The predecessor is one less than the number.'

    UNION ALL SELECT
    'Which number is the greatest?',
    '65,432', '65,423', '65,342', '65,324',
    'A', '65,432 is the greatest of these numbers.'

    UNION ALL SELECT
    'What is 2,450 + 3,650?',
    '5,000', '6,000', '6,100', '5,900',
    'B', '2,450 + 3,650 = 6,100.'
) AS q
WHERE NOT EXISTS (
    SELECT 1
    FROM questions existing
    WHERE existing.chapter_id = 1
      AND existing.question_text = q.question_text
);
