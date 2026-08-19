import unittest
import json
import csv
import os

class TestCasesDataset(unittest.TestCase):
    def setUp(self):
        self.cases_json_path = os.path.join(os.path.dirname(__file__), "..", "data", "cases.json")
        self.cases_csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "cases.csv")
        if not os.path.exists(self.cases_csv_path):
            self.cases_csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "cases.csv")

    def test_json_cases_count_and_schema(self):
        self.assertTrue(os.path.exists(self.cases_json_path), "cases.json must exist")
        with open(self.cases_json_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        self.assertGreaterEqual(len(cases), 30, f"Expected at least 30 cases, found {len(cases)}")
        
        required_fields = [
            "case_id", "title", "concept_tag", "osi_layer", "severity",
            "symptom", "topology_notes", "show_outputs", "expected_fault",
            "ground_truth_fix", "verification_command"
        ]

        seen_ids = set()
        for c in cases:
            for field in required_fields:
                self.assertIn(field, c, f"Case {c.get('case_id')} missing {field}")
                self.assertTrue(len(str(c[field]).strip()) > 0, f"Case {c.get('case_id')} has empty {field}")
            
            case_id = c["case_id"]
            self.assertNotIn(case_id, seen_ids, f"Duplicate case_id {case_id}")
            seen_ids.add(case_id)

    def test_csv_cases_sync(self):
        self.assertTrue(os.path.exists(self.cases_csv_path), "cases.csv must exist")
        with open(self.cases_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertGreaterEqual(len(rows), 30, f"Expected at least 30 cases in CSV, found {len(rows)}")

if __name__ == "__main__":
    unittest.main()
