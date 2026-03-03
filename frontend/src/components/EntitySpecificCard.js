import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { User, Building2, Users, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

const EntitySpecificCard = ({ vendor }) => {
  const registrationType = vendor.registration_type;

  // Render based on registration type
  if (registrationType === 'UDYAM' && vendor.udyam_data) {
    return (
      <Card data-testid="udyam-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5 text-purple-600" />
            Udyam Registration (MSME)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm text-slate-600">Udyam Registration Number (URN)</p>
            <p data-testid="urn" className="font-mono text-base font-medium text-slate-900">
              {vendor.udyam_data.urn}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-slate-600">Registration Date</p>
              <p className="text-base font-medium text-slate-900">
                {vendor.udyam_data.registration_date}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600">MSME Category</p>
              <Badge className="bg-purple-50 text-purple-700 border-purple-200">
                {vendor.udyam_data.msme_category}
              </Badge>
            </div>
          </div>
          <div>
            <p className="text-sm text-slate-600 flex items-center gap-1">
              <User className="h-3 w-3" /> Owner/Authorized Signatory
            </p>
            <p data-testid="owner-name" className="text-base font-medium text-slate-900 mt-1">
              {vendor.udyam_data.owner_name}
            </p>
          </div>
          {vendor.udyam_data.name_match_score && (
            <div>
              <p className="text-sm text-slate-600">Name Match Score</p>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex-1 bg-slate-100 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${vendor.udyam_data.name_match_score}%` }}
                  ></div>
                </div>
                <span className="text-sm font-semibold text-slate-900">
                  {vendor.udyam_data.name_match_score}%
                </span>
                {vendor.udyam_data.name_match_score >= 80 ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  if (registrationType === 'PARTNERSHIP_EPFO' && vendor.partnership_data) {
    return (
      <Card data-testid="partnership-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5 text-indigo-600" />
            Partnership Firm Registration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm text-slate-600">EPFO Establishment Code</p>
            <p data-testid="epfo-code" className="font-mono text-base font-medium text-slate-900">
              {vendor.partnership_data.epfo_establishment_code}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-600">Establishment Name</p>
            <p className="text-base font-medium text-slate-900">
              {vendor.partnership_data.establishment_name}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-600">Earliest GST Registration Date (Proxy for Incorporation)</p>
            <p className="text-base font-medium text-slate-900">
              {vendor.partnership_data.earliest_gst_date}
            </p>
          </div>
          {vendor.partnership_data.partners && vendor.partnership_data.partners.length > 0 && (
            <div>
              <p className="text-sm text-slate-600 flex items-center gap-1 mb-2">
                <Users className="h-3 w-3" /> Partners
              </p>
              <div className="space-y-1">
                {vendor.partnership_data.partners.map((partner, idx) => (
                  <p key={idx} data-testid={`partner-${idx}`} className="text-sm text-slate-700 pl-4 border-l-2 border-slate-200">
                    {partner}
                  </p>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  if (
    (registrationType === 'TRUST_SOCIETY' || registrationType === 'TRUST_SOCIETY_PENDING') &&
    vendor.trust_society_data
  ) {
    return (
      <Card data-testid="trust-society-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-teal-600" />
            {vendor.trust_society_data.registration_type} Registration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {registrationType === 'TRUST_SOCIETY_PENDING' ? (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="text-sm text-amber-800 font-medium">
                Document Upload Required
              </p>
              <p className="text-xs text-amber-600 mt-1">
                Please upload Trust Deed or Society Registration Certificate for verification
              </p>
            </div>
          ) : (
            <>
              {vendor.trust_society_data.registration_number && (
                <div>
                  <p className="text-sm text-slate-600">Registration Number</p>
                  <p data-testid="trust-reg-number" className="font-mono text-base font-medium text-slate-900">
                    {vendor.trust_society_data.registration_number}
                  </p>
                </div>
              )}
              {vendor.trust_society_data.date_of_formation && (
                <div>
                  <p className="text-sm text-slate-600">Date of Formation</p>
                  <p className="text-base font-medium text-slate-900">
                    {vendor.trust_society_data.date_of_formation}
                  </p>
                </div>
              )}
              {vendor.trust_society_data.ngo_darpan_id && (
                <div>
                  <p className="text-sm text-slate-600">NGO Darpan ID</p>
                  <p className="font-mono text-base font-medium text-slate-900">
                    {vendor.trust_society_data.ngo_darpan_id}
                  </p>
                </div>
              )}
              {vendor.trust_society_data.trustees_members && vendor.trust_society_data.trustees_members.length > 0 && (
                <div>
                  <p className="text-sm text-slate-600 flex items-center gap-1 mb-2">
                    <Users className="h-3 w-3" /> Trustees/Members
                  </p>
                  <div className="space-y-1">
                    {vendor.trust_society_data.trustees_members.map((member, idx) => (
                      <p key={idx} data-testid={`member-${idx}`} className="text-sm text-slate-700 pl-4 border-l-2 border-slate-200">
                        {member}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    );
  }

  return null;
};

export default EntitySpecificCard;