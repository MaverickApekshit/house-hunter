# Project Context: House Hunter (Local Scraper Boilerplate)
**Last Updated:** May 20, 2026

## 1. Ultimate Commercial & Product Vision
- **Core Product:** "House Hunter" is a high-performance Rental Listing Aggregator & Recommender built with an elite, clean-code architecture.
- **Commercialization Strategy:** The codebase will be commercialized and sold on Gumroad as a premium digital asset ("Local Scraper Boilerplate") targeted globally at software engineers, makers, and builders.
- **Quality Mandate:** Because this is a developer asset, code must remain exceptionally clean, strictly typed, highly modular, fully decoupled, and simple for a buyer to extend or run locally out of the box.

## 2. Core Architectural Principles & Decisions
- **Residential Scraping High Leverage:** Real estate sites aggressively block cloud platform IP ranges. To bypass expensive residential proxies, scraping pipelines run locally using the user's residential IP address.
- **The Hybrid Edge Model (Multi-Environment Sync):** - *Data Gathering:* Done locally once a week on localhost.
  - *Cloud Persistence:* Local data is upserted to a free cloud database instance via a standalone sync utility module.
  - *Presentation Layer:* A lightweight web app reads directly from the cloud layer, enabling high-performance, secure, global anywhere-access without ongoing infrastructure upkeep costs or proxy fees.

## 3. Technology Stack
- **Automation Layer:** Python, Playwright, BeautifulSoup (scrapes real estate platforms locally).
- **Local Persistence Layer:** SQLite (single file database optimized for minimal environment requirements).
- **Cloud Database Layer:** Supabase (PostgreSQL) hosted in AWS `ap-south-1` (Mumbai) to ensure zero-latency loops relative to the initial Bangalore market entry.
- **Data Transport Strategy:** Local-to-Cloud sync uses the PostgREST-driven `supabase-py` SDK over HTTPS, avoiding direct IPv4 connection string drops and connection pool overloads on port 5432.
- **Backend Service Layer:** FastAPI (Python) serving highly optimized REST endpoints.
- **Frontend Dashboard:** Next.js (React) + TailwindCSS for a highly polished, responsive dashboard.

## 4. Decoupled Parameters & Configurations
All local business and geography constraints are systematically abstracted out of scripts into a `.env` / `config.py` structural layer:
- `MAX_RENT`: Max budget filter (Baseline: ₹45,000 / month)
- `MIN_BHK`: Layout structural rule (Baseline: 3 BHK or larger)
- `TARGET_LAT` / `TARGET_LNG`: Geolocation anchoring coordinates (Baseline: Bagmane Constellation, Bangalore)
- `MAX_COMMUTE_MINS`: Max transit threshold (Baseline: <= 60 minutes)
- `ARRIVE_BY_TIME`: Shift-matched arrival parsing (Baseline: ~1:00 PM calculated against dynamic traffic)
- `Maps_API_KEY`: API authentication for Distance Matrix lookups.
- `SUPABASE_URL` / `SUPABASE_KEY`: REST API exposure endpoints for sync mechanics.

## 5. Security & Isolation Matrix
- **Row-Level Security (RLS):** Enabled globally on the Supabase `properties` table.
- **Public Policies:** Globally accessible anonymous reads (`select using (true)`) to fetch dashboard view data easily.
- **Private Policies:** Authenticated write controls (`update to authenticated`) to secure status transactions (`Interested`, `Contacted`, `Rejected`).
- **Boilerplate Auth Constraint:** Keep operational barriers low by using simple environment variable checks (e.g., Master Password protection) or native Supabase Magic Links to assign roles for interactive updates.

## 6. Current Milestones & Progress Log
- [x] Provision cloud base infrastructure (Supabase PostgreSQL live in Mumbai).
- [x] Configure robust table schemas, B-Tree lookups (`idx_properties_url`), and RLS layers.
- [ ] Implement Configuration Decoupling (`config.py` + `.env`) & Refactor local scraper engine variables.
- [ ] Build HTTPS-driven `cloud_sync.py` standalone module to stream local data to Supabase.
- [ ] Update FastAPI layer to pivot queries cleanly based on active dynamic environments.
- [ ] Build and launch Next.js UI with a clean global dashboard and lightweight protection layer.