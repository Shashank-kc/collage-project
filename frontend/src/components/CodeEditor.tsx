import React, { useRef } from 'react';
import { Play, ShieldAlert, CheckCircle, RotateCcw, Shield, Sparkles } from 'lucide-react';
import type { Finding } from '../types';

interface CodeEditorProps {
  code: string;
  setCode: (code: string) => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
  onLoadSample: (type: 'vulnerable' | 'clean') => void;
  enableRuff: boolean;
  setEnableRuff: (val: boolean) => void;
  enableBandit: boolean;
  setEnableBandit: (val: boolean) => void;
  findings?: Finding[];
  onSelectLineFinding?: (line: number) => void;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  code,
  setCode,
  onAnalyze,
  isAnalyzing,
  onLoadSample,
  enableRuff,
  setEnableRuff,
  enableBandit,
  setEnableBandit,
  findings = [],
  onSelectLineFinding,
}) => {
  const lineNumbersRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const lines = code.split('\n');
  const lineCount = Math.max(lines.length, 1);
  const charCount = code.length;
  const byteSize = new Blob([code]).size;
  const isNearLimit = byteSize > 90 * 1024;

  // Build a map of line number -> list of findings for line gutter markers
  const lineFindingMap = React.useMemo(() => {
    const map = new Map<number, Finding[]>();
    for (const f of findings) {
      if (f.line) {
        const existing = map.get(f.line) || [];
        existing.push(f);
        map.set(f.line, existing);
      }
    }
    return map;
  }, [findings]);

  // Synchronize line numbers scroll with textarea scroll
  const handleScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  // Keyboard shortcut: Ctrl+Enter / Cmd+Enter to run analysis
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (!isAnalyzing && code.trim().length > 0 && (enableRuff || enableBandit)) {
        onAnalyze();
      }
    }
  };

  return (
    <div className="panel-card" style={{ flex: 1 }}>
      {/* Editor Header Bar */}
      <div className="panel-header">
        <div className="panel-title-group">
          <span style={{ color: 'var(--color-primary-electric)', fontFamily: 'var(--font-mono)' }}>
            submission.py
          </span>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', fontWeight: 400 }}>
            (Python 3.x AST)
          </span>
        </div>

        <div className="panel-actions">
          <div className="sample-btn-group">
            <button
              type="button"
              className="btn-ghost-sm"
              onClick={() => onLoadSample('vulnerable')}
              title="Load code with intentional security flaws & quality issues"
            >
              <ShieldAlert size={14} style={{ color: 'var(--color-danger)' }} />
              <span>Vulnerable Sample</span>
            </button>

            <button
              type="button"
              className="btn-ghost-sm"
              onClick={() => onLoadSample('clean')}
              title="Load secure, typed, PEP-8 compliant code"
            >
              <CheckCircle size={14} style={{ color: 'var(--color-success)' }} />
              <span>Clean Sample</span>
            </button>

            {code.length > 0 && (
              <button
                type="button"
                className="btn-ghost-sm"
                onClick={() => setCode('')}
                title="Clear code"
              >
                <RotateCcw size={13} />
                <span>Clear</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Editor Body */}
      <div className="editor-wrapper">
        <div className="editor-container">
          {/* Synchronized Line Numbers with Issue Indicators */}
          <div className="line-numbers" ref={lineNumbersRef} aria-hidden="true">
            {Array.from({ length: lineCount }, (_, i) => {
              const lineNum = i + 1;
              const lineFindings = lineFindingMap.get(lineNum);
              const hasCritical = lineFindings?.some((f) => f.severity === 'CRITICAL' || f.severity === 'HIGH');
              const hasMedium = lineFindings?.some((f) => f.severity === 'MEDIUM');

              return (
                <div
                  key={lineNum}
                  className="gutter-line"
                  style={{ cursor: lineFindings ? 'pointer' : 'default' }}
                  onClick={() => lineFindings && onSelectLineFinding?.(lineNum)}
                  title={lineFindings ? `${lineFindings.length} issue(s) on line ${lineNum}` : undefined}
                >
                  {lineFindings && (
                    <span
                      className="gutter-marker"
                      style={{
                        backgroundColor: hasCritical
                          ? 'var(--color-danger)'
                          : hasMedium
                          ? 'var(--color-warning)'
                          : 'var(--color-primary)',
                      }}
                    />
                  )}
                  <span>{lineNum}</span>
                </div>
              );
            })}
          </div>

          {/* Main Code Textarea */}
          <textarea
            ref={textareaRef}
            className="code-textarea"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            onScroll={handleScroll}
            onKeyDown={handleKeyDown}
            placeholder={`# Paste or write Python code here...\n# Click 'Vulnerable Sample' or 'Clean Sample' above to test immediately.\n\ndef calculate_discount(price: float, rate: float) -> float:\n    return price * (1.0 - rate)`}
            spellCheck={false}
            aria-label="Python Code Editor"
          />
        </div>

        {/* Scanner Selection Options Bar */}
        <div className="editor-options-bar">
          <div className="scanner-toggles">
            <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>Active Scanners:</span>
            <label className="toggle-label" title="Enable Ruff AST linter for quality, syntax & conventions">
              <input
                type="checkbox"
                checked={enableRuff}
                onChange={(e) => setEnableRuff(e.target.checked)}
              />
              <Sparkles size={13} style={{ color: 'var(--color-violet)' }} />
              <span>Ruff (Quality & PEP 8)</span>
            </label>

            <label className="toggle-label" title="Enable Bandit AST scanner for security vulnerabilities">
              <input
                type="checkbox"
                checked={enableBandit}
                onChange={(e) => setEnableBandit(e.target.checked)}
              />
              <Shield size={13} style={{ color: 'var(--color-danger)' }} />
              <span>Bandit (Security AST)</span>
            </label>
          </div>

          <div style={{ color: 'var(--text-dim)' }}>
            Ctrl + Enter to run
          </div>
        </div>

        {/* Footer Metrics & Primary Action */}
        <div className="editor-footer">
          <div className="editor-metrics">
            <span>{lineCount} {lineCount === 1 ? 'line' : 'lines'}</span>
            <span>{charCount} characters</span>
            <span style={{ color: isNearLimit ? 'var(--color-danger)' : 'inherit' }}>
              {(byteSize / 1024).toFixed(1)} KB / 100 KB
            </span>
          </div>

          <button
            type="button"
            className="btn-primary"
            onClick={onAnalyze}
            disabled={isAnalyzing || code.trim().length === 0 || (!enableRuff && !enableBandit)}
            title={
              code.trim().length === 0
                ? 'Enter code to analyze'
                : !enableRuff && !enableBandit
                ? 'Enable at least one scanner'
                : 'Execute static analysis'
            }
          >
            {isAnalyzing ? (
              <>
                <div className="spinner" />
                <span>Running Scanners...</span>
              </>
            ) : (
              <>
                <Play size={14} fill="currentColor" />
                <span>Analyze Code</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
