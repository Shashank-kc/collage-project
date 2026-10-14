import React, { useState, useEffect } from 'react';
import { Header, type ActiveTab } from './components/Header';
import { CodeEditor } from './components/CodeEditor';
import { FindingsSummary } from './components/FindingsSummary';
import { FindingsList } from './components/FindingsList';
import { DashboardView } from './components/DashboardView';
import { HistoryView } from './components/HistoryView';
import { SettingsView } from './components/SettingsView';
import {
  analyzeCode,
  checkBackendHealth,
  fetchMetrics,
  fetchSampleCodes,
  fetchScanHistory,
  fetchSettings,
  ApiError,
} from './services/api';
import type {
  CodeAnalysisResponse,
  DashboardMetrics,
  HealthCheckResponse,
  ScanHistoryItem,
  SettingsInfo,
} from './types';
import { AlertTriangle, Shield, Info } from 'lucide-react';

export const App: React.FC = () => {
  // Navigation & View state
  const [activeTab, setActiveTab] = useState<ActiveTab>('workspace');

  // Code & Analysis state
  const [code, setCode] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [result, setResult] = useState<CodeAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedLine, setSelectedLine] = useState<number | null>(null);

  // Scanner options
  const [enableRuff, setEnableRuff] = useState<boolean>(true);
  const [enableBandit, setEnableBandit] = useState<boolean>(true);

  // Telemetry & Data state
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [samples, setSamples] = useState<{ vulnerable: string; clean: string } | null>(null);
  const [history, setHistory] = useState<ScanHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState<boolean>(false);
  const [settings, setSettings] = useState<SettingsInfo | null>(null);
  const [loadingSettings, setLoadingSettings] = useState<boolean>(false);

  // Initial load: check health and fetch sample code
  useEffect(() => {
    async function init() {
      try {
        const healthData = await checkBackendHealth();
        setHealth(healthData);

        const samplesData = await fetchSampleCodes();
        setSamples(samplesData);
        // Pre-fill vulnerable sample so the user has immediate interactive experience
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

  // Refresh tab-specific data when tab changes
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadMetrics();
    } else if (activeTab === 'history') {
      loadHistory();
    } else if (activeTab === 'settings') {
      loadSettings();
    }
  }, [activeTab]);

  const loadMetrics = async () => {
    setLoadingMetrics(true);
    const data = await fetchMetrics();
    setMetrics(data);
    setLoadingMetrics(false);
  };

  const loadHistory = async () => {
    setLoadingHistory(true);
    const data = await fetchScanHistory(25);
    setHistory(data);
    setLoadingHistory(false);
  };

  const loadSettings = async () => {
    setLoadingSettings(true);
    const data = await fetchSettings();
    setSettings(data);
    setLoadingSettings(false);
  };

  // Sample loader
  const handleLoadSample = (type: 'vulnerable' | 'clean') => {
    setError(null);
    setSelectedLine(null);
    if (samples && samples[type]) {
      setCode(samples[type]);
    } else {
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

  // Start fresh analysis
  const handleNewAnalysis = () => {
    setCode('');
    setResult(null);
    setError(null);
    setSelectedLine(null);
    setActiveTab('workspace');
  };

  // Select past scan code from Dashboard or History
  const handleSelectPastScan = (codePreview: string) => {
    setCode(codePreview);
    setResult(null);
    setSelectedLine(null);
    setActiveTab('workspace');
  };

  // Run analysis
  const handleAnalyze = async () => {
    if (!code.trim()) {
      setError('Please provide Python source code to analyze.');
      return;
    }

    if (!enableRuff && !enableBandit) {
      setError('Please enable at least one static analysis engine (Ruff or Bandit).');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setSelectedLine(null);

    try {
      const response = await analyzeCode(code, 'submission.py', enableRuff, enableBandit);
      setResult(response);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(`Analysis failed (${err.status}): ${err.message}`);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while communicating with the analysis server.');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header
        health={health}
        loadingHealth={loadingHealth}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onNewAnalysis={handleNewAnalysis}
      />

      {/* View Switcher Routing */}
      {activeTab === 'workspace' && (
        <main className="workspace-grid">
          {/* Left Column: Code Editor */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {error && (
              <div className="alert-banner alert-error" role="alert">
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
              enableRuff={enableRuff}
              setEnableRuff={setEnableRuff}
              enableBandit={enableBandit}
              setEnableBandit={setEnableBandit}
              findings={result?.findings || []}
              onSelectLineFinding={(line) => setSelectedLine(line === selectedLine ? null : line)}
            />
          </div>

          {/* Right Column: Findings & Metrics Panel */}
          <div className="panel-card" style={{ flex: 1, minHeight: '520px' }}>
            <div className="panel-header">
              <div className="panel-title-group">
                <Shield size={16} style={{ color: 'var(--color-primary-electric)' }} />
                <span>Inspection Findings</span>
                {result && (
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: 400 }}>
                    ({result.lines_analyzed} lines analyzed)
                  </span>
                )}
              </div>

              {selectedLine && (
                <button
                  type="button"
                  className="btn-ghost-sm"
                  onClick={() => setSelectedLine(null)}
                  title="Clear line filter"
                >
                  Clear Line {selectedLine} Filter
                </button>
              )}
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
              scanners={result?.scanners || []}
              hasScanned={result !== null}
              selectedLine={selectedLine}
            />
          </div>
        </main>
      )}

      {activeTab === 'dashboard' && (
        <DashboardView
          metrics={metrics}
          loadingMetrics={loadingMetrics}
          onSelectScan={handleSelectPastScan}
          onGoToWorkspace={() => setActiveTab('workspace')}
        />
      )}

      {activeTab === 'history' && (
        <HistoryView
          history={history}
          loadingHistory={loadingHistory}
          onSelectScan={handleSelectPastScan}
          onRefresh={loadHistory}
        />
      )}

      {activeTab === 'settings' && (
        <SettingsView
          settings={settings}
          loadingSettings={loadingSettings}
          enableRuff={enableRuff}
          setEnableRuff={setEnableRuff}
          enableBandit={enableBandit}
          setEnableBandit={setEnableBandit}
        />
      )}

      {/* Persistent Disclaimer Bar */}
      <footer className="disclaimer-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Info size={14} style={{ color: 'var(--color-primary-electric)', flexShrink: 0 }} />
          <span>
            {result?.disclaimer ||
              'Static analysis inspects code structure without execution. It aids defect detection but cannot guarantee 100% bug-free software.'}
          </span>
        </div>
        <div style={{ whiteSpace: 'nowrap', color: 'var(--text-dim)', fontSize: '0.73rem' }}>
          FastAPI · Ruff · Bandit · SQLite · Isolated AST
        </div>
      </footer>
    </div>
  );
};

export default App;
