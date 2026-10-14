import React, { useState } from 'react';
import type { Finding, ScannerTelemetry } from '../types';
import { Shield, Sparkles, ExternalLink, Lightbulb, CheckCircle2, Code2, AlertCircle, AlertTriangle } from 'lucide-react';

interface FindingsListProps {
  findings: Finding[];
  scanners?: ScannerTelemetry[];
  hasScanned: boolean;
  selectedLine?: number | null;
}

type FilterCategory = 'all' | 'security' | 'quality' | 'high_critical';

export const FindingsList: React.FC<FindingsListProps> = ({
  findings,
  scanners = [],
  hasScanned,
  selectedLine,
}) => {
  const [activeFilter, setActiveFilter] = useState<FilterCategory>('all');

  const securityCount = findings.filter((f) => f.category === 'security').length;
  const qualityCount = findings.filter(
    (f) => f.category === 'quality' || f.category === 'style' || f.category === 'syntax'
  ).length;
  const highCriticalCount = findings.filter(
    (f) => f.severity === 'CRITICAL' || f.severity === 'HIGH'
  ).length;

  const filteredFindings = findings.filter((f) => {
    if (selectedLine) {
      return f.line === selectedLine;
    }
    if (activeFilter === 'security') return f.category === 'security';
    if (activeFilter === 'quality') {
      return f.category === 'quality' || f.category === 'style' || f.category === 'syntax';
    }
    if (activeFilter === 'high_critical') {
      return f.severity === 'CRITICAL' || f.severity === 'HIGH';
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      {/* Scanner Telemetry Chips */}
      {hasScanned && scanners.length > 0 && (
        <div className="telemetry-bar">
          <span style={{ fontWeight: 600 }}>Scanners:</span>
          {scanners.map((s) => (
            <div key={s.name} className="telemetry-chip">
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor:
                    s.status === 'completed'
                      ? 'var(--color-success)'
                      : s.status === 'timed_out' || s.status === 'failed'
                      ? 'var(--color-danger)'
                      : 'var(--text-dim)',
                }}
              />
              <strong style={{ textTransform: 'capitalize' }}>{s.name}</strong>
              <span>
                {s.status === 'disabled'
                  ? 'Disabled'
                  : s.status === 'timed_out'
                  ? 'Timed Out'
                  : s.status === 'failed'
                  ? 'Failed'
                  : `${s.duration_ms}ms (${s.findings_count} found)`}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Filter Tabs */}
      {hasScanned && findings.length > 0 && (
        <div className="filter-bar">
          {selectedLine && (
            <button
              type="button"
              className="filter-pill active"
              onClick={() => {}}
              title="Filtering by selected line marker"
            >
              <span>Line {selectedLine}</span>
              <span className="pill-count">{filteredFindings.length}</span>
            </button>
          )}

          <button
            type="button"
            className={`filter-pill ${activeFilter === 'all' && !selectedLine ? 'active' : ''}`}
            onClick={() => setActiveFilter('all')}
          >
            <span>All Findings</span>
            <span className="pill-count">{findings.length}</span>
          </button>

          <button
            type="button"
            className={`filter-pill ${activeFilter === 'security' && !selectedLine ? 'active' : ''}`}
            onClick={() => setActiveFilter('security')}
          >
            <Shield size={12} />
            <span>Security</span>
            <span className="pill-count">{securityCount}</span>
          </button>

          <button
            type="button"
            className={`filter-pill ${activeFilter === 'quality' && !selectedLine ? 'active' : ''}`}
            onClick={() => setActiveFilter('quality')}
          >
            <Sparkles size={12} />
            <span>Quality & Style</span>
            <span className="pill-count">{qualityCount}</span>
          </button>

          {highCriticalCount > 0 && (
            <button
              type="button"
              className={`filter-pill ${activeFilter === 'high_critical' && !selectedLine ? 'active' : ''}`}
              onClick={() => setActiveFilter('high_critical')}
            >
              <span style={{ color: 'var(--color-danger)' }}>●</span>
              <span>High / Critical</span>
              <span className="pill-count">{highCriticalCount}</span>
            </button>
          )}
        </div>
      )}

      {/* Findings List Area */}
      <div className="findings-container">
        {!hasScanned ? (
          <div className="empty-state">
            <Code2 size={44} style={{ color: 'var(--text-dim)' }} />
            <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.96rem' }}>
              Workspace Ready
            </div>
            <p style={{ fontSize: '0.82rem', maxWidth: '340px' }}>
              Paste or edit your Python code on the left and click <strong>Analyze Code</strong> to inspect AST structures with Ruff and Bandit.
            </p>
          </div>
        ) : findings.length === 0 ? (
          <div className="empty-state">
            <CheckCircle2 size={44} style={{ color: 'var(--color-success)' }} />
            <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '1rem' }}>
              No Issues Detected!
            </div>
            <p style={{ fontSize: '0.82rem', maxWidth: '340px' }}>
              Both Ruff and Bandit scanned this submission without discovering any security flaws or PEP-8 quality defects.
            </p>
          </div>
        ) : filteredFindings.length === 0 ? (
          <div className="empty-state">
            <AlertCircle size={36} style={{ color: 'var(--text-dim)' }} />
            <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>No matching findings</div>
            <p style={{ fontSize: '0.82rem' }}>Switch filter to &ldquo;All Findings&rdquo; to view all results.</p>
          </div>
        ) : (
          filteredFindings.map((finding) => (
            <div key={finding.id} className="finding-card">
              {/* Finding Header */}
              <div className="finding-card-header">
                <div className="finding-title-group">
                  <span className={`tool-tag ${finding.tool}`}>{finding.tool}</span>
                  <span className="rule-code">{finding.rule_id}</span>
                  <span className={`severity-badge sev-${finding.severity}`}>{finding.severity}</span>
                </div>

                {finding.line !== null && finding.line !== undefined && (
                  <span className="line-indicator">
                    Line {finding.line}
                    {finding.column !== null && finding.column !== undefined ? `:${finding.column}` : ''}
                  </span>
                )}
              </div>

              {/* Message */}
              <div className="finding-message">{finding.message}</div>

              {/* Code Snippet */}
              {finding.code_snippet && (
                <pre className="snippet-box">
                  <code>{finding.code_snippet}</code>
                </pre>
              )}

              {/* Why this matters (Security / Defect Explanation) */}
              {finding.why_it_matters && (
                <div className="detail-section-box why">
                  <div className="detail-box-title">
                    <AlertTriangle size={13} />
                    <span>Why This Matters</span>
                  </div>
                  <div className="detail-box-text">{finding.why_it_matters}</div>
                </div>
              )}

              {/* Recommended Remediation */}
              {finding.recommendation && (
                <div className="detail-section-box rec">
                  <div className="detail-box-title">
                    <Lightbulb size={13} />
                    <span>Recommended Remediation</span>
                  </div>
                  <div className="detail-box-text">{finding.recommendation}</div>
                  {finding.documentation_url && (
                    <a
                      href={finding.documentation_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="doc-link"
                    >
                      <span>Official Rule Documentation</span>
                      <ExternalLink size={11} />
                    </a>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
