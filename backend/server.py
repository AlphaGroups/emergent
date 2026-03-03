from fastapi import FastAPI, APIRouter, HTTPException, status, Depends, Cookie, Response, UploadFile, File, Header
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
    authorization: Optional[str] = Header(default=None)
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
    """Phase 1: Verify GSTIN and fetch corporate details with entity-specific branching"""
    try:
        # Verify GSTIN
        gst_data = await cashfree_service.verify_gstin(
            request.gstin,
            request.business_name
        )
        
        pan = gst_data["pan"]
        entity_type = gst_data["entity_type"]
        pan_char4 = pan[3].upper() if len(pan) > 3 else None
        
        # Initialize vendor document
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
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Fetch all GSTINs for this PAN
        all_gstins_data = await cashfree_service.get_all_gstins_by_pan(pan)
        vendor_doc["all_gstins"] = all_gstins_data
        
        # Branching logic based on entity type
        mca_data = None
        udyam_data = None
        partnership_data = None
        trust_society_data = None
        
        # Case 1: Company or LLP - Use MCA
        if pan_char4 in ['C', 'L']:
            mca_data = await cashfree_service.verify_cin(pan)
            vendor_doc["mca_data"] = {
                "cin": mca_data["cin"],
                "company_name": mca_data["company_name"],
                "incorporation_year": mca_data["incorporation_year"],
                "directors": mca_data["directors"],
                "company_status": mca_data["company_status"],
                "verified_at": datetime.now(timezone.utc)
            }
            vendor_doc["registration_type"] = "MCA"
        
        # Case 2: Sole Proprietorship - Use Udyam
        elif pan_char4 == 'P':
            # Step 1: Get Udyam Registration Number
            pan_udyam_response = await cashfree_service.verify_pan_udyam(pan)
            
            if pan_udyam_response.get("is_registered"):
                urn = pan_udyam_response["urn"]
                
                # Step 2: Fetch Udyam details
                udyam_details = await cashfree_service.verify_udyam(urn, pan)
                
                udyam_data = {
                    "urn": udyam_details["urn"],
                    "registration_date": udyam_details["registration_date"],
                    "msme_category": udyam_details["msme_category"],
                    "owner_name": udyam_details["owner_name"],
                    "business_name": udyam_details["business_name"],
                    "name_match_score": udyam_details["name_match_score"],
                    "verified_at": datetime.now(timezone.utc)
                }
                vendor_doc["udyam_data"] = udyam_data
                vendor_doc["registration_type"] = "UDYAM"
        
        # Case 3: Partnership Firm - Use GST earliest date + EPFO
        elif pan_char4 == 'F':
            # Get earliest GST registration date
            gst_earliest = await cashfree_service.verify_pan_gstin_earliest(pan)
            
            # Get EPFO establishment details
            epfo_details = await cashfree_service.verify_epfo_establishment(pan)
            
            partnership_data = {
                "earliest_gst_date": gst_earliest["earliest_gst_date"],
                "epfo_establishment_code": epfo_details["establishment_code"],
                "establishment_name": epfo_details["establishment_name"],
                "partners": [],  # Partners list would come from additional API if available
                "verified_at": datetime.now(timezone.utc)
            }
            vendor_doc["partnership_data"] = partnership_data
            vendor_doc["registration_type"] = "PARTNERSHIP_EPFO"
        
        # Case 4: Trust or Society - Requires OCR (handled separately via upload)
        elif pan_char4 in ['T', 'S']:
            trust_society_data = {
                "registration_type": "Trust" if pan_char4 == 'T' else "Society",
                "note": "Document upload required for verification"
            }
            vendor_doc["trust_society_data"] = trust_society_data
            vendor_doc["registration_type"] = "TRUST_SOCIETY_PENDING"
        
        # Upsert vendor
        await db.vendors.update_one(
            {"pan": pan, "user_id": user["user_id"]},
            {"$set": vendor_doc, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
            upsert=True
        )
        
        return {
            "gst_details": gst_data,
            "mca_data": mca_data,
            "udyam_data": udyam_data,
            "partnership_data": partnership_data,
            "trust_society_data": trust_society_data,
            "all_gstins": all_gstins_data,
            "registration_type": vendor_doc["registration_type"]
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

@api_router.post("/vendors/{pan}/upload-trust-society-doc")
async def upload_trust_society_document(
    pan: str,
    document_type: str,
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """Upload and verify Trust/Society registration document with OCR"""
    try:
        # Read file
        contents = await file.read()
        
        # Save file temporarily
        upload_dir = Path("/app/backend/uploads")
        upload_dir.mkdir(exist_ok=True)
        file_id = uuid.uuid4().hex
        file_path = upload_dir / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Perform OCR verification
        ocr_result = await cashfree_service.verify_trust_society_ocr(
            document_type,
            str(file_path)
        )
        
        # Update vendor with trust/society data
        trust_society_data = {
            "registration_number": ocr_result["registration_number"],
            "registration_type": document_type,
            "date_of_formation": ocr_result["date_of_formation"],
            "ngo_darpan_id": ocr_result.get("ngo_darpan_id"),
            "trustees_members": ocr_result["trustees_members"],
            "verified_at": datetime.now(timezone.utc)
        }
        
        await db.vendors.update_one(
            {"pan": pan, "user_id": user["user_id"]},
            {
                "$set": {
                    "trust_society_data": trust_society_data,
                    "registration_type": "TRUST_SOCIETY",
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {
            "success": True,
            "trust_society_data": trust_society_data
        }
        
    except Exception as e:
        logging.error(f"Trust/Society document upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
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
        
        # Generate PDF report
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        
        file_path = Path(f"/tmp/vendor_report_{pan}.pdf")
        
        # Create PDF
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#004EEB'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#334155')
        )
        
        # Title
        elements.append(Paragraph("Vendor Due Diligence Report", title_style))
        elements.append(Paragraph("FinTrust Intelligence", normal_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Report metadata
        from datetime import datetime
        report_date = datetime.now().strftime("%B %d, %Y at %H:%M")
        elements.append(Paragraph(f"<b>Report Generated:</b> {report_date}", normal_style))
        elements.append(Paragraph(f"<b>Report ID:</b> {pan}-{datetime.now().strftime('%Y%m%d%H%M')}", normal_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Phase 1: Corporate Identity
        elements.append(Paragraph("Phase 1: Corporate Identity & Registration", heading_style))
        
        if vendor.get('gst_details'):
            gst = vendor['gst_details']
            
            data = [
                ['Field', 'Value'],
                ['Legal Name', gst.get('legal_name', 'N/A')],
                ['Trade Name', gst.get('trade_name', 'N/A')],
                ['Entity Type', gst.get('entity_type', 'N/A')],
                ['PAN', gst.get('pan', 'N/A')],
                ['GSTIN', gst.get('gstin', 'N/A')],
                ['Status', gst.get('status', 'N/A')],
                ['State', gst.get('state', 'N/A')],
                ['Registered Address', gst.get('registered_address', 'N/A')],
            ]
            
            table = Table(data, colWidths=[2*inch, 4.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))
        
        # MCA Data
        if vendor.get('mca_data'):
            elements.append(Paragraph("MCA Registration Details", subheading_style))
            mca = vendor['mca_data']
            
            data = [
                ['Field', 'Value'],
                ['CIN', mca.get('cin', 'N/A')],
                ['Company Name', mca.get('company_name', 'N/A')],
                ['Incorporation Year', mca.get('incorporation_year', 'N/A')],
                ['Company Status', mca.get('company_status', 'N/A')],
            ]
            
            table = Table(data, colWidths=[2*inch, 4.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.15*inch))
            
            # Directors
            if mca.get('directors'):
                elements.append(Paragraph("<b>Directors/Key Personnel:</b>", normal_style))
                for idx, director in enumerate(mca['directors'], 1):
                    elements.append(Paragraph(f"{idx}. {director}", normal_style))
                elements.append(Spacer(1, 0.2*inch))
        
        # Phase 2: Network Analysis
        elements.append(Paragraph("Phase 2: Multi-State GST Network", heading_style))
        
        if vendor.get('all_gstins') and len(vendor['all_gstins']) > 0:
            elements.append(Paragraph(f"Total Registrations: <b>{len(vendor['all_gstins'])}</b>", normal_style))
            elements.append(Spacer(1, 0.1*inch))
            
            gstin_data = [['GSTIN', 'State', 'Filing Status', 'Status']]
            for gstin in vendor['all_gstins']:
                gstin_data.append([
                    gstin.get('gstin', 'N/A'),
                    gstin.get('state', 'N/A'),
                    gstin.get('filing_status', 'N/A'),
                    gstin.get('status', 'N/A')
                ])
            
            table = Table(gstin_data, colWidths=[2.2*inch, 1.8*inch, 1.5*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Phase 3: Financial Data
        if vendor.get('financial_history'):
            elements.append(Paragraph("Phase 3: Financial Insights & Compliance", heading_style))
            fin = vendor['financial_history']
            
            data = [
                ['Financial Metric', 'Value'],
                ['ITR Filing Status', fin.get('itr_filing_status', 'N/A')],
                ['Turnover - Year 1 (Latest)', f"₹ {fin.get('turnover_year_1', 0):,.2f}" if fin.get('turnover_year_1') else 'N/A'],
                ['Turnover - Year 2', f"₹ {fin.get('turnover_year_2', 0):,.2f}" if fin.get('turnover_year_2') else 'N/A'],
                ['Turnover - Year 3', f"₹ {fin.get('turnover_year_3', 0):,.2f}" if fin.get('turnover_year_3') else 'N/A'],
                ['EPF Number', fin.get('epf_number', 'N/A')],
                ['ESIC Number', fin.get('esic_number', 'N/A')],
                ['PF Number', fin.get('pf_number', 'N/A')],
            ]
            
            table = Table(data, colWidths=[2.5*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))
        else:
            elements.append(Paragraph("Phase 3: Financial Insights & Compliance", heading_style))
            elements.append(Paragraph("<i>Financial data not unlocked. OTP verification required.</i>", normal_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # License Documents
        if vendor.get('licenses') and len(vendor['licenses']) > 0:
            elements.append(Paragraph("License Documents", subheading_style))
            
            license_data = [['License Type', 'License Number', 'Validity']]
            for lic in vendor['licenses']:
                license_data.append([
                    lic.get('license_type', 'N/A'),
                    lic.get('license_number', 'Not extracted'),
                    lic.get('validity', 'Not extracted')
                ])
            
            table = Table(license_data, colWidths=[2*inch, 2.5*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Footer
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#64748B'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph("___________________________________________________________________________", footer_style))
        elements.append(Paragraph("This report is confidential and for authorized use only.", footer_style))
        elements.append(Paragraph("Generated by FinTrust Intelligence - Vendor Due Diligence Platform", footer_style))
        
        # Build PDF
        doc.build(elements)
        
        return FileResponse(
            path=str(file_path),
            filename=f"VendorReport_{pan}_{datetime.now().strftime('%Y%m%d')}.pdf",
            media_type="application/pdf"
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