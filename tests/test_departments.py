import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from werkzeug.security import generate_password_hash

from app import create_app, get_db, load_site_data


class DepartmentWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATABASE": Path(self.directory.name) / "test.sqlite", "SECRET_KEY": "test-session", "STAFF_PASSWORD_HASH": generate_password_hash("test-password")})
        self.client = self.app.test_client()

    def tearDown(self):
        self.directory.cleanup()

    def token(self):
        with self.client.session_transaction() as state:
            return state["csrf"]

    def submit(self):
        self.client.get("/departments/sangguniang-bayan/")
        return self.client.post("/departments/sangguniang-bayan/", data={"csrf": self.token(), "name": "Private Citizen", "email": "private@example.com", "kind": "Document request", "message": "Please advise about a council resolution."})

    def test_all_offices_have_profiles_and_valid_services(self):
        data = load_site_data()
        offices = data["departments"]
        self.assertEqual(sum(office["branch"] == "executive" for office in offices), 20)
        self.assertEqual(sum(office["branch"] == "legislative" for office in offices), 2)
        names = {item["name"] for item in data["services"]}
        for office in offices:
            self.assertEqual(self.client.get(f"/departments/{office['slug']}/").status_code, 200)
            self.assertTrue(set(office["services"]).issubset(names))
        self.assertEqual(self.client.get("/departments/unknown/").status_code, 404)
        self.assertIn(b"Sanggunian Secretary Office", self.client.get("/search/?q=sanggunian").data)

    def test_validation_and_csrf_do_not_save_bad_requests(self):
        self.client.get("/departments/health/")
        self.assertEqual(self.client.post("/departments/health/", data={"csrf": "invalid"}).status_code, 400)
        self.assertEqual(self.client.post("/departments/health/", data={"csrf": "non-ascii-\u00e9"}).status_code, 400)
        self.assertEqual(self.client.post("/departments/health/", data={"csrf": self.token(), "name": "Citizen", "email": "bad", "kind": "Feedback", "message": "Test"}).status_code, 400)
        with self.app.app_context():
            self.assertEqual(get_db().execute("SELECT COUNT(*) FROM department_requests").fetchone()[0], 0)

    def test_saved_reference_staff_update_and_private_tracking(self):
        result = self.submit()
        self.assertEqual(result.status_code, 303)
        reference = parse_qs(urlparse(result.location).query)["reference"][0]
        receipt = self.client.get(result.location)
        self.assertIn(reference.encode(), receipt.data)
        self.assertNotIn(b"private@example.com", receipt.data)
        self.assertNotIn(b"Private Citizen", receipt.data)
        self.assertEqual(self.client.get("/submissions/").status_code, 302)
        self.assertEqual(self.client.post("/staff/department-requests/1/", data={"csrf": self.token(), "status": "Resolved"}).status_code, 403)
        self.client.get("/staff/login/")
        login = self.client.post("/staff/login/", data={"csrf": self.token(), "username": "staff", "password": "test-password"})
        self.assertEqual(login.status_code, 303)
        self.assertIn(b"private@example.com", self.client.get("/submissions/").data)
        self.assertEqual(self.client.post("/staff/department-requests/1/", data={"csrf": self.token(), "status": "Invalid"}).status_code, 400)
        update = self.client.post("/staff/department-requests/1/", data={"csrf": self.token(), "status": "In review"})
        self.assertEqual(update.status_code, 303)
        self.assertIn(b"In review", self.client.get(f"/departments/track/?reference={reference}").data)
        self.client.post("/staff/logout/", data={"csrf": self.token()})
        self.assertEqual(self.client.get("/submissions/").status_code, 302)


if __name__ == "__main__":
    unittest.main()
