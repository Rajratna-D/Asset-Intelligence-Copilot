import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Domain Reference Time: Test Dataset "Today" is 15 Jan 2027
REFERENCE_DATE = os.getenv("REFERENCE_DATE", "2027-01-15")
SAMPLE_DATA_DIR = ROOT_DIR / "sample-data"

# Database Configuration
SQLITE_DB_PATH = ROOT_DIR / os.getenv("SQLITE_DB_PATH", "backend/db/assets.db")
SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
