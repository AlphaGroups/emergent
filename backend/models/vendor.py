from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class GSTDetails(BaseModel):
    gstin: str
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    entity_type: Optional[str] = None
    pan: Optional[str] = None
    registered_address: Optional[str] = None
    status: Optional[str] = None
    state: Optional[str] = None
    filing_status: Optional[str] = None
    verified_at: Optional[datetime] = None

class MCAData(BaseModel):
    cin: Optional[str] = None
    company_name: Optional[str] = None
    incorporation_year: Optional[str] = None
    directors: Optional[List[str]] = []
    company_status: Optional[str] = None
    verified_at: Optional[datetime] = None

class UdyamData(BaseModel):
    urn: Optional[str] = None  # Udyam Registration Number
    registration_date: Optional[str] = None
    msme_category: Optional[str] = None  # Micro/Small/Medium
    owner_name: Optional[str] = None
    business_name: Optional[str] = None
    name_match_score: Optional[float] = None
    verified_at: Optional[datetime] = None

class PartnershipData(BaseModel):
    earliest_gst_date: Optional[str] = None
    epfo_establishment_code: Optional[str] = None
    establishment_name: Optional[str] = None
    partners: Optional[List[str]] = []
    verified_at: Optional[datetime] = None

class TrustSocietyData(BaseModel):
    registration_number: Optional[str] = None
    registration_type: Optional[str] = None  # "Trust Deed", "Society Registration", "NGO Darpan"
    date_of_formation: Optional[str] = None
    ngo_darpan_id: Optional[str] = None
    trustees_members: Optional[List[str]] = []
    verified_at: Optional[datetime] = None

class FinancialHistory(BaseModel):
    itr_filing_status: Optional[str] = None
    turnover_year_1: Optional[float] = None
    turnover_year_2: Optional[float] = None
    turnover_year_3: Optional[float] = None
    epf_number: Optional[str] = None
    esic_number: Optional[str] = None
    pf_number: Optional[str] = None
    unlocked_at: Optional[datetime] = None

class LicenseDocument(BaseModel):
    license_type: str
    license_number: Optional[str] = None
    validity: Optional[str] = None
    file_url: Optional[str] = None
    uploaded_at: Optional[datetime] = None

class Vendor(BaseModel):
    pan: str = Field(..., description="PAN as unique identifier")
    user_id: str
    registration_type: Optional[str] = None  # "MCA", "UDYAM", "EPFO", "GST_PROXY", "TRUST_SOCIETY"
    gst_details: Optional[GSTDetails] = None
    all_gstins: Optional[List[GSTDetails]] = []
    mca_data: Optional[MCAData] = None
    udyam_data: Optional[UdyamData] = None
    partnership_data: Optional[PartnershipData] = None
    trust_society_data: Optional[TrustSocietyData] = None
    financial_history: Optional[FinancialHistory] = None
    licenses: Optional[List[LicenseDocument]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)