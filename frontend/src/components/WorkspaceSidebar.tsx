import React from 'react';
import {
  FileCode2,
  FolderGit2,
  ShieldAlert,
  CheckCircle2,
  Clock,
  Sparkles,
  Shield,
  ChevronLeft,
  ChevronRight,
  PlusCircle,
} from 'lucide-react';
import type { ScanHistoryItem } from '../types';

interface WorkspaceSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  fileName: string;
  lineCount: number;
  byteSize: number;
  onLoadSample: (type: 'vulnerable' | 'clean') => void;
  recentScans: ScanHistoryItem[];
  onSelectScan: (codePreview: string) => void;
  onNewAnalysis: () => void;
  enableRuff: boolean;
  enableBandit: boolean;
}

export const WorkspaceSidebar: React.FC<WorkspaceSidebarProps> = ({
  isOpen,
  onToggle,
  fileName,
  lineCount,
  byteSize,
  onLoadSample,
  recentScans,
  onSelectScan,
  onNewAnalysis,
  enableRuff,
  enableBandit,
}) => {
  if (!isOpen) {
    return (
      <aside className="workspace-sidebar collapsed" title="Expand Project Explorer">
        <button
          type="button"
          className="sidebar-toggle-btn"
          onClick={onToggle}
          aria-label="Expand sidebar"
        >
          <ChevronRight size={16} />
        </button>
        <div className="collapsed-vertical-text">
          <FolderGit2 size={14} style={{ color: 'var(--color-primary-electric)' }} />
          <span>PROJECT</span>
        </div>
      </aside>
    );
  }

  return (
    <aside className="workspace-sidebar open">
      {/* Sidebar Header */}
      <div className="sidebar-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FolderGit2 size={16} style={{ color: 'var(--color-primary-electric)' }} />
          <span style={{ fontWeight: 700, fontSize: '0.84rem', letterSpacing: '0.04em' }}>
            PROJECT EXPLORER
          </span>
        </div>
        <button
          type="button"
          className="btn-icon"
          onClick={onToggle}
          title="Collapse sidebar"
          aria-label="Collapse sidebar"
        >
          <ChevronLeft size={16} />
        </button>
      </div>

      {/* Active File Tree */}
      <div className="sidebar-section">
        <div className="sidebar-section-title">ACTIVE WORKSPACE</div>
        <div className="file-tree-item active">
          <FileCode2 size={14} style={{ color: 'var(--color-primary-electric)' }} />
          <div className="file-tree-meta">
            <span className="file-name">{fileName}</span>
            <span className="file-stats">
              {lineCount} lines · {(byteSize / 1024).toFixed(1)} KB
            </span>
          </div>
        </div>

        <button
          type="button"
          className="btn-ghost-sm"
          style={{ width: '100%', justifyContent: 'flex-start', marginTop: '6px' }}
          onClick={onNewAnalysis}
          title="Clear editor for fresh analysis"
        >
          <PlusCircle size={13} style={{ color: 'var(--color-primary)' }} />
          <span>New Analysis</span>
        </button>
      </div>

      {/* Test Scenarios / Samples */}
      <div className="sidebar-section">
        <div className="sidebar-section-title">PRESET TEST SUITES</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <button
            type="button"
            className="sample-preset-btn vulnerable"
            onClick={() => onLoadSample('vulnerable')}
            title="Load vulnerable Python sample (SQLi, eval, MD5, hardcoded password)"
          >
            <ShieldAlert size={14} style={{ color: 'var(--color-danger)', flexShrink: 0 }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.78rem' }}>Vulnerable Sample</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                SQLi, eval, assert, MD5
              </div>
            </div>
          </button>

          <button
            type="button"
            className="sample-preset-btn clean"
            onClick={() => onLoadSample('clean')}
            title="Load clean, PEP-8 compliant Python sample"
          >
            <CheckCircle2 size={14} style={{ color: 'var(--color-success)', flexShrink: 0 }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.78rem' }}>Clean / Secure Sample</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                Type-annotated & hardened
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Active Static Analysis Scanners */}
      <div className="sidebar-section">
        <div className="sidebar-section-title">ACTIVE ENGINES</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div className="engine-status-row">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={13} style={{ color: 'var(--color-violet)' }} />
              <span style={{ fontSize: '0.78rem' }}>Ruff AST Linter</span>
            </div>
            <span className={`engine-badge ${enableRuff ? 'active' : 'disabled'}`}>
              {enableRuff ? 'ACTIVE' : 'OFF'}
            </span>
          </div>

          <div className="engine-status-row">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Shield size={13} style={{ color: 'var(--color-danger)' }} />
              <span style={{ fontSize: '0.78rem' }}>Bandit Security</span>
            </div>
            <span className={`engine-badge ${enableBandit ? 'active' : 'disabled'}`}>
              {enableBandit ? 'ACTIVE' : 'OFF'}
            </span>
          </div>
        </div>
      </div>

      {/* Recent Analysis History */}
      <div className="sidebar-section" style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        <div className="sidebar-section-title">
          <span>RECENT SCANS</span>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>SQLite</span>
        </div>
        {recentScans.length === 0 ? (
          <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', padding: '6px 0' }}>
            No prior scans recorded yet.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {recentScans.slice(0, 5).map((scan) => {
              const time = new Date(scan.timestamp).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              });

              return (
                <button
                  key={scan.id}
                  type="button"
                  className="recent-scan-item"
                  onClick={() => onSelectScan(scan.code_preview)}
                  title={`Load Scan #${scan.id} (${scan.total_findings} issues, Grade ${scan.health_grade})`}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className={`grade-badge grade-${scan.health_grade}`} style={{ width: '20px', height: '20px', fontSize: '0.68rem' }}>
                      {scan.health_grade}
                    </span>
                    <span style={{ fontWeight: 600, fontSize: '0.76rem' }}>
                      Scan #{scan.id}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                    <Clock size={11} />
                    <span>{time}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
};
