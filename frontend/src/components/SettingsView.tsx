import React from 'react';
import type { SettingsInfo } from '../types';
import { Shield, Lock, FileCode, CheckCircle2, Database } from 'lucide-react';

interface SettingsViewProps {
  settings: SettingsInfo | null;
  loadingSettings: boolean;
  enableRuff: boolean;
  setEnableRuff: (val: boolean) => void;
  enableBandit: boolean;
  setEnableBandit: (val: boolean) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  settings,
  loadingSettings,
  enableRuff,
  setEnableRuff,
  enableBandit,
  setEnableBandit,
}) => {
  if (loadingSettings) {
    return (
      <div className="dashboard-view-container">
        <div className="empty-state">
          <div className="spinner" />
          <p style={{ marginTop: '10px' }}>Loading server settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-view-container">
      <div className="settings-grid">
        {/* Left Column: Scanner Options & Execution Controls */}
        <div className="settings-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileCode size={18} style={{ color: 'var(--color-primary-electric)' }} />
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Static Analysis Engines
            </h2>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Configure which static analysis engines run during your code reviews. Both tools operate exclusively via AST inspection without executing code.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '6px' }}>
            {/* Ruff Toggle */}
            <div className="settings-row">
              <div className="settings-label-group">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="settings-label">Astral Ruff (Code Quality & PEP 8)</span>
                  <span className="tool-tag ruff">RUFF</span>
                </div>
                <span className="settings-desc">
                  Rust-based AST linter checking syntax errors, unused imports, dead variables, and conventions.
                </span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                  Binary: {settings?.ruff_path || 'ruff.exe'}
                </span>
              </div>
              <div>
                <input
                  type="checkbox"
                  checked={enableRuff}
                  onChange={(e) => setEnableRuff(e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary)' }}
                />
              </div>
            </div>

            {/* Bandit Toggle */}
            <div className="settings-row">
              <div className="settings-label-group">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="settings-label">OpenStack Bandit (Security AST)</span>
                  <span className="tool-tag bandit">BANDIT</span>
                </div>
                <span className="settings-desc">
                  Scans Python Abstract Syntax Trees for vulnerabilities (SQLi, eval, hardcoded passwords, weak hashes).
                </span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                  Binary: {settings?.bandit_path || 'bandit.exe'}
                </span>
              </div>
              <div>
                <input
                  type="checkbox"
                  checked={enableBandit}
                  onChange={(e) => setEnableBandit(e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary)' }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Server Limits & Security Policy */}
        <div className="settings-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Shield size={18} style={{ color: 'var(--color-success)' }} />
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Security Boundaries & Limits
            </h2>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Active server-side safeguards preventing Denial of Service (DoS) and resource exhaustion.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '6px' }}>
            <div className="settings-row">
              <div className="settings-label-group">
                <span className="settings-label">Max Code Submission Size</span>
                <span className="settings-desc">Enforced via HTTP 413 Content Too Large</span>
              </div>
              <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                {settings?.max_code_size_kb || 100} KB
              </span>
            </div>

            <div className="settings-row">
              <div className="settings-label-group">
                <span className="settings-label">Scanner Process Timeout</span>
                <span className="settings-desc">Maximum execution time before subprocess termination</span>
              </div>
              <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                {settings?.timeout_seconds || 15} seconds
              </span>
            </div>

            <div className="settings-row">
              <div className="settings-label-group">
                <span className="settings-label">Client Rate Limiter</span>
                <span className="settings-desc">Sliding-window threshold per client IP (HTTP 429)</span>
              </div>
              <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                {settings?.rate_limit_requests || 30} req / {settings?.rate_limit_window_seconds || 60}s
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Privacy & Data Handling Policy Card */}
      <div className="panel-card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Lock size={16} style={{ color: 'var(--color-primary-electric)' }} />
          <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Privacy & Code Sandboxing Model
          </h3>
        </div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          {settings?.privacy_policy ||
            'CodeGuard AI performs pure static AST analysis. Submitted Python code is written temporarily to an isolated OS temporary directory, analyzed via safe subprocess argument arrays without shell=True, and deleted immediately when the request finishes. Code is never imported or executed.'}
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginTop: '14px', fontSize: '0.76rem', color: 'var(--text-dim)', flexWrap: 'wrap' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <CheckCircle2 size={13} style={{ color: 'var(--color-success)' }} />
            Zero Code Execution (`eval`/`exec` disabled)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <CheckCircle2 size={13} style={{ color: 'var(--color-success)' }} />
            Safe Subprocess Argument Vector
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <CheckCircle2 size={13} style={{ color: 'var(--color-success)' }} />
            Strict Temporary File Cleanup
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Database size={13} style={{ color: 'var(--color-primary)' }} />
            Local SQLite Storage (`codeguard.db`)
          </span>
        </div>
      </div>
    </div>
  );
};
