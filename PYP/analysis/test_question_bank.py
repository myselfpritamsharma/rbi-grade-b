import json
import re
import unittest
from collections import Counter

from build_question_bank import OUTPUT, SUBJECTS, topic_for


class QuestionBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = json.loads((OUTPUT / "phase1_question_bank.json").read_text(encoding="utf-8"))
        cls.questions = cls.bank["questions"]

    def test_all_available_subject_year_questions_are_present(self):
        counts = Counter((q["year"], q["subject"]) for q in self.questions)
        for year in (2019, 2021, 2022, 2023, 2024, 2025, 2026):
            for subject in SUBJECTS:
                self.assertEqual(counts[(year, subject)], 60 if subject == "Reasoning" else 30)
        self.assertEqual(len({q["id"] for q in self.questions}), 840)
        self.assertTrue(all(not row["indexed_markers_not_recovered"] for row in self.bank["audit"]))

    def test_original_question_and_context_assets_exist(self):
        for question in self.questions:
            self.assertTrue(question["images"], question["id"])
            self.assertTrue(question["pages"], question["id"])
            for path in question["images"] + question["contexts"]:
                self.assertTrue((OUTPUT / path).is_file(), path)
            self.assertFalse(re.search(r"(?im)^.*answer\s*key", question["search_text"]),
                             question["id"])

    def test_numbering_anomalies_are_retained_not_merged(self):
        reasoning = [q for q in self.questions if q["year"] == 2025 and q["subject"] == "Reasoning"]
        self.assertEqual(sum(q["original_number"] == 155 for q in reasoning), 2)
        self.assertEqual(sum(q["original_number"] == 170 for q in reasoning), 1)
        self.assertEqual(sum(q["original_number"] == 125 for q in reasoning), 0)

    def test_di_data_spans_chart_and_table_pages(self):
        questions = [q for q in self.questions if q["year"] == 2024
                     and q["subject"] == "Quantitative Aptitude"
                     and 101 <= q["original_number"] <= 106]
        self.assertEqual(len(questions), 6)
        self.assertTrue(all(len(q["contexts"]) == 2 for q in questions))
        self.assertEqual(len({tuple(q["contexts"]) for q in questions}), 1)
        self.assertTrue(all(q["topic"] == "Mixed chart/table DI" for q in questions))

    def test_standalone_data_sufficiency_is_not_a_seating_set(self):
        question = next(q for q in self.questions if q["year"] == 2023
                        and q["subject"] == "Reasoning" and q["original_number"] == 135)
        self.assertEqual(question["topic"], "Data sufficiency")
        self.assertIn("square table", question["search_text"])

    def test_passage_before_first_question_page_is_preserved(self):
        question = next(q for q in self.questions if q["year"] == 2021
                        and q["subject"] == "English" and q["original_number"] == 171)
        self.assertIn("A tailor and a goldsmith were travelling together", question["search_text"])
        self.assertEqual(len(question["contexts"]), 2)
        self.assertEqual(question["chapter"], "Reading comprehension")

    def test_typo_in_source_direction_range_does_not_drop_parcel_puzzle(self):
        question = next(q for q in self.questions if q["year"] == 2025
                        and q["subject"] == "Reasoning" and q["original_number"] == 124)
        self.assertTrue(question["contexts"])
        self.assertIn("Ten persons", question["search_text"])
        self.assertEqual(question["chapter"], "Puzzles")

    def test_independent_word_question_does_not_inherit_seating_context(self):
        question = next(q for q in self.questions if q["year"] == 2019
                        and q["subject"] == "Reasoning" and q["original_number"] == 34)
        self.assertEqual(question["contexts"], [])
        self.assertEqual(question["topic"], "Alphanumeric / word operations")

    def test_classification_avoids_generic_instruction_traps(self):
        self.assertEqual(topic_for("Reasoning", "Directions: statements and conclusions A > B")[1],
                         "Inequalities")
        self.assertEqual(topic_for("Reasoning", "Which can be inferred from the statement?")[1],
                         "Critical reasoning")
        self.assertEqual(topic_for("English", "The bold part should replace the phrase; no improvement")[0],
                         "Sentence / phrase improvement")
        self.assertEqual(topic_for("English", "Identify the sentence that does not logically fit")[0],
                         "Paragraph coherence / odd sentence")
        self.assertEqual(topic_for("English", "Read the passage and fill the numbered blanks", True)[0],
                         "Cloze test / fillers")


if __name__ == "__main__":
    unittest.main()
