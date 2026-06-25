# Buguard Asset Management System
> DarkAtlas Attack Surface Monitoring — AI Applications Track (Track B)

A FastAPI + PostgreSQL + LangChain system for managing and analyzing internet-facing security assets, powered by Groq's Llama 3.3 70B model.

## Features

- **Bulk asset import** with deduplication — re-importing the same asset updates it instead of creating duplicates
- **Natural-language asset querying** — ask questions in plain English about your assets
- **AI risk scoring** — get a risk score, summary, and recommendations for any asset
- **Automated enrichment & categorization** — classify assets by environment, category, and criticality
- **Executive report generation** — generate a full security inventory report in natural language
- **Lifecycle management** — tracks first_seen, last_seen, and asset status (active/stale/archived)

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy
- **Database:** PostgreSQL 15
- **AI Layer:** LangChain + Groq API (llama-3.3-70b-versatile)
- **Infrastructure:** Docker, Docker Compose

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
Edit `.env` and add your Groq API key:

### 3. Run with Docker
```bash
docker compose up --build
```

The API will be available at **http://localhost:8000**

### 4. View API docs
Open **http://localhost:8000/docs** in your browser.

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `GROQ_API_KEY` | Your Groq API key | `gsk_...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@db:5432/assetdb` |

## API Endpoints

### Assets
| Method | Endpoint | Description |
|---|---|---|
| POST | `/import` | Bulk import assets with deduplication |
| GET | `/assets` | List assets with filtering and pagination |
| GET | `/assets/{id}` | Get a single asset |
| PATCH | `/assets/{id}/stale` | Mark an asset as stale |
| GET | `/assets/{id}/relationships` | Get asset relationships |

### AI Analysis
| Method | Endpoint | Description |
|---|---|---|
| POST | `/analyze/query` | Natural-language asset query |
| POST | `/analyze/risk` | Risk scoring for an asset |
| POST | `/analyze/enrich` | Enrich and categorize an asset |
| POST | `/analyze/report` | Generate executive security report |

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
  "answer": "Found 1 expired certificate",
  "matches": ["CN=staging.example.com"]
}
```

### 2. Risk scoring
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
  "summary": "This is an expired TLS certificate for api.example.com issued by Let's Encrypt. The certificate expired on January 2, 2024, posing a critical risk to secure communications.",
  "risks": [
    "Expired certificate breaks HTTPS connections",
    "Users will see browser security warnings",
    "Potential for man-in-the-middle attacks"
  ],
  "recommendations": [
    "Renew the certificate immediately",
    "Set up auto-renewal with Let's Encrypt certbot"
  ]
}
```

### 3. Enrich asset
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
    "notes": "Production API endpoint — requires strong security controls"
  }
}
```

### 4. Executive report
**Request:**
```json
{
  "filter_type": null,
  "filter_status": null
}
```
**Response:** A full markdown security report covering asset inventory, identified risks, and recommendations.

## Design Decisions & Assumptions

- **Deduplication** is based on `value` + `type` combination — if an asset with the same value and type exists, it updates `last_seen` and merges tags and metadata instead of creating a duplicate.
- **Stale assets** that are re-imported automatically return to `active` status.
- **Hallucination guard** — all AI analysis endpoints only operate on assets that exist in the database. The LLM is explicitly instructed never to invent assets.
- **Malformed records** in bulk import are skipped gracefully — the batch continues and errors are reported in the response.
- **LangChain** is used for all prompt templates and LLM chains following current best practices (`langchain_core.prompts`).
- **Groq** was chosen as the LLM provider because it offers a generous free tier suitable for development and testing.

## Project Structure