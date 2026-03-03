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
    gst_details: Optional[GSTDetails] = None
    all_gstins: Optional[List[GSTDetails]] = []
    mca_data: Optional[MCAData] = None
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