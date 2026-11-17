import type { DiagnosisCase } from "@/api/diagnosis";

export const appRoutePatterns = {
  home: "/",
  start: "/start",
  login: "/login",
  register: "/register",
  workspace: "/workspace",
  settings: "/settings",
  basicInterview: "/cases/:caseId/basic",
  basicReport: "/cases/:caseId/reports/basic",
  advancedInterview: "/cases/:caseId/advanced",
  finalReport: "/cases/:caseId/reports/final",
  legacyAdmin: "/admin/*",
  notFound: "*",
} as const;

export const appPaths = {
  home: "/",
  start: "/start",
  workspace: "/workspace",
  settings: "/settings",
  basicInterview: (caseId: string) => `/cases/${encodeURIComponent(caseId)}/basic`,
  basicReport: (caseId: string) => `/cases/${encodeURIComponent(caseId)}/reports/basic`,
  advancedInterview: (caseId: string) => `/cases/${encodeURIComponent(caseId)}/advanced`,
  finalReport: (caseId: string) => `/cases/${encodeURIComponent(caseId)}/reports/final`,
} as const;

export function casePathByStatus(row: DiagnosisCase): string {
  if (row.status === "basic_collecting" || row.status === "basic_generating") {
    return appPaths.basicInterview(row.id);
  }
  if (row.status === "basic_report_ready") {
    return appPaths.basicReport(row.id);
  }
  if (row.status === "advanced_collecting" || row.status === "final_generating") {
    return appPaths.advancedInterview(row.id);
  }
  return appPaths.finalReport(row.id);
}
