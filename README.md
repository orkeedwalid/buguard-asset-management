# Buguard Asset Management System
> DarkAtlas Attack Surface Monitoring — AI Applications Track (Track B)

A FastAPI + PostgreSQL + LangChain system for managing and analyzing internet-facing security assets, powered by Groq's Llama 3.3 70B model.

## Features

### Core
- **Bulk asset import** with deduplication — re-importing the same asset updates it instead of creating duplicates
- **Natural-language asset querying** — ask questions in plain English about your assets
- **AI risk scoring** — get a risk score, summary, and recommendations for any asset
- **Automated enrichment & categorization** — classify assets by environment, category, and criticality
- **Executive report generation** — generate a full security inventory report in natural language
- **Lifecycle management** — tracks first_seen, last_seen, and asset status (active/stale/archived)
- **Hallucination guard** — LLM only answers from real database assets, never invents data

### Bonus
- **API key authentication** — all write operations require X-API-Key header
- **LLM response caching** — repeated queries return instantly with cached: true
- **Multi-tenancy** — complete organization isolation, one org never sees another's assets

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy
- **Database:** PostgreSQL 15
- **AI Layer:** LangChain + Groq API (llama-3.3-70b-versatile)
- **Infrastructure:** Docker, Docker Compose
- **Testing:** pytest (7 passing tests)

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/orkeedwalid/buguard-asset-management.git
cd buguard-asset-management
```

### 2. Set up environment variables
```bash
cp .env.example .env
```
Edit `.env` and add your keys:

### 3. Run with Docker
```bash
docker compose up --build
```

The API will be available at **http://localhost:8000**

### 4. View API docs
Open **http://localhost:8000/docs** in your browser.

### 5. Create your organization
```bash
curl -X POST "http://localhost:8000/organizations?name=myorg"
```
Save the returned `api_key` — use it as `X-API-Key` header for all requests.

### 6. Import sample data
```bash
curl -X POST "http://localhost:8000/import" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d @sample_data.json
```

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `GROQ_API_KEY` | Your Groq API key | `gsk_...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@db:5432/assetdb` |

## API Endpoints

### Organization
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/organizations` | None | Create organization, get API key |
| GET | `/organizations/me` | Required | Get current org info |

### Assets
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/import` | Required | Bulk import with deduplication |
| GET | `/assets` | Required | List assets with filtering and pagination |
| GET | `/assets/{id}` | Required | Get a single asset |
| PATCH | `/assets/{id}/stale` | Required | Mark an asset as stale |
| GET | `/assets/{id}/relationships` | Required | Get asset relationships |

### AI Analysis
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/analyze/query` | Required | Natural-language asset query |
| POST | `/analyze/risk` | Required | Risk scoring for an asset |
| POST | `/analyze/enrich` | Required | Enrich and categorize an asset |
| POST | `/analyze/report` | Required | Generate executive security report |
| GET | `/cache/stats` | Required | View cache statistics |
| DELETE | `/cache/clear` | Required | Clear LLM cache |

## Example Prompts & Outputs

### 1. Natural-language query
**Request:**
```json
{
  "question": "show me all expired certificates"
}
```
**Response:**
```json
{
  "answer": "Found certificates with expiration dates earlier than the current date",
  "matches": ["CN=staging.example.com"]
}
```

### 2. Cached response (second call)
```json
{
  "answer": "Found certificates with expiration dates earlier than the current date",
  "matches": ["CN=staging.example.com"],
  "cached": true
}
```

### 3. Risk scoring
**Request:**
```json
{
  "asset_id": "a3"
}
```
**Response:**
```json
{
  "risk_score": 9,
  "risk_level": "critical",
  "summary": "Expired TLS certificate for api.example.com. Expired January 2024.",
  "risks": [
    "Expired certificate breaks HTTPS",
    "Browser security warnings",
    "Man-in-the-middle attack risk"
  ],
  "recommendations": [
    "Renew certificate immediately",
    "Set up auto-renewal with certbot"
  ]
}
```

### 4. Enrich asset
**Request:**
```json
{
  "asset_id": "a2"
}
```
**Response:**
```json
{
  "environment": "production",
  "category": "api",
  "criticality": "high",
  "enrichment": {
    "probable_owner": "Backend engineering team",
    "exposure": "external",
    "notes": "Production API endpoint requiring strong security controls"
  }
}
```

### 5. Multi-tenancy isolation
```bash
# Org A imports 10 assets
curl -X GET "http://localhost:8000/assets" -H "X-API-Key: org_a_key"
# Returns 10 assets

# Org B sees nothing
curl -X GET "http://localhost:8000/assets" -H "X-API-Key: org_b_key"
# Returns []
```

## Running Tests

```bash
pip install pytest httpx
pytest tests/ -v
```

Expected output: **7 passed**

## Design Decisions & Assumptions

- **Deduplication** is based on `value` + `type` + `org_id` — same asset from two sources updates instead of duplicating.
- **Stale assets** that are re-imported automatically return to `active` status.
- **Hallucination guard** — all AI endpoints only operate on real database assets. The LLM is explicitly instructed never to invent assets.
- **Malformed records** in bulk import are skipped gracefully — the batch continues and errors are reported.
- **Multi-tenancy** — each organization has its own API key. All queries are scoped to the organization — cross-org data leakage is impossible at the query level.
- **LLM caching** — responses are cached for 300 seconds (5 minutes) using an in-memory store. Cache key includes the question and asset count.
- **Groq** was chosen as the LLM provider because it offers a generous free tier and extremely fast inference.

## Project Structure