# CIIS — Build Contract (Phases 2–14)

Read this first. Every module must follow it exactly, so the parts fit together.
Do NOT invent different table names, column names, function names, or session keys.

## Paths / imports
- Project root: `~/workspace/CIIS` (run from there; `venv/bin/python` is the interpreter)
- `config.py` already exists — import from it, do not duplicate its constants.
- All modules run from the project root, so `from database.database import get_db`,
  `from config import ...`, `from models.xxx import ...` must work.
- Models must be pure Python: NO streamlit, NO database imports inside `models/`.
- UI modules live in `modules/` and expose `render()` with no arguments.
- NEVER overwrite `app.py`, `config.py`, `requirements.txt` (integration owner does that).
- NEVER overwrite another agent's files. Your file list is in your brief.

## Database — exact tables (database/schema.sql + database/database.py)
SQLite, `PRAGMA foreign_keys = ON`, parameterised queries only (`?` placeholders).

```
users(id INTEGER PK AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL, full_name TEXT, role TEXT CHECK(role IN ('ADMIN','INVESTIGATOR','VIEWER')),
  status TEXT DEFAULT 'Active' CHECK(status IN ('Active','Inactive')),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP)
detectives(id INTEGER PK AUTOINCREMENT, detective_id TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL, badge_number TEXT UNIQUE NOT NULL, department TEXT,
  contact TEXT, designation TEXT, status TEXT DEFAULT 'Active', created_at TEXT DEFAULT CURRENT_TIMESTAMP)
cases(id INTEGER PK AUTOINCREMENT, case_id TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL, category TEXT NOT NULL, description TEXT,
  crime_date TEXT, registration_date TEXT, location TEXT,
  latitude REAL, longitude REAL, priority TEXT, status TEXT,
  detective_id TEXT REFERENCES detectives(detective_id),
  notes TEXT, progress INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP)
suspects(id INTEGER PK AUTOINCREMENT, suspect_id TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL, age INTEGER, gender TEXT, contact TEXT, address TEXT,
  case_id TEXT REFERENCES cases(case_id), investigation_status TEXT,
  description TEXT, registration_date TEXT DEFAULT CURRENT_TIMESTAMP)
witnesses(id INTEGER PK AUTOINCREMENT, witness_id TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL, age INTEGER, contact TEXT, address TEXT,
  case_id TEXT REFERENCES cases(case_id), statement_date TEXT,
  statement_summary TEXT, record_status TEXT DEFAULT 'Active')
evidence(id INTEGER PK AUTOINCREMENT, evidence_id TEXT UNIQUE NOT NULL,
  evidence_type TEXT, description TEXT, case_id TEXT REFERENCES cases(case_id),
  collection_date TEXT, collection_location TEXT, collected_by TEXT,
  storage_reference TEXT, status TEXT DEFAULT 'Collected', file_reference TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP)
case_suspects(id INTEGER PK AUTOINCREMENT, case_id TEXT REFERENCES cases(case_id),
  suspect_id TEXT REFERENCES suspects(suspect_id), relationship TEXT DEFAULT 'Associated with',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(case_id, suspect_id))
case_witnesses(id INTEGER PK AUTOINCREMENT, case_id TEXT REFERENCES cases(case_id),
  witness_id TEXT REFERENCES witnesses(witness_id), created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(case_id, witness_id))
case_evidence(id INTEGER PK AUTOINCREMENT, case_id TEXT REFERENCES cases(case_id),
  evidence_id TEXT REFERENCES evidence(evidence_id), created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(case_id, evidence_id))
case_assignments(id INTEGER PK AUTOINCREMENT, case_id TEXT REFERENCES cases(case_id),
  detective_id TEXT REFERENCES detectives(detective_id), assigned_date TEXT,
  status TEXT DEFAULT 'Active')
investigation_updates(id INTEGER PK AUTOINCREMENT, case_id TEXT REFERENCES cases(case_id),
  detective_id TEXT, update_text TEXT, progress INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP)
evidence_custody(id INTEGER PK AUTOINCREMENT, evidence_id TEXT REFERENCES evidence(evidence_id),
  action TEXT, handled_by TEXT, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)
audit_logs(id INTEGER PK AUTOINCREMENT, username TEXT, action TEXT, table_name TEXT,
  record_id TEXT, details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)
```
Indexes: on cases(category), cases(status), cases(crime_date), suspects(case_id),
witnesses(case_id), evidence(case_id), audit_logs(created_at).

