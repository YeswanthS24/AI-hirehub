from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Helper functions for MongoDB serialization
def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and 'T' in value:
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password: str
    name: str
    user_type: str  # "job_seeker" or "employer"
    profile_image: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    skills: List[str] = []
    experience: Optional[str] = None
    education: Optional[str] = None
    resume: Optional[str] = None  # base64 encoded
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    user_type: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    user_type: str
    profile_image: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    skills: List[str] = []
    experience: Optional[str] = None
    education: Optional[str] = None
    created_at: datetime

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    company: str
    location: str
    job_type: str  # "full-time", "part-time", "contract", "remote"
    salary_range: Optional[str] = None
    description: str
    requirements: List[str] = []
    benefits: List[str] = []
    employer_id: str
    posted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    status: str = "active"  # "active", "closed", "draft"

class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    job_type: str
    salary_range: Optional[str] = None
    description: str
    requirements: List[str] = []
    benefits: List[str] = []

class JobResponse(BaseModel):
    id: str
    title: str
    company: str
    location: str
    job_type: str
    salary_range: Optional[str] = None
    description: str
    requirements: List[str] = []
    benefits: List[str] = []
    employer_id: str
    posted_at: datetime
    status: str

class Application(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    applicant_id: str
    cover_letter: Optional[str] = None
    status: str = "pending"  # "pending", "reviewed", "shortlisted", "rejected", "hired"
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

class ApplicationCreate(BaseModel):
    job_id: str
    cover_letter: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    applicant_id: str
    cover_letter: Optional[str] = None
    status: str
    applied_at: datetime
    job_title: Optional[str] = None
    company: Optional[str] = None
    applicant_name: Optional[str] = None

# Authentication Routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user_data.dict()
    user_obj = User(**user_dict)
    user_mongo = prepare_for_mongo(user_obj.dict())
    
    await db.users.insert_one(user_mongo)
    return UserResponse(**user_obj.dict())

@api_router.post("/auth/login", response_model=UserResponse)
async def login_user(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email, "password": login_data.password})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = parse_from_mongo(user)
    return UserResponse(**user)

# User Routes
@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = parse_from_mongo(user)
    return UserResponse(**user)

@api_router.put("/users/{user_id}/profile")
async def update_user_profile(user_id: str, profile_data: dict):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": profile_data}
    )
    return {"message": "Profile updated successfully"}

# Job Routes
@api_router.post("/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate, employer_id: str):
    job_dict = job_data.dict()
    job_dict["employer_id"] = employer_id
    job_obj = Job(**job_dict)
    job_mongo = prepare_for_mongo(job_obj.dict())
    
    await db.jobs.insert_one(job_mongo)
    return JobResponse(**job_obj.dict())

@api_router.get("/jobs", response_model=List[JobResponse])
async def get_jobs(skip: int = 0, limit: int = 20, search: Optional[str] = None, 
                  location: Optional[str] = None, job_type: Optional[str] = None):
    query = {"status": "active"}
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    
    if job_type:
        query["job_type"] = job_type
    
    jobs = await db.jobs.find(query).skip(skip).limit(limit).sort("posted_at", -1).to_list(length=None)
    jobs = [parse_from_mongo(job) for job in jobs]
    return [JobResponse(**job) for job in jobs]

@api_router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = parse_from_mongo(job)
    return JobResponse(**job)

@api_router.get("/jobs/employer/{employer_id}", response_model=List[JobResponse])
async def get_employer_jobs(employer_id: str):
    jobs = await db.jobs.find({"employer_id": employer_id}).sort("posted_at", -1).to_list(length=None)
    jobs = [parse_from_mongo(job) for job in jobs]
    return [JobResponse(**job) for job in jobs]

# Application Routes
@api_router.post("/applications", response_model=ApplicationResponse)
async def apply_for_job(application_data: ApplicationCreate, applicant_id: str):
    # Check if already applied
    existing_application = await db.applications.find_one({
        "job_id": application_data.job_id,
        "applicant_id": applicant_id
    })
    if existing_application:
        raise HTTPException(status_code=400, detail="Already applied for this job")
    
    app_dict = application_data.dict()
    app_dict["applicant_id"] = applicant_id
    app_obj = Application(**app_dict)
    app_mongo = prepare_for_mongo(app_obj.dict())
    
    await db.applications.insert_one(app_mongo)
    
    # Get job details for response
    job = await db.jobs.find_one({"id": application_data.job_id})
    applicant = await db.users.find_one({"id": applicant_id})
    
    response_data = app_obj.dict()
    if job:
        response_data["job_title"] = job["title"]
        response_data["company"] = job["company"]
    if applicant:
        response_data["applicant_name"] = applicant["name"]
    
    return ApplicationResponse(**response_data)

@api_router.get("/applications/user/{user_id}", response_model=List[ApplicationResponse])
async def get_user_applications(user_id: str):
    applications = await db.applications.find({"applicant_id": user_id}).sort("applied_at", -1).to_list(length=None)
    applications = [parse_from_mongo(app) for app in applications]
    
    # Enrich with job details
    enriched_apps = []
    for app in applications:
        job = await db.jobs.find_one({"id": app["job_id"]})
        app_data = app.copy()
        if job:
            app_data["job_title"] = job["title"]
            app_data["company"] = job["company"]
        enriched_apps.append(ApplicationResponse(**app_data))
    
    return enriched_apps

@api_router.get("/applications/job/{job_id}", response_model=List[ApplicationResponse])
async def get_job_applications(job_id: str):
    applications = await db.applications.find({"job_id": job_id}).sort("applied_at", -1).to_list(length=None)
    applications = [parse_from_mongo(app) for app in applications]
    
    # Enrich with applicant details
    enriched_apps = []
    for app in applications:
        applicant = await db.users.find_one({"id": app["applicant_id"]})
        job = await db.jobs.find_one({"id": job_id})
        app_data = app.copy()
        if applicant:
            app_data["applicant_name"] = applicant["name"]
        if job:
            app_data["job_title"] = job["title"]
            app_data["company"] = job["company"]
        enriched_apps.append(ApplicationResponse(**app_data))
    
    return enriched_apps

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user_id: str, user_type: str):
    if user_type == "job_seeker":
        applications_count = await db.applications.count_documents({"applicant_id": user_id})
        pending_count = await db.applications.count_documents({"applicant_id": user_id, "status": "pending"})
        shortlisted_count = await db.applications.count_documents({"applicant_id": user_id, "status": "shortlisted"})
        return {
            "total_applications": applications_count,
            "pending": pending_count,
            "shortlisted": shortlisted_count
        }
    else:  # employer
        jobs_count = await db.jobs.count_documents({"employer_id": user_id})
        active_jobs = await db.jobs.count_documents({"employer_id": user_id, "status": "active"})
        
        # Get total applications for employer's jobs
        employer_jobs = await db.jobs.find({"employer_id": user_id}).to_list(length=None)
        job_ids = [job["id"] for job in employer_jobs]
        total_applications = await db.applications.count_documents({"job_id": {"$in": job_ids}}) if job_ids else 0
        
        return {
            "total_jobs": jobs_count,
            "active_jobs": active_jobs,
            "total_applications": total_applications
        }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()