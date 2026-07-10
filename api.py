from fastapi import FastAPI, HTTPException, status as status_codes, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import config

# Set up logging for API telemetry
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="House Hunter API",
    description="Environment-aware API feeding standardized property listings to the frontend application.",
    version="1.1.0"
)

# Enable CORS for frontend cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=not ("*" in config.ALLOWED_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Output Normalization (Unified Pydantic Schema)
# ==========================================
class PropertyResponse(BaseModel):
    """
    Standardized payload contract representing a property listing.
    Ensures complete interoperability between Local SQLite and Cloud Supabase schemas.
    """
    id: int
    title: str
    price: int
    bhk: str
    location: str
    url: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    commute_duration_mins: Optional[int] = None
    status: str
    created_at: str
    source: str
    deposit: int
    area_sqft: Optional[int] = None


class VerifyPasswordRequest(BaseModel):
    """
    Payload for validating master password mutations.
    """
    password: str


# ==========================================
# External Clients Initialization
# ==========================================
supabase_client: Optional[Client] = None

if config.ENVIRONMENT == "production":
    logger.info("Application starting in PRODUCTION mode. Initializing Supabase client...")
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        logger.error("Supabase integration credentials missing in .env configurations.")
        raise RuntimeError("Missing Supabase credentials in production mode.")
    try:
        supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize Supabase client: {e}")
        raise RuntimeError(f"Supabase init failure: {e}")
else:
    logger.info("Application starting in LOCAL mode. SQLite will be used as the primary data store.")

# ==========================================
# API Endpoints
# ==========================================
@app.post("/api/auth/verify")
async def verify_password(payload: VerifyPasswordRequest):
    """
    Verifies the provided master password against the system environment.
    """
    logger.info("Received POST /api/auth/verify request")
    if payload.password == config.MASTER_PASSWORD:
        return {"valid": True}
    else:
        raise HTTPException(
            status_code=status_codes.HTTP_401_UNAUTHORIZED,
            detail="Incorrect master password."
        )


