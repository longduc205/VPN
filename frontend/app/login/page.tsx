'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

/* Inline SVG icons to avoid importing lucide-react on the login page bundle */
function ShieldIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
      <path d="m9 12 2 2 4-4"></path>
    </svg>
  );
}

function UserIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
      <circle cx="12" cy="7" r="4"></circle>
    </svg>
  );
}

function LockIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
    </svg>
  );
}

function KeypadIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="2" width="6" height="6" rx="1"></rect>
      <rect x="9" y="2" width="6" height="6" rx="1"></rect>
      <rect x="16" y="2" width="6" height="6" rx="1"></rect>
      <rect x="2" y="9" width="6" height="6" rx="1"></rect>
      <rect x="9" y="9" width="6" height="6" rx="1"></rect>
      <rect x="16" y="9" width="6" height="6" rx="1"></rect>
      <rect x="9" y="16" width="6" height="6" rx="1"></rect>
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [mfaRequired, setMfaRequired] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      // Send login request to FastAPI backend with credentials: 'include'
      // to allow setting the HttpOnly secure session cookie.
      const res = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest', // Standard custom header CSRF protection
        },
        body: JSON.stringify({ username, password }),
        credentials: 'include',
      });

      const data = await res.json();

      if (!res.ok) {
        let errMsg = 'Invalid username or password.';
        if (data && data.detail) {
          if (typeof data.detail === 'string') {
            errMsg = data.detail;
          } else if (Array.isArray(data.detail)) {
            errMsg = data.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
          } else if (typeof data.detail === 'object') {
            errMsg = data.detail.message || JSON.stringify(data.detail);
          }
        }
        throw new Error(errMsg);
      }

      if (data.status === 'mfa_required') {
        setMfaRequired(true);
        setSuccess('Credentials verified. Please enter your 2FA code.');
      } else {
        setSuccess('Logged in successfully! Redirecting...');
        setTimeout(() => {
          router.push('/');
          router.refresh();
        }, 1000);
      }
    } catch (err: any) {
      setError(err.message || 'Connection to authentication server failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/auth/login/mfa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({ username, code: mfaCode }),
        credentials: 'include',
      });

      const data = await res.json();

      if (!res.ok) {
        let errMsg = 'Invalid 2FA code.';
        if (data && data.detail) {
          if (typeof data.detail === 'string') {
            errMsg = data.detail;
          } else if (Array.isArray(data.detail)) {
            errMsg = data.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
          } else if (typeof data.detail === 'object') {
            errMsg = data.detail.message || JSON.stringify(data.detail);
          }
        }
        throw new Error(errMsg);
      }

      setSuccess('Logged in successfully! Redirecting...');
      setTimeout(() => {
        router.push('/');
        router.refresh();
      }, 1000);
    } catch (err: any) {
      setError(err.message || 'Verification failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="glass-card login-card">
        {/* Brand */}
        <div className="login-brand">
          <h1>
            <ShieldIcon />
            AEGIS
          </h1>
          <p className="login-subtitle">
            VPN Management Portal<br />
            Sign in to manage your secure tunnel
          </p>
        </div>

        {/* Alerts */}
        {error && (
          <div className="alert-card alert-danger">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="alert-card alert-success">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            <span>{success}</span>
          </div>
        )}

        {/* Login Form or MFA form */}
        {!mfaRequired ? (
          <form onSubmit={handleSubmit}>
            <div className="input-group">
              <label className="input-label" htmlFor="username">Username</label>
              <div className="input-with-icon">
                <span className="input-icon"><UserIcon /></span>
                <input
                  className="input-field"
                  type="text"
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  required
                  disabled={loading}
                  autoComplete="username"
                />
              </div>
            </div>

            <div className="input-group" style={{ marginBottom: '2rem' }}>
              <label className="input-label" htmlFor="password">Password</label>
              <div className="input-with-icon">
                <span className="input-icon"><LockIcon /></span>
                <input
                  className="input-field"
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  disabled={loading}
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? (
                <span>
                  <span className="loading-spinner" style={{ marginRight: '0.5rem' }}></span>
                  Authenticating...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleMfaSubmit}>
            <div className="input-group" style={{ marginBottom: '2rem' }}>
              <label className="input-label" htmlFor="mfaCode">Two-Factor Authentication Code</label>
              <div className="input-with-icon">
                <span className="input-icon"><KeypadIcon /></span>
                <input
                  className="input-field"
                  type="text"
                  id="mfaCode"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value)}
                  placeholder="6-digit verification code"
                  required
                  maxLength={6}
                  disabled={loading}
                  autoFocus
                  autoComplete="one-time-code"
                  style={{ letterSpacing: '0.15em', textAlign: 'center' }}
                />
              </div>
            </div>

            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? (
                <span>
                  <span className="loading-spinner" style={{ marginRight: '0.5rem' }}></span>
                  Verifying...
                </span>
              ) : (
                'Verify Code'
              )}
            </button>

            <button
              type="button"
              className="ghost-btn"
              onClick={() => {
                setMfaRequired(false);
                setMfaCode('');
                setError('');
                setSuccess('');
              }}
              style={{ marginTop: '1rem', width: '100%' }}
            >
              Back to Login
            </button>
          </form>
        )}

        {/* Footer */}
        <div className="login-footer">
          <p>
            Protected by AES-256 GCM &amp; Session Auditing<br />
            Forgot password? Contact your system administrator.
          </p>
        </div>
      </div>
    </div>
  );
}
