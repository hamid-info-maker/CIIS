"""
CIIS — config.py
Phase 1: Project configuration.

Simple English: this file holds all the settings in one place,
so no other file needs to hard-code paths, colours, or lists.
Change a value here and the whole app uses the new value.
"""

from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "ciis.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = BASE_DIR / "backups"
LOGS_DIR = BASE_DIR / "logs"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"

# --- App ---
APP_NAME = "Crime Investigation Intelligence System"
APP_SHORT = "CIIS"
APP_VERSION = "2.0.0"
APP_ICON = "🛡️"

# --- Dark Intelligence Dashboard theme (Section 4 of the brief) ---
THEME = {
    "background": "#0B1120",
    "sidebar": "#111827",
    "card": "#172337",
    "primary": "#2563EB",
    "accent": "#38BDF8",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "text": "#F8FAFC",
    "secondary_text": "#94A3B8",
}

# --- Roles (Section 6) ---
ROLES = ["ADMIN", "INVESTIGATOR", "VIEWER"]

# --- Case lists (used from Phase 6 onwards) ---
CASE_CATEGORIES = [
    "Theft",
    "Burglary",
    "Assault",
    "Fraud",
    "Cybercrime",
    "Drug Offence",
    "Homicide",
    "Missing Person",
    "Vandalism",
    "Other",
]
CASE_PRIORITIES = ["Low", "Medium", "High", "Critical"]
CASE_STATUSES = ["Open", "Under Investigation", "Pending", "Closed", "Archived"]
EVIDENCE_TYPES = ["Document", "Photograph", "Video", "Audio", "Physical Item", "Digital Device", "Forensic Sample", "Other"]
INVESTIGATION_STATUSES = ["Person of Interest", "Alleged Suspect", "Under Investigation", "Cleared", "Charged"]

# --- Security / uploads (Sections 21-22) ---
ALLOWED_UPLOAD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".mp4", ".mp3", ".txt"}
MAX_UPLOAD_MB = 10
# Default admin login — CHANGE THIS after first login (Phase 5).
# Password is stored only as a hash in the database, never here in plain text.
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Admin@123"

# --- Sample-data note ---
# All sample data in this project is FICTIONAL, for development only.
# It must never be presented as official crime statistics.
SAMPLE_DATA_NOTICE = "Fictional sample data — for development and demonstration only."
