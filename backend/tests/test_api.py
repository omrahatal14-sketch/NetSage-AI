import unittest
import json
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app

class TestNetSageAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_cases(self):
        res = self.client.get('/api/cases')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertGreaterEqual(data["count"], 30)

    def test_get_single_case(self):
        res = self.client.get('/api/cases/CASE-001')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["case_id"], "CASE-001")

    def test_diagnose_endpoint(self):
        res = self.client.post('/api/diagnose', json={
            "case_id": "CASE-001",
            "symptom": "PC-A cannot ping PC-B",
            "show_outputs": "encapsulation dot1Q 25"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("ai_diagnosis", data)
        self.assertIn("root_cause", data["ai_diagnosis"])

    def test_rule_check_endpoint(self):
        res = self.client.post('/api/rule_check', json={
            "show_outputs": "GigabitEthernet0/1 administratively down down",
            "symptom": "Link down"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertGreater(data["count"], 0)

    def test_reviews_crud(self):
        # GET reviews
        res_get = self.client.get('/api/reviews')
        self.assertEqual(res_get.status_code, 200)
        data_get = json.loads(res_get.data)
        self.assertGreaterEqual(data_get["count"], 5)

        # POST new review
        res_post = self.client.post('/api/reviews', json={
            "case_id": "CASE-002",
            "verdict": "Accepted",
            "reviewer": "Automated Tester",
            "notes": "Verified by automated unit test."
        })
        self.assertEqual(res_post.status_code, 201)

    def test_stats_endpoint(self):
        res = self.client.get('/api/stats')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("total_cases", data)
        self.assertIn("category_counts", data)
        self.assertIn("osi_counts", data)

    def test_simulate_fix_endpoint(self):
        res = self.client.post('/api/simulate_fix', json={
            "case_id": "CASE-001",
            "commands": ["interface Gi0/0/0.20", "encapsulation dot1Q 20", "ip address 192.168.20.1 255.255.255.0"]
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["verification_result"], "PASSED")

if __name__ == "__main__":
    unittest.main()
