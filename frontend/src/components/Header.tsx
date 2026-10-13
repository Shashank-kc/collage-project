import React from 'react';
import { ShieldCheck, Terminal } from 'lucide-react';
import type { HealthCheckResponse } from '../types';

interface HeaderProps {
  health: HealthCheckResponse | null;
  loadingHealth: boolean;
}

export const Header: React.FC<HeaderProps> = ({ health, loadingHealth }) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="top-header">
      <div className="brand-wrapper">
        <div className="brand-icon">
          <ShieldCheck size={22} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="brand-title">CodeGuard AI</span>
            <span className="brand-badge">v1.0</span>
          </div>
        </div>
      </div>

      <div className="header-meta">
        <div className="system-status" title={isHealthy ? 'Backend API connected' : 'Connecting to API...'}>
          <div className={`status-dot ${isHealthy ? '' : 'offline'}`} />
          {loadingHealth ? (
            <span>Connecting...</span>
          ) : isHealthy ? (
            <span>Ruff & Bandit Online</span>
          ) : (
            <span>Backend Offline</span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
          <Terminal size={14} />
          <span>AST Static Analysis</span>
        </div>
      </div>
    </header>
  );
};
