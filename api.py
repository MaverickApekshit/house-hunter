from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/listings")
async def get_listings():
    conn = sqlite3.connect('rentals.sqlite')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM listings WHERE commute_time_mins IS NOT NULL AND commute_time_mins <= 60 AND status != "Rejected" ORDER BY commute_time_mins ASC')
    listings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return listings

@app.post("/api/listings/{listing_id}/status")
async def update_listing_status(listing_id: int, status: str):
    conn = sqlite3.connect('rentals.sqlite')
    cursor = conn.cursor()
    cursor.execute('UPDATE listings SET status = ? WHERE id = ?', (status, listing_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
