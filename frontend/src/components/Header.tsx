import React from 'react';
import { ShieldCheck, PlusCircle, LayoutDashboard, Code2, History, Settings } from 'lucide-react';
import type { HealthCheckResponse } from '../types';

export type ActiveTab = 'workspace' | 'dashboard' | 'history' | 'settings';

interface HeaderProps {
  health: HealthCheckResponse | null;
  loadingHealth: boolean;
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  onNewAnalysis: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  loadingHealth,
  activeTab,
  setActiveTab,
  onNewAnalysis,
}) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="top-header">
      {/* Brand */}
      <div className="brand-wrapper">
        <div className="brand-icon">
          <ShieldCheck size={22} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="brand-title">CodeGuard AI</span>
            <span className="brand-badge">v1.1</span>
          </div>
        </div>
      </div>

      {/* Navigation Switcher */}
      <nav className="nav-tab-group" aria-label="Main Navigation">
        <button
          type="button"
          className={`nav-tab-btn ${activeTab === 'workspace' ? 'active' : ''}`}
          onClick={() => setActiveTab('workspace')}
        >
          <Code2 size={15} />
          <span>Workspace</span>
        </button>

        <button
          type="button"
          className={`nav-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <LayoutDashboard size={15} />
          <span>Dashboard</span>
        </button>

        <button
          type="button"
          className={`nav-tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <History size={15} />
          <span>Scan History</span>
        </button>

        <button
          type="button"
          className={`nav-tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          <Settings size={15} />
          <span>Settings</span>
        </button>
      </nav>

      {/* Header Actions & Status */}
      <div className="header-meta">
        <button
          type="button"
          className="btn-ghost-sm"
          onClick={onNewAnalysis}
          title="Start fresh code analysis"
        >
          <PlusCircle size={14} style={{ color: 'var(--color-primary-electric)' }} />
          <span>New Analysis</span>
        </button>

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
      </div>
    </header>
  );
};
