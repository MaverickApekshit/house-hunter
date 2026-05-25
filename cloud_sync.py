import sqlite3
import logging
import time
from supabase import create_client, Client
import config

# Configure robust logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def sync_to_cloud():
    logger.info("Initializing Supabase Client...")
    
    if not config.SUPABASE_URL or not config.SUPABASE_KEY or config.SUPABASE_URL == 'your_supabase_url_here':
        logger.error("Supabase credentials missing or invalid in configuration. Cannot sync.")
        return

    try:
        supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return

    logger.info(f"Connecting to local SQLite database at: {config.DATABASE_PATH}")
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Fetch all property records from the local listings table
        cursor.execute("SELECT * FROM listings")
        rows = cursor.fetchall()
        logger.info(f"Successfully retrieved {len(rows)} local records for sync.")
    except Exception as e:
        logger.error(f"Failed to connect or query local database: {e}")
        return finally_close(conn)

    # Process and map rows to the Supabase schema
    batch_data = []
    success_tally = 0
    batch_size = 100

    for idx, row in enumerate(rows):
        mapped_record = {
            "title": row["title"],
            "price": row["rent"],
            "bhk": row["bhk"],
            "location": row["locality"],
            "url": row["url"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "commute_duration_mins": row["commute_time_mins"],
            "status": row["status"],
            "created_at": row["added_at"]
        }
        batch_data.append(mapped_record)

        # Upsert when we reach batch_size or at the end of the records
        if len(batch_data) >= batch_size or idx == len(rows) - 1:
            try:
                logger.info(f"Upserting batch of {len(batch_data)} records...")
                # Execute the upsert via the PostgREST library pattern using 'url' constraint
                response = supabase.table("properties").upsert(batch_data, on_conflict="url").execute()
                
                # Check response logic based on PostgREST return structure
                success_tally += len(response.data) if hasattr(response, 'data') and response.data else len(batch_data)
                
                logger.info(f"Batch upsert successful. Total synced so far: {success_tally}")
            except Exception as e:
                logger.error(f"Error during batch upsert: {e}")
            
            # Reset batch array
            batch_data = []

    logger.info(f"Sync complete. Successfully processed and upserted {success_tally} records.")
    
    conn.close()

def finally_close(conn):
    if conn:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting Cloud Sync Process...")
    start_time = time.time()
    sync_to_cloud()
    elapsed = time.time() - start_time
    logger.info(f"Process completed in {elapsed:.2f} seconds.")
