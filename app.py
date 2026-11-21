"""
CIIS — Crime Investigation Intelligence System
app.py — Phases 2–14: full application entry point.

Simple English: Streamlit runs this file. It
1. initialises the SQLite database (creates + seeds it on first run),
2. shows the login screen until the user signs in,
3. then shows the dark sidebar with all 13 navigation items and
   calls the matching module's render() function for the chosen page.

All data comes from SQLite. Nothing on the dashboard is hard-coded.
"""

from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from config import APP_NAME, APP_SHORT, APP_VERSION, SAMPLE_DATA_NOTICE
from database.database import get_db
from modules.authentication import (
    current_role,
    current_username,
    is_authenticated,
    logout_user,
    render_login,
    render_user_management,
)

st.set_page_config(
    page_title=f"{APP_SHORT} — {APP_NAME}",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css() -> None:
    """Load the dark theme from assets/styles.css."""
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


load_css()

# Initialise the database on first run (creates tables + fictional seed data).
db = get_db()
db.initialize()

NAV_ITEMS = [
    ("🏠", "Dashboard"),
    ("📁", "Case Management"),
    ("👤", "Suspect Management"),
    ("👁️", "Witness Management"),
    ("🕵️", "Detective Management"),
    ("🔍", "Evidence Management"),
    ("📊", "Crime Analytics"),
    ("🕸️", "Relationship Network"),
    ("🗺️", "Crime Heatmap"),
    ("📄", "Investigation Reports"),
    ("👥", "User Management"),
    ("⚙️", "Settings"),
    ("🚪", "Logout"),
]

# ---------------------------------------------------------------------------
# Login gate — nothing else renders until the user is signed in.
# ---------------------------------------------------------------------------
if not is_authenticated():
    render_login()
    st.stop()


# ---------------------------------------------------------------------------
# Sidebar: search, navigation, notifications, profile
# ---------------------------------------------------------------------------
def _notification_counts():
    """Live notification counts from the database."""
    try:
        urgent = db.fetch_one(
            "SELECT COUNT(*) AS c FROM cases WHERE status IN ('Open','Under Investigation') "
            "AND priority IN ('Critical','High')"
        )["c"]
        unassigned = db.fetch_one(
            "SELECT COUNT(*) AS c FROM cases WHERE status IN ('Open','Under Investigation') "
            "AND (detective_id IS NULL OR detective_id = '')"
        )["c"]
        return urgent, unassigned
    except Exception:  # noqa: BLE001 - notifications must never break the sidebar
        return 0, 0


with st.sidebar:
    st.markdown(f"## 🛡️ {APP_SHORT}")
    st.caption(APP_NAME)
    st.caption(f"Version {APP_VERSION}")
    st.divider()

    search_q = st.text_input("🔎 Global search", placeholder="Case ID, name, title…")
    st.divider()

    choice = st.radio(
        "Navigation",
        options=[name for _, name in NAV_ITEMS],
        format_func=lambda name: next(f"{icon} {n}" for icon, n in NAV_ITEMS if n == name),
        label_visibility="collapsed",
    )

    urgent, unassigned = _notification_counts()
    if urgent or unassigned:
        st.divider()
        st.markdown("**🔔 Notifications**")
        if urgent:
            st.warning(f"⚠️ {urgent} urgent open case(s) (Critical/High priority)")
        if unassigned:
            st.info(f"📌 {unassigned} open case(s) with no detective assigned")

    st.divider()
    st.markdown("**👤 Signed in**")
    st.write(f"{st.session_state.get('full_name') or current_username()}")
    st.caption(f"@{current_username()} · {current_role()}")
    if st.button("🚪 Log out", use_container_width=True):
        logout_user()
        st.rerun()

# Logout via the nav item as well.
if choice == "Logout":
    logout_user()
    st.rerun()


# ---------------------------------------------------------------------------
# Global search results (shown instead of the chosen page while searching)
# ---------------------------------------------------------------------------
def render_search(query: str) -> bool:
    """Search cases, suspects, witnesses, evidence and detectives. Returns True if shown."""
    q = (query or "").strip()
    if not q:
        return False
    st.title(f"🔎 Search results for “{q}”")
    like = f"%{q}%"
    found = False
    for title, sql in [
        ("Cases", "SELECT case_id AS ID, title AS Title, category AS Category, status AS Status, location AS Location FROM cases WHERE case_id LIKE ? OR title LIKE ? OR location LIKE ?"),
        ("Suspects", "SELECT suspect_id AS ID, full_name AS Name, investigation_status AS Status, case_id AS Case FROM suspects WHERE suspect_id LIKE ? OR full_name LIKE ? OR case_id LIKE ?"),
        ("Witnesses", "SELECT witness_id AS ID, full_name AS Name, record_status AS Status, case_id AS Case FROM witnesses WHERE witness_id LIKE ? OR full_name LIKE ? OR case_id LIKE ?"),
        ("Evidence", "SELECT evidence_id AS ID, evidence_type AS Type, description AS Description, status AS Status, case_id AS Case FROM evidence WHERE evidence_id LIKE ? OR description LIKE ? OR case_id LIKE ?"),
        ("Detectives", "SELECT detective_id AS ID, full_name AS Name, badge_number AS Badge, department AS Department, status AS Status FROM detectives WHERE detective_id LIKE ? OR full_name LIKE ? OR badge_number LIKE ?"),
    ]:
        rows = db.fetch_all(sql, (like, like, like))
        if rows:
            found = True
            st.subheader(title)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if not found:
        st.info("No matches found. Try a case ID (e.g. CIIS-2026-0001), a name, or a place.")
    if st.button("← Clear search"):
        st.rerun()
    return True


if render_search(search_q):
    st.stop()


# ---------------------------------------------------------------------------
# Pages rendered inline here (network, heatmap, reports)
# ---------------------------------------------------------------------------
def render_network():
    st.title("🕸️ Relationship Network")
    st.caption("Only documented relationships from the database are shown. "
               "Nothing is inferred from shared locations or names.")
    from analytics.relationship_graph import build_network, get_node_details

    cases = db.fetch_all("SELECT case_id, title FROM cases ORDER BY case_id")
    case_options = ["All cases"] + [f"{c['case_id']} — {c['title']}" for c in cases]
    picked = st.selectbox("Case filter", case_options)
    case_id = None if picked == "All cases" else picked.split(" — ")[0]
    node_types = st.multiselect(
        "Node types",
        ["Case", "Suspect", "Witness", "Detective", "Evidence"],
        default=["Case", "Suspect", "Witness", "Detective", "Evidence"],
    )
    graph, fig = build_network(db, case_id=case_id, node_types=node_types or None)
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"**{graph.number_of_nodes()} nodes · {graph.number_of_edges()} documented relationships**")
    st.caption("🔒 " + SAMPLE_DATA_NOTICE)
    st.subheader("Node details")
    node_q = st.text_input("Enter a node ID (e.g. CIIS-2026-0001, SUS-001, DET-001)")
    if node_q.strip():
        details = get_node_details(db, node_q.strip())
        if details:
            st.json(details)
        else:
            st.info("No record found with that ID.")


def render_heatmap():
    st.title("🗺️ Crime Heatmap")
    st.caption("Fictional Peshawar-area coordinates. Exact witness addresses are never plotted.")
    from analytics.crime_heatmap import build_map, location_summary
    from config import CASE_CATEGORIES

    col1, col2, col3 = st.columns(3)
    with col1:
        cat = st.selectbox("Category", ["All"] + CASE_CATEGORIES)
    with col2:
        start = st.date_input("From date", value=None)
    with col3:
        end = st.date_input("To date", value=None)
    fmap = build_map(
        db,
        category=None if cat == "All" else cat,
        start_date=start.isoformat() if start else None,
        end_date=end.isoformat() if end else None,
    )
    st_folium(fmap, width=1100, height=520)
    st.subheader("Cases by location")
    summary = location_summary(db)
    if not summary.empty:
        st.dataframe(summary, use_container_width=True, hide_index=True)
    st.caption("🔒 " + SAMPLE_DATA_NOTICE)


def render_reports():
    st.title("📄 Investigation Reports")
    st.caption("Professional PDF reports generated from SQLite with ReportLab.")
    from reports.pdf_generator import ReportGenerator

    gen = ReportGenerator(db)
    report_type = st.selectbox(
        "Report type",
        ["Case report", "Suspect profile", "Witness report", "Evidence summary",
         "Investigation progress", "Crime statistics", "Detective workload"],
    )
    pdf_bytes = None
    filename = "ciis_report.pdf"
    if report_type in ("Crime statistics", "Detective workload", "Evidence summary"):
        if st.button(f"Generate {report_type}"):
            if report_type == "Crime statistics":
                pdf_bytes = gen.generate_statistics_report()
            elif report_type == "Detective workload":
                pdf_bytes = gen.generate_workload_report()
            else:
                pdf_bytes = gen.generate_evidence_report()
            filename = f"ciis_{report_type.lower().replace(' ', '_')}.pdf"
    else:
        if report_type == "Case report":
            options = [c["case_id"] for c in db.fetch_all("SELECT case_id FROM cases ORDER BY case_id")]
            label = "Select case"
        elif report_type == "Suspect profile":
            options = [s["suspect_id"] for s in db.fetch_all("SELECT suspect_id FROM suspects ORDER BY suspect_id")]
            label = "Select suspect"
        elif report_type == "Witness report":
            options = [w["witness_id"] for w in db.fetch_all("SELECT witness_id FROM witnesses ORDER BY witness_id")]
            label = "Select witness"
        else:
            options = [c["case_id"] for c in db.fetch_all("SELECT case_id FROM cases ORDER BY case_id")]
            label = "Select case"
        record_id = st.selectbox(label, options) if options else None
        if record_id and st.button(f"Generate {report_type}"):
            if report_type == "Case report":
                pdf_bytes = gen.generate_case_report(record_id)
            elif report_type == "Suspect profile":
                pdf_bytes = gen.generate_suspect_report(record_id)
            elif report_type == "Witness report":
                pdf_bytes = gen.generate_witness_report(record_id)
            else:
                pdf_bytes = gen.generate_progress_report(record_id)
            filename = f"ciis_{record_id}.pdf"
    if pdf_bytes:
        st.success(f"Report ready — {len(pdf_bytes):,} bytes.")
        st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name=filename, mime="application/pdf")
        db.log_audit(current_username(), "GENERATE", "reports", filename, f"Generated {report_type}.")
    st.caption("🔒 " + SAMPLE_DATA_NOTICE)


# ---------------------------------------------------------------------------
# Router — every sidebar item opens its own functional page.
# ---------------------------------------------------------------------------
if choice == "Dashboard":
    from modules.dashboard import render as _render
    _render()
elif choice == "Case Management":
    from modules.case_management import render as _render
    _render()
elif choice == "Suspect Management":
    from modules.suspect_management import render as _render
    _render()
elif choice == "Witness Management":
    from modules.witness_management import render as _render
    _render()
elif choice == "Detective Management":
    from modules.detective_management import render as _render
    _render()
elif choice == "Evidence Management":
    from modules.evidence_management import render as _render
    _render()
elif choice == "Crime Analytics":
    from modules.analytics import render as _render
    _render()
elif choice == "Relationship Network":
    render_network()
elif choice == "Crime Heatmap":
    render_heatmap()
elif choice == "Investigation Reports":
    render_reports()
elif choice == "User Management":
    render_user_management()
elif choice == "Settings":
    from modules.settings import render as _render
    _render()

st.divider()
st.caption("CIIS • All sample data is fictional • Allegations and investigation statuses are recorded without determining guilt.")