ID formats: cases `CIIS-2026-0001` (year + 4-digit sequence), detectives `DET-001`,
suspects `SUS-001`, witnesses `WIT-001`, evidence `EVD-001`.

## database/database.py — DatabaseManager API (exact names)
- `class DatabaseManager(db_path=None)` — default `config.DATABASE_PATH`
- `get_connection()` -> sqlite3 connection, `row_factory=sqlite3.Row`, foreign_keys ON
- `initialize()` -> run schema.sql, seed if `users` table is empty
- `execute(query, params=(), commit=True)` -> cursor
- `fetch_one(query, params=())` -> dict | None
- `fetch_all(query, params=())` -> list[dict]
- `fetch_df(query, params=())` -> pandas DataFrame
- `next_id(prefix, table, id_column)` -> str (cases use prefix `CIIS-2026`, others `DET`/`SUS`/`WIT`/`EVD`)
- `log_audit(username, action, table_name="", record_id="", details="")`
- `backup(backup_path=None)` -> pathlib.Path (copies ciis.db into backups/ with timestamp)
- `restore(backup_path)` -> bool
- `seed_sample_data()` -> loads `data/sample_data.json` (fallback: built-in list if file missing)
- `def get_db()` -> module-level singleton DatabaseManager
- `close()`

## Auth — modules/authentication.py API (exact names)
- `hash_password(password) -> str` — `salt$hash`, hashlib.pbkdf2_hmac('sha256', 100_000 iterations, 16-byte salt)
- `verify_password(password, stored) -> bool`
- `authenticate(username, password) -> dict | None` (only Active users)
- `login_user(user: dict)`, `logout_user()`, `is_authenticated() -> bool`
- `current_user() -> dict`, `current_role() -> str`, `current_username() -> str`
- `require_role(*roles) -> bool`, `can_write() -> bool` (ADMIN or INVESTIGATOR),
  `can_view_witness_contact() -> bool` (ADMIN or INVESTIGATOR; VIEWER sees masked contact)
- `create_user(db, username, password, full_name, role)`, `list_users(db)`,
  `update_user_status(db, user_id, status)`, `change_password(db, username, new_password)`
- `render_login() -> bool`, `render_user_management()`
- Session keys: `st.session_state["authenticated"]`, `["user_id"]`, `["username"]`,
  `["role"]`, `["full_name"]`. Logout clears all five.
- Default users (seeded): admin / Admin@123 (ADMIN, Administrator),
  investigator / Inv@123 (INVESTIGATOR, Ali Khan), viewer / View@123 (VIEWER, Sara Ahmed).
  Passwords stored ONLY as hashes.

## OOP models — models/ (pure Python, all four pillars)
- `person.py`: `class Person(ABC)` — protected `_full_name, _age, _contact, _address`;
  properties `full_name, age, contact, address`; `@abstractmethod display_details() -> str`;
  `to_dict()`, `__str__`. Constructor uses `super()` in children.
- `detective.py`: `Detective(Person)` + `badge_number, department, designation, status, detective_id`;
  `display_details()` returns detective-style string; `to_dict()/from_dict()`.
- `suspect.py`: `Suspect(Person)` + `gender, case_id, investigation_status, description, suspect_id`;
  neutral labels only — never "guilty". `display_details()`, `to_dict()/from_dict()`.
- `witness.py`: `Witness(Person)` + `case_id, statement_date, statement_summary, record_status, witness_id`;
  `display_details()`, `to_dict()/from_dict()`.
- `evidence.py`: `class Evidence` (not a Person) — fields exactly as evidence table;
  `display_details()`, `to_dict()/from_dict()`, `add_custody_note(action, handled_by, notes) -> dict`.
