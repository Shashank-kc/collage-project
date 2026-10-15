import React, { useState, useMemo } from 'react';
import type { Finding, ScannerTelemetry } from '../types';
import {
  Shield,
  Sparkles,
  CheckCircle2,
  Code2,
  AlertCircle,
  AlertTriangle,
  Search,
  ArrowUpDown,
  Wrench,
  ChevronRight,
  Bot,
} from 'lucide-react';

interface FindingsListProps {
  findings: Finding[];
  scanners?: ScannerTelemetry[];
  hasScanned: boolean;
  selectedLine?: number | null;
  onSelectFinding?: (finding: Finding) => void;
  selectedFindingId?: string | null;
  onAskAIAboutFinding?: (finding: Finding) => void;
}

type FilterCategory = 'all' | 'security' | 'quality' | 'high_critical' | 'ruff' | 'bandit';
type SortOption = 'line' | 'severity' | 'tool';

const SEVERITY_WEIGHT: Record<string, number> = {
  CRITICAL: 5,
  HIGH: 4,
  MEDIUM: 3,
  LOW: 2,
  INFO: 1,
};

export const FindingsList: React.FC<FindingsListProps> = ({
  findings,
  scanners = [],
  hasScanned,
  selectedLine,
  onSelectFinding,
  selectedFindingId,
  onAskAIAboutFinding,
}) => {
  const [activeFilter, setActiveFilter] = useState<FilterCategory>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortBy, setSortBy] = useState<SortOption>('line');

  const securityCount = findings.filter((f) => f.category === 'security').length;
  const qualityCount = findings.filter(
    (f) => f.category === 'quality' || f.category === 'style' || f.category === 'syntax'
  ).length;
  const highCriticalCount = findings.filter(
    (f) => f.severity === 'CRITICAL' || f.severity === 'HIGH'
  ).length;

  const filteredAndSortedFindings = useMemo(() => {
    let result = findings.filter((f) => {
      // Line filter from gutter
      if (selectedLine && f.line !== selectedLine) {
        return false;
      }

      // Category / Tool filter
      if (activeFilter === 'security' && f.category !== 'security') return false;
      if (
        activeFilter === 'quality' &&
        f.category !== 'quality' &&
        f.category !== 'style' &&
        f.category !== 'syntax'
      ) {
        return false;
      }
      if (activeFilter === 'high_critical' && f.severity !== 'CRITICAL' && f.severity !== 'HIGH') {
        return false;
      }
      if (activeFilter === 'ruff' && f.tool !== 'ruff') return false;
      if (activeFilter === 'bandit' && f.tool !== 'bandit') return false;

      // Text search
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchRule = f.rule_id.toLowerCase().includes(query);
        const matchMsg = f.message.toLowerCase().includes(query);
        const matchSnippet = f.code_snippet?.toLowerCase().includes(query) || false;
        if (!matchRule && !matchMsg && !matchSnippet) {
          return false;
        }
      }

      return true;
    });

    // Sorting
    result.sort((a, b) => {
      if (sortBy === 'severity') {
        const weightA = SEVERITY_WEIGHT[a.severity] || 0;
        const weightB = SEVERITY_WEIGHT[b.severity] || 0;
        return weightB - weightA;
      }
      if (sortBy === 'tool') {
        return a.tool.localeCompare(b.tool);
      }
      // Default: line number ascending
      const lineA = a.line ?? 999999;
      const lineB = b.line ?? 999999;
      return lineA - lineB;
    });

    return result;
  }, [findings, selectedLine, activeFilter, searchQuery, sortBy]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      {/* Scanner Telemetry Chips */}
      {hasScanned && scanners.length > 0 && (
        <div className="telemetry-bar">
          <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>Engines:</span>
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

      {/* Filter & Search Bar */}
      {hasScanned && findings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '10px 14px', borderBottom: '1px solid var(--border-subtle)' }}>
          {/* Top Row: Search input & Sort dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={13} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
              <input
                type="text"
                placeholder="Search rule ID, message, or keyword..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  backgroundColor: 'var(--bg-canvas)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '5px 8px 5px 30px',
                  fontSize: '0.78rem',
                  color: 'var(--text-main)',
                  outline: 'none',
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ArrowUpDown size={12} style={{ color: 'var(--text-dim)' }} />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                style={{
                  backgroundColor: 'var(--bg-canvas)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '4px 8px',
                  fontSize: '0.76rem',
                  color: 'var(--text-main)',
                  outline: 'none',
                  cursor: 'pointer',
                }}
                aria-label="Sort findings"
              >
                <option value="line">Sort: Line (asc)</option>
                <option value="severity">Sort: Severity (high to low)</option>
                <option value="tool">Sort: Tool engine</option>
              </select>
            </div>
          </div>

          {/* Bottom Row: Category Pills */}
          <div className="filter-bar" style={{ padding: 0, border: 'none' }}>
            {selectedLine && (
              <button
                type="button"
                className="filter-pill active"
                onClick={() => {}}
                title="Filtering by selected line marker"
              >
                <span>Line {selectedLine}</span>
                <span className="pill-count">{filteredAndSortedFindings.length}</span>
              </button>
            )}

            <button
              type="button"
              className={`filter-pill ${activeFilter === 'all' && !selectedLine ? 'active' : ''}`}
              onClick={() => setActiveFilter('all')}
            >
              <span>All</span>
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
              <span>Quality</span>
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
        </div>
      )}

      {/* Findings Cards List */}
      <div className="findings-container">
        {!hasScanned ? (
          <div className="empty-state">
            <Code2 size={44} style={{ color: 'var(--text-dim)' }} />
            <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.96rem' }}>
              Workspace Ready
            </div>
            <p style={{ fontSize: '0.82rem', maxWidth: '340px' }}>
              Paste or edit your Python code in the center editor and click <strong>Analyze Code</strong> to inspect AST structures with Ruff and Bandit.
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
        ) : filteredAndSortedFindings.length === 0 ? (
          <div className="empty-state">
            <AlertCircle size={36} style={{ color: 'var(--text-dim)' }} />
            <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>No matching findings</div>
            <p style={{ fontSize: '0.82rem' }}>Adjust your search query or reset filter to view all results.</p>
          </div>
        ) : (
          filteredAndSortedFindings.map((finding) => {
            const isSelected = selectedFindingId === finding.id;

            return (
              <div
                key={finding.id}
                className={`finding-card ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectFinding?.(finding)}
              >
                {/* Finding Header */}
                <div className="finding-card-header">
                  <div className="finding-title-group">
                    <span className={`tool-tag ${finding.tool}`}>{finding.tool}</span>
                    <span className="rule-code">{finding.rule_id}</span>
                    <span className={`severity-badge sev-${finding.severity}`}>
                      {finding.severity}
                    </span>
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

                {/* Educational Preview */}
                {finding.why_it_matters && (
                  <div className="detail-section-box why" style={{ padding: '8px 10px', fontSize: '0.78rem' }}>
                    <div className="detail-box-title">
                      <AlertTriangle size={12} />
                      <span>Why This Matters</span>
                    </div>
                    <div className="detail-box-text" style={{ WebkitLineClamp: 2, display: '-webkit-box', WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {finding.why_it_matters}
                    </div>
                  </div>
                )}

                {/* Action Footer: Inspect & Verify Fix */}
                <div className="finding-card-footer">
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                    {finding.safer_example ? 'Fix template available' : 'Advisory guidance'}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {onAskAIAboutFinding && (
                      <button
                        type="button"
                        className="btn-ghost-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onAskAIAboutFinding(finding);
                        }}
                        title="Ask AI Assistant about this finding"
                        style={{ fontSize: '0.72rem', padding: '4px 8px' }}
                      >
                        <Bot size={12} style={{ color: 'var(--color-amber)' }} />
                        <span>Ask AI</span>
                      </button>
                    )}

                    <button
                      type="button"
                      className="btn-inspect-fix"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectFinding?.(finding);
                      }}
                      title="Inspect root cause and verify remediation fix"
                    >
                      <Wrench size={12} />
                      <span>Explain · Fix · Verify</span>
                      <ChevronRight size={13} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
