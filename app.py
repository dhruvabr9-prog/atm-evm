"""Flask web interface for the ATM-EVM classroom/demo project."""
import os
import hmac
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from database import connect_database, init_db, transaction


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get("ATM_EVM_SECRET_KEY", "development-only-change-me"), ADMIN_PASSWORD=os.environ.get("ATM_EVM_ADMIN_PASSWORD", ""))
    if test_config:
        app.config.update(test_config)
    init_db()

    def admin_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("is_admin"):
                return redirect(url_for("admin_login"))
            return view(*args, **kwargs)
        return wrapped

    @app.get("/")
    def index():
        with connect_database() as db:
            election = db.execute("SELECT * FROM election ORDER BY election_id DESC LIMIT 1").fetchone()
            candidates = db.execute("SELECT candidate_id,name,party FROM candidates ORDER BY name").fetchall()
        return render_template("index.html", election=election, candidates=candidates)

    @app.post("/vote")
    def cast_vote():
        voter_id = request.form.get("voter_id", "").strip()
        dob = request.form.get("date_of_birth", "").strip()
        candidate_id = request.form.get("candidate_id", "").strip()
        try:
            with transaction() as db:
                election = db.execute("SELECT election_id FROM election WHERE status='RUNNING' ORDER BY election_id DESC LIMIT 1").fetchone()
                voter = db.execute("SELECT voter_id,has_voted FROM voters WHERE voter_id=? AND date_of_birth=?", (voter_id, dob)).fetchone()
                candidate = db.execute("SELECT candidate_id FROM candidates WHERE candidate_id=?", (candidate_id,)).fetchone()
                if not election:
                    flash("Voting is currently closed.", "error")
                elif not voter:
                    flash("Voter ID and date of birth did not match.", "error")
                elif voter["has_voted"]:
                    flash("This voter has already voted.", "error")
                elif not candidate:
                    flash("Choose a valid candidate.", "error")
                else:
                    db.execute("INSERT INTO votes(election_id,candidate_id) VALUES(?,?)", (election["election_id"], candidate_id))
                    db.execute("UPDATE voters SET has_voted=1 WHERE voter_id=?", (voter_id,))
                    flash("Your vote was recorded.", "success")
        except Exception:
            app.logger.exception("Vote transaction failed")
            flash("The vote could not be recorded. Please retry or contact the administrator.", "error")
        return redirect(url_for("index"))

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            password = app.config.get("ADMIN_PASSWORD", "")
            if not password:
                flash("Set ATM_EVM_ADMIN_PASSWORD before using the admin area.", "error")
            elif hmac.compare_digest(request.form.get("password", ""), password):
                session["is_admin"] = True
                return redirect(url_for("admin_dashboard"))
            else:
                flash("Incorrect password.", "error")
        return render_template("login.html")

    @app.post("/admin/logout")
    def admin_logout():
        session.clear()
        return redirect(url_for("index"))

    @app.get("/admin")
    @admin_required
    def admin_dashboard():
        with connect_database() as db:
            voters = db.execute("SELECT voter_id,name,date_of_birth,has_voted FROM voters ORDER BY name").fetchall()
            candidates = db.execute("SELECT * FROM candidates ORDER BY name").fetchall()
            election = db.execute("SELECT * FROM election ORDER BY election_id DESC LIMIT 1").fetchone()
            results = []
            if election:
                results = db.execute("SELECT c.candidate_id,c.name,c.party,COUNT(v.vote_id) votes FROM candidates c LEFT JOIN votes v ON v.candidate_id=c.candidate_id AND v.election_id=? GROUP BY c.candidate_id ORDER BY votes DESC", (election["election_id"],)).fetchall()
        return render_template("admin.html", voters=voters, candidates=candidates, election=election, results=results)

    @app.post("/admin/voters")
    @admin_required
    def add_voter():
        try:
            datetime.strptime(request.form.get("date_of_birth", ""), "%Y-%m-%d")
            with transaction() as db:
                db.execute("INSERT INTO voters(voter_id,name,date_of_birth) VALUES(?,?,?)", (request.form["voter_id"].strip(), request.form["name"].strip(), request.form["date_of_birth"]))
            flash("Voter added.", "success")
        except (ValueError, KeyError):
            flash("Enter a valid date and complete voter details.", "error")
        except Exception:
            flash("Could not add voter. Check for a duplicate voter ID.", "error")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/candidates")
    @admin_required
    def add_candidate():
        try:
            with transaction() as db:
                db.execute("INSERT INTO candidates(candidate_id,name,party) VALUES(?,?,?)", (request.form["candidate_id"].strip(), request.form["name"].strip(), request.form["party"].strip()))
            flash("Candidate added.", "success")
        except Exception:
            flash("Could not add candidate. Check for a duplicate candidate ID.", "error")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/election/start")
    @admin_required
    def start_election():
        name = request.form.get("name", "").strip()
        if not name:
            flash("Enter an election name.", "error")
        else:
            with transaction() as db:
                if db.execute("SELECT 1 FROM election WHERE status='RUNNING'").fetchone():
                    flash("An election is already running.", "error")
                else:
                    db.execute("INSERT INTO election(name,status,start_time) VALUES(?,'RUNNING',?)", (name, datetime.now(timezone.utc).isoformat()))
                    flash("Election started.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/election/stop")
    @admin_required
    def stop_election():
        with transaction() as db:
            result = db.execute("UPDATE election SET status='ENDED',end_time=? WHERE status='RUNNING'", (datetime.now(timezone.utc).isoformat(),))
        flash("Election ended." if result.rowcount else "No election is currently running.", "success" if result.rowcount else "error")
        return redirect(url_for("admin_dashboard"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
