import React, { useState } from 'react';
import type { ScanHistoryItem } from '../types';
import { History, Search, Clock, ArrowRight, CheckCircle2, XCircle } from 'lucide-react';

interface HistoryViewProps {
  history: ScanHistoryItem[];
  loadingHistory: boolean;
  onSelectScan: (codePreview: string) => void;
  onRefresh: () => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  history,
  loadingHistory,
  onSelectScan,
  onRefresh,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredHistory = history.filter((scan) => {
    if (!searchQuery.trim()) return true;
    return (
      scan.code_preview.toLowerCase().includes(searchQuery.toLowerCase()) ||
      scan.health_grade.toLowerCase() === searchQuery.toLowerCase() ||
      scan.id.toString() === searchQuery
    );
  });

  return (
    <div className="dashboard-view-container">
      <div className="panel-card">
        {/* Header Bar */}
        <div className="panel-header">
          <div className="panel-title-group">
            <History size={18} style={{ color: 'var(--color-primary-electric)' }} />
            <span>Persisted Scan History (SQLite Database)</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: 400 }}>
              ({history.length} total recorded)
            </span>
          </div>

          <div className="panel-actions">
            {/* Search Input */}
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Search
                size={14}
                style={{ position: 'absolute', left: '10px', color: 'var(--text-dim)' }}
              />
              <input
                type="text"
                placeholder="Search scans..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  backgroundColor: 'var(--bg-canvas)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '5px 10px 5px 30px',
                  color: 'var(--text-main)',
                  fontSize: '0.78rem',
                  width: '180px',
                  outline: 'none',
                }}
              />
            </div>

            <button type="button" className="btn-ghost-sm" onClick={onRefresh}>
              Refresh
            </button>
          </div>
        </div>

        {/* Table Body */}
        <div className="data-table-container">
          {loadingHistory ? (
            <div className="empty-state">
              <div className="spinner" />
              <p style={{ marginTop: '10px' }}>Loading scan history...</p>
            </div>
          ) : filteredHistory.length === 0 ? (
            <div className="empty-state">
              <Clock size={40} style={{ color: 'var(--text-dim)' }} />
              <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>No scan records found</div>
              <p style={{ fontSize: '0.82rem' }}>
                {searchQuery ? 'No scans match your search query.' : 'Run your first code analysis in the Workspace!'}
              </p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Timestamp</th>
                  <th>Status</th>
                  <th>Health</th>
                  <th>Security Flaws</th>
                  <th>Quality Defects</th>
                  <th>Total</th>
                  <th>Speed</th>
                  <th>Code Preview</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredHistory.map((scan) => {
                  const dateStr = new Date(scan.timestamp).toLocaleString();
                  const isCompleted = scan.status === 'completed';

                  return (
                    <tr key={scan.id}>
                      <td style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        #{scan.id}
                      </td>
                      <td style={{ whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>
                        {dateStr}
                      </td>
                      <td>
                        <span className={`status-chip ${isCompleted ? 'completed' : 'failed'}`}>
                          {isCompleted ? <CheckCircle2 size={11} /> : <XCircle size={11} />}
                          <span>{scan.status}</span>
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span
                            className={`grade-badge grade-${scan.health_grade}`}
                            style={{ width: '26px', height: '26px', fontSize: '0.85rem' }}
                          >
                            {scan.health_grade}
                          </span>
                          <span style={{ fontWeight: 600 }}>{scan.health_score}/100</span>
                        </div>
                      </td>
                      <td>
                        <span
                          style={{
                            color: scan.security_findings > 0 ? 'var(--color-danger)' : 'inherit',
                            fontWeight: scan.security_findings > 0 ? 600 : 400,
                          }}
                        >
                          {scan.security_findings}
                        </span>
                      </td>
                      <td>
                        <span
                          style={{
                            color: scan.quality_findings > 0 ? 'var(--color-warning)' : 'inherit',
                            fontWeight: scan.quality_findings > 0 ? 600 : 400,
                          }}
                        >
                          {scan.quality_findings}
                        </span>
                      </td>
                      <td style={{ fontWeight: 700 }}>{scan.total_findings}</td>
                      <td style={{ color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>
                        {scan.execution_time_ms}ms
                      </td>
                      <td style={{ maxWidth: '240px' }}>
                        <code
                          style={{
                            display: 'block',
                            backgroundColor: 'var(--bg-code)',
                            padding: '4px 8px',
                            borderRadius: 'var(--radius-xs)',
                            fontSize: '0.73rem',
                            color: 'var(--text-muted)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {scan.code_preview}
                        </code>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn-ghost-sm"
                          onClick={() => onSelectScan(scan.code_preview)}
                          title="Load this code into the active workspace"
                        >
                          <span>Load</span>
                          <ArrowRight size={11} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
