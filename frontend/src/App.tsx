import React, { useState, useEffect, useCallback } from 'react';
import { Header, type ActiveTab } from './components/Header';
import { WorkspaceSidebar } from './components/WorkspaceSidebar';
import { CodeEditor } from './components/CodeEditor';
import { FindingsSummary } from './components/FindingsSummary';
import { FindingsList } from './components/FindingsList';
import { FixVerificationPanel } from './components/FixVerificationPanel';
import { ScanComparisonModal } from './components/ScanComparisonModal';
import { DashboardView } from './components/DashboardView';
import { HistoryView } from './components/HistoryView';
import { SettingsView } from './components/SettingsView';
import { AssistantView } from './components/AssistantView';
import { AuthView } from './components/AuthView';
import {
  analyzeCode,
  checkBackendHealth,
  fetchCurrentUser,
  fetchMetrics,
  fetchSampleCodes,
  fetchScanHistory,
  fetchSettings,
  logoutUser,
  verifyFix,
  ApiError,
} from './services/api';
import type {
  CodeAnalysisResponse,
  DashboardMetrics,
  Finding,
  FindingContext,
  HealthCheckResponse,
  ScanHistoryItem,
  SettingsInfo,
  User,
  VerifyFixResponse,
} from './types';
import { AlertTriangle, Info, Wrench, ListFilter, X } from 'lucide-react';

