import type { AnswerValue } from "@/api/diagnosis";

const lowInformationPatterns = ["暂不确定", "暂未明确", "待确认", "不知道", "不清楚", "没有", "无", "随便", "测试"];

export function isLowInformationText(value: string): boolean {
  const text = value.trim();
  if (!text) return true;
  const compact = text.replace(/\s+/g, "");
  const semanticChars = compact.match(/[\u4e00-\u9fffA-Za-z]/g) ?? [];
  if (semanticChars.length < 4) return true;
  if (/^[\d\W_]+$/.test(compact)) return true;
  if (compact.length >= 4 && new Set([...compact]).size <= 2) return true;
  const lowered = compact.toLowerCase();
  if (["na", "n/a", "none", "null", "todo", "test"].includes(lowered)) return true;
  if (lowInformationPatterns.some((pattern) => compact.includes(pattern)) && semanticChars.length < 10) return true;
  if (/^这是关于.+的(?:真实|进阶)?回答$/.test(compact)) return true;
  return false;
}

export function hasUsefulAnswer(value: AnswerValue | undefined): boolean {
  if (Array.isArray(value)) return value.some((item) => !isLowInformationText(item));
  return Boolean(value && !isLowInformationText(value));
}

export function isMeaningfulProblemDescription(value: string): boolean {
  return value.trim().length >= 8 && !isLowInformationText(value);
}
