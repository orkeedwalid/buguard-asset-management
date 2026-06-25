from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from sqlalchemy.orm import Session
from app.models import Asset
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    return ChatGroq(
        groq_api_key=api_key,
        model="llama-3.3-70b-versatile",
        temperature=0.1
    )

def safe_parse_json(text: str, fallback: dict) -> dict:
    try:
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception:
        return fallback

# ─── Feature 1: Natural-language query ───────────────────────────────────────

def natural_language_query(question: str, db: Session):
    if not question or len(question.strip()) < 3:
        return {"answer": "Please provide a valid question.", "matches": []}

    assets = get_all_assets(db)

    if not assets:
        return {"answer": "No assets found in the database.", "matches": []}

    prompt = PromptTemplate(
        input_variables=["assets", "question"],
        template="""
You are a security asset analysis assistant.
You have access to the following asset inventory in JSON format:

{assets}

The user asks: {question}

Your job:
1. Find all assets from the list above that match the user's question.
2. Return ONLY assets that exist in the list above — never invent assets.
3. Respond in this exact JSON format:
{{
  "answer": "short explanation of what you found",
  "matches": [list of matching asset values]
}}

If nothing matches, return empty matches list.
Respond with JSON only, no extra text.
"""
    )

    try:
        llm = get_llm()
        chain = prompt | llm
        result = chain.invoke({
            "assets": json.dumps(assets, indent=2),
            "question": question
        })
        return safe_parse_json(result.content, {
            "answer": result.content,
            "matches": []
        })
    except ValueError as e:
        return {"error": str(e), "matches": []}
    except Exception as e:
        return {"error": f"LLM service unavailable: {str(e)}", "matches": []}


# ─── Feature 2: Risk scoring & summarization ─────────────────────────────────

def risk_scoring(asset_id: str, db: Session):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return {"error": f"Asset '{asset_id}' not found in database"}

    asset_data = {
        "id": asset.id,
        "type": asset.type,
        "value": asset.value,
        "status": asset.status,
        "tags": asset.tags or [],
        "metadata": asset.metadata_ or {}
    }

    prompt = PromptTemplate(
        input_variables=["asset"],
        template="""
You are a cybersecurity expert analyzing an asset for risk.

Asset data:
{asset}

Analyze this asset and respond in this exact JSON format:
{{
  "risk_score": <number from 1 to 10>,
  "risk_level": "<low|medium|high|critical>",
  "summary": "<2-3 sentence summary of the asset>",
  "risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
  "recommendations": ["<action 1>", "<action 2>"]
}}

Consider:
- Expired or expiring certificates are high risk
- Services exposed on sensitive ports are high risk
- Stale assets that reappear are medium risk
- Production assets have higher impact

Respond with JSON only, no extra text.
"""
    )

    try:
        llm = get_llm()
        chain = prompt | llm
        result = chain.invoke({"asset": json.dumps(asset_data, indent=2)})
        return safe_parse_json(result.content, {"raw_response": result.content})
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"LLM service unavailable: {str(e)}"}


# ─── Feature 3: Enrichment & categorization ──────────────────────────────────

def enrich_asset(asset_id: str, db: Session):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return {"error": "Asset not found"}

    asset_data = {
        "id": asset.id,
        "type": asset.type,
        "value": asset.value,
        "tags": asset.tags or [],
        "metadata": asset.metadata_ or {}
    }

    prompt = PromptTemplate(
        input_variables=["asset"],
        template="""
You are a security asset classification expert.

Given this asset:
{asset}

Classify and enrich it. Respond in this exact JSON format:
{{
  "environment": "<production|staging|development|unknown>",
  "category": "<web|api|database|infrastructure|email|cdn|unknown>",
  "criticality": "<low|medium|high|critical>",
  "enrichment": {{
    "probable_owner": "<team or system that likely owns this>",
    "exposure": "<internal|external|unknown>",
    "notes": "<any useful observations about this asset>"
  }}
}}

Base your answer only on the asset data provided.
Respond with JSON only, no extra text.
"""
    )

    llm = get_llm()
    chain = prompt | llm

    result = chain.invoke({"asset": json.dumps(asset_data, indent=2)})

    try:
        text = result.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        enrichment = json.loads(text)
        asset.metadata_ = {**(asset.metadata_ or {}), "enrichment": enrichment}
        db.commit()
        return enrichment
    except Exception:
        return {"raw_response": result.content}


# ─── Feature 4: Natural-language report generation ───────────────────────────

def generate_report(db: Session, filter_type: str = None, filter_status: str = None):
    query = db.query(Asset)
    if filter_type:
        query = query.filter(Asset.type == filter_type)
    if filter_status:
        query = query.filter(Asset.status == filter_status)

    assets = query.all()

    if not assets:
        return {"report": "No assets found matching the filter criteria."}

    asset_list = [
        {
            "type": a.type,
            "value": a.value,
            "status": a.status,
            "tags": a.tags or [],
            "metadata": a.metadata_ or {}
        }
        for a in assets
    ]

    prompt = PromptTemplate(
        input_variables=["assets", "total"],
        template="""
You are a cybersecurity analyst writing an executive report.

You have {total} assets in the inventory:
{assets}

Write a professional security inventory report that includes:
1. Executive summary (2-3 sentences)
2. Asset breakdown by type
3. Key risks identified
4. Top recommendations

Base the report ONLY on the assets provided above.
Write in clear professional English suitable for a security team.
"""
    )

    try:
        llm = get_llm()
        chain = prompt | llm
        result = chain.invoke({
            "assets": json.dumps(asset_list, indent=2),
            "total": len(asset_list)
        })
        return {"report": result.content}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"LLM service unavailable: {str(e)}"}