export const App: React.FC = () => {
  // Authentication state
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');

  // Navigation & View state
  const [activeTab, setActiveTab] = useState<ActiveTab>('workspace');

  // AI Assistant Context state
  const [pendingFindingContext, setPendingFindingContext] = useState<FindingContext | null>(null);

  // 3-Panel Workspace state
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [rightPanelTab, setRightPanelTab] = useState<'findings' | 'inspector'>('findings');
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  // Code & Analysis state
  const [code, setCode] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [result, setResult] = useState<CodeAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedLine, setSelectedLine] = useState<number | null>(null);

  // Fix Verification Engine state
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [lastVerificationResult, setLastVerificationResult] = useState<VerifyFixResponse | null>(null);

  // Scan Comparison state
  const [showComparisonModal, setShowComparisonModal] = useState<boolean>(false);

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

  // Initial load: resolve current session, check health, and fetch samples
  useEffect(() => {
    async function init() {
      try {
        // Resolve authenticated user session if present
        const user = await fetchCurrentUser();
        setCurrentUser(user);

        const healthData = await checkBackendHealth();
        setHealth(healthData);

        const samplesData = await fetchSampleCodes();
        setSamples(samplesData);
        if (samplesData?.vulnerable) {
          setCode(samplesData.vulnerable);
        }

        const historyData = await fetchScanHistory(10);
        setHistory(historyData);
      } catch (err) {
        console.warn('Initial backend fetch warning:', err);
      } finally {
        setLoadingHealth(false);
      }
    }
    init();
  }, []);

  const loadMetrics = useCallback(async () => {
    setLoadingMetrics(true);
    const data = await fetchMetrics();
    setMetrics(data);
    setLoadingMetrics(false);
  }, []);

  const loadHistory = useCallback(async () => {
    setLoadingHistory(true);
    const data = await fetchScanHistory(25);
    setHistory(data);
    setLoadingHistory(false);
  }, []);

  const loadSettings = useCallback(async () => {
    setLoadingSettings(true);
    const data = await fetchSettings();
    setSettings(data);
    setLoadingSettings(false);
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
  }, [activeTab, loadMetrics, loadHistory, loadSettings]);

  // Auth Handlers
  const handleAuthSuccess = (user: User) => {
    setCurrentUser(user);
    setShowAuthModal(false);
    // Reload isolated history and metrics for the logged-in user
    loadHistory();
    loadMetrics();
  };

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch (err) {
      console.warn('Logout warning:', err);
    } finally {
      setCurrentUser(null);
      loadHistory();
      loadMetrics();
    }
  };

  // Open AI Assistant with finding context ("Ask AI about this finding")
  const handleAskAIAboutFinding = (finding: Finding) => {
    setPendingFindingContext({
      rule_id: finding.rule_id,
      tool: finding.tool,
      severity: finding.severity,
      message: finding.message,
      line: finding.line,
      code_snippet: finding.code_snippet,
    });
    setActiveTab('assistant');
  };

  // Sample loader
  const handleLoadSample = (type: 'vulnerable' | 'clean') => {
    setError(null);
    setSelectedLine(null);
    setSelectedFinding(null);
    setLastVerificationResult(null);
    setRightPanelTab('findings');

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
    setSelectedFinding(null);
    setLastVerificationResult(null);
    setRightPanelTab('findings');
    setActiveTab('workspace');
  };

  // Select past scan code from Dashboard or History
  const handleSelectPastScan = (codePreview: string) => {
    setCode(codePreview);
    setResult(null);
    setSelectedLine(null);
    setSelectedFinding(null);
    setLastVerificationResult(null);
    setRightPanelTab('findings');
    setActiveTab('workspace');
  };

  // Run full static analysis
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
    setSelectedFinding(null);
    setLastVerificationResult(null);

    try {
      const response = await analyzeCode(code, 'submission.py', enableRuff, enableBandit);
      setResult(response);
      setRightPanelTab('findings');
      // Refresh history silently
      fetchScanHistory(10).then((h) => setHistory(h));
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

  // Select a finding to inspect in Fix Verification Panel
  const handleSelectFinding = (finding: Finding) => {
    setSelectedFinding(finding);
    setRightPanelTab('inspector');
    if (finding.line) {
      setSelectedLine(finding.line);
    }
  };

  // Apply proposed safer code snippet to editor
  const handleApplyFixSnippet = (saferSnippet: string) => {
    if (selectedFinding?.code_snippet && code.includes(selectedFinding.code_snippet)) {
      const updated = code.replace(selectedFinding.code_snippet, saferSnippet.trim());
      setCode(updated);
    } else {
      setCode((prev) => `${prev.trim()}\n\n# Verified Remediation Applied:\n${saferSnippet.trim()}\n`);
    }
  };

  // Re-Scan & Verify Fix
  const handleVerifyFix = async (ruleId: string, line?: number | null) => {
    setIsVerifying(true);
    try {
      const verifyRes = await verifyFix({
        original_rule_id: ruleId,
        original_line: line,
        prior_score: result?.summary.health_score || 100,
        prior_finding_count: result?.findings.length || 1,
        updated_code: code,
        enable_ruff: enableRuff,
        enable_bandit: enableBandit,
      });

      setLastVerificationResult(verifyRes);

      if (verifyRes.subsequent_analysis) {
        setResult(verifyRes.subsequent_analysis);
      }

      return verifyRes;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Fix verification failed.';
      setError(`Verification error: ${msg}`);
      return null;
    } finally {
      setIsVerifying(false);
    }
  };

  const lines = code.split('\n');
  const lineCount = Math.max(lines.length, 1);
  const byteSize = new Blob([code]).size;

  return (
    <div className="app-container">
      {/* Top Header with AI Assistant Tab and User Auth Controls */}
      <Header
        health={health}
        loadingHealth={loadingHealth}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onNewAnalysis={handleNewAnalysis}
        onOpenComparison={() => setShowComparisonModal(true)}
        currentUser={currentUser}
        onOpenAuth={() => {
          setAuthModalMode('login');
          setShowAuthModal(true);
        }}
        onLogout={handleLogout}
      />

      {/* Main Views */}
      {activeTab === 'workspace' && (
        <main className="workspace-3panel-layout">
          {/* Panel 1: Left Navigation & File Tree Sidebar */}
          <WorkspaceSidebar
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen((prev) => !prev)}
            fileName="submission.py"
            lineCount={lineCount}
            byteSize={byteSize}
            onLoadSample={handleLoadSample}
            recentScans={history}
            onSelectScan={handleSelectPastScan}
            onNewAnalysis={handleNewAnalysis}
            enableRuff={enableRuff}
            enableBandit={enableBandit}
          />

          {/* Panel 2: Center Code Editor */}
          <div className="workspace-center-panel">
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
              onSelectLineFinding={(line) => {
                setSelectedLine(line === selectedLine ? null : line);
                const matching = result?.findings.find((f) => f.line === line);
                if (matching) {
                  setSelectedFinding(matching);
                  setRightPanelTab('inspector');
                }
              }}
            />
          </div>

          {/* Panel 3: Right Findings & Fix Verification Panel */}
          <div className="workspace-right-panel panel-card">
            {/* Right Panel Header Tabs */}
            <div className="panel-header" style={{ padding: '8px 14px' }}>
              <div className="right-panel-tab-group">
                <button
                  type="button"
                  className={`right-tab-btn ${rightPanelTab === 'findings' ? 'active' : ''}`}
                  onClick={() => setRightPanelTab('findings')}
                >
                  <ListFilter size={14} />
                  <span>Findings</span>
                  {result && (
                    <span className="tab-count-badge">
                      {result.findings.length}
                    </span>
                  )}
                </button>

                <button
                  type="button"
                  className={`right-tab-btn ${rightPanelTab === 'inspector' ? 'active' : ''}`}
                  onClick={() => setRightPanelTab('inspector')}
                >
                  <Wrench size={14} style={{ color: 'var(--color-amber)' }} />
                  <span>Explain · Fix · Verify</span>
                  {selectedFinding && (
                    <span className="tab-active-dot" />
                  )}
                </button>
              </div>

              {selectedLine && (
                <button
                  type="button"
                  className="btn-ghost-sm"
                  onClick={() => {
                    setSelectedLine(null);
                    setSelectedFinding(null);
                  }}
                  title="Clear line filter"
                >
                  Clear Line {selectedLine}
                </button>
              )}
            </div>

            {/* Content View Based on Tab */}
            {rightPanelTab === 'findings' ? (
              <>
                {result && (
                  <FindingsSummary
                    summary={result.summary}
                    executionTimeMs={result.execution_time_ms}
                  />
                )}
                <FindingsList
                  findings={result?.findings || []}
                  scanners={result?.scanners || []}
                  hasScanned={result !== null}
                  selectedLine={selectedLine}
                  onSelectFinding={handleSelectFinding}
                  selectedFindingId={selectedFinding?.id}
                  onAskAIAboutFinding={handleAskAIAboutFinding}
                />
              </>
            ) : (
              <FixVerificationPanel
                finding={selectedFinding}
                onClose={() => setRightPanelTab('findings')}
                onApplyFixSnippet={handleApplyFixSnippet}
                onVerifyFix={handleVerifyFix}
                isVerifying={isVerifying}
                lastVerificationResult={lastVerificationResult}
                onClearVerificationResult={() => setLastVerificationResult(null)}
                onAskAIAboutFinding={handleAskAIAboutFinding}
              />
            )}
          </div>
        </main>
      )}

      {/* AI Assistant Tab View */}
      {activeTab === 'assistant' && (
        <AssistantView
          currentUser={currentUser}
          onRequireAuth={() => {
            setAuthModalMode('login');
            setShowAuthModal(true);
          }}
          pendingFindingContext={pendingFindingContext}
          onClearPendingFinding={() => setPendingFindingContext(null)}
        />
      )}

      {/* Developer Analytics Dashboard */}
      {activeTab === 'dashboard' && (
        <DashboardView
          metrics={metrics}
          loadingMetrics={loadingMetrics}
          onSelectScan={handleSelectPastScan}
          onGoToWorkspace={() => setActiveTab('workspace')}
        />
      )}

      {/* Isolated Scan History */}
      {activeTab === 'history' && (
        <HistoryView
          history={history}
          loadingHistory={loadingHistory}
          onSelectScan={handleSelectPastScan}
          onRefresh={loadHistory}
        />
      )}

      {/* System Settings & Telemetry */}
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

      {/* Global Scan Comparison Modal */}
      <ScanComparisonModal
        isOpen={showComparisonModal}
        onClose={() => setShowComparisonModal(false)}
        history={history}
      />

      {/* Auth Modal Overlay */}
      {showAuthModal && (
        <div className="modal-backdrop" onClick={() => setShowAuthModal(false)}>
          <div className="modal-content auth-modal-box" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '-16px' }}>
              <button
                type="button"
                className="btn-icon"
                onClick={() => setShowAuthModal(false)}
                title="Close"
              >
                <X size={18} />
              </button>
            </div>
            <AuthView
              onAuthSuccess={handleAuthSuccess}
              onCancel={() => setShowAuthModal(false)}
              initialMode={authModalMode}
            />
          </div>
        </div>
      )}

      {/* Persistent Status / Disclaimer Bar */}
      <footer className="disclaimer-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Info size={14} style={{ color: 'var(--color-amber)', flexShrink: 0 }} />
          <span>
            {result?.disclaimer ||
              'Static AST inspection analyzes code structure without execution. It aids defect detection but cannot guarantee 100% bug-free software.'}
          </span>
        </div>
        <div style={{ whiteSpace: 'nowrap', color: 'var(--text-dim)', fontSize: '0.73rem' }}>
          CodeGuard AI 2.1 · Explain. Fix. Verify. · Ruff & Bandit AST · OpenAI API
        </div>
      </footer>
    </div>
  );
};

export default App;
