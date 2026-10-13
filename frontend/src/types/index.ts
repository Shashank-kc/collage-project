export type FindingSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export type FindingCategory = 'security' | 'quality' | 'style' | 'syntax';

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
  recommendation?: string | null;
  documentation_url?: string | null;
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
  summary: AnalysisSummary;
  findings: Finding[];
  disclaimer: string;
}

export interface ScanHistoryItem {
  id: number;
  timestamp: string;
  total_findings: number;
  security_findings: number;
  quality_findings: number;
  health_score: number;
  health_grade: string;
  execution_time_ms: number;
  code_preview: string;
}

export interface HealthCheckResponse {
  status: string;
  service: string;
  tools: {
    ruff: { configured_path: string; available: boolean };
    bandit: { configured_path: string; available: boolean };
  };
}
