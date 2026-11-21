# 🛡️ Crime Investigation Intelligence System (CIIS)

A centralized intelligence management platform for authorized investigators:
register and manage cases, suspects, witnesses, detectives and evidence,
monitor progress, analyse crime statistics, visualise relationships and
geography, and generate professional PDF investigation reports.

> **Important:** The platform records allegations and investigation statuses
> **without automatically determining guilt or criminal responsibility.**
> All sample data in this project is **fictional**, for development only.
> It must never be presented as official crime statistics.

## What is built (Phases 1–14, complete)

- **Dark Intelligence Dashboard** — live counts, charts and notifications, all from SQLite
- **Authentication** — PBKDF2-hashed passwords, sessions, roles ADMIN / INVESTIGATOR / VIEWER,
  ADMIN-only user management, audit-logged sign-ins
- **Case Management** — full CRUD, auto IDs (`CIIS-2026-0001`), search/filter, detective
  assignment, investigation updates + progress, case history, archive (no silent hard delete)
- **Suspect / Witness / Detective Management** — full CRUD, case links, workload, masked
  witness contact for VIEWER
- **Evidence Management** — CRUD, restricted file uploads (type + 10 MB limit, unique
  filenames, originals never overwritten), chain-of-custody log
- **Crime Analytics** — Plotly charts from real DB records, date/category filters, CSV export
- **Relationship Network** — NetworkX + Plotly, documented relationships only
- **Crime Heatmap** — Folium + HeatMap, fictional Peshawar coordinates, no witness addresses
- **PDF Reports** — ReportLab: case, suspect, witness, evidence, progress, statistics,
  workload reports, with header, Report ID, confidentiality line and page numbers
- **Async (Phase 13)** — `generate_reports_async()` builds independent PDFs concurrently
  with `asyncio.to_thread`; Settings → Batch reports runs it
- **OOP (Phase 3)** — `Person` ABC → `Detective` / `Suspect` / `Witness` (inheritance,
  `super()`, polymorphism via `display_details()`), plus `CrimeCase`, `Evidence`,
  `Investigation`, `DatabaseManager`, `ReportGenerator`; encapsulation via
  protected attributes + properties
- **Database (Phase 4)** — SQLite, 13 tables, PKs/FKs/CHECKs/UNIQUEs, indexes,
  parameterised queries, transactions, backup/restore, JSON export
- **Testing (Phase 14)** — `pytest` suite covering models, database, authentication,
  reports, network and heatmap

## Technology

Python 3.12 • Streamlit 1.67 • SQLite • Pandas • Plotly • NetworkX • Folium /
Streamlit-Folium • ReportLab • Pillow • pytest

## Installation & execution — Windows

```bat
cd CIIS
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501

### Linux / macOS

```bash
cd CIIS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The database is created automatically on first run (`database/ciis.db`) and
seeded with fictional sample data (3 users, 5 detectives, 12 cases, 10 suspects,
8 witnesses, 12 evidence items). Delete `database/ciis.db` and re-run to re-seed,
or use Settings → Reset sample data (ADMIN).

## Demo logins (fictional — change after first sign-in)

| Username | Password | Role |
|---|---|---|
| admin | Admin@123 | ADMIN — full access |
| investigator | Inv@123 | INVESTIGATOR — can write, assigned records |
| viewer | View@123 | VIEWER — read-only, witness contact masked |

Change your password in Settings → Change my password.

## Project structure

```
CIIS/
├── app.py                  # Entry point: login gate, sidebar, router, search
├── requirements.txt
├── README.md
├── config.py               # Paths, theme, roles, lists, upload limits
├── BUILD_CONTRACT.md       # Shared API/schema agreement between modules
├── database/
│   ├── database.py         # DatabaseManager (SQLite, backup/restore, seeding)
│   ├── schema.sql          # 13-table schema
│   └── ciis.db             # Created on first run (git-ignored)
├── models/                 # person, detective, suspect, witness, evidence,
│                           # crime_case, investigation (OOP, pure Python)
├── modules/                # authentication, dashboard, case/suspect/witness/
│                           # detective/evidence management, analytics,
│                           # settings, ui_helpers
├── analytics/              # crime_statistics, relationship_graph, crime_heatmap
├── reports/                # pdf_generator, report_templates
├── assets/                 # logo.png, styles.css (dark theme)
├── data/                   # sample_data.json (fictional), uploads/
├── backups/                # database backups
└── tests/                  # test_setup, test_models, test_database,
                            # test_authentication, test_reports
```

## Backup & restore

- In the app: **Settings → Create backup now** (saves a timestamped copy in `backups/`),
  then **Restore from backup** (ADMIN).
- Manually: copy `database/ciis.db` to a safe place; to restore, replace that file
  while the app is stopped.

## Testing

```bash
venv\Scripts\activate
python -m pytest tests/ -v
```

Expected: all tests pass (57+ tests covering models, database, auth, reports).

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit: command not found` | Activate the venv first, then `pip install -r requirements.txt` |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| `pip` is old | `python -m pip install --upgrade pip` |
| Database locked error | Stop other copies of the app / tests, then retry — SQLite allows one writer |
| Map tiles look blank | Folium's CartoDB tiles sometimes need an API key; switch `tiles=` to `"OpenStreetMap"` in `analytics/crime_heatmap.py` |
| Forgot the admin password | Delete `database/ciis.db` and re-run — it re-seeds with admin / Admin@123 (all other records are lost, so back up first) |
| A package fails to build on Windows | Use Python 3.11 or 3.12 from python.org (not the Store version) |

## Security notes

- Parameterized SQL queries only; no string-built SQL.
- Passwords stored only as PBKDF2 hashes (`salt$hash`), never plain text.
- VIEWER cannot write and cannot see full witness contact details.
- Evidence uploads are type/size-checked and saved under unique names.
- Every write is audit-logged (`audit_logs` table, visible on the Dashboard).
- Never use the fictional sample data as real crime statistics.