- `crime_case.py`: `class CrimeCase` — fields exactly as cases table;
  `display_details()`, `to_dict()/from_dict()`, `is_active()`, `progress_label()`.
- `investigation.py`: `class Investigation` — `case_id, detective_id, title`;
  `add_update(db, text, progress)`, `get_updates(db) -> list[dict]`, `to_dict()`.

## UI modules — each exposes render()
- `modules/ui_helpers.py` (new, shared): `badge(status)->str` (HTML span),
  `stat_card(label, value, icon, colour)`, `mask_contact(contact, can_see)->str`,
  `show_readonly_notice()`, `confirm_delete(label)->bool` (use st.checkbox pattern, not a blocking dialog).
- Every `render()` uses `db = get_db()`, checks `can_write()` before showing add/edit/delete
  forms (VIEWER gets a read-only notice and no write buttons), and calls
  `db.log_audit(current_username(), ...)` after every write.
- Dashboard stats come from SQL counts only — never hard-coded numbers.
- Witness contact/address: mask with `mask_contact` unless `can_view_witness_contact()`.
- All sample data is fictional — every analytics/report page shows the notice from config.

## Analytics / network / heatmap — function names
- `analytics/crime_statistics.py`: `load_cases_df(db)`, `monthly_cases(df)`,
  `by_category(df)`, `by_status(df)`, `by_location(df)`, `evidence_by_type(db)`,
  `workload_by_detective(db)` — each returns a Plotly figure (or (fig, df) where useful).
- `analytics/relationship_graph.py`: `build_network(db, case_id=None, node_types=None) -> (nx.Graph, plotly Figure)`,
  `get_node_details(db, node_id) -> dict`.
- `analytics/crime_heatmap.py`: `build_map(db, category=None, start_date=None, end_date=None) -> folium.Map`,
  `location_summary(db) -> pandas.DataFrame`. Coordinates are fictional Peshawar-area
  points (34.0, 71.5 ± 0.1); never plot exact witness addresses.
- `modules/analytics.py`: `render()` — date/category filters, calls the functions above, CSV download buttons.

## Reports — reports/pdf_generator.py
- `class ReportGenerator(db=None)`: methods returning `bytes`:
  `generate_case_report(case_id)`, `generate_suspect_report(suspect_id)`,
  `generate_witness_report(witness_id)`, `generate_evidence_report(evidence_id=None)`,
  `generate_statistics_report()`, `generate_workload_report()`, `generate_progress_report(case_id)`.
- `async def generate_reports_async(requests) -> list[bytes]` using `asyncio.to_thread`
  (requests = list of (method_name, record_id)). This is the Phase 13 asyncio use.
- `reports/report_templates.py`: `CONFIDENTIALITY = "CONFIDENTIAL — CIIS INTERNAL USE ONLY"`,
  ReportLab styles, header/footer helper used by the generator.
- Every PDF: CIIS header, Report ID, generation date, confidentiality line,
  organised tables, page numbers in footer.

## Sample data — data/sample_data.json
Fictional Peshawar-area data: 5 detectives, 12 cases (Jan–Nov 2026, categories from
config.CASE_CATEGORIES, locations: University Town 34.015,71.52; Hayatabad 33.99,71.45;
Saddar 34.01,71.57; Gulbahar 34.02,71.55; Cantonment 34.00,71.58; Tehkal 34.005,71.50;
Charsadda Road 34.03,71.60; Ring Road 33.98,71.52; Faqirabad 34.02,71.53; Warsak Road 34.03,71.48),
10 suspects, 8 witnesses, 12 evidence items, all cross-linked by case_id.
Seed only when tables are empty; seeding must also fill case_suspects / case_witnesses /
case_evidence link tables and a few investigation_updates + evidence_custody rows.

## Testing (each agent tests its own files)
Run with the venv: `venv/bin/python -m pytest tests/ -v` for your tests,
`venv/bin/python -c "from <your module> import ..."` for imports, and
`venv/bin/python -c "from database.database import get_db; db=get_db(); db.initialize(); print(db.fetch_all('SELECT COUNT(*) c FROM cases'))"`
after seeding. Report exact test output; fix errors, do not hide them.
