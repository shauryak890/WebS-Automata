"""
API Module - Exposes the lead generation and email service via a REST API.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from lead_finder import LeadFinder
from lead_analyzer import LeadAnalyzer
from email_generator import EmailGenerator
import json
import time

# Load environment variables
load_dotenv()

# Get service type from environment variable or use default
SERVICE_TYPE = os.getenv("SERVICE_TYPE", "general")
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
LOCAL_LLM_TYPE = os.getenv("LOCAL_LLM_TYPE", "lm_studio")

app = FastAPI(
    title="LangChain AutoMailer API",
    description="API for automated lead generation and personalized email outreach",
    version="0.1.0"
)

# Initialize components
lead_finder = LeadFinder(
    use_local_llm=USE_LOCAL_LLM,
    local_llm_type=LOCAL_LLM_TYPE
)
lead_analyzer = LeadAnalyzer(
    use_local_llm=USE_LOCAL_LLM,
    service_type=SERVICE_TYPE,
    local_llm_type=LOCAL_LLM_TYPE
)
email_generator = EmailGenerator(
    use_local_llm=USE_LOCAL_LLM,
    service_type=SERVICE_TYPE,
    local_llm_type=LOCAL_LLM_TYPE
)

# Create default email templates
email_generator.create_default_templates()

# Data models
class SearchRequest(BaseModel):
    keywords: str
    platform: str = "instagram.com"
    location: Optional[str] = None
    contact_info: str = "@gmail.com OR @hotmail.com"
    limit: int = Field(default=5, ge=1, le=20)
    
class LeadResponse(BaseModel):
    id: str
    title: str
    link: str
    source: str
    keywords: str
    
class AnalysisRequest(BaseModel):
    lead_id: str
    service_type: Optional[str] = None
    
class EmailRequest(BaseModel):
    lead_id: str
    template: Optional[str] = "basic_template.txt"
    service_type: Optional[str] = None
    variations: int = Field(default=1, ge=1, le=3)

class EmailResponse(BaseModel):
    lead_id: str
    variations: List[Dict]

# In-memory storage for leads (in a production app, use a database)
leads_db = {}
analysis_db = {}

@app.get("/")
async def root():
    return {
        "message": "Welcome to LangChain AutoMailer API",
        "service_type": SERVICE_TYPE,
        "using_local_llm": USE_LOCAL_LLM,
        "local_llm_type": LOCAL_LLM_TYPE if USE_LOCAL_LLM else None
    }

@app.post("/search", response_model=List[LeadResponse])
async def search_leads(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Search for leads based on keywords and platform.
    """
    try:
        query_params = {
            "keywords": request.keywords,
            "platform": request.platform,
            "limit": request.limit,
            "contact_info": request.contact_info
        }
        
        if request.location:
            query_params["location"] = request.location
        
        leads = lead_finder.search_for_leads(query_params)
        
        # Store leads in memory with generated IDs
        results = []
        for i, lead in enumerate(leads):
            lead_id = f"{int(time.time())}-{i}"
            leads_db[lead_id] = lead
            
            # Add ID to the lead
            lead_with_id = lead.copy()
            lead_with_id["id"] = lead_id
            results.append(lead_with_id)
            
            # Start background task to extract contact info
            background_tasks.add_task(
                extract_contact_info_task,
                lead_id=lead_id,
                url=lead["link"]
            )
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def extract_contact_info_task(lead_id: str, url: str):
    """
    Background task to extract contact information.
    """
    if lead_id in leads_db:
        try:
            contact_info = lead_finder.extract_contact_info(url)
            leads_db[lead_id].update(contact_info)
        except Exception as e:
            print(f"Error extracting contact info: {e}")

@app.get("/leads", response_model=List[Dict])
async def get_leads():
    """
    Get all stored leads.
    """
    results = []
    for lead_id, lead in leads_db.items():
        lead_with_id = lead.copy()
        lead_with_id["id"] = lead_id
        results.append(lead_with_id)
    
    return results

@app.get("/leads/{lead_id}", response_model=Dict)
async def get_lead(lead_id: str):
    """
    Get a specific lead by ID.
    """
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = leads_db[lead_id].copy()
    lead["id"] = lead_id
    return lead

@app.post("/analyze", response_model=Dict)
async def analyze_lead(request: AnalysisRequest):
    """
    Analyze a lead to gather additional information.
    """
    if request.lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    try:
        lead_data = leads_db[request.lead_id]
        
        # Use specified service type or default
        service_type = request.service_type or SERVICE_TYPE
        
        # Create analyzer with the appropriate service type
        analyzer = LeadAnalyzer(
            use_local_llm=USE_LOCAL_LLM,
            service_type=service_type,
            local_llm_type=LOCAL_LLM_TYPE
        )
        
        analyzed_lead = analyzer.analyze_lead(lead_data)
        
        # Store analysis in memory
        analysis_db[request.lead_id] = analyzed_lead
        
        # Return the analysis
        return analyzed_lead
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-email", response_model=EmailResponse)
async def generate_email(request: EmailRequest):
    """
    Generate personalized email for a lead.
    """
    if request.lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    try:
        # Use analyzed lead data if available, otherwise use raw lead data
        lead_data = analysis_db.get(request.lead_id, leads_db[request.lead_id])
        
        # Use specified service type or default
        service_type = request.service_type or SERVICE_TYPE
        
        # Create email generator with the appropriate service type
        generator = EmailGenerator(
            use_local_llm=USE_LOCAL_LLM,
            service_type=service_type,
            local_llm_type=LOCAL_LLM_TYPE
        )
        
        # Generate email variations
        variations = generator.generate_email_variations(lead_data, request.variations)
        
        return {
            "lead_id": request.lead_id,
            "variations": variations
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates")
async def list_templates():
    """
    List available email templates.
    """
    templates = []
    for filename in os.listdir(email_generator.template_dir):
        if filename.endswith(".txt") or filename.endswith(".html"):
            templates.append(filename)
    
    return {"templates": templates}

@app.get("/service-types")
async def get_service_types():
    """
    Get a list of example service types that can be used.
    """
    service_types = [
        "web_development",
        "graphic_design",
        "content_writing",
        "digital_marketing",
        "seo",
        "social_media_management",
        "video_editing",
        "photography",
        "consulting",
        "coaching",
        "accounting",
        "legal_services",
        "it_support",
        "app_development",
        "virtual_assistant"
    ]
    
    return {
        "current_service_type": SERVICE_TYPE,
        "available_service_types": service_types
    }

@app.get("/llm-info")
async def get_llm_info():
    """
    Get information about the LLM configuration.
    """
    return {
        "using_local_llm": USE_LOCAL_LLM,
        "local_llm_type": LOCAL_LLM_TYPE if USE_LOCAL_LLM else None,
        "lm_studio_url": os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1") if USE_LOCAL_LLM and LOCAL_LLM_TYPE == "lm_studio" else None
    } 