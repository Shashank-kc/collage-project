import React, { useState } from 'react';
import type { Finding, VerifyFixResponse } from '../types';
import {
  Sparkles,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  Play,
  Copy,
  Check,
  RotateCcw,
  Bot,
  Info,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

interface FixVerificationPanelProps {
  finding: Finding | null;
  onClose: () => void;
  onApplyFixSnippet: (saferSnippet: string) => void;
  onVerifyFix: (ruleId: string, line?: number | null) => Promise<VerifyFixResponse | null>;
  isVerifying: boolean;
  lastVerificationResult: VerifyFixResponse | null;
  onClearVerificationResult: () => void;
  onAskAIAboutFinding?: (finding: Finding) => void;
}

export const FixVerificationPanel: React.FC<FixVerificationPanelProps> = ({
  finding,
  onClose,
  onApplyFixSnippet,
  onVerifyFix,
  isVerifying,
  lastVerificationResult,
  onClearVerificationResult,
  onAskAIAboutFinding,
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [appliedNotice, setAppliedNotice] = useState<boolean>(false);

  if (!finding) {
    return (
      <div className="fix-panel-empty">
        <ShieldCheck size={44} style={{ color: 'var(--color-primary-electric)', opacity: 0.8 }} />
        <div style={{ fontWeight: 700, fontSize: '0.96rem', color: 'var(--text-main)', marginTop: '8px' }}>
          Explain · Fix · Verify Engine
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: '280px', textAlign: 'center', lineHeight: 1.5 }}>
          Select any finding from the list or click a line marker in the code gutter to inspect the root cause, review remediation diffs, and verify fixes.
        </p>
      </div>
    );
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleApply = (snippet: string) => {
    onApplyFixSnippet(snippet);
    setAppliedNotice(true);
    setTimeout(() => setAppliedNotice(false), 3000);
  };

  const isCurrentResult = lastVerificationResult?.rule_id.toUpperCase() === finding.rule_id.toUpperCase();

  return (
    <div className="fix-panel-container">
      {/* Header */}
      <div className="fix-panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span className={`tool-tag ${finding.tool}`}>{finding.tool}</span>
          <span className="rule-code" style={{ fontSize: '0.88rem', fontWeight: 700 }}>
            {finding.rule_id}
          </span>
          <span className={`severity-badge sev-${finding.severity}`}>
            {finding.severity}
          </span>
          {finding.line && (
            <span className="line-indicator">Line {finding.line}</span>
          )}
        </div>

        <button
          type="button"
          className="btn-icon"
          onClick={() => {
            onClearVerificationResult();
            onClose();
          }}
          title="Close Fix Inspector"
        >
          <RotateCcw size={14} />
        </button>
      </div>

      {/* Main Scrollable Content */}
      <div className="fix-panel-scroll">
        {/* Verification Status Banner if Re-scan Occurred */}
        {isCurrentResult && lastVerificationResult && (
          <div
            className={`verification-banner status-${lastVerificationResult.status.toLowerCase()}`}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
              {lastVerificationResult.status === 'RESOLVED' ? (
                <CheckCircle2 size={20} style={{ color: 'var(--color-success)', flexShrink: 0 }} />
              ) : lastVerificationResult.status === 'STILL_DETECTED' ? (
                <AlertTriangle size={20} style={{ color: 'var(--color-warning)', flexShrink: 0 }} />
              ) : (
                <Info size={20} style={{ color: 'var(--color-primary-electric)', flexShrink: 0 }} />
              )}
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className="verification-status-tag">
                    {lastVerificationResult.status.replace('_', ' ')}
                  </span>
                  <span style={{ fontSize: '0.74rem', fontWeight: 600 }}>
                    Score Delta: {lastVerificationResult.health_score_delta >= 0 ? '+' : ''}
                    {lastVerificationResult.health_score_delta} pts
                  </span>
                </div>
                <p style={{ fontSize: '0.78rem', marginTop: '4px', lineHeight: 1.4 }}>
                  {lastVerificationResult.message}
                </p>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                  Prior Health: {lastVerificationResult.prior_score} → New Health: {lastVerificationResult.new_score}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Section 1: What was detected */}
        <div className="explain-section">
          <div className="explain-section-title">
            <span className="section-step">1</span>
            <span>WHAT WAS DETECTED?</span>
          </div>
          <div className="explain-text">
            {finding.what_detected || finding.message}
          </div>
          {finding.code_snippet && (
            <div className="snippet-container">
              <div className="snippet-header">
                <span>DETECTED PATTERN (LINE {finding.line || 1})</span>
              </div>
              <pre className="snippet-body">
                <code>{finding.code_snippet}</code>
              </pre>
            </div>
          )}
        </div>

        {/* Section 2: Why it matters */}
        <div className="explain-section">
          <div className="explain-section-title">
            <span className="section-step">2</span>
            <span>WHY DOES IT MATTER?</span>
          </div>
          <div className="explain-text" style={{ borderLeft: '2px solid var(--color-warning)', paddingLeft: '10px' }}>
            {finding.why_it_matters ||
              'This pattern deviates from Python security or quality best practices and may lead to runtime defects or unauthorized behavior.'}
          </div>
        </div>

        {/* Section 3: How to improve */}
        <div className="explain-section">
          <div className="explain-section-title">
            <span className="section-step">3</span>
            <span>HOW CAN IT BE IMPROVED?</span>
          </div>
          <div className="explain-text">
            {finding.how_to_improve || finding.recommendation || 'Refactor using secure, idiomatic Python patterns.'}
          </div>
        </div>

        {/* Section 4: Safer Code Approach */}
        {finding.safer_example && (
          <div className="explain-section">
            <div className="explain-section-title">
              <span className="section-step">4</span>
              <span>EXAMPLE OF A SAFER APPROACH</span>
            </div>
            <div className="snippet-container safer">
              <div className="snippet-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle2 size={13} style={{ color: 'var(--color-success)' }} />
                  <span>RECOMMENDED REPLACEMENT</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    type="button"
                    className="btn-icon"
                    onClick={() => handleCopy(finding.safer_example!)}
                    title="Copy code to clipboard"
                  >
                    {copied ? <Check size={12} style={{ color: 'var(--color-success)' }} /> : <Copy size={12} />}
                  </button>
                </div>
              </div>
              <pre className="snippet-body safer-code">
                <code>{finding.safer_example}</code>
              </pre>
            </div>

            {/* Quick Actions */}
            <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
              <button
                type="button"
                className="btn-ghost-sm"
                onClick={() => handleCopy(finding.safer_example!)}
                title="Copy suggested code snippet to clipboard"
              >
                <Copy size={12} />
                <span>{copied ? 'Copied!' : 'Copy Code'}</span>
              </button>

              <button
                type="button"
                className="btn-secondary-sm"
                onClick={() => handleApply(finding.safer_example!)}
                title="Paste recommended safer pattern into editor"
              >
                <Sparkles size={12} style={{ color: 'var(--color-primary-electric)' }} />
                <span>{appliedNotice ? 'Pasted to Editor!' : 'Apply Pattern to Editor'}</span>
              </button>
            </div>
          </div>
        )}

        {/* Section 5: Verification Guide & Re-scan Action */}
        <div className="explain-section verification-box">
          <div className="explain-section-title">
            <span className="section-step">5</span>
            <span>HOW CAN I VERIFY THE CHANGE?</span>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: '6px 0 12px 0' }}>
            {finding.verification_guide ||
              'Apply the recommended remediation to the source code on the left, then click Verify Fix to execute a subsequent static analysis scan.'}
          </p>

          <button
            type="button"
            className="btn-verify-primary"
            onClick={() => onVerifyFix(finding.rule_id, finding.line)}
            disabled={isVerifying}
          >
            {isVerifying ? (
              <>
                <div className="spinner" style={{ width: '14px', height: '14px' }} />
                <span>Re-scanning Code with AST Parsers...</span>
              </>
            ) : (
              <>
                <Play size={13} fill="currentColor" />
                <span>Re-Scan & Verify Fix for {finding.rule_id}</span>
                <ArrowRight size={13} />
              </>
            )}
          </button>
        </div>

        {/* Dedicated AI Assistant Action */}
        <div className="explain-section" style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', fontWeight: 600 }}>
              <Bot size={15} style={{ color: 'var(--color-amber)' }} />
              <span>AI Security Mentor</span>
              <span className="advisory-badge" style={{ backgroundColor: 'var(--color-amber-dim)', color: 'var(--color-amber)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>OPENAI</span>
            </div>
          </div>

          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: '8px 0 10px 0' }}>
            Open this finding in the dedicated AI Assistant to explore root cause analysis, security implications, and remediation guidance.
          </p>

          <button
            type="button"
            className="btn-ask-ai-finding"
            onClick={() => onAskAIAboutFinding?.(finding)}
            title="Ask AI Assistant about this finding"
          >
            <Bot size={14} style={{ color: 'var(--color-amber)' }} />
            <span>Ask AI Assistant About This Finding</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {/* Official Documentation Link */}
        {finding.documentation_url && (
          <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
            <a
              href={finding.documentation_url}
              target="_blank"
              rel="noopener noreferrer"
              className="doc-link"
            >
              <span>Read Official Documentation for {finding.rule_id}</span>
              <ExternalLink size={12} />
            </a>
          </div>
        )}
      </div>
    </div>
  );
};
