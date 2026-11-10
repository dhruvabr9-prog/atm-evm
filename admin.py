"""Administration CLI: python admin.py --help"""
import argparse
from datetime import datetime, timezone
from getpass import getpass

from database import init_db, transaction, connect_database


def main():
    init_db()
    parser = argparse.ArgumentParser(description="Manage the ATM-EVM demo election")
    commands = parser.add_subparsers(dest="command", required=True)
    voter = commands.add_parser("add-voter", help="Add a synthetic voter")
    voter.add_argument("voter_id")
    voter.add_argument("name")
    voter.add_argument("date_of_birth", help="ISO date YYYY-MM-DD")
    cand = commands.add_parser("add-candidate", help="Add a candidate")
    cand.add_argument("candidate_id")
    cand.add_argument("name")
    cand.add_argument("party")
    start = commands.add_parser("start", help="Start a new election")
    start.add_argument("name")
    commands.add_parser("stop", help="End the current election")
    commands.add_parser("status", help="Show election status")
    commands.add_parser("results", help="Show current election results")
    args = parser.parse_args()
    if args.command == "add-voter":
        datetime.strptime(args.date_of_birth, "%Y-%m-%d")
        with transaction() as db:
            db.execute("INSERT INTO voters(voter_id,name,date_of_birth) VALUES(?,?,?)", (args.voter_id, args.name, args.date_of_birth))
        print("Voter added.")
    elif args.command == "add-candidate":
        with transaction() as db:
            db.execute("INSERT INTO candidates(candidate_id,name,party) VALUES(?,?,?)", (args.candidate_id, args.name, args.party))
        print("Candidate added.")
    elif args.command == "start":
        with transaction() as db:
            if db.execute("SELECT 1 FROM election WHERE status='RUNNING'").fetchone():
                raise SystemExit("An election is already running.")
            db.execute("INSERT INTO election(name,status,start_time) VALUES(?,'RUNNING',?)", (args.name, datetime.now(timezone.utc).isoformat()))
        print("Election started.")
    elif args.command == "stop":
        with transaction() as db:
            cur = db.execute("UPDATE election SET status='ENDED',end_time=? WHERE status='RUNNING'", (datetime.now(timezone.utc).isoformat(),))
            if not cur.rowcount:
                raise SystemExit("No election is currently running.")
        print("Election ended.")
    elif args.command == "status":
        with connect_database() as db:
            row = db.execute("SELECT name,status,start_time,end_time FROM election ORDER BY election_id DESC LIMIT 1").fetchone()
        print(dict(row) if row else "No election yet.")
    elif args.command == "results":
        with connect_database() as db:
            election = db.execute("SELECT election_id,name,status FROM election ORDER BY election_id DESC LIMIT 1").fetchone()
            if not election:
                print("No election yet.")
            else:
                print(f"{election['name']} ({election['status']})")
                for row in db.execute("SELECT c.candidate_id,c.name,c.party,COUNT(v.vote_id) votes FROM candidates c LEFT JOIN votes v ON v.candidate_id=c.candidate_id AND v.election_id=? GROUP BY c.candidate_id ORDER BY votes DESC", (election['election_id'],)):
                    print(f"{row['candidate_id']} | {row['name']} | {row['party']} | {row['votes']} votes")


if __name__ == "__main__":
    main()
