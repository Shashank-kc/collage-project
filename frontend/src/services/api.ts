import type {
  AIStatus,
  AuthSuccessResponse,
  ChatMessage,
  CodeAnalysisResponse,
  ConversationDetail,
  ConversationSummary,
  DashboardMetrics,
  FindingContext,
  FindingExplanationResponse,
  HealthCheckResponse,
  ScanComparisonResponse,
  ScanHistoryItem,
  SettingsInfo,
  User,
  VerifyFixResponse,
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

async function handleResponse<T>(response: Response, defaultErrorMsg: string): Promise<T> {
  if (!response.ok) {
    let errorMsg = defaultErrorMsg;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      errorMsg = `${defaultErrorMsg} (${response.status}: ${response.statusText})`;
    }
    throw new ApiError(response.status, errorMsg);
  }
  return response.json();
}

// =========================================================================
// AUTHENTICATION APIs
// =========================================================================

export async function registerUser(fullName: string, email: string, password: string): Promise<AuthSuccessResponse> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ full_name: fullName, email, password }),
  });
  return handleResponse<AuthSuccessResponse>(response, 'Registration failed.');
}

export async function loginUser(email: string, password: string, rememberMe: boolean = false): Promise<AuthSuccessResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, remember_me: rememberMe }),
  });
  return handleResponse<AuthSuccessResponse>(response, 'Sign in failed.');
}

export async function logoutUser(): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  return handleResponse<{ message: string }>(response, 'Sign out failed.');
}

export async function fetchCurrentUser(): Promise<User | null> {
  try {
    const response = await fetch(`${API_BASE}/auth/me`, {
      method: 'GET',
      credentials: 'include',
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

// =========================================================================
// CODE ANALYSIS & SCANNERS
// =========================================================================

export async function analyzeCode(
  code: string,
  filename: string = 'submission.py',
  enableRuff: boolean = true,
  enableBandit: boolean = true
): Promise<CodeAnalysisResponse> {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    credentials: 'include',
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
  return handleResponse<CodeAnalysisResponse>(response, 'Failed to analyze code.');
}

export async function fetchScanHistory(limit: number = 20): Promise<ScanHistoryItem[]> {
  try {
    const response = await fetch(`${API_BASE}/history?limit=${limit}`, {
      credentials: 'include',
    });
    if (!response.ok) return [];
    return response.json();
  } catch {
    return [];
  }
}

export async function fetchMetrics(): Promise<DashboardMetrics | null> {
  try {
    const response = await fetch(`${API_BASE}/metrics`, {
      credentials: 'include',
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function fetchSettings(): Promise<SettingsInfo | null> {
  try {
    const response = await fetch(`${API_BASE}/settings`, {
      credentials: 'include',
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function fetchSampleCodes(): Promise<{ vulnerable: string; clean: string }> {
  const response = await fetch(`${API_BASE}/samples`, {
    credentials: 'include',
  });
  return handleResponse<{ vulnerable: string; clean: string }>(response, 'Unable to load sample codes.');
}

export async function checkBackendHealth(): Promise<HealthCheckResponse | null> {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      credentials: 'include',
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function verifyFix(payload: {
  original_rule_id: string;
  original_line?: number | null;
  prior_score?: number;
  prior_finding_count?: number;
  updated_code: string;
  enable_ruff?: boolean;
  enable_bandit?: boolean;
}): Promise<VerifyFixResponse> {
  const response = await fetch(`${API_BASE}/verify-fix`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<VerifyFixResponse>(response, 'Failed to verify fix.');
}

export async function compareScans(baseScanId: number, subsequentScanId: number): Promise<ScanComparisonResponse> {
  const response = await fetch(`${API_BASE}/compare-scans`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      base_scan_id: baseScanId,
      subsequent_scan_id: subsequentScanId,
    }),
  });
  return handleResponse<ScanComparisonResponse>(response, 'Unable to compare scans.');
}

export async function explainFinding(
  ruleId: string,
  message: string,
  codeSnippet?: string | null
): Promise<FindingExplanationResponse> {
  const response = await fetch(`${API_BASE}/explain-finding`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      rule_id: ruleId,
      message,
      code_snippet: codeSnippet || null,
    }),
  });
  return handleResponse<FindingExplanationResponse>(response, 'Unable to generate explanation.');
}

// =========================================================================
// AI ASSISTANT APIS (OPENAI RESPONSES API)
// =========================================================================

export async function fetchAIStatus(): Promise<AIStatus> {
  const response = await fetch(`${API_BASE}/assistant/status`, {
    credentials: 'include',
  });
  return handleResponse<AIStatus>(response, 'Unable to check AI Assistant status.');
}

export async function fetchConversations(): Promise<ConversationSummary[]> {
  const response = await fetch(`${API_BASE}/assistant/conversations`, {
    credentials: 'include',
  });
  return handleResponse<ConversationSummary[]>(response, 'Failed to load conversations.');
}

export async function createConversation(title?: string): Promise<ConversationSummary> {
  const url = title
    ? `${API_BASE}/assistant/conversations?title=${encodeURIComponent(title)}`
    : `${API_BASE}/assistant/conversations`;
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'include',
  });
  return handleResponse<ConversationSummary>(response, 'Failed to start conversation.');
}

export async function fetchConversationDetail(conversationId: string): Promise<ConversationDetail> {
  const response = await fetch(`${API_BASE}/assistant/conversations/${conversationId}`, {
    credentials: 'include',
  });
  return handleResponse<ConversationDetail>(response, 'Failed to load conversation history.');
}

export async function deleteConversation(conversationId: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/assistant/conversations/${conversationId}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  return handleResponse<{ message: string }>(response, 'Failed to delete conversation.');
}

export async function sendChatMessage(payload: {
  message: string;
  conversation_id?: string;
  finding_context?: FindingContext;
  include_code?: boolean;
}): Promise<ChatMessage> {
  const response = await fetch(`${API_BASE}/assistant/chat`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<ChatMessage>(response, 'AI Assistant request failed.');
}
