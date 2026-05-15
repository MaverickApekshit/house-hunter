from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import database

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_listings(request: Request):
    import sqlite3
    conn = sqlite3.connect('rentals.sqlite')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM listings WHERE commute_time_mins IS NOT NULL AND commute_time_mins <= 60 ORDER BY commute_time_mins ASC')
    listings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "listings": listings})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
