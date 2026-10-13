import React, { useRef } from 'react';
import { Play, ShieldAlert, CheckCircle, RotateCcw } from 'lucide-react';

interface CodeEditorProps {
  code: string;
  setCode: (code: string) => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
  onLoadSample: (type: 'vulnerable' | 'clean') => void;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  code,
  setCode,
  onAnalyze,
  isAnalyzing,
  onLoadSample,
}) => {
  const lineNumbersRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const lines = code.split('\n');
  const lineCount = Math.max(lines.length, 1);
  const charCount = code.length;
  const byteSize = new Blob([code]).size;
  const isNearLimit = byteSize > 90 * 1024;

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
      if (!isAnalyzing && code.trim().length > 0) {
        onAnalyze();
      }
    }
  };

  return (
    <div className="panel-card" style={{ flex: 1 }}>
      <div className="panel-header">
        <div className="panel-title-group">
          <span style={{ color: 'var(--color-primary)' }}>submission.py</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 400 }}>
            (Python 3.x AST)
          </span>
        </div>

        <div className="panel-actions">
          <div className="sample-btn-group">
            <button
              type="button"
              className="btn-ghost-sm"
              onClick={() => onLoadSample('vulnerable')}
              title="Load code with common security flaws & quality issues"
            >
              <ShieldAlert size={14} style={{ color: 'var(--color-danger)' }} />
              <span>Vulnerable Sample</span>
            </button>
            <button
              type="button"
              className="btn-ghost-sm"
              onClick={() => onLoadSample('clean')}
              title="Load clean, PEP-8 compliant code"
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

      <div className="editor-wrapper">
        <div className="editor-container">
          {/* Synchronized Line Numbers */}
          <div className="line-numbers" ref={lineNumbersRef}>
            {Array.from({ length: lineCount }, (_, i) => (
              <div key={i + 1}>{i + 1}</div>
            ))}
          </div>

          {/* Main Code Textarea */}
          <textarea
            ref={textareaRef}
            className="code-textarea"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            onScroll={handleScroll}
            onKeyDown={handleKeyDown}
            placeholder={`# Paste or write your Python code here...\n# Or click "Vulnerable Sample" above to test instantly.\n\ndef calculate_discount(price, rate):\n    return price * (1 - rate)`}
            spellCheck={false}
          />
        </div>

        <div className="editor-footer">
          <div className="editor-metrics">
            <span>{lineCount} {lineCount === 1 ? 'line' : 'lines'}</span>
            <span>{charCount} chars</span>
            <span style={{ color: isNearLimit ? 'var(--color-danger)' : 'inherit' }}>
              {(byteSize / 1024).toFixed(1)} KB / 100 KB
            </span>
            <span style={{ color: 'var(--text-dim)' }}>Tip: Press Ctrl + Enter to run</span>
          </div>

          <button
            type="button"
            className="btn-primary"
            onClick={onAnalyze}
            disabled={isAnalyzing || code.trim().length === 0}
            title={code.trim().length === 0 ? 'Enter code to analyze' : 'Run static analysis'}
          >
            {isAnalyzing ? (
              <>
                <div className="spinner" />
                <span>Analyzing Code...</span>
              </>
            ) : (
              <>
                <Play size={15} fill="currentColor" />
                <span>Analyze Code</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
