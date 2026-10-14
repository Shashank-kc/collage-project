import type {
  CodeAnalysisResponse,
  DashboardMetrics,
  HealthCheckResponse,
  ScanHistoryItem,
  SettingsInfo,
} from '../types';

const API_BASE = '/api/v1';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

export async function analyzeCode(
  code: string,
  filename: string = 'submission.py',
  enableRuff: boolean = true,
  enableBandit: boolean = true
): Promise<CodeAnalysisResponse> {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      code,
      filename,
      enable_ruff: enableRuff,
      enable_bandit: enableBandit,
    }),
  });

  if (!response.ok) {
    let errorMsg = 'Failed to analyze code.';
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      errorMsg = `Server error (${response.status}: ${response.statusText})`;
    }
    throw new ApiError(response.status, errorMsg);
  }

  return response.json();
}

export async function fetchScanHistory(limit: number = 20): Promise<ScanHistoryItem[]> {
  try {
    const response = await fetch(`${API_BASE}/history?limit=${limit}`);
    if (!response.ok) return [];
    return response.json();
  } catch {
    return [];
  }
}

export async function fetchMetrics(): Promise<DashboardMetrics | null> {
  try {
    const response = await fetch(`${API_BASE}/metrics`);
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function fetchSettings(): Promise<SettingsInfo | null> {
  try {
    const response = await fetch(`${API_BASE}/settings`);
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function fetchSampleCodes(): Promise<{ vulnerable: string; clean: string }> {
  const response = await fetch(`${API_BASE}/samples`);
  if (!response.ok) {
    throw new Error('Unable to load sample codes.');
  }
  return response.json();
}

export async function checkBackendHealth(): Promise<HealthCheckResponse | null> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}
