import React, { useState, useEffect } from 'react';
import { Building2 } from 'lucide-react';

const Login = () => {
  const [showError, setShowError] = useState(false);

  useEffect(() => {
    // Check if there's an error in the URL
    const params = new URLSearchParams(window.location.search);
    if (params.get('error')) {
      setShowError(true);
    }
  }, []);

  const handleGoogleLogin = () => {
    // Clear error state
    setShowError(false);
    
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    
    // Clear any existing session first
    document.cookie = 'session_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    
    // Redirect to Emergent Auth
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen grid md:grid-cols-2">
      {/* Left side - Branding */}
      <div 
        className="hidden md:flex flex-col justify-center items-center p-12 bg-cover bg-center relative"
        style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1721995019477-99729ca02594?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTZ8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBvZmZpY2UlMjBidWlsZGluZyUyMGFyY2hpdGVjdHVyZSUyMGFic3RyYWN0fGVufDB8fHx8MTc3MjUyOTU5NXww&ixlib=rb-4.1.0&q=85)' }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900/90 to-blue-900/90"></div>
        <div className="relative z-10 text-center">
          <div className="flex justify-center mb-6">
            <div className="bg-blue-600 p-4 rounded-2xl shadow-2xl">
              <Building2 className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold text-white mb-4 font-heading">FinTrust Intelligence</h1>
          <p className="text-xl text-slate-200 max-w-md">
            Comprehensive vendor due diligence powered by real-time verification
          </p>
        </div>
      </div>

      {/* Right side - Login Form */}
      <div className="flex flex-col justify-center items-center p-8 bg-white">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-slate-900 font-heading">Welcome Back</h2>
            <p className="mt-2 text-slate-600">Sign in to access your dashboard</p>
          </div>

          <div className="space-y-6">
            <button
              data-testid="google-login-button"
              onClick={handleGoogleLogin}
              className="w-full flex items-center justify-center gap-3 px-6 py-4 border border-slate-200 rounded-lg hover:bg-slate-50 transition-all shadow-sm hover:shadow-md font-medium text-slate-700"
            >
              <svg className="h-6 w-6" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Continue with Google
            </button>

            <div className="text-center text-sm text-slate-500">
              <p>Secure authentication powered by Emergent</p>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-slate-200">
            <div className="text-center text-sm text-slate-600">
              <p className="mb-2 font-semibold">Trusted by compliance teams at</p>
              <p className="text-slate-500">Leading FinTech, Banking & Enterprise organizations</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;