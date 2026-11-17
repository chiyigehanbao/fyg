export type DiagnosisStatus =
  | "basic_collecting"
  | "basic_generating"
  | "basic_report_ready"
  | "advanced_collecting"
  | "final_generating"
  | "final_report_ready";

export type ModelStatus = {
  connected: boolean;
  model: string;
  available: boolean;
  provider: "ollama";
  models?: string[];
  error?: string | null;
};

export type SystemStatus = {
  api: {
    connected: boolean;
    status: string;
    service?: string;
    capabilities?: string[];
  };
  database: {
    connected: boolean;
    driver: string;
    host: string | null;
    name: string | null;
    error: string | null;
  };
  data: {
    cases: number;
    interview_sessions: number;
    reports: number;
    report_revisions: number;
  };
  model: ModelStatus;
  config: {
    ollama_base_url: string;
    ollama_model: string;
    ollama_keep_alive: string;
    cors_allowed_origins?: string[];
    frontend_dist_dir?: string | null;
  };
};

export type DiagnosisCase = {
  id: string;
  scenario: string;
  challenge: string;
  subject_label: string;
  status: DiagnosisStatus;
  created_at: string | null;
  updated_at: string | null;
};

export type InterviewQuestion = {
  id: string;
  title: string;
  prompt: string;
  hint: string;
  type: "text" | "textarea" | "single" | "multi";
  options: string[];
  required: boolean;
};

export type AnswerValue = string | string[];

export type Interview = {
  case_id: string;
  stage: "basic" | "advanced";
  questions: InterviewQuestion[];
  answers: Record<string, AnswerValue>;
};

export type InsightItem = {
  title: string;
  detail: string;
  evidence?: string;
};

export type OpportunityItem = {
  title: string;
  description: string;
  priority: string;
  why: string;
};

export type BasicReportContent = {
  diagnosis: string;
  pain_points: InsightItem[];
  opportunities: OpportunityItem[];
  quick_start: { title: string; steps: string[] };
  readiness: { level: string; detail: string };
  missing_information: string[];
  conclusion: string;
  generation_mode?: string;
};

export type CapabilityItem = { title: string; detail: string };
export type ImplementationPhase = { name: string; goal: string; deliverables: string[] };
export type RiskItem = { risk: string; mitigation: string };

export type FinalReportContent = {
  executive_summary: string;
  solution: { name: string; positioning: string; description: string };
  capabilities: CapabilityItem[];
  target_journey: string[];
  data_and_integrations: string[];
  implementation_phases: ImplementationPhase[];
  success_metrics: string[];
  risks: RiskItem[];
  deliverables: string[];
  next_action: string;
  source_diagnosis?: string;
  generation_mode?: string;
};

export type DiagnosisReport<T> = {
  case_id: string;
  stage: "basic" | "final";
  title: string;
  summary: string;
  content: T;
  version: number;
  updated_at: string | null;
};

type ApiValidationError = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
};

type ApiErrorDetail = string | ApiValidationError[] | {
  message?: string;
  question_ids?: string[];
};

export class ApiError extends Error {
  status: number;
  detail: ApiErrorDetail | null;
  questionIds: string[];

  constructor(status: number, detail: ApiErrorDetail | null, fallback: string) {
    const message = Array.isArray(detail)
      ? detail.find((item) => item.msg)?.msg
      : typeof detail === "string"
        ? detail
        : detail?.message;
    super(message || fallback);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.questionIds = detail && !Array.isArray(detail) && typeof detail === "object" ? detail.question_ids ?? [] : [];
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${apiBaseUrl}${normalizedPath}`;
}

async function parseResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    let detail: ApiErrorDetail | null = null;
    if (text) {
      try {
        const parsed = JSON.parse(text) as { detail?: ApiErrorDetail };
        detail = parsed.detail ?? text;
      } catch {
        detail = text;
      }
    }
    throw new ApiError(res.status, detail, `request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  return parseResponse(await fetch(apiUrl(path), init));
}

async function apiRequestVoid(path: string, init?: RequestInit): Promise<void> {
  const res = await fetch(apiUrl(path), init);
  if (!res.ok) {
    await parseResponse<never>(res);
  }
}

export async function fetchModelStatus(): Promise<ModelStatus> {
  return apiRequest("/api/model/status");
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  return apiRequest("/api/system/status");
}

export function systemBackupUrl(): string {
  return apiUrl("/api/system/backup");
}

export async function createDiagnosisCase(payload: {
  scenario: string;
  challenge: string;
  subject_label?: string;
}): Promise<DiagnosisCase> {
  return apiRequest("/api/cases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchDiagnosisCases(): Promise<DiagnosisCase[]> {
  return apiRequest("/api/cases");
}

export async function fetchDiagnosisCase(caseId: string): Promise<DiagnosisCase> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}`);
}

export async function duplicateDiagnosisCase(caseId: string): Promise<DiagnosisCase> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/duplicate`, {
    method: "POST",
  });
}

export async function deleteDiagnosisCase(caseId: string): Promise<void> {
  await apiRequestVoid(`/api/cases/${encodeURIComponent(caseId)}`, {
    method: "DELETE",
  });
}

export function caseExportUrl(caseId: string): string {
  return apiUrl(`/api/cases/${encodeURIComponent(caseId)}/export.json`);
}

export async function fetchInterview(
  caseId: string,
  stage: "basic" | "advanced",
): Promise<Interview> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/interviews/${stage}`);
}

export async function saveInterviewAnswers(
  caseId: string,
  stage: "basic" | "advanced",
  answers: Record<string, AnswerValue>,
): Promise<Interview> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/interviews/${stage}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });
}

export async function generateBasicReport(
  caseId: string,
  note = "",
): Promise<DiagnosisReport<BasicReportContent>> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/reports/basic/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
}

export async function startAdvancedInterview(caseId: string): Promise<Interview> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/advanced/start`, {
    method: "POST",
  });
}

export async function rebuildAdvancedInterview(caseId: string): Promise<Interview> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/advanced/rebuild`, {
    method: "POST",
  });
}

export async function generateFinalReport(
  caseId: string,
  note = "",
): Promise<DiagnosisReport<FinalReportContent>> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/reports/final/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
}

export async function fetchBasicReport(
  caseId: string,
): Promise<DiagnosisReport<BasicReportContent>> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/reports/basic`);
}

export async function fetchFinalReport(
  caseId: string,
): Promise<DiagnosisReport<FinalReportContent>> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/reports/final`);
}

export async function fetchReportVersions(
  caseId: string,
  stage: "basic",
): Promise<DiagnosisReport<BasicReportContent>[]>;
export async function fetchReportVersions(
  caseId: string,
  stage: "final",
): Promise<DiagnosisReport<FinalReportContent>[]>;
export async function fetchReportVersions(
  caseId: string,
  stage: "basic" | "final",
): Promise<DiagnosisReport<BasicReportContent | FinalReportContent>[]> {
  return apiRequest(`/api/cases/${encodeURIComponent(caseId)}/reports/${stage}/versions`);
}

export async function fetchReportVersion(
  caseId: string,
  stage: "basic" | "final",
  version: number,
): Promise<DiagnosisReport<BasicReportContent | FinalReportContent>> {
  return apiRequest(
    `/api/cases/${encodeURIComponent(caseId)}/reports/${stage}/versions/${encodeURIComponent(version)}`,
  );
}

export function reportExportUrl(
  caseId: string,
  stage: "basic" | "final",
  version?: number,
  format: "docx" | "pdf" = "docx",
): string {
  const base = `/api/cases/${encodeURIComponent(caseId)}/reports/${stage}`;
  if (version) return apiUrl(`${base}/versions/${encodeURIComponent(version)}/export.${format}`);
  return apiUrl(`${base}/export.${format}`);
}
