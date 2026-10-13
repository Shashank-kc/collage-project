import React, { useState } from 'react';
import type { Finding } from '../types';
import { Shield, Sparkles, ExternalLink, Lightbulb, CheckCircle2, Code2 } from 'lucide-react';

interface FindingsListProps {
  findings: Finding[];
  hasScanned: boolean;
}

type FilterCategory = 'all' | 'security' | 'quality' | 'high_critical';

export const FindingsList: React.FC<FindingsListProps> = ({ findings, hasScanned }) => {
  const [activeFilter, setActiveFilter] = useState<FilterCategory>('all');

  const securityCount = findings.filter((f) => f.category === 'security').length;
  const qualityCount = findings.filter(
    (f) => f.category === 'quality' || f.category === 'style' || f.category === 'syntax'
  ).length;
  const highCriticalCount = findings.filter(
    (f) => f.severity === 'CRITICAL' || f.severity === 'HIGH'
  ).length;

  const filteredFindings = findings.filter((f) => {
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
      {/* Filter Tabs */}
      {hasScanned && findings.length > 0 && (
        <div className="filter-bar">
          <button
            type="button"
            className={`filter-pill ${activeFilter === 'all' ? 'active' : ''}`}
            onClick={() => setActiveFilter('all')}
          >
            <span>All Findings</span>
            <span className="pill-count">{findings.length}</span>
          </button>

          <button
            type="button"
            className={`filter-pill ${activeFilter === 'security' ? 'active' : ''}`}
            onClick={() => setActiveFilter('security')}
          >
            <Shield size={12} />
            <span>Security</span>
            <span className="pill-count">{securityCount}</span>
          </button>

          <button
            type="button"
            className={`filter-pill ${activeFilter === 'quality' ? 'active' : ''}`}
            onClick={() => setActiveFilter('quality')}
          >
            <Sparkles size={12} />
            <span>Quality & Style</span>
            <span className="pill-count">{qualityCount}</span>
          </button>

          {highCriticalCount > 0 && (
            <button
              type="button"
              className={`filter-pill ${activeFilter === 'high_critical' ? 'active' : ''}`}
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
            <Code2 className="empty-state-icon" />
            <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>No Analysis Yet</div>
            <p style={{ fontSize: '0.85rem', maxWidth: '320px' }}>
              Paste your Python code on the left and click <strong>Analyze Code</strong>, or load a sample snippet to see Bandit & Ruff findings.
            </p>
          </div>
        ) : findings.length === 0 ? (
          <div className="empty-state">
            <CheckCircle2 size={44} style={{ color: 'var(--color-success)' }} />
            <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '1rem' }}>
              No Issues Detected!
            </div>
            <p style={{ fontSize: '0.85rem', maxWidth: '320px' }}>
              Ruff and Bandit found no vulnerabilities or quality warnings in this submission.
            </p>
          </div>
        ) : filteredFindings.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>No findings match this filter</div>
            <p style={{ fontSize: '0.85rem' }}>Select &ldquo;All Findings&rdquo; to see all detected items.</p>
          </div>
        ) : (
          filteredFindings.map((finding) => (
            <div key={finding.id} className="finding-card">
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

              <div className="finding-message">{finding.message}</div>

              {/* Offending Code Snippet */}
              {finding.code_snippet && (
                <pre className="snippet-box">
                  <code>{finding.code_snippet}</code>
                </pre>
              )}

              {/* Educational Mentor Recommendation */}
              {finding.recommendation && (
                <div className="recommendation-box">
                  <div className="rec-title">
                    <Lightbulb size={13} />
                    <span>Mentor Recommendation</span>
                  </div>
                  <div className="rec-text">{finding.recommendation}</div>
                  {finding.documentation_url && (
                    <a
                      href={finding.documentation_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="doc-link"
                    >
                      <span>Read rule docs</span>
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
