# ATM-EVM

ATM-EVM is a small Flask and SQLite educational demonstration of an electronic voting workflow. It provides a voter screen, an administrator panel, a command-line administration tool, and a results view.

> **Demo only.** This project is not suitable for public elections or production identity verification. It has not undergone security, accessibility, election-integrity, privacy, or legal review. Use synthetic data only. It deliberately does not collect Aadhaar numbers or other government identity numbers.

## Features

- Start and end named demo elections.
- Register synthetic voters and candidates in the browser or via the CLI.
- Verify a demo voter using voter ID and date of birth.
- Record one vote per voter for a running election with an atomic SQLite transaction.
- View candidate totals in the administrator panel and CLI.
- Initialize the schema automatically on app startup or CLI use.
- Keep the SQLite database at a stable project-relative location by default.

## Architecture

```text
Browser ── Flask routes (app.py) ── database.py ── SQLite
                                      ▲
                    admin.py CLI ─────┘
```

The Flask application factory is `create_app()` in `app.py`. `database.py` owns connection settings, schema creation, and transaction handling. HTML lives in `templates/`; CSS is in `static/`.

## Requirements

- Python 3.10 or later
- pip
- A modern browser

## Setup and run

From the project directory:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
```

Set secrets before running. PowerShell example:

```powershell
$env:ATM_EVM_SECRET_KEY = "use-a-long-random-secret"
$env:ATM_EVM_ADMIN_PASSWORD = "use-a-strong-password"
python app.py
```

macOS/Linux example:

```bash
export ATM_EVM_SECRET_KEY="use-a-long-random-secret"
export ATM_EVM_ADMIN_PASSWORD="use-a-strong-password"
python app.py
```

Open <http://127.0.0.1:5000/>. The database and tables are created automatically at `instance/atm_evm.db`. To choose another database file, set `ATM_EVM_DATABASE` to its path.

For local development only, `flask --app app run --debug` enables Flask's debugger. Never expose debug mode to a network.

## Administrator usage

Visit `/admin/login` and enter `ATM_EVM_ADMIN_PASSWORD`. The panel lets you create voters and candidates, start or end an election, and review results. The CLI offers the same core operations:

```bash
python admin.py --help
python admin.py add-voter DEMO-001 "Alex Example" 1990-01-02
python admin.py add-candidate C-1 "Jordan Example" "Demo Group A"
python admin.py start "Classroom Demo"
python admin.py status
python admin.py results
python admin.py stop
```

Voter IDs and dates of birth shown above are examples. Replace them with invented demo values only. The CLI does not store or request Aadhaar numbers.

## Database schema

| Table | Purpose | Important fields |
|---|---|---|
| `voters` | Synthetic demo voter registry | `voter_id` primary key, `name`, `date_of_birth`, `has_voted` |
| `candidates` | Candidate list | `candidate_id` primary key, `name`, `party` |
| `election` | Election lifecycle | `election_id`, `name`, `status`, timestamps |
| `votes` | Ballot records | `vote_id`, `election_id`, `candidate_id`, `cast_at` |

Votes are associated with an election and candidate; the voter identity is not stored alongside the ballot. The `has_voted` flag prevents a second ballot in the demo workflow. SQLite foreign keys are enabled on each connection.

## Troubleshooting

- **Admin sign-in says a password is not configured:** set `ATM_EVM_ADMIN_PASSWORD`, then restart the app.
- **Database appears in an unexpected location:** the default path is relative to `database.py`, not the current shell directory. Check `ATM_EVM_DATABASE` for an override.
- **Address already in use:** stop the other local Flask process or choose another port with `flask --app app run --port 5001`.
- **Duplicate ID error:** voter and candidate IDs must be unique in the current database.
- **Voting is closed:** an administrator must add a candidate and start an election.

## Security, privacy, and demo-data caveats

- Never commit `.env`, databases, backups, real personal information, or real voter records. These are excluded by `.gitignore`.
- Do not use real Aadhaar numbers or identity documents. This version has no Aadhaar field or Aadhaar verification.
- The default Flask secret is only a local development fallback. Set a random `ATM_EVM_SECRET_KEY` and a strong admin password before use.
- The app uses a single shared administrator password and has no account management, rate limiting, CSRF protection, audit trail, or hardened deployment configuration.
- The demo's date-of-birth check is not adequate identity proof. Results and ballot handling are illustrative, not election-grade.
- Deploy only behind a properly configured production WSGI server and HTTPS for a controlled demonstration. Never expose this demo as an election service.

## License

No license is included yet. Ask the project owner before reusing or redistributing the code.

