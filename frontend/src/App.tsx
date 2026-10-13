import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { CodeEditor } from './components/CodeEditor';
import { FindingsSummary } from './components/FindingsSummary';
import { FindingsList } from './components/FindingsList';
import { ScanHistoryModal } from './components/ScanHistoryModal';
import {
  analyzeCode,
  checkBackendHealth,
  fetchSampleCodes,
  fetchScanHistory,
  ApiError,
} from './services/api';
import type { CodeAnalysisResponse, HealthCheckResponse, ScanHistoryItem } from './types';
import { AlertTriangle, History, Shield, Info } from 'lucide-react';

export const App: React.FC = () => {
  const [code, setCode] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [result, setResult] = useState<CodeAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [samples, setSamples] = useState<{ vulnerable: string; clean: string } | null>(null);
  const [history, setHistory] = useState<ScanHistoryItem[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);

  // Initialize: Check backend health and prefetch sample codes
  useEffect(() => {
    async function init() {
      try {
        const healthData = await checkBackendHealth();
        setHealth(healthData);

        const samplesData = await fetchSampleCodes();
        setSamples(samplesData);
        // Default with vulnerable sample code so the user has immediate interactive experience
        if (samplesData?.vulnerable) {
          setCode(samplesData.vulnerable);
        }
      } catch (err) {
        console.warn('Initial backend fetch warning:', err);
      } finally {
        setLoadingHealth(false);
      }
    }
    init();
  }, []);

  // Handle sample loading
  const handleLoadSample = (type: 'vulnerable' | 'clean') => {
    setError(null);
    if (samples && samples[type]) {
      setCode(samples[type]);
    } else {
      // Local fallbacks if backend samples endpoint wasn't reached yet
      if (type === 'vulnerable') {
        setCode(
          'import os\n' +
          'import sys\n' +
          'import hashlib\n\n' +
          'def get_user_profile(user_input_id):\n' +
          '    # WARNING: SQL Injection vulnerability\n' +
          '    query = f"SELECT * FROM users WHERE id = {user_input_id}"\n' +
          '    print("Executing:", query)\n\n' +
          'DATABASE_PASSWORD = "super_secret_admin_password_123"\n\n' +
          'def verify_token(token):\n' +
          '    assert token is not None, "Token must exist"\n' +
          '    return hashlib.md5(token.encode()).hexdigest()\n\n' +
          'def run_calc(expr):\n' +
          '    return eval(expr)\n'
        );
      } else {
        setCode(
          'import hashlib\n' +
          'import os\n' +
          'from typing import Optional\n\n' +
          'def get_user_profile(user_id: int) -> dict:\n' +
          '    # Clean function with typed arguments\n' +
          '    return {"user_id": user_id, "status": "active"}\n\n' +
          'def verify_token(token: str) -> str:\n' +
          '    if not token:\n' +
          '        raise ValueError("Token must not be empty")\n' +
          '    return hashlib.sha256(token.encode()).hexdigest()\n'
        );
      }
    }
  };

  // Run code analysis
  const handleAnalyze = async () => {
    if (!code.trim()) {
      setError('Please provide Python source code to analyze.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await analyzeCode(code, 'submission.py');
      setResult(response);
      // Refresh history list
      const updatedHistory = await fetchScanHistory();
      setHistory(updatedHistory);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(`Analysis failed: ${err.message}`);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while communicating with the analysis server.');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Open history modal
  const handleOpenHistory = async () => {
    const list = await fetchScanHistory();
    setHistory(list);
    setIsHistoryOpen(true);
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header health={health} loadingHealth={loadingHealth} />

      {/* Main Workspace */}
      <main className="workspace-grid">
        {/* Left Column: Code Editor */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {error && (
            <div className="alert-banner alert-error">
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
          )}

          <CodeEditor
            code={code}
            setCode={setCode}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
            onLoadSample={handleLoadSample}
          />
        </div>

        {/* Right Column: Findings & Metrics Panel */}
        <div className="panel-card" style={{ flex: 1, minHeight: '520px' }}>
          <div className="panel-header">
            <div className="panel-title-group">
              <Shield size={16} style={{ color: 'var(--color-primary)' }} />
              <span>Analysis Findings</span>
              {result && (
                <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: 400 }}>
                  ({result.lines_analyzed} lines analyzed)
                </span>
              )}
            </div>

            <div className="panel-actions">
              <button
                type="button"
                className="btn-ghost-sm"
                onClick={handleOpenHistory}
                title="View scan history from SQLite database"
              >
                <History size={14} />
                <span>History</span>
              </button>
            </div>
          </div>

          {/* Metrics summary banner if a scan was completed */}
          {result && (
            <FindingsSummary
              summary={result.summary}
              executionTimeMs={result.execution_time_ms}
            />
          )}

          {/* Detailed findings list */}
          <FindingsList
            findings={result?.findings || []}
            hasScanned={result !== null}
          />
        </div>
      </main>

      {/* Persistent Disclaimer Bar */}
      <footer className="disclaimer-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Info size={14} style={{ color: 'var(--color-primary)', flexShrink: 0 }} />
          <span>
            {result?.disclaimer ||
              'Static analysis checks source structure without running code. It aids detection but cannot guarantee 100% bug-free software.'}
          </span>
        </div>
        <div style={{ whiteSpace: 'nowrap', color: 'var(--text-dim)' }}>
          FastAPI · Ruff · Bandit · SQLite
        </div>
      </footer>

      {/* Scan History Modal */}
      <ScanHistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={history}
      />
    </div>
  );
};

export default App;
