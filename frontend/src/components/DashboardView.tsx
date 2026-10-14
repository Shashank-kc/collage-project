import React from 'react';
import type { DashboardMetrics } from '../types';
import {
  ShieldAlert,
  Sparkles,
  BarChart3,
  CheckCircle2,
  Clock,
  ArrowRight,
  Database,
} from 'lucide-react';

interface DashboardViewProps {
  metrics: DashboardMetrics | null;
  loadingMetrics: boolean;
  onSelectScan: (codePreview: string) => void;
  onGoToWorkspace: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  metrics,
  loadingMetrics,
  onSelectScan,
  onGoToWorkspace,
}) => {
  if (loadingMetrics) {
    return (
      <div className="dashboard-view-container">
        <div className="empty-state">
          <div className="spinner" style={{ width: '24px', height: '24px' }} />
          <p style={{ marginTop: '12px' }}>Loading analytics telemetry from SQLite...</p>
        </div>
      </div>
    );
  }

  if (!metrics || metrics.total_scans === 0) {
    return (
      <div className="dashboard-view-container">
        <div className="panel-card" style={{ padding: '48px 24px', textAlign: 'center' }}>
          <div className="empty-state">
            <Database size={48} style={{ color: 'var(--color-primary)' }} />
            <div style={{ fontWeight: 700, fontSize: '1.2rem', color: 'var(--text-main)' }}>
              No Historical Scan Data Yet
            </div>
            <p style={{ fontSize: '0.85rem', maxWidth: '420px', color: 'var(--text-muted)' }}>
              Run your first static code analysis in the <strong>Workspace</strong>. Results, health scores, and vulnerability breakdowns will automatically appear here.
            </p>
            <button
              type="button"
              className="btn-primary"
              style={{ marginTop: '14px' }}
              onClick={onGoToWorkspace}
            >
              Go to Workspace
            </button>
          </div>
        </div>
      </div>
    );
  }

  const grades = metrics.grade_distribution || { A: 0, B: 0, C: 0, D: 0, F: 0 };
  const totalGraded = Math.max(1, metrics.completed_scans);

  return (
    <div className="dashboard-view-container">
      {/* KPI Stat Cards */}
      <div className="kpi-grid">
        {/* Total Scans */}
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Total Analyses</span>
            <BarChart3 size={18} style={{ color: 'var(--color-primary-electric)' }} />
          </div>
          <div className="kpi-value">{metrics.total_scans}</div>
          <div className="kpi-subtext">
            {metrics.completed_scans} completed · {metrics.failed_scans} failed
          </div>
        </div>

        {/* Avg Health Score */}
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Average Health Score</span>
            <CheckCircle2 size={18} style={{ color: 'var(--color-success)' }} />
          </div>
          <div className="kpi-value" style={{ color: metrics.average_health_score >= 80 ? 'var(--color-success)' : 'var(--color-warning)' }}>
            {metrics.average_health_score}
            <span style={{ fontSize: '1rem', color: 'var(--text-dim)', fontWeight: 400 }}> / 100</span>
          </div>
          <div className="kpi-subtext">Across all completed scans</div>
        </div>

        {/* Total Security Issues */}
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Security Flaws Discovered</span>
            <ShieldAlert size={18} style={{ color: 'var(--color-danger)' }} />
          </div>
          <div className="kpi-value" style={{ color: metrics.total_security_issues > 0 ? 'var(--color-danger)' : 'var(--text-main)' }}>
            {metrics.total_security_issues}
          </div>
          <div className="kpi-subtext">Bandit AST security rules</div>
        </div>

        {/* Total Quality Issues */}
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Quality Defects Discovered</span>
            <Sparkles size={18} style={{ color: 'var(--color-violet)' }} />
          </div>
          <div className="kpi-value" style={{ color: metrics.total_quality_issues > 0 ? 'var(--color-warning)' : 'var(--text-main)' }}>
            {metrics.total_quality_issues}
          </div>
          <div className="kpi-subtext">Ruff PEP 8 & linter rules</div>
        </div>
      </div>

      {/* Split Section: Grade Distribution & Recent Activity */}
      <div className="dashboard-split">
        {/* Grade Distribution */}
        <div className="panel-card">
          <div className="panel-header">
            <div className="panel-title-group">
              <span>Code Health Grade Distribution</span>
            </div>
          </div>
          <div style={{ padding: '18px 20px' }}>
            {(['A', 'B', 'C', 'D', 'F'] as const).map((grade) => {
              const count = grades[grade] || 0;
              const percentage = Math.round((count / totalGraded) * 100);
              const colorClass =
                grade === 'A'
                  ? 'var(--color-success)'
                  : grade === 'B'
                  ? 'var(--color-primary)'
                  : grade === 'C'
                  ? 'var(--color-warning)'
                  : 'var(--color-danger)';

              return (
                <div key={grade} className="grade-dist-row">
                  <span className={`grade-badge grade-${grade}`} style={{ width: '28px', height: '28px', fontSize: '0.85rem' }}>
                    {grade}
                  </span>
                  <div className="grade-dist-bar-bg">
                    <div
                      className="grade-dist-bar-fill"
                      style={{ width: `${percentage}%`, backgroundColor: colorClass }}
                    />
                  </div>
                  <span style={{ fontSize: '0.78rem', minWidth: '70px', textAlign: 'right', color: 'var(--text-muted)' }}>
                    {count} ({percentage}%)
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Scan History Preview */}
        <div className="panel-card">
          <div className="panel-header">
            <div className="panel-title-group">
              <span>Recent Scans</span>
            </div>
            <button
              type="button"
              className="btn-ghost-sm"
              onClick={onGoToWorkspace}
            >
              <span>Workspace</span>
              <ArrowRight size={13} />
            </button>
          </div>

          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Grade</th>
                  <th>Issues</th>
                  <th>Speed</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {metrics.recent_scans.map((scan) => {
                  const dateStr = new Date(scan.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  });

                  return (
                    <tr key={scan.id}>
                      <td style={{ color: 'var(--text-muted)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Clock size={12} style={{ color: 'var(--text-dim)' }} />
                          <span>{dateStr}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`grade-badge grade-${scan.health_grade}`} style={{ width: '24px', height: '24px', fontSize: '0.75rem' }}>
                          {scan.health_grade}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontWeight: 600 }}>{scan.total_findings}</span>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginLeft: '4px' }}>
                          ({scan.security_findings} sec / {scan.quality_findings} qual)
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-dim)' }}>{scan.execution_time_ms}ms</td>
                      <td>
                        <button
                          type="button"
                          className="btn-ghost-sm"
                          onClick={() => onSelectScan(scan.code_preview)}
                          title="Load code snippet from this scan into Workspace"
                        >
                          Load
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
