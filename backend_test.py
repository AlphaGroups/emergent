#!/usr/bin/env python3
import requests
import sys
import json
from datetime import datetime

class UnifiedBizAPITester:
    def __init__(self, base_url="https://unified-biz-verify.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session_token = "test_session_1772530102010"
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        
        # Add authorization header
        test_headers['Authorization'] = f'Bearer {self.session_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_auth_me(self):
        """Test /auth/me endpoint"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        if success and 'user_id' in response:
            self.user_id = response['user_id']
            print(f"   User ID: {self.user_id}")
        return success

    def test_gstin_verification(self):
        """Test GSTIN verification"""
        success, response = self.run_test(
            "GSTIN Verification",
            "POST",
            "verify/gstin",
            200,
            data={"gstin": "27AABCU9603R1ZX", "business_name": "Test Business"}
        )
        return success, response

    def test_get_vendors(self):
        """Test get all vendors"""
        success, response = self.run_test(
            "Get All Vendors",
            "GET",
            "vendors",
            200
        )
        return success, response

    def test_get_vendor_by_pan(self, pan):
        """Test get vendor by PAN"""
        success, response = self.run_test(
            f"Get Vendor by PAN ({pan})",
            "GET",
            f"vendors/{pan}",
            200
        )
        return success, response

    def test_initiate_otp(self, pan):
        """Test OTP initiation"""
        success, response = self.run_test(
            "Initiate OTP",
            "POST",
            "verify/initiate-otp",
            200,
            data={"mobile": "9876543210", "pan": pan}
        )
        return success, response

    def test_verify_otp(self, otp_id, pan):
        """Test OTP verification"""
        success, response = self.run_test(
            "Verify OTP",
            "POST",
            "verify/verify-otp",
            200,
            data={"otp_id": otp_id, "otp": "123456", "pan": pan}
        )
        return success, response

    def test_download_report(self, pan):
        """Test report download"""
        url = f"{self.base_url}/vendors/{pan}/download-report"
        headers = {'Authorization': f'Bearer {self.session_token}'}
        
        print(f"\n🔍 Testing Download Report for PAN {pan}...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            self.tests_run += 1
            
            if response.status_code == 200:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                return True
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

def main():
    print("🚀 Starting Unified Business Intelligence Dashboard API Tests")
    print("=" * 60)
    
    tester = UnifiedBizAPITester()
    
    # Test 1: Authentication
    print("\n📋 PHASE 1: Authentication Testing")
    if not tester.test_auth_me():
        print("❌ Authentication failed, stopping tests")
        return 1

    # Test 2: GSTIN Verification
    print("\n📋 PHASE 2: GSTIN Verification Testing")
    gstin_success, gstin_data = tester.test_gstin_verification()
    pan = None
    if gstin_success and gstin_data and 'gst_details' in gstin_data:
        pan = gstin_data['gst_details'].get('pan')
        print(f"   Extracted PAN: {pan}")

    # Test 3: Vendor Management
    print("\n📋 PHASE 3: Vendor Management Testing")
    tester.test_get_vendors()
    
    if pan:
        tester.test_get_vendor_by_pan(pan)

    # Test 4: OTP Flow
    print("\n📋 PHASE 4: OTP Flow Testing")
    if pan:
        otp_success, otp_data = tester.test_initiate_otp(pan)
        if otp_success and otp_data and 'otp_id' in otp_data:
            otp_id = otp_data['otp_id']
            tester.test_verify_otp(otp_id, pan)

    # Test 5: Report Download
    print("\n📋 PHASE 5: Report Download Testing")
    if pan:
        tester.test_download_report(pan)

    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())