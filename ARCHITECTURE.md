# Architecture and data handling

## Request flow

1. A voter submits voter ID, date of birth, and a candidate selection to `/vote`.
2. Flask opens an immediate SQLite transaction, checks that an election is running, verifies the synthetic voter record, and validates the candidate.
3. It inserts the ballot and updates the voter's `has_voted` flag in the same transaction. Any failure rolls both operations back.
4. Administrators sign in with the configured shared password and manage voters, candidates, and election state at `/admin`.

## Files

- `app.py`: Flask app factory, routes, admin session check, voting flow.
- `database.py`: stable database path, schema initialization, SQLite connection and transaction helpers.
- `admin.py`: command-line voter, candidate, election, status, and results commands.
- `templates/`: voter screen and administrator views.
- `static/style.css`: responsive visual styling.

## Data minimization

No Aadhaar number is requested or persisted. The demo stores voter ID and date of birth for eligibility checks, and ballots are linked to elections and candidates without recording voter IDs in the ballot table. The separate `has_voted` marker still links participation status to the voter registry. Only synthetic records belong in this demonstration.
