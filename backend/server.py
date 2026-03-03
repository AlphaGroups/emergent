from fastapi import FastAPI, APIRouter, HTTPException, status, Depends, Cookie, Response, UploadFile, File
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import base64
from io import BytesIO
from PIL import Image
import pytesseract

from config import settings
from models.vendor import Vendor, GSTDetails, MCAData, FinancialHistory, LicenseDocument
from services.cashfree_service import cashfree_service
from services.auth_service import AuthService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

auth_service = AuthService(db)

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Pydantic models for requests
class SessionExchangeRequest(BaseModel):
    session_id: str

class GSTINVerifyRequest(BaseModel):
    gstin: str
    business_name: Optional[str] = None

class OTPInitiateRequest(BaseModel):
    mobile: str
    pan: str

class OTPVerifyRequest(BaseModel):
    otp_id: str
    otp: str
    pan: str

class DocumentUploadResponse(BaseModel):
    license_type: str
    license_number: Optional[str] = None
    validity: Optional[str] = None
    file_url: str

# Dependency to get current user from cookie or header
async def get_current_user(
    session_token: Optional[str] = Cookie(default=None),
    authorization: Optional[str] = None
):
    # Try cookie first, then Authorization header
    token = session_token
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = await auth_service.verify_session(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    return user

# Auth routes
@api_router.post("/auth/session")
async def exchange_session(request: SessionExchangeRequest, response: Response):
    """Exchange session_id for session_token"""
    try:
        result = await auth_service.exchange_session_id(request.session_id)
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=result["session_token"],
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7*24*60*60  # 7 days
        )
        
        return {
            "user_id": result["user_id"],
            "email": result["email"],
            "name": result["name"],
            "picture": result.get("picture")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/auth/me")
async def get_current_user_info(user = Depends(get_current_user)):
    """Get current user information"""
    return user

@api_router.post("/auth/logout")
async def logout(
    response: Response,
    session_token: Optional[str] = Cookie(default=None)
):
    """Logout user"""
    if session_token:
        await auth_service.logout(session_token)
    
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out successfully"}

# Vendor verification routes
@api_router.post("/verify/gstin")
async def verify_gstin(
    request: GSTINVerifyRequest,
    user = Depends(get_current_user)
):
    """Phase 1: Verify GSTIN and fetch corporate details"""
    try:
        # Verify GSTIN
        gst_data = await cashfree_service.verify_gstin(
            request.gstin,
            request.business_name
        )
        
        pan = gst_data["pan"]
        entity_type = gst_data["entity_type"]
        
        # Check if Company or LLP, fetch CIN
        mca_data = None
        if entity_type in ["Company", "LLP"]:
            mca_data = await cashfree_service.verify_cin(pan)
        
        # Fetch all GSTINs for this PAN
        all_gstins_data = await cashfree_service.get_all_gstins_by_pan(pan)
        
        # Store/update vendor in MongoDB
        vendor_doc = {
            "pan": pan,
            "user_id": user["user_id"],
            "gst_details": {
                "gstin": gst_data["gstin"],
                "legal_name": gst_data["legal_name"],
                "trade_name": gst_data["trade_name"],
                "entity_type": gst_data["entity_type"],
                "pan": gst_data["pan"],
                "registered_address": gst_data["registered_address"],
                "status": gst_data["status"],
                "state": gst_data["state"],
                "verified_at": datetime.now(timezone.utc)
            },
            "all_gstins": all_gstins_data,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if mca_data:
            vendor_doc["mca_data"] = {
                "cin": mca_data["cin"],
                "company_name": mca_data["company_name"],
                "incorporation_year": mca_data["incorporation_year"],
                "directors": mca_data["directors"],
                "company_status": mca_data["company_status"],
                "verified_at": datetime.now(timezone.utc)
            }
        
        # Upsert vendor
        await db.vendors.update_one(
            {"pan": pan, "user_id": user["user_id"]},
            {"$set": vendor_doc, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
            upsert=True
        )
        
        return {
            "gst_details": gst_data,
            "mca_data": mca_data,
            "all_gstins": all_gstins_data
        }
        
    except Exception as e:
        logging.error(f"GSTIN verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/verify/initiate-otp")
async def initiate_financial_otp(
    request: OTPInitiateRequest,
    user = Depends(get_current_user)
):
    """Phase 3: Initiate OTP for financial data unlock"""
    try:
        result = await cashfree_service.initiate_otp(request.mobile)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/verify/verify-otp")
async def verify_otp_and_unlock_financials(
    request: OTPVerifyRequest,
    user = Depends(get_current_user)
):
    """Phase 3: Verify OTP and fetch financial data"""
    try:
        # Verify OTP and fetch financials
        financial_data = await cashfree_service.verify_otp_and_fetch_financials(
            request.otp_id,
            request.otp,
            request.pan
        )
        
        # Update vendor with financial data
        await db.vendors.update_one(
            {"pan": request.pan, "user_id": user["user_id"]},
            {"$set": {
                "financial_history": {
                    "itr_filing_status": financial_data["itr_filing_status"],
                    "turnover_year_1": financial_data["turnover_year_1"],
                    "turnover_year_2": financial_data["turnover_year_2"],
                    "turnover_year_3": financial_data["turnover_year_3"],
                    "epf_number": financial_data["epf_number"],
                    "esic_number": financial_data["esic_number"],
                    "pf_number": financial_data["pf_number"],
                    "unlocked_at": datetime.now(timezone.utc)
                },
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        return financial_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/vendors")
async def get_all_vendors(user = Depends(get_current_user)):
    """Get all vendors for current user"""
    vendors = await db.vendors.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(100)
    
    return {"vendors": vendors, "count": len(vendors)}

@api_router.get("/vendors/{pan}")
async def get_vendor_by_pan(pan: str, user = Depends(get_current_user)):
    """Get vendor details by PAN"""
    vendor = await db.vendors.find_one(
        {"pan": pan, "user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return vendor

@api_router.post("/vendors/{pan}/upload-license")
async def upload_license_document(
    pan: str,
    license_type: str,
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """Upload license document with OCR"""
    try:
        # Read file
        contents = await file.read()
        
        # Basic OCR to extract license details
        license_number = None
        validity = None
        
        try:
            # Try OCR on image
            image = Image.open(BytesIO(contents))
            text = pytesseract.image_to_string(image)
            
            # Simple keyword search
            lines = text.split('\n')
            for line in lines:
                if 'license' in line.lower() and any(char.isdigit() for char in line):
                    license_number = line.strip()
                if 'valid' in line.lower() or 'expiry' in line.lower():
                    validity = line.strip()
        except Exception as ocr_error:
            logging.warning(f"OCR failed: {str(ocr_error)}")
        
        # Store file (in production, upload to S3)
        file_id = uuid.uuid4().hex
        file_url = f"/uploads/{file_id}_{file.filename}"
        
        # Save to disk for now
        upload_dir = Path("/app/backend/uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / f"{file_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Update vendor
        license_doc = {
            "license_type": license_type,
            "license_number": license_number,
            "validity": validity,
            "file_url": file_url,
            "uploaded_at": datetime.now(timezone.utc)
        }
        
        await db.vendors.update_one(
            {"pan": pan, "user_id": user["user_id"]},
            {"$push": {"licenses": license_doc}}
        )
        
        return license_doc
        
    except Exception as e:
        logging.error(f"License upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/vendors/{pan}/download-report")
async def download_due_diligence_report(
    pan: str,
    user = Depends(get_current_user)
):
    """Generate and download PDF due diligence report"""
    try:
        vendor = await db.vendors.find_one(
            {"pan": pan, "user_id": user["user_id"]},
            {"_id": 0}
        )
        
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # In production, generate actual PDF with reportlab
        # For now, return JSON as text file
        import json
        report_content = json.dumps(vendor, indent=2, default=str)
        
        file_path = Path(f"/tmp/vendor_report_{pan}.txt")
        file_path.write_text(report_content)
        
        return FileResponse(
            path=str(file_path),
            filename=f"vendor_report_{pan}.txt",
            media_type="text/plain"
        )
        
    except Exception as e:
        logging.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()