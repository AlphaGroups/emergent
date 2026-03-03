import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { exchangeSession } from '../services/api';

const AuthCallback = () => {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // CRITICAL: Prevent duplicate processing under StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      try {
        // Extract session_id from URL (try both query params and hash)
        let sessionId = null;
        
        // First try query parameters
        const searchParams = new URLSearchParams(window.location.search);
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
          navigate('/login');
          return;
        }

        // Exchange session_id for user data
        const userData = await exchangeSession(sessionId);

        // Navigate to dashboard with user data
        navigate('/dashboard', { state: { user: userData }, replace: true });
      } catch (error) {
        console.error('Auth callback error:', error);
        navigate('/login');
      }
    };

    processAuth();
  }, [navigate]);

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