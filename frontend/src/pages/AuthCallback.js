import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { exchangeSession } from '../services/api';

const AuthCallback = () => {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);
  const [error, setError] = React.useState(null);

  useEffect(() => {
    // CRITICAL: Prevent duplicate processing under StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      try {
        // Check for error in URL first
        const searchParams = new URLSearchParams(window.location.search);
        const errorParam = searchParams.get('error');
        const errorDescription = searchParams.get('error_description');
        
        if (errorParam) {
          console.error('OAuth Error:', errorParam, errorDescription);
          setError(errorDescription || errorParam);
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        // Extract session_id from URL (try both query params and hash)
        let sessionId = null;
        
        // First try query parameters
        sessionId = searchParams.get('session_id');
        
        // If not in query params, try hash fragment
        if (!sessionId) {
          const hash = window.location.hash;
          const hashParams = new URLSearchParams(hash.substring(1));
          sessionId = hashParams.get('session_id');
        }

        if (!sessionId) {
          console.error('No session_id found in URL');
          console.log('Search:', window.location.search);
          console.log('Hash:', window.location.hash);
          setError('No session ID received from authentication');
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        // Exchange session_id for user data
        const userData = await exchangeSession(sessionId);

        // Navigate to dashboard with user data
        navigate('/dashboard', { state: { user: userData }, replace: true });
      } catch (error) {
        console.error('Auth callback error:', error);
        setError(error.response?.data?.detail || 'Authentication failed');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    processAuth();
  }, [navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center max-w-md">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-4">
            <p className="text-red-800 font-semibold mb-2">Authentication Error</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
          <p className="text-slate-600 text-sm">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-slate-600">Authenticating...</p>
      </div>
    </div>
  );
};

export default AuthCallback;