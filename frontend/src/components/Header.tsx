import React from 'react';
import {
  ShieldCheck,
  PlusCircle,
  LayoutDashboard,
  Code2,
  History,
  Settings,
  GitCompare,
  Bot,
  User as UserIcon,
  LogOut,
  LogIn,
} from 'lucide-react';
import type { HealthCheckResponse, User } from '../types';

export type ActiveTab = 'workspace' | 'dashboard' | 'history' | 'assistant' | 'settings';

interface HeaderProps {
  health: HealthCheckResponse | null;
  loadingHealth: boolean;
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  onNewAnalysis: () => void;
  onOpenComparison?: () => void;
  currentUser: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  loadingHealth,
  activeTab,
  setActiveTab,
  onNewAnalysis,
  onOpenComparison,
  currentUser,
  onOpenAuth,
  onLogout,
}) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="top-header">
      {/* Brand */}
      <div className="brand-wrapper" onClick={() => setActiveTab('workspace')} style={{ cursor: 'pointer' }}>
        <div className="brand-icon">
          <ShieldCheck size={22} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="brand-title">CodeGuard AI</span>
            <span className="brand-badge">v2.1</span>
          </div>
          <div className="brand-tagline">EXPLAIN. FIX. VERIFY.</div>
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
          className={`nav-tab-btn ${activeTab === 'assistant' ? 'active' : ''}`}
          onClick={() => setActiveTab('assistant')}
        >
          <Bot size={15} style={{ color: 'var(--color-amber)' }} />
          <span>AI Assistant</span>
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

      {/* Header Actions & User Authentication */}
      <div className="header-meta">
        {onOpenComparison && (
          <button
            type="button"
            className="btn-ghost-sm"
            onClick={onOpenComparison}
            title="Compare two scan runs"
          >
            <GitCompare size={14} style={{ color: 'var(--color-amber)' }} />
            <span>Compare</span>
          </button>
        )}

        <button
          type="button"
          className="btn-ghost-sm"
          onClick={onNewAnalysis}
          title="Start fresh code analysis"
        >
          <PlusCircle size={14} style={{ color: 'var(--color-amber)' }} />
          <span>New Analysis</span>
        </button>

        {/* User Account / Auth Section */}
        {currentUser ? (
          <div className="user-profile-badge" title={`Signed in as ${currentUser.email}`}>
            <div className="user-avatar-circle">
              <UserIcon size={13} />
            </div>
            <span className="user-display-name truncate">
              {currentUser.full_name || currentUser.email}
            </span>
            <button
              type="button"
              className="btn-logout-icon"
              onClick={onLogout}
              title="Sign out"
            >
              <LogOut size={13} />
            </button>
          </div>
        ) : (
          <button
            type="button"
            className="btn-auth-trigger"
            onClick={onOpenAuth}
            title="Sign in or create account"
          >
            <LogIn size={13} />
            <span>Sign In</span>
          </button>
        )}

        {/* System Telemetry Status */}
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
