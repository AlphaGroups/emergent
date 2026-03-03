import httpx
import logging
from typing import Optional, Dict, Any, List
from config import settings
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

def calculate_name_match_score(name1: str, name2: str) -> float:
    """Calculate similarity score between two names (0-100)"""
    if not name1 or not name2:
        return 0.0
    
    # Normalize names
    name1 = name1.lower().strip()
    name2 = name2.lower().strip()
    
    # Use SequenceMatcher for fuzzy matching
    ratio = SequenceMatcher(None, name1, name2).ratio()
    return round(ratio * 100, 2)

class CashfreeService:
    def __init__(self):
        self.client_id = settings.CASHFREE_CLIENT_ID
        self.client_secret = settings.CASHFREE_CLIENT_SECRET
        self.base_url = "https://payout-api.cashfree.com/payout/v1.2"
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-client-id": self.client_id,
            "x-client-secret": self.client_secret
        }
    
    async def verify_gstin(self, gstin: str, business_name: Optional[str] = None) -> Dict[str, Any]:
        """Verify GSTIN and fetch business details"""
        try:
            # Mock response for sandbox/testing
            # In production, replace with actual Cashfree API call
            pan = gstin[2:12]  # Extract PAN from GSTIN
            
            mock_response = {
                "gstin": gstin,
                "legal_name": f"Sample Business Legal Name",
                "trade_name": f"Sample Trade Name",
                "entity_type": self._get_entity_type_from_pan(pan),
                "pan": pan,
                "registered_address": "123 Business Street, City, State - 123456",
                "status": "Active",
                "state": gstin[:2]
            }
            
            logger.info(f"GST verification successful for {gstin}")
            return mock_response
            
        except Exception as e:
            logger.error(f"GST verification failed: {str(e)}")
            raise ValueError(f"GST verification failed: {str(e)}")
    
    def _get_entity_type_from_pan(self, pan: str) -> str:
        """Determine entity type from PAN character 4"""
        if len(pan) < 4:
            return "Unknown"
        
        char4 = pan[3].upper()
        entity_map = {
            'C': 'Company',
            'P': 'Proprietorship',
            'F': 'Partnership',
            'L': 'LLP',
            'H': 'HUF',
            'T': 'Trust'
        }
        return entity_map.get(char4, 'Unknown')
    
    async def verify_cin(self, pan: str) -> Dict[str, Any]:
        """Fetch CIN and MCA data for Companies/LLPs"""
        try:
            # Mock MCA response
            mock_response = {
                "cin": f"U{pan[5:9]}MH2020PTC123456",
                "company_name": "Sample Private Limited",
                "incorporation_year": "2020",
                "directors": [
                    "Rajesh Kumar",
                    "Priya Sharma",
                    "Amit Patel"
                ],
                "company_status": "Active"
            }
            
            logger.info(f"CIN verification successful for PAN {pan}")
            return mock_response
            
        except Exception as e:
            logger.error(f"CIN verification failed: {str(e)}")
            raise ValueError(f"CIN verification failed: {str(e)}")
    
    async def verify_pan_udyam(self, pan: str) -> Dict[str, Any]:
        """Verify PAN and fetch Udyam Registration Number for Sole Proprietorship"""
        try:
            # Mock Udyam URN response
            mock_response = {
                "pan": pan,
                "urn": f"UDYAM-MH-{pan[5:9]}-{pan[7:10]}",
                "is_registered": True,
                "name_on_pan": "Sample Proprietor Name"
            }
            
            logger.info(f"PAN-Udyam verification successful for PAN {pan}")
            return mock_response
            
        except Exception as e:
            logger.error(f"PAN-Udyam verification failed: {str(e)}")
            raise ValueError(f"PAN-Udyam verification failed: {str(e)}")
    
    async def verify_udyam(self, urn: str, pan: str) -> Dict[str, Any]:
        """Verify Udyam Registration and fetch MSME details"""
        try:
            # Mock Udyam details response
            mock_response = {
                "urn": urn,
                "business_name": "Sample Proprietorship Business",
                "owner_name": "Sample Proprietor Name",
                "registration_date": "2021-05-15",
                "msme_category": "Micro",
                "major_activity": "Manufacturing",
                "status": "Active",
                "name_match_score": 95.5
            }
            
            logger.info(f"Udyam verification successful for URN {urn}")
            return mock_response
            
        except Exception as e:
            logger.error(f"Udyam verification failed: {str(e)}")
            raise ValueError(f"Udyam verification failed: {str(e)}")
    
    async def verify_pan_gstin_earliest(self, pan: str) -> Dict[str, Any]:
        """Fetch earliest GST registration date for Partnership firms"""
        try:
            all_gstins = await self.get_all_gstins_by_pan(pan)
            
            # Find earliest registration (mock date for now)
            earliest_date = "2018-07-01"
            
            mock_response = {
                "pan": pan,
                "earliest_gst_date": earliest_date,
                "total_registrations": len(all_gstins),
                "status": "Active"
            }
            
            logger.info(f"Earliest GST date found for PAN {pan}: {earliest_date}")
            return mock_response
            
        except Exception as e:
            logger.error(f"PAN-GSTIN earliest date fetch failed: {str(e)}")
            raise ValueError(f"Failed to fetch earliest GST date: {str(e)}")
    
    async def verify_epfo_establishment(self, pan: str) -> Dict[str, Any]:
        """Fetch EPFO establishment details using PAN"""
        try:
            # Mock EPFO response
            mock_response = {
                "establishment_code": f"MH/MUM/{pan[5:10]}",
                "establishment_name": "Sample Partnership Firm",
                "registration_date": "2018-08-15",
                "status": "Active",
                "covered_employees": 15,
                "address": "123 Partnership Street, Mumbai"
            }
            
            logger.info(f"EPFO establishment verification successful for PAN {pan}")
            return mock_response
            
        except Exception as e:
            logger.error(f"EPFO verification failed: {str(e)}")
            raise ValueError(f"EPFO verification failed: {str(e)}")
    
    async def verify_trust_society_ocr(self, document_type: str, file_path: str) -> Dict[str, Any]:
        """Extract trust/society details using OCR"""
        try:
            # Mock OCR response
            mock_response = {
                "document_type": document_type,
                "registration_number": f"REG/{document_type[:4].upper()}/2019/12345",
                "date_of_formation": "2019-03-20",
                "entity_name": "Sample Trust/Society Name",
                "registration_authority": "Registrar of Societies",
                "trustees_members": [
                    "Member 1 Name",
                    "Member 2 Name",
                    "Member 3 Name"
                ],
                "ngo_darpan_id": None
            }
            
            logger.info(f"Trust/Society OCR verification successful")
            return mock_response
            
        except Exception as e:
            logger.error(f"Trust/Society OCR verification failed: {str(e)}")
            raise ValueError(f"OCR verification failed: {str(e)}")
    
    async def get_all_gstins_by_pan(self, pan: str) -> List[Dict[str, Any]]:
        """Fetch all GSTINs associated with a PAN"""
        try:
            # Mock response with multiple GSTINs
            mock_gstins = [
                {
                    "gstin": f"27{pan}1Z5",
                    "state": "Maharashtra",
                    "filing_status": "Regular",
                    "status": "Active"
                },
                {
                    "gstin": f"29{pan}1Z5",
                    "state": "Karnataka",
                    "filing_status": "Regular",
                    "status": "Active"
                },
                {
                    "gstin": f"06{pan}1Z5",
                    "state": "Haryana",
                    "filing_status": "Quarterly",
                    "status": "Active"
                }
            ]
            
            logger.info(f"Retrieved {len(mock_gstins)} GSTINs for PAN {pan}")
            return mock_gstins
            
        except Exception as e:
            logger.error(f"Failed to fetch GSTINs: {str(e)}")
            raise ValueError(f"Failed to fetch GSTINs: {str(e)}")
    
    async def initiate_otp(self, mobile: str) -> Dict[str, Any]:
        """Initiate OTP for financial data unlock"""
        try:
            # Mock OTP initiation
            mock_response = {
                "otp_id": "otp_123456789",
                "message": "OTP sent successfully",
                "mobile": mobile
            }
            
            logger.info(f"OTP initiated for mobile {mobile}")
            return mock_response
            
        except Exception as e:
            logger.error(f"OTP initiation failed: {str(e)}")
            raise ValueError(f"OTP initiation failed: {str(e)}")
    
    async def verify_otp_and_fetch_financials(self, otp_id: str, otp: str, pan: str) -> Dict[str, Any]:
        """Verify OTP and fetch financial data"""
        try:
            # Mock financial data
            mock_response = {
                "itr_filing_status": "Filed",
                "turnover_year_1": 15000000.00,
                "turnover_year_2": 12500000.00,
                "turnover_year_3": 10000000.00,
                "epf_number": "MH/12345/123456",
                "esic_number": "12345678901234567",
                "pf_number": "MH/MUM/123456"
            }
            
            logger.info(f"Financial data fetched for PAN {pan}")
            return mock_response
            
        except Exception as e:
            logger.error(f"OTP verification failed: {str(e)}")
            raise ValueError(f"OTP verification failed: {str(e)}")

cashfree_service = CashfreeService()