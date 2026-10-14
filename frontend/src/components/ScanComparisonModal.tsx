import React, { useState } from 'react';
import type { ScanComparisonResponse, ScanHistoryItem } from '../types';
import {
  GitCompare,
  X,
  CheckCircle2,
  AlertTriangle,
  PlusCircle,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';
import { compareScans } from '../services/api';

interface ScanComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  history: ScanHistoryItem[];
  defaultBaseId?: number;
  defaultSubsequentId?: number;
}

export const ScanComparisonModal: React.FC<ScanComparisonModalProps> = ({
  isOpen,
  onClose,
  history,
  defaultBaseId,
  defaultSubsequentId,
}) => {
  const [baseId, setBaseId] = useState<number>(
    defaultBaseId || (history.length > 1 ? history[1].id : history[0]?.id || 1)
  );
  const [subsequentId, setSubsequentId] = useState<number>(
    defaultSubsequentId || (history[0]?.id || 2)
  );
  const [comparisonResult, setComparisonResult] = useState<ScanComparisonResponse | null>(null);
  const [isComparing, setIsComparing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleRunComparison = async () => {
    if (baseId === subsequentId) {
      setError('Please select two distinct scans to compare.');
      return;
    }

    setIsComparing(true);
    setError(null);
    try {
      const result = await compareScans(baseId, subsequentId);
      setComparisonResult(result);
    } catch {
      setError('Failed to compute comparison between the selected scans.');
    } finally {
      setIsComparing(false);
    }
  };

  const baseScan = history.find((h) => h.id === baseId);
  const subScan = history.find((h) => h.id === subsequentId);

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GitCompare size={18} style={{ color: 'var(--color-primary-electric)' }} />
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>
              Scan Comparison Engine
            </h2>
          </div>
          <button type="button" className="btn-icon" onClick={onClose} aria-label="Close modal">
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: 1.5 }}>
            Compare two distinct static analysis runs stored in SQLite history to verify resolved security findings, evaluate newly introduced defects, and track health score progression.
          </p>

          {/* Selectors for Base and Subsequent Scans */}
          <div className="comparison-selectors">
            {/* Base Scan */}
            <div className="comparison-select-card">
              <span className="comparison-select-label">BASE SCAN (BASELINE)</span>
              <select
                className="select-input"
                value={baseId}
                onChange={(e) => setBaseId(Number(e.target.value))}
              >
                {history.map((s) => (
                  <option key={`base-${s.id}`} value={s.id}>
                    Scan #{s.id} — Grade {s.health_grade} ({s.total_findings} issues) [{new Date(s.timestamp).toLocaleTimeString()}]
                  </option>
                ))}
              </select>
              {baseScan && (
                <div className="scan-mini-meta">
                  <span>Score: {baseScan.health_score}/100</span>
                  <span>{baseScan.security_findings} sec / {baseScan.quality_findings} qual</span>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ArrowRight size={20} style={{ color: 'var(--color-primary-electric)' }} />
            </div>

            {/* Subsequent Scan */}
            <div className="comparison-select-card">
              <span className="comparison-select-label">SUBSEQUENT SCAN (RE-SCAN)</span>
              <select
                className="select-input"
                value={subsequentId}
                onChange={(e) => setSubsequentId(Number(e.target.value))}
              >
                {history.map((s) => (
                  <option key={`sub-${s.id}`} value={s.id}>
                    Scan #{s.id} — Grade {s.health_grade} ({s.total_findings} issues) [{new Date(s.timestamp).toLocaleTimeString()}]
                  </option>
                ))}
              </select>
              {subScan && (
                <div className="scan-mini-meta">
                  <span>Score: {subScan.health_score}/100</span>
                  <span>{subScan.security_findings} sec / {subScan.quality_findings} qual</span>
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="alert-banner alert-error" style={{ marginTop: '12px' }}>
              <span>{error}</span>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '16px' }}>
            <button
              type="button"
              className="btn-primary"
              onClick={handleRunComparison}
              disabled={isComparing || history.length < 2}
            >
              <GitCompare size={14} />
              <span>{isComparing ? 'Comparing...' : 'Compute Scan Delta'}</span>
            </button>
          </div>

          {/* Comparison Results Card */}
          {comparisonResult && (
            <div className="comparison-results-card">
              <div className="comparison-kpi-grid">
                {/* Resolved Findings */}
                <div className="comparison-kpi-box resolved">
                  <div className="comp-kpi-header">
                    <CheckCircle2 size={16} style={{ color: 'var(--color-success)' }} />
                    <span>Resolved</span>
                  </div>
                  <div className="comp-kpi-val" style={{ color: 'var(--color-success)' }}>
                    {comparisonResult.resolved_count}
                  </div>
                  <span className="comp-kpi-sub">Issues eliminated</span>
                </div>

                {/* Remaining Findings */}
                <div className="comparison-kpi-box remaining">
                  <div className="comp-kpi-header">
                    <AlertTriangle size={16} style={{ color: 'var(--color-warning)' }} />
                    <span>Remaining</span>
                  </div>
                  <div className="comp-kpi-val" style={{ color: 'var(--color-warning)' }}>
                    {comparisonResult.remaining_count}
                  </div>
                  <span className="comp-kpi-sub">Still persistent</span>
                </div>

                {/* New Findings */}
                <div className="comparison-kpi-box new">
                  <div className="comp-kpi-header">
                    <PlusCircle size={16} style={{ color: 'var(--color-danger)' }} />
                    <span>New Issues</span>
                  </div>
                  <div className="comp-kpi-val" style={{ color: 'var(--color-danger)' }}>
                    {comparisonResult.new_count}
                  </div>
                  <span className="comp-kpi-sub">Newly introduced</span>
                </div>

                {/* Score Delta */}
                <div className="comparison-kpi-box delta">
                  <div className="comp-kpi-header">
                    {comparisonResult.score_delta > 0 ? (
                      <TrendingUp size={16} style={{ color: 'var(--color-success)' }} />
                    ) : comparisonResult.score_delta < 0 ? (
                      <TrendingDown size={16} style={{ color: 'var(--color-danger)' }} />
                    ) : (
                      <Minus size={16} style={{ color: 'var(--text-dim)' }} />
                    )}
                    <span>Score Delta</span>
                  </div>
                  <div
                    className="comp-kpi-val"
                    style={{
                      color:
                        comparisonResult.score_delta > 0
                          ? 'var(--color-success)'
                          : comparisonResult.score_delta < 0
                          ? 'var(--color-danger)'
                          : 'var(--text-main)',
                    }}
                  >
                    {comparisonResult.score_delta > 0 ? '+' : ''}
                    {comparisonResult.score_delta}
                  </div>
                  <span className="comp-kpi-sub">Health points</span>
                </div>
              </div>

              <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: '14px', textAlign: 'center', lineHeight: 1.4 }}>
                {comparisonResult.disclaimer}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
