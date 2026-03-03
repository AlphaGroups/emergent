import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Building2, MapPin, User, ShieldCheck, Lock, Unlock, Download, Upload, CheckCircle2, AlertCircle } from 'lucide-react';
import { getVendorByPAN, initiateOTP, verifyOTP, uploadLicense, downloadReport } from '../services/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const VendorProfile = () => {
  const { pan } = useParams();
  const navigate = useNavigate();
  const [vendor, setVendor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [mobile, setMobile] = useState('');
  const [otp, setOtp] = useState('');
  const [otpId, setOtpId] = useState(null);
  const [otpStep, setOtpStep] = useState('mobile'); // 'mobile' or 'otp'
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [licenseType, setLicenseType] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  const loadVendor = useCallback(async () => {
    try {
      const data = await getVendorByPAN(pan);
      setVendor(data);
    } catch (err) {
      setError('Failed to load vendor details');
    } finally {
      setLoading(false);
    }
  }, [pan]);

  useEffect(() => {
    loadVendor();
  }, [loadVendor]);

  const handleInitiateOTP = async () => {
    try {
      const result = await initiateOTP(mobile, pan);
      setOtpId(result.otp_id);
      setOtpStep('otp');
    } catch (err) {
      alert('Failed to send OTP');
    }
  };

  const handleVerifyOTP = async () => {
    try {
      await verifyOTP(otpId, otp, pan);
      setShowOTPModal(false);
      loadVendor(); // Reload to show unlocked data
    } catch (err) {
      alert('Invalid OTP');
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile || !licenseType) return;

    try {
      await uploadLicense(pan, licenseType, selectedFile);
      setUploadModalOpen(false);
      setLicenseType('');
      setSelectedFile(null);
      loadVendor();
    } catch (err) {
      alert('Upload failed');
    }
  };

  const handleDownloadReport = async () => {
    try {
      const blob = await downloadReport(pan);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vendor_report_${pan}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert('Failed to download report');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !vendor) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <p className="text-slate-600">{error || 'Vendor not found'}</p>
          <Button onClick={() => navigate('/dashboard')} className="mt-4">Back to Dashboard</Button>
        </div>
      </div>
    );
  }

  const isFinancialsUnlocked = vendor.financial_history?.unlocked_at;

  const turnoverData = isFinancialsUnlocked ? [
    { year: 'Year 3', amount: vendor.financial_history.turnover_year_3 / 100000 },
    { year: 'Year 2', amount: vendor.financial_history.turnover_year_2 / 100000 },
    { year: 'Year 1', amount: vendor.financial_history.turnover_year_1 / 100000 },
  ] : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              data-testid="back-button"
              variant="ghost"
              onClick={() => navigate('/dashboard')}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" /> Back
            </Button>
            <div className="h-8 w-px bg-slate-200"></div>
            <h1 className="text-xl font-bold text-slate-900 font-heading">Vendor Due Diligence</h1>
          </div>
          <Button
            data-testid="download-report-button"
            onClick={handleDownloadReport}
            className="gap-2 bg-blue-600 hover:bg-blue-700"
          >
            <Download className="h-4 w-4" /> Download Report
          </Button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Phase 1: Identity & Corporate */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 mb-4">
            <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">
              <CheckCircle2 className="h-3 w-3 mr-1" /> Phase 1: Instant Verification
            </Badge>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Corporate Identity */}
            <Card data-testid="corporate-identity-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-blue-600" />
                  Corporate Identity
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-slate-600">Legal Name</p>
                  <p data-testid="legal-name" className="text-lg font-semibold text-slate-900">{vendor.gst_details?.legal_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-600">Trade Name</p>
                  <p className="text-base font-medium text-slate-900">{vendor.gst_details?.trade_name}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-600">Entity Type</p>
                    <p className="text-base font-medium text-slate-900">{vendor.gst_details?.entity_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">PAN</p>
                    <p data-testid="pan" className="font-mono text-base font-medium text-slate-900">{vendor.pan}</p>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-slate-600 flex items-center gap-1">
                    <MapPin className="h-3 w-3" /> Registered Address
                  </p>
                  <p className="text-sm text-slate-700 mt-1">{vendor.gst_details?.registered_address}</p>
                </div>
                <Badge data-testid="status-badge" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                  <ShieldCheck className="h-3 w-3 mr-1" /> {vendor.gst_details?.status}
                </Badge>
              </CardContent>
            </Card>

            {/* MCA Data */}
            {vendor.mca_data && (
              <Card data-testid="mca-data-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5 text-indigo-600" />
                    MCA Registration
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm text-slate-600">CIN</p>
                    <p data-testid="cin" className="font-mono text-base font-medium text-slate-900">{vendor.mca_data.cin}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Company Name</p>
                    <p className="text-base font-medium text-slate-900">{vendor.mca_data.company_name}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-slate-600">Incorporation Year</p>
                      <p className="text-base font-medium text-slate-900">{vendor.mca_data.incorporation_year}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Status</p>
                      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">{vendor.mca_data.company_status}</Badge>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 flex items-center gap-1 mb-2">
                      <User className="h-3 w-3" /> Directors
                    </p>
                    <div className="space-y-1">
                      {vendor.mca_data.directors?.map((director, idx) => (
                        <p key={idx} data-testid={`director-${idx}`} className="text-sm text-slate-700 pl-4 border-l-2 border-slate-200">{director}</p>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </motion.div>

        {/* Phase 2: The Network */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <div className="flex items-center gap-2 mb-4">
            <Badge className="bg-blue-50 text-blue-700 border-blue-200">
              <CheckCircle2 className="h-3 w-3 mr-1" /> Phase 2: Network Analysis
            </Badge>
          </div>

          <Card data-testid="network-card">
            <CardHeader>
              <CardTitle>Multi-State GST Registrations</CardTitle>
              <CardDescription>All GSTINs associated with PAN {vendor.pan}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-4">
                {vendor.all_gstins?.map((gstin, idx) => (
                  <div key={idx} data-testid={`gstin-card-${idx}`} className="border border-slate-200 rounded-lg p-4 hover:border-blue-300 transition-all">
                    <p className="font-mono text-sm font-medium text-slate-900 mb-2">{gstin.gstin}</p>
                    <div className="space-y-1">
                      <p className="text-xs text-slate-600">State: <span className="font-medium text-slate-900">{gstin.state}</span></p>
                      <p className="text-xs text-slate-600">Filing: <span className="font-medium text-slate-900">{gstin.filing_status}</span></p>
                      <Badge variant="outline" className="text-xs">{gstin.status}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Phase 3: Financials */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <div className="flex items-center gap-2 mb-4">
            <Badge className={isFinancialsUnlocked ? "bg-purple-50 text-purple-700 border-purple-200" : "bg-slate-50 text-slate-600 border-slate-200"}>
              {isFinancialsUnlocked ? <Unlock className="h-3 w-3 mr-1" /> : <Lock className="h-3 w-3 mr-1" />}
              Phase 3: Financial Insights {!isFinancialsUnlocked && '(Locked)'}
            </Badge>
          </div>

          <div className="relative">
            {!isFinancialsUnlocked && (
              <div className="absolute inset-0 bg-slate-900/20 backdrop-blur-sm z-10 rounded-xl flex items-center justify-center">
                <Card className="max-w-md">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lock className="h-5 w-5 text-amber-600" />
                      Unlock Financial Data
                    </CardTitle>
                    <CardDescription>Verify your mobile number with OTP to access financial insights</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      data-testid="unlock-financials-button"
                      onClick={() => setShowOTPModal(true)}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                    >
                      <Unlock className="h-4 w-4 mr-2" /> Unlock Financials
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}

            <div className={!isFinancialsUnlocked ? 'blur-sm pointer-events-none' : ''}>
              <div className="grid md:grid-cols-2 gap-6">
                {/* Turnover Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle>Annual Turnover (Last 3 Years)</CardTitle>
                    <CardDescription>Amount in Lakhs (₹)</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={turnoverData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="year" stroke="#64748b" />
                        <YAxis stroke="#64748b" />
                        <Tooltip />
                        <Bar dataKey="amount" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* Financial Details */}
                <Card>
                  <CardHeader>
                    <CardTitle>Financial & Compliance Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="text-sm text-slate-600">ITR Filing Status</p>
                      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 mt-1">
                        <CheckCircle2 className="h-3 w-3 mr-1" /> {vendor.financial_history?.itr_filing_status || 'N/A'}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm font-semibold text-slate-900">EPF/ESIC Registration</p>
                      <div className="grid grid-cols-1 gap-2">
                        <div className="border border-slate-200 rounded-lg p-2">
                          <p className="text-xs text-slate-600">EPF Number</p>
                          <p data-testid="epf-number" className="font-mono text-sm font-medium text-slate-900">{vendor.financial_history?.epf_number || 'N/A'}</p>
                        </div>
                        <div className="border border-slate-200 rounded-lg p-2">
                          <p className="text-xs text-slate-600">ESIC Number</p>
                          <p className="font-mono text-sm font-medium text-slate-900">{vendor.financial_history?.esic_number || 'N/A'}</p>
                        </div>
                        <div className="border border-slate-200 rounded-lg p-2">
                          <p className="text-xs text-slate-600">PF Number</p>
                          <p className="font-mono text-sm font-medium text-slate-900">{vendor.financial_history?.pf_number || 'N/A'}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </motion.div>

        {/* License Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle>License Documents</CardTitle>
            <CardDescription>Upload Class A/B licenses with OCR extraction</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {vendor.licenses && vendor.licenses.length > 0 ? (
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  {vendor.licenses.map((license, idx) => (
                    <div key={idx} className="border border-slate-200 rounded-lg p-4">
                      <p className="font-semibold text-slate-900 mb-2">{license.license_type}</p>
                      {license.license_number && (
                        <p className="text-sm text-slate-600">Number: <span className="font-mono">{license.license_number}</span></p>
                      )}
                      {license.validity && (
                        <p className="text-sm text-slate-600">Validity: {license.validity}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No licenses uploaded yet</p>
              )}
              <Button
                data-testid="upload-license-button"
                onClick={() => setUploadModalOpen(true)}
                variant="outline"
                className="gap-2"
              >
                <Upload className="h-4 w-4" /> Upload License
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* OTP Modal */}
      <Dialog open={showOTPModal} onOpenChange={setShowOTPModal}>
        <DialogContent data-testid="otp-modal">
          <DialogHeader>
            <DialogTitle>Unlock Financial Data</DialogTitle>
            <DialogDescription>
              {otpStep === 'mobile'
                ? 'Enter your mobile number to receive OTP'
                : 'Enter the OTP sent to your mobile'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {otpStep === 'mobile' ? (
              <>
                <Input
                  data-testid="mobile-input"
                  type="tel"
                  placeholder="Enter 10-digit mobile number"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                  maxLength={10}
                />
                <Button
                  data-testid="send-otp-button"
                  onClick={handleInitiateOTP}
                  disabled={mobile.length !== 10}
                  className="w-full"
                >
                  Send OTP
                </Button>
              </>
            ) : (
              <>
                <Input
                  data-testid="otp-input"
                  type="text"
                  placeholder="Enter 6-digit OTP"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  maxLength={6}
                />
                <Button
                  data-testid="verify-otp-button"
                  onClick={handleVerifyOTP}
                  disabled={otp.length !== 6}
                  className="w-full"
                >
                  Verify & Unlock
                </Button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Upload Modal */}
      <Dialog open={uploadModalOpen} onOpenChange={setUploadModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload License Document</DialogTitle>
            <DialogDescription>Upload PDF or Image. OCR will extract license details.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              data-testid="license-type-input"
              type="text"
              placeholder="License Type (e.g., Class A, FSSAI)"
              value={licenseType}
              onChange={(e) => setLicenseType(e.target.value)}
            />
            <Input
              data-testid="file-input"
              type="file"
              accept="image/*,application/pdf"
              onChange={(e) => setSelectedFile(e.target.files[0])}
            />
            <Button
              data-testid="upload-file-button"
              onClick={handleFileUpload}
              disabled={!licenseType || !selectedFile}
              className="w-full"
            >
              <Upload className="h-4 w-4 mr-2" /> Upload
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default VendorProfile;