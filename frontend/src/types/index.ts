export type FindingSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export type FindingCategory = 'security' | 'quality' | 'style' | 'syntax';

export type VerificationStatus = 'RESOLVED' | 'STILL_DETECTED' | 'NEW_FINDING' | 'INCONCLUSIVE';

export interface Finding {
  id: string;
  tool: 'ruff' | 'bandit';
  category: FindingCategory;
  rule_id: string;
  message: string;
  severity: FindingSeverity;
  line?: number | null;
  column?: number | null;
  end_line?: number | null;
  end_column?: number | null;
  code_snippet?: string | null;
  what_detected?: string | null;
  why_it_matters?: string | null;
  where_is_it?: string | null;
  how_to_improve?: string | null;
  safer_example?: string | null;
  verification_guide?: string | null;
  recommendation?: string | null;
  documentation_url?: string | null;
}

export interface ScannerTelemetry {
  name: string;
  status: 'completed' | 'failed' | 'timed_out' | 'disabled';
  duration_ms: number;
  findings_count: number;
  error_message?: string | null;
}

export interface AnalysisSummary {
  total_findings: number;
  security_findings: number;
  quality_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  health_score: number;
  health_grade: 'A' | 'B' | 'C' | 'D' | 'F';
}

export interface CodeAnalysisResponse {
  scan_id?: number | null;
  timestamp: string;
  execution_time_ms: number;
  lines_analyzed: number;
  scanners: ScannerTelemetry[];
  summary: AnalysisSummary;
  findings: Finding[];
  disclaimer: string;
}

export interface ScanHistoryItem {
  id: number;
  timestamp: string;
  status: string;
  total_findings: number;
  security_findings: number;
  quality_findings: number;
  health_score: number;
  health_grade: string;
  execution_time_ms: number;
  code_preview: string;
}

export interface DashboardMetrics {
  total_scans: number;
  completed_scans: number;
  failed_scans: number;
  average_health_score: number;
  total_security_issues: number;
  total_quality_issues: number;
  grade_distribution: Record<string, number>;
  recent_scans: ScanHistoryItem[];
}

export interface SettingsInfo {
  ruff_available: boolean;
  bandit_available: boolean;
  ruff_path: string;
  bandit_path: string;
  max_code_size_kb: number;
  timeout_seconds: number;
  rate_limit_requests: number;
  rate_limit_window_seconds: number;
  cors_origins: string[];
  privacy_policy: string;
}

export interface HealthCheckResponse {
  status: string;
  service: string;
  tools: {
    ruff: { configured_path: string; available: boolean };
    bandit: { configured_path: string; available: boolean };
  };
}

export interface VerifyFixRequest {
  original_rule_id: string;
  original_line?: number | null;
  prior_score?: number;
  prior_finding_count?: number;
  updated_code: string;
  enable_ruff?: boolean;
  enable_bandit?: boolean;
}

export interface VerifyFixResponse {
  status: VerificationStatus;
  rule_id: string;
  message: string;
  health_score_delta: number;
  prior_score: number;
  new_score: number;
  prior_finding_count: number;
  new_finding_count: number;
  subsequent_analysis: CodeAnalysisResponse;
  disclaimer: string;
}

export interface ScanComparisonRequest {
  base_scan_id: number;
  subsequent_scan_id: number;
}

export interface ScanComparisonResponse {
  base_scan_id?: number | null;
  subsequent_scan_id?: number | null;
  resolved_count: number;
  remaining_count: number;
  new_count: number;
  score_delta: number;
  disclaimer: string;
}

export interface FindingExplanationResponse {
  rule_id: string;
  explanation: string;
  is_ai_generated: boolean;
  disclaimer: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  created_at: string;
}

export interface AuthSuccessResponse {
  user: User;
  message: string;
  token: string;
}

export interface FindingContext {
  rule_id: string;
  tool: string;
  severity: FindingSeverity;
  message: string;
  line?: number | null;
  code_snippet?: string | null;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender: 'user' | 'assistant';
  content: string;
  created_at: string;
  finding_context?: FindingContext | null;
  is_ai?: boolean;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface AIStatus {
  available: boolean;
  model: string;
  message: string;
}
