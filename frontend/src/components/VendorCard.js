import React from 'react';
import { Building2, MapPin, ShieldCheck, AlertCircle } from 'lucide-react';
import { Badge } from './ui/badge';

const VendorCard = ({ vendor, onClick }) => {
  const hasFinancials = vendor.financial_history?.unlocked_at;
  const hasMCA = vendor.mca_data?.cin;

  return (
    <div
      data-testid="vendor-card"
      onClick={onClick}
      className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all cursor-pointer hover:border-blue-200"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="bg-blue-100 p-2 rounded-lg">
            <Building2 className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 line-clamp-1">
              {vendor.gst_details?.legal_name || 'Unknown Business'}
            </h3>
            <p className="text-xs text-slate-500 font-mono">{vendor.pan}</p>
          </div>
        </div>
        <Badge
          variant={vendor.gst_details?.status === 'Active' ? 'default' : 'secondary'}
          className="bg-emerald-50 text-emerald-700 border-emerald-200"
        >
          <ShieldCheck className="h-3 w-3 mr-1" />
          {vendor.gst_details?.status || 'Unknown'}
        </Badge>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex items-start gap-2 text-sm">
          <MapPin className="h-4 w-4 text-slate-400 mt-0.5" />
          <p className="text-slate-600 line-clamp-2">
            {vendor.gst_details?.registered_address || 'No address available'}
          </p>
        </div>
      </div>

      <div className="flex gap-2 pt-4 border-t border-slate-100">
        {hasMCA && (
          <Badge variant="outline" className="text-xs">
            MCA Verified
          </Badge>
        )}
        <Badge variant="outline" className="text-xs">
          {vendor.all_gstins?.length || 0} GSTINs
        </Badge>
        {hasFinancials ? (
          <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700 border-purple-200">
            Financials Unlocked
          </Badge>
        ) : (
          <Badge variant="outline" className="text-xs bg-slate-50 text-slate-600">
            Financials Locked
          </Badge>
        )}
      </div>
    </div>
  );
};

export default VendorCard;