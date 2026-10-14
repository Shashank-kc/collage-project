import React from 'react';
import type { AnalysisSummary } from '../types';
import { Shield, Sparkles, Clock, HelpCircle } from 'lucide-react';

interface FindingsSummaryProps {
  summary: AnalysisSummary;
  executionTimeMs: number;
}

export const FindingsSummary: React.FC<FindingsSummaryProps> = ({ summary, executionTimeMs }) => {
  return (
    <div className="metrics-row">
      {/* Code Health Grade & Score */}
      <div className="metric-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span className="metric-title">Health Score</span>
          <span
            title="Deductions: Critical -25pts, High -15pts, Medium -8pts, Low -3pts, Info -1pt. Base: 100."
            style={{ cursor: 'help', color: 'var(--text-dim)' }}
          >
            <HelpCircle size={12} />
          </span>
        </div>
        <div className="metric-value-group">
          <div className={`grade-badge grade-${summary.health_grade}`}>
            {summary.health_grade}
          </div>
          <div>
            <div className="metric-number">{summary.health_score}</div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>out of 100</div>
          </div>
        </div>
      </div>

      {/* Security Risks */}
      <div className="metric-card">
        <span className="metric-title">Security Risks</span>
        <div className="metric-value-group">
          <div
            className="metric-number"
            style={{ color: summary.security_findings > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}
          >
            {summary.security_findings}
          </div>
          <Shield
            size={18}
            style={{
              color: summary.security_findings > 0 ? 'var(--color-danger)' : 'var(--color-success)',
              marginLeft: 'auto',
            }}
          />
        </div>
        <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
          {summary.critical_count + summary.high_count} critical/high
        </div>
      </div>

      {/* Code Quality & Conventions */}
      <div className="metric-card">
        <span className="metric-title">Quality & Style</span>
        <div className="metric-value-group">
          <div
            className="metric-number"
            style={{ color: summary.quality_findings > 0 ? 'var(--color-warning)' : 'var(--color-success)' }}
          >
            {summary.quality_findings}
          </div>
          <Sparkles size={18} style={{ color: 'var(--color-violet)', marginLeft: 'auto' }} />
        </div>
        <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
          Ruff AST & PEP 8
        </div>
      </div>

      {/* Total & Speed */}
      <div className="metric-card">
        <span className="metric-title">Total Issues</span>
        <div className="metric-value-group">
          <div className="metric-number">
            {summary.total_findings}
          </div>
          <div
            style={{
              marginLeft: 'auto',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.74rem',
              color: 'var(--text-dim)',
            }}
          >
            <Clock size={12} />
            <span>{executionTimeMs}ms</span>
          </div>
        </div>
        <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
          Pipeline execution
        </div>
      </div>
    </div>
  );
};