@app.get("/api/listings", response_model=List[PropertyResponse])
async def get_listings():
    """
    Retrieves filtered list of property options within acceptable commute times.
    Dynamically routes query based on current environment settings.
    """
    logger.info(f"Received GET /api/listings request (Environment: {config.ENVIRONMENT})")
    
    # ------------------------------------------
    # Production Mode: Cloud Supabase Data Feed
    # ------------------------------------------
    if config.ENVIRONMENT == "production":
        if not supabase_client:
            logger.error("Supabase client is not initialized in production.")
            raise HTTPException(
                status_code=status_codes.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database client is uninitialized."
            )
        try:
            logger.info("Querying Supabase properties table...")
            # Derived-staleness delisting: hide rows that are still 'New' and
            # whose last_seen is older than DELIST_AFTER_DAYS. Keep a row if it
            # is NOT 'New' (triaged rows are always shown), OR last_seen is fresh,
            # OR last_seen is unknown. No status is ever written.
            stale_cutoff = (datetime.now(timezone.utc) - timedelta(days=config.DELIST_AFTER_DAYS)).isoformat()
            # Query properties from Supabase using PostgREST filter constraints
            response = supabase_client.table("properties") \
                .select("*") \
                .lte("commute_duration_mins", config.MAX_COMMUTE_DURATION_MINS) \
                .neq("status", "Rejected") \
                .or_(f"status.neq.New,last_seen.gte.{stale_cutoff},last_seen.is.null") \
                .order("commute_duration_mins", desc=False) \
                .execute()

            properties = []
            for record in response.data:
                # Normalize Supabase schema keys to match unified PropertyResponse payload
                properties.append(PropertyResponse(
                    id=record["id"],
                    title=record["title"],
                    price=record["price"],
                    bhk=record["bhk"],
                    location=record["location"],
                    url=record["url"],
                    latitude=record.get("latitude"),
                    longitude=record.get("longitude"),
                    commute_duration_mins=record.get("commute_duration_mins"),
                    status=record["status"],
                    created_at=record["created_at"],
                    source=record.get("source", "Cloud"),
                    deposit=record.get("deposit", 0), # Fallback to prevent UI crash on .toLocaleString()
                    area_sqft=record.get("area_sqft")  # Optional fallback
                ))
            
            logger.info(f"Successfully retrieved and normalized {len(properties)} listings from Supabase.")
            return properties

        except Exception as e:
            logger.error(f"Error querying properties from Supabase: {e}", exc_info=True)
            raise HTTPException(
                status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch cloud properties: {e}"
            )

    # ------------------------------------------
    # Local Mode: SQLite Local File Data Feed
    # ------------------------------------------
    else:
        try:
            logger.info(f"Querying local SQLite database at: {config.DATABASE_PATH}")
            conn = sqlite3.connect(config.DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Derived-staleness delisting: hide rows that are still 'New' and
            # whose last_seen is older than DELIST_AFTER_DAYS. Triaged rows and
            # rows with unknown last_seen are always kept. No status is written.
            stale_cutoff = (datetime.now(timezone.utc) - timedelta(days=config.DELIST_AFTER_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                'SELECT * FROM listings '
                'WHERE commute_time_mins IS NOT NULL AND commute_time_mins <= ? '
                'AND status != "Rejected" '
                "AND NOT (status = 'New' AND last_seen IS NOT NULL AND last_seen < ?) "
                'ORDER BY commute_time_mins ASC',
                (config.MAX_COMMUTE_DURATION_MINS, stale_cutoff)
            )
            rows = cursor.fetchall()
            conn.close()

            properties = []
            for row in rows:
                # Normalize SQLite schema keys to match unified PropertyResponse payload
                properties.append(PropertyResponse(
                    id=row["id"],
                    title=row["title"],
                    price=row["rent"], # Map local rent to standardized price
                    bhk=row["bhk"],
                    location=row["locality"], # Map local locality to standardized location
                    url=row["url"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    commute_duration_mins=row["commute_time_mins"], # Map local commute_time_mins to standardized commute_duration_mins
                    status=row["status"],
                    created_at=str(row["added_at"]), # Map added_at to standardized created_at
                    source=row["source"] if row["source"] else "Local",
                    deposit=row["deposit"] if row["deposit"] is not None else 0,
                    area_sqft=row["area_sqft"]
                ))
            
            logger.info(f"Successfully retrieved and normalized {len(properties)} listings from SQLite.")
            return properties

        except Exception as e:
            logger.error(f"Error querying SQLite database: {e}", exc_info=True)
            raise HTTPException(
                status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch local properties: {e}"
            )


@app.post("/api/listings/{listing_id}/status")
async def update_listing_status(
    listing_id: int,
    status: str,
    x_master_password: Optional[str] = Header(None, alias="X-Master-Password"),
    password: Optional[str] = None
):
    """
    Updates the selection status (e.g. 'Rejected', 'Interested') of a specific property listing.
    Routes execution to SQLite or Supabase based on environment.
    """
    logger.info(f"Received POST /api/listings/{listing_id}/status?status={status} request (Environment: {config.ENVIRONMENT})")
    
    # Authenticate via Header or Query parameter
    incoming_pw = x_master_password or password
    if incoming_pw != config.MASTER_PASSWORD:
        logger.warning(f"Unauthorized status mutation attempt on listing {listing_id} (Environment: {config.ENVIRONMENT})")
        raise HTTPException(
            status_code=status_codes.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Incorrect or missing master password."
        )
    
    # ------------------------------------------
    # Production Mode: Supabase Cloud Update
    # ------------------------------------------
    if config.ENVIRONMENT == "production":
        if not supabase_client:
            logger.error("Supabase client is not initialized in production.")
            raise HTTPException(
                status_code=status_codes.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database client is uninitialized."
            )
        try:
            logger.info(f"Updating property ID {listing_id} status to '{status}' in Supabase...")
            response = supabase_client.table("properties") \
                .update({"status": status}) \
                .eq("id", listing_id) \
                .execute()
            
            if not response.data:
                logger.warning(f"Property with ID {listing_id} not found in Supabase properties table.")
                raise HTTPException(
                    status_code=status_codes.HTTP_404_NOT_FOUND,
                    detail=f"Property with ID {listing_id} not found in Cloud database."
                )
                
            logger.info(f"Property ID {listing_id} updated successfully in Supabase.")
            return {"status": "success"}

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error updating property status in Supabase: {e}", exc_info=True)
            raise HTTPException(
                status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update cloud property status: {e}"
            )

    # ------------------------------------------
    # Local Mode: SQLite Local File Update
    # ------------------------------------------
    else:
        try:
            logger.info(f"Updating listing ID {listing_id} status to '{status}' in SQLite database...")
            conn = sqlite3.connect(config.DATABASE_PATH)
            cursor = conn.cursor()
            
            # First check if record exists
            cursor.execute('SELECT 1 FROM listings WHERE id = ?', (listing_id,))
            if not cursor.fetchone():
                conn.close()
                logger.warning(f"Listing with ID {listing_id} not found in SQLite database.")
                raise HTTPException(
                    status_code=status_codes.HTTP_404_NOT_FOUND,
                    detail=f"Listing with ID {listing_id} not found in Local database."
                )
                
            cursor.execute('UPDATE listings SET status = ? WHERE id = ?', (status, listing_id))
            conn.commit()
            conn.close()
            
            logger.info(f"Listing ID {listing_id} updated successfully in SQLite.")
            return {"status": "success"}

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error updating SQLite listing status: {e}", exc_info=True)
            raise HTTPException(
                status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update local property status: {e}"
            )


if __name__ == "__main__":
    import uvicorn
    # Bind to standard port 8000 and enable default uvicorn serving
    logger.info("Initializing API application via Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
