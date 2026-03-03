import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Search, Building2, ShieldCheck, TrendingUp } from 'lucide-react';
import { verifyGSTIN, getAllVendors } from '../services/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import VendorCard from '../components/VendorCard';

const Dashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(location.state?.user || null);
  const [gstin, setGstin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recentVendors, setRecentVendors] = useState([]);

  useEffect(() => {
    loadRecentVendors();
  }, []);

  const loadRecentVendors = async () => {
    try {
      const data = await getAllVendors();
      setRecentVendors(data.vendors || []);
    } catch (err) {
      console.error('Failed to load vendors:', err);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!gstin || gstin.length !== 15) {
      setError('Please enter a valid 15-character GSTIN');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await verifyGSTIN(gstin);
      const pan = result.gst_details.pan;
      navigate(`/vendor/${pan}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVendorClick = (pan) => {
    navigate(`/vendor/${pan}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Building2 className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 font-heading">FinTrust Intelligence</h1>
          </div>
          <div className="flex items-center gap-4">
            {user && (
              <div className="flex items-center gap-3">
                {user.picture && (
                  <img src={user.picture} alt={user.name} className="h-10 w-10 rounded-full border-2 border-slate-200" />
                )}
                <div className="text-right hidden md:block">
                  <p className="text-sm font-semibold text-slate-900">{user.name}</p>
                  <p className="text-xs text-slate-500">{user.email}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Hero Search Section */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center mb-8">
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4 font-heading tracking-tight">
            Vendor Due Diligence Made Simple
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Enter a GSTIN to instantly access corporate identity, network analysis, and financial insights
          </p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="max-w-3xl mx-auto mb-8">
          <div className="relative">
            <Input
              data-testid="gstin-search-input"
              type="text"
              placeholder="Enter 15-digit GSTIN (e.g., 27AABCU9603R1ZX)"
              value={gstin}
              onChange={(e) => setGstin(e.target.value.toUpperCase())}
              className="h-14 text-lg px-6 pr-32 rounded-full shadow-sm border-slate-200 focus-visible:ring-blue-600"
              maxLength={15}
            />
            <Button
              data-testid="search-button"
              type="submit"
              disabled={loading}
              className="absolute right-2 top-2 h-10 px-6 rounded-full bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <><Search className="h-4 w-4 mr-2" /> Search</>
              )}
            </Button>
          </div>
          {error && (
            <p data-testid="error-message" className="text-red-600 text-sm mt-2 text-center">{error}</p>
          )}
        </form>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all">
            <div className="flex items-center gap-4">
              <div className="bg-emerald-100 p-3 rounded-lg">
                <ShieldCheck className="h-6 w-6 text-emerald-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{recentVendors.length}</p>
                <p className="text-sm text-slate-600">Vendors Verified</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all">
            <div className="flex items-center gap-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <Building2 className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">Instant</p>
                <p className="text-sm text-slate-600">Corporate Data</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all">
            <div className="flex items-center gap-4">
              <div className="bg-purple-100 p-3 rounded-lg">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">3 Years</p>
                <p className="text-sm text-slate-600">Financial History</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Vendors */}
        {recentVendors.length > 0 && (
          <div>
            <h3 className="text-2xl font-semibold text-slate-900 mb-6 font-heading">Recent Verifications</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recentVendors.map((vendor) => (
                <VendorCard
                  key={vendor.pan}
                  vendor={vendor}
                  onClick={() => handleVendorClick(vendor.pan)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;