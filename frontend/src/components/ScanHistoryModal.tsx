import React from 'react';
import type { ScanHistoryItem } from '../types';
import { History, X, Clock } from 'lucide-react';

interface ScanHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  history: ScanHistoryItem[];
}

export const ScanHistoryModal: React.FC<ScanHistoryModalProps> = ({
  isOpen,
  onClose,
  history,
}) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        backdropFilter: 'blur(3px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        className="panel-card"
        style={{
          width: '100%',
          maxWidth: '680px',
          maxHeight: '80vh',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-header">
          <div className="panel-title-group">
            <History size={18} style={{ color: 'var(--color-primary)' }} />
            <span>Scan History (SQLite Database)</span>
          </div>
          <button
            type="button"
            className="btn-ghost-sm"
            onClick={onClose}
            style={{ padding: '4px' }}
          >
            <X size={16} />
          </button>
        </div>

        <div style={{ padding: '16px 18px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {history.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)' }}>
              No previous scans recorded yet. Run your first analysis!
            </div>
          ) : (
            history.map((scan) => {
              const dateStr = new Date(scan.timestamp).toLocaleString();
              return (
                <div
                  key={scan.id}
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 14px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className={`grade-badge grade-${scan.health_grade}`} style={{ width: '28px', height: '28px', fontSize: '0.9rem' }}>
                        {scan.health_grade}
                      </span>
                      <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Score: {scan.health_score}/100</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={12} /> {scan.execution_time_ms}ms
                      </span>
                    </div>

                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{dateStr}</span>
                  </div>

                  <div style={{ display: 'flex', gap: '14px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    <span>Total: <strong>{scan.total_findings}</strong></span>
                    <span style={{ color: scan.security_findings > 0 ? 'var(--color-danger)' : 'inherit' }}>
                      Security: <strong>{scan.security_findings}</strong>
                    </span>
                    <span>Quality: <strong>{scan.quality_findings}</strong></span>
                  </div>

                  {scan.code_preview && (
                    <pre
                      style={{
                        backgroundColor: 'var(--bg-code)',
                        padding: '6px 10px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.75rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--text-dim)',
                        whiteSpace: 'pre-wrap',
                        maxHeight: '60px',
                        overflow: 'hidden',
                      }}
                    >
                      {scan.code_preview}
                    </pre>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
