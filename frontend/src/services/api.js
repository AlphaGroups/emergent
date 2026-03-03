import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth APIs
export const exchangeSession = async (sessionId) => {
  const response = await api.post('/auth/session', { session_id: sessionId });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

export const logout = async () => {
  const response = await api.post('/auth/logout');
  return response.data;
};

// Vendor APIs
export const verifyGSTIN = async (gstin, businessName = null) => {
  const response = await api.post('/verify/gstin', {
    gstin,
    business_name: businessName,
  });
  return response.data;
};

export const initiateOTP = async (mobile, pan) => {
  const response = await api.post('/verify/initiate-otp', { mobile, pan });
  return response.data;
};

export const verifyOTP = async (otpId, otp, pan) => {
  const response = await api.post('/verify/verify-otp', {
    otp_id: otpId,
    otp,
    pan,
  });
  return response.data;
};

export const getAllVendors = async () => {
  const response = await api.get('/vendors');
  return response.data;
};

export const getVendorByPAN = async (pan) => {
  const response = await api.get(`/vendors/${pan}`);
  return response.data;
};

export const uploadLicense = async (pan, licenseType, file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('license_type', licenseType);

  const response = await api.post(`/vendors/${pan}/upload-license?license_type=${licenseType}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const downloadReport = async (pan) => {
  const response = await api.get(`/vendors/${pan}/download-report`, {
    responseType: 'blob',
  });
  return response.data;
};

export default api;