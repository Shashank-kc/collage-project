import React, { useState } from 'react';
import { ShieldCheck, Eye, EyeOff, Lock, Mail, User as UserIcon, ArrowRight, CheckCircle2, AlertTriangle, KeyRound } from 'lucide-react';
import { loginUser, registerUser, ApiError } from '../services/api';
import type { User } from '../types';

interface AuthViewProps {
  onAuthSuccess: (user: User) => void;
  onCancel?: () => void;
  initialMode?: 'login' | 'register';
}

export const AuthView: React.FC<AuthViewProps> = ({
  onAuthSuccess,
  onCancel,
  initialMode = 'login',
}) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);

  // Form fields
  const [fullName, setFullName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [rememberMe, setRememberMe] = useState<boolean>(false);

  // Visibility toggles
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState<boolean>(false);

  // State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Password strength calculation
  const calculatePasswordStrength = (pwd: string): { score: number; label: string; color: string } => {
    if (!pwd) return { score: 0, label: 'None', color: 'var(--border-subtle)' };
    let score = 0;
    if (pwd.length >= 8) score += 1;
    if (pwd.length >= 12) score += 1;
    if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;

    if (score <= 2) return { score: 25, label: 'Weak (needs numbers & symbols)', color: 'var(--color-danger)' };
    if (score <= 3) return { score: 60, label: 'Moderate', color: 'var(--color-warning)' };
    return { score: 100, label: 'Strong', color: 'var(--color-success)' };
  };

  const strength = calculatePasswordStrength(password);

  const validateForm = (): boolean => {
    setErrorMessage(null);

    const emailTrimmed = email.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailTrimmed) {
      setErrorMessage('Email address is required.');
      return false;
    }
    if (!emailRegex.test(emailTrimmed)) {
      setErrorMessage('Please provide a valid email address (e.g., name@domain.com).');
      return false;
    }

    if (!password) {
      setErrorMessage('Password is required.');
      return false;
    }

    if (mode === 'register') {
      if (!fullName.trim()) {
        setErrorMessage('Full name is required.');
        return false;
      }
      if (password.length < 8) {
        setErrorMessage('Password must be at least 8 characters long.');
        return false;
      }
      if (password === password.toLowerCase() && password === password.toUpperCase()) {
        setErrorMessage('Password must contain letters and numbers or symbols.');
        return false;
      }
      if (password !== confirmPassword) {
        setErrorMessage('Passwords do not match. Please re-enter your password.');
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      if (mode === 'login') {
        const response = await loginUser(email.trim(), password, rememberMe);
        setSuccessMessage('Sign in successful.');
        setTimeout(() => {
          onAuthSuccess(response.user);
        }, 400);
      } else {
        const response = await registerUser(fullName.trim(), email.trim(), password);
        setSuccessMessage('Account created successfully! Welcome to CodeGuard AI.');
        setTimeout(() => {
          onAuthSuccess(response.user);
        }, 600);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setErrorMessage('Invalid email or password. Please verify your credentials.');
        } else if (err.status === 409) {
          setErrorMessage('An account with this email address already exists. Please sign in instead.');
        } else if (err.status === 429) {
          setErrorMessage('Too many authentication attempts. Please wait 60 seconds before trying again.');
        } else {
          setErrorMessage(err.message || 'Authentication failed.');
        }
      } else if (err instanceof TypeError && err.message.includes('fetch')) {
        setErrorMessage('Backend service is unreachable. Please ensure the CodeGuard server is running on port 8000.');
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('An unexpected error occurred during authentication.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        {/* Brand Header */}
        <div className="auth-header">
          <div className="auth-brand-badge">
            <ShieldCheck size={28} className="auth-shield-icon" />
          </div>
          <h1 className="auth-title">CODEGUARD AI 2.1</h1>
          <p className="auth-subtitle">EXPLAIN. FIX. VERIFY.</p>
          <div className="auth-edition-tag">INDUSTRIAL PRECISION & SECURITY SUITE</div>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="auth-tabs" role="tablist" aria-label="Authentication Mode">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'login'}
            className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
            onClick={() => {
              setMode('login');
              setErrorMessage(null);
              setSuccessMessage(null);
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'register'}
            className={`auth-tab-btn ${mode === 'register' ? 'active' : ''}`}
            onClick={() => {
              setMode('register');
              setErrorMessage(null);
              setSuccessMessage(null);
            }}
          >
            Create Account
          </button>
        </div>

        {/* Feedback Banners */}
        {errorMessage && (
          <div className="alert-banner alert-error auth-alert" role="alert">
            <AlertTriangle size={18} className="alert-icon" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="alert-banner alert-success auth-alert" role="status">
            <CheckCircle2 size={18} className="alert-icon" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Main Auth Form */}
        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          {mode === 'register' && (
            <div className="form-group">
              <label htmlFor="reg-fullname" className="form-label">
                Full Name
              </label>
              <div className="input-with-icon">
                <UserIcon size={16} className="input-icon" />
                <input
                  id="reg-fullname"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Elena Rostova"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={isLoading}
                  autoComplete="name"
                  required
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="auth-email" className="form-label">
              Email Address
            </label>
            <div className="input-with-icon">
              <Mail size={16} className="input-icon" />
              <input
                id="auth-email"
                type="email"
                className="form-input"
                placeholder="developer@codeguard.local"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <div className="label-row">
              <label htmlFor="auth-password" className="form-label">
                Password
              </label>
            </div>
            <div className="input-with-icon">
              <Lock size={16} className="input-icon" />
              <input
                id="auth-password"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                placeholder={mode === 'register' ? 'At least 8 characters' : 'Enter your password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
              />
              <button
                type="button"
                className="input-action-btn"
                onClick={() => setShowPassword((prev) => !prev)}
                title={showPassword ? 'Hide password' : 'Show password'}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {/* Password strength bar during registration */}
            {mode === 'register' && password.length > 0 && (
              <div className="strength-meter-container">
                <div className="strength-meter-bar-bg">
                  <div
                    className="strength-meter-bar-fill"
                    style={{ width: `${strength.score}%`, backgroundColor: strength.color }}
                  />
                </div>
                <div className="strength-label" style={{ color: strength.color }}>
                  Strength: {strength.label}
                </div>
              </div>
            )}
          </div>

          {mode === 'register' && (
            <div className="form-group">
              <label htmlFor="reg-confirm-password" className="form-label">
                Confirm Password
              </label>
              <div className="input-with-icon">
                <KeyRound size={16} className="input-icon" />
                <input
                  id="reg-confirm-password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  className="form-input"
                  placeholder="Re-enter your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={isLoading}
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  className="input-action-btn"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                  title={showConfirmPassword ? 'Hide password' : 'Show password'}
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          )}

          {mode === 'login' && (
            <div className="auth-options-row">
              <label className="checkbox-label" htmlFor="remember-me-check">
                <input
                  id="remember-me-check"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  disabled={isLoading}
                  className="custom-checkbox"
                />
                <span>Remember me for 30 days</span>
              </label>
            </div>
          )}

          {/* Action button */}
          <button
            type="submit"
            className="btn-primary auth-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <div className="spinner auth-spinner" />
                <span>{mode === 'login' ? 'Verifying Credentials...' : 'Securing Account with Argon2id...'}</span>
              </>
            ) : (
              <>
                <span>{mode === 'login' ? 'Authenticate & Enter' : 'Create Protected Account'}</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Footer Toggle */}
        <div className="auth-footer">
          {mode === 'login' ? (
            <p>
              New to CodeGuard AI?{' '}
              <button
                type="button"
                className="link-button"
                onClick={() => {
                  setMode('register');
                  setErrorMessage(null);
                }}
              >
                Register developer account
              </button>
            </p>
          ) : (
            <p>
              Already registered?{' '}
              <button
                type="button"
                className="link-button"
                onClick={() => {
                  setMode('login');
                  setErrorMessage(null);
                }}
              >
                Sign in to existing account
              </button>
            </p>
          )}

          {onCancel && (
            <div style={{ marginTop: '12px' }}>
              <button
                type="button"
                className="btn-ghost-sm"
                onClick={onCancel}
              >
                Continue in Guest Workspace
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
