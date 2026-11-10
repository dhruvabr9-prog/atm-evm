import tempfile
import unittest
from pathlib import Path

import database
from app import create_app


class VotingFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent.parent)
        database.DB_PATH = Path(self.temp_dir.name) / "test.db"
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret", "ADMIN_PASSWORD": "test-password"})
        self.client = self.app.test_client()
        database.init_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_home_and_protected_admin(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/admin").status_code, 302)

    def test_admin_can_add_records_and_start_election(self):
        self.client.post("/admin/login", data={"password": "test-password"})
        self.client.post("/admin/voters", data={"voter_id": "D-1", "name": "Demo Voter", "date_of_birth": "1990-01-01"})
        self.client.post("/admin/candidates", data={"candidate_id": "C-1", "name": "Demo Candidate", "party": "Demo"})
        self.client.post("/admin/election/start", data={"name": "Test Election"})
        page = self.client.get("/admin")
        self.assertIn(b"Demo Voter", page.data)
        self.assertIn(b"RUNNING", page.data)

    def test_vote_is_recorded_once_and_election_can_end(self):
        with database.transaction() as db:
            db.execute("INSERT INTO voters(voter_id,name,date_of_birth) VALUES('D-1','Demo','1990-01-01')")
            db.execute("INSERT INTO candidates(candidate_id,name,party) VALUES('C-1','Candidate','Demo')")
            db.execute("INSERT INTO election(name,status) VALUES('Test','RUNNING')")
        response = self.client.post("/vote", data={"voter_id": "D-1", "date_of_birth": "1990-01-01", "candidate_id": "C-1"})
        self.assertEqual(response.status_code, 302)
        self.client.post("/vote", data={"voter_id": "D-1", "date_of_birth": "1990-01-01", "candidate_id": "C-1"})
        with database.connect_database() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM votes").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT has_voted FROM voters WHERE voter_id='D-1'").fetchone()[0], 1)
        self.client.post("/admin/login", data={"password": "test-password"})
        self.client.post("/admin/election/stop")
        with database.connect_database() as db:
            self.assertEqual(db.execute("SELECT status FROM election").fetchone()[0], "ENDED")


if __name__ == "__main__":
    unittest.main()
