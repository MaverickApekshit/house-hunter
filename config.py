"""
Configuration Loader Module for House Hunter.

This module acts as the single source of truth for all environment-specific configurations.
It loads variables from a local `.env` file and exposes them as strongly-typed constants.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==========================================
# Application Settings
# ==========================================
# File path to the SQLite local database
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "rentals.sqlite")

# Deployment environment (e.g., 'local' or 'production')
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")

# Master password protecting state mutations
MASTER_PASSWORD: str = os.getenv("MASTER_PASSWORD", "admin")

# Comma-separated list of allowed CORS origins
_allowed_origins_raw: str = os.getenv("ALLOWED_ORIGINS", "")
if ENVIRONMENT == "production":
    ALLOWED_ORIGINS: list[str] = [
        origin.strip() for origin in _allowed_origins_raw.split(",") if origin.strip()
    ]
else:
    # Local developer fallback: default to wildcard if not explicitly configured
    if _allowed_origins_raw:
        ALLOWED_ORIGINS = [
            origin.strip() for origin in _allowed_origins_raw.split(",") if origin.strip()
        ]
    else:
        ALLOWED_ORIGINS = ["*"]

# ==========================================
# Scraping & Filtering Constraints
# ==========================================
# Maximum rent budget threshold in local currency (e.g., INR Rs. 45,000)
MAX_RENT: int = int(os.getenv("MAX_RENT", "45000"))

# Structural requirement layout string for targets (e.g., '3 BHK')
TARGET_BHK: str = os.getenv("TARGET_BHK", "3 BHK")

# ==========================================
# Commute & Logistics Configurations
# ==========================================
# Name of the destination hub/office park
TARGET_DESTINATION_NAME: str = os.getenv(
    "TARGET_DESTINATION_NAME", "Bagmane Constellation, Bangalore"
)

# Latitude coordinate of the target destination
TARGET_LAT: Optional[float] = None
_target_lat_str = os.getenv("TARGET_LAT")
if _target_lat_str:
    try:
        TARGET_LAT = float(_target_lat_str)
    except ValueError:
        pass

# Longitude coordinate of the target destination
TARGET_LNG: Optional[float] = None
_target_lng_str = os.getenv("TARGET_LNG")
if _target_lng_str:
    try:
        TARGET_LNG = float(_target_lng_str)
    except ValueError:
        pass

# Expected arrival time at target destination (in 24-hour HH:MM format)
TARGET_ARRIVAL_TIME: str = os.getenv("TARGET_ARRIVAL_TIME", "13:00")

# Maximum acceptable one-way transit commute duration in minutes
MAX_COMMUTE_DURATION_MINS: int = int(os.getenv("MAX_COMMUTE_DURATION_MINS", "60"))

# Days after which a still-'New' listing not re-seen in a scrape is treated as
# delisted and hidden by the API. Derived staleness via last_seen — never a
# status write (status is cloud-managed and stripped on sync). Triaged rows
# (Interested/Contacted/etc.) are always returned regardless of staleness.
DELIST_AFTER_DAYS: int = int(os.getenv("DELIST_AFTER_DAYS", "14"))

# ==========================================
# External Integrations
# ==========================================
# Google Maps Platform API key (for Distance Matrix calculations)
GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")

# Supabase REST API URL endpoint for sync operations
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")

# Supabase public anonymous API key
SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
