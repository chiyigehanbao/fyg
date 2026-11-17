import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CircleAlert,
  Circle,
  Clock3,
  HelpCircle,
  LoaderCircle,
  RefreshCw,
  Save,
  Sparkles,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ApiError,
  type AnswerValue,
  type DiagnosisCase,
  type Interview,
  fetchDiagnosisCase,
  fetchInterview,
  generateBasicReport,
  generateFinalReport,
  rebuildAdvancedInterview,
  saveInterviewAnswers,
} from "@/api/diagnosis";
import { hasUsefulAnswer } from "@/domain/answerQuality";
import { cancelDeferred, defer } from "@/platform/browserEffects";
import { appPaths } from "@/routes";

type InterviewPageProps = Readonly<{ stage: "basic" | "advanced" }>;

export default function InterviewPage({ stage }: InterviewPageProps) {
  const { caseId = "" } = useParams();
  const navigate = useNavigate();
  const [diagnosis, setDiagnosis] = useState<DiagnosisCase | null>(null);
  const [interview, setInterview] = useState<Interview | null>(null);
  const [answers, setAnswers] = useState<Record<string, AnswerValue>>({});
  const [current, setCurrent] = useState(0);
  const [hydrated, setHydrated] = useState(false);
  const [saveState, setSaveState] = useState<"saved" | "saving" | "error">("saved");
  const [generating, setGenerating] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const saveVersion = useRef(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchDiagnosisCase(caseId), fetchInterview(caseId, stage)])
      .then(([caseRow, interviewRow]) => {
        if (cancelled) return;
        setError(null);
        setDiagnosis(caseRow);
        setInterview(interviewRow);
        setAnswers(interviewRow.answers);
        const firstOpen = interviewRow.questions.findIndex(
          (question) => question.required && !hasUsefulAnswer(interviewRow.answers[question.id]),
        );
        setCurrent(firstOpen >= 0 ? firstOpen : 0);
        setSaveState("saved");
        setHydrated(true);
      })
      .catch(() => {
        if (!cancelled) setError("无法读取这次诊断，请返回工作台后重试。");
      });
    return () => {
      cancelled = true;
    };
  }, [caseId, stage]);

  useEffect(() => {
    if (!hydrated || !interview) return;
    const version = ++saveVersion.current;
    const timer = defer(() => {
      setSaveState("saving");
      saveInterviewAnswers(caseId, stage, answers)
        .then(() => {
          if (version === saveVersion.current) setSaveState("saved");
        })
        .catch(() => {
          if (version === saveVersion.current) setSaveState("error");
          setError("自动保存暂时失败，请不要关闭页面并稍后重试。");
        });
    }, 650);
    return () => cancelDeferred(timer);
  }, [answers, caseId, hydrated, interview, stage]);

  const questions = useMemo(() => interview?.questions ?? [], [interview]);
  const question = questions[current];
  const answeredCount = useMemo(
    () => questions.filter((item) => hasUsefulAnswer(answers[item.id])).length,
    [answers, questions],
  );
  const percent = questions.length ? Math.round((answeredCount / questions.length) * 100) : 0;
  const remainingCount = Math.max(0, questions.length - answeredCount);
  const remainingMinutes = Math.max(1, Math.ceil(remainingCount * (stage === "basic" ? 0.6 : 1)));
  const currentValue = question && typeof answers[question.id] === "string" ? answers[question.id] as string : "";
  const currentNeedsDetail = question.required && currentValue.trim().length > 0 && !hasUsefulAnswer(currentValue);

  const setValue = (value: AnswerValue) => {
    if (!question) return;
    setAnswers((previous) => ({ ...previous, [question.id]: value }));
    setError(null);
  };

  const toggleMulti = (option: string) => {
    if (!question) return;
    const currentValue = answers[question.id];
    const selected = Array.isArray(currentValue) ? currentValue : [];
    setValue(selected.includes(option) ? selected.filter((item) => item !== option) : [...selected, option]);
  };

  const handleNext = () => {
    if (!question) return;
    if (question.required && !hasUsefulAnswer(answers[question.id])) {
      setError("请先补充有效信息；如果确实不确定，可以写明还缺什么、谁来确认或什么时候验证。");
      return;
    }
    setError(null);
    setCurrent((value) => Math.min(questions.length - 1, value + 1));
  };

  const handleUnsure = () => {
    setValue("暂不确定，需要在方案验证阶段进一步确认。");
  };

  const handleExit = async () => {
    setError(null);
    try {
      await saveInterviewAnswers(caseId, stage, answers);
      navigate(stage === "advanced" ? appPaths.basicReport(caseId) : appPaths.workspace);
    } catch {
      setSaveState("error");
      setError("暂时无法保存，请保持页面开启后重试。");
    }
  };

  const handleRebuild = async () => {
    if (stage !== "advanced" || answeredCount > 0 || rebuilding) return;
    setRebuilding(true);
    setError(null);
    try {
      const refreshed = await rebuildAdvancedInterview(caseId);
      setInterview(refreshed);
      setAnswers(refreshed.answers);
      setCurrent(0);
      setSaveState("saved");
    } catch {
      setError("问题暂时无法重新定制；如果已经填写过内容，系统会优先保护现有答案。");
    } finally {
      setRebuilding(false);
    }
  };

  const handleComplete = async () => {
    if (!interview || generating) return;
    const missingIndex = questions.findIndex(
      (item) => item.required && !hasUsefulAnswer(answers[item.id]),
    );
    if (missingIndex >= 0) {
      setCurrent(missingIndex);
      setError("还有核心问题缺少有效信息。请补充具体场景、流程、影响或验证方式后再生成报告。");
      return;
    }
    setGenerating(true);
    setError(null);
    try {
      await saveInterviewAnswers(caseId, stage, answers);
      if (stage === "basic") {
        await generateBasicReport(caseId);
        navigate(appPaths.basicReport(caseId));
      } else {
        await generateFinalReport(caseId);
        navigate(appPaths.finalReport(caseId));
      }
    } catch (err) {
      if (err instanceof ApiError && err.questionIds.length > 0) {
        const rejectedIndex = questions.findIndex((item) => err.questionIds.includes(item.id));
        if (rejectedIndex >= 0) setCurrent(rejectedIndex);
        setError("这些核心问题还缺少有效信息。请补充具体场景、流程、影响或验证方式后再生成报告。");
        return;
      }
      setError("报告生成没有完成，请稍后重试。你的回答已经保存。");
    } finally {
      setGenerating(false);
    }
  };

  if (error && (!diagnosis || !interview)) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-20 text-center">
        <p className="text-sm text-red-600">{error}</p>
        <button type="button" onClick={() => navigate(appPaths.workspace)} className="mt-5 rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-white">
          返回我的诊断
        </button>
      </main>
    );
  }

  if (!diagnosis || !interview || !question) {
    return (
      <main className="flex min-h-[70vh] items-center justify-center">
        <LoaderCircle className="h-6 w-6 animate-spin text-brand" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
      {generating || rebuilding ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-white/60 bg-white p-6 text-center sm:p-8">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-soft text-brand">
              <LoaderCircle className="h-6 w-6 animate-spin" />
            </span>
            <h2 className="mt-4 text-xl font-semibold text-slate-900">
              {rebuilding ? "本地 AI 正在重新定制问题" : stage === "basic" ? "本地 AI 正在梳理诊断报告" : "本地 AI 正在生成专属方案"}
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              {rebuilding
                ? "系统会忽略测试文字和无效信息，重新整理为 8 个更聚焦的问题。"
                : "内容只在你的设备上处理，通常需要 15–60 秒；如果本地模型超时或输出不完整，系统会自动根据你的全部回答生成可继续预览的方案。"}
            </p>
            <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full w-2/3 animate-pulse rounded-full bg-brand" />
            </div>
          </div>
        </div>
      ) : null}
      <div className="mb-5 flex items-center justify-between gap-3">
        <button type="button" onClick={handleExit} className="inline-flex min-h-10 items-center gap-2 rounded-lg px-2 text-sm font-medium text-slate-500 transition hover:bg-white hover:text-brand">
          <ArrowLeft className="h-4 w-4" />
          {stage === "advanced" ? "保存并返回基础报告" : "保存并返回工作台"}
        </button>
        {stage === "advanced" && answeredCount === 0 ? (
          <button type="button" disabled={rebuilding} onClick={handleRebuild} className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 transition hover:border-brand/30 hover:text-brand disabled:opacity-50">
            <RefreshCw className={`h-3.5 w-3.5 ${rebuilding ? "animate-spin" : ""}`} />重新定制问题
          </button>
        ) : null}
      </div>
      <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand">
            {stage === "basic" ? "阶段一 · 基础诊断" : "阶段二 · 深度共创"}
          </p>
          <h1 className="mt-2 text-2xl font-bold text-slate-900 sm:text-3xl">
            {stage === "basic" ? "先看清真正的问题" : "把方案做到足够具体"}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            {diagnosis.scenario} · {diagnosis.challenge}
          </p>
        </div>
        <div className="min-w-44">
          <div className="mb-2 flex justify-between text-xs text-slate-500">
            <span>{answeredCount}/{questions.length} 已完成</span>
            <span className="inline-flex items-center gap-1"><Clock3 className="h-3.5 w-3.5" />{remainingCount === 0 ? "可以生成" : `约 ${remainingMinutes} 分钟`}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-200">
            <div className="h-full rounded-full bg-brand transition-all" style={{ width: `${percent}%` }} />
          </div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[15rem_minmax(0,1fr)]">
        <aside className="surface-card hidden self-start p-3 lg:block">
          <p className="px-2 py-2 text-xs font-semibold text-slate-500">问题导航</p>
          <div className="space-y-1">
            {questions.map((item, index) => {
              const done = hasUsefulAnswer(answers[item.id]);
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setCurrent(index)}
                  className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-2.5 text-left text-sm transition ${
                    index === current ? "bg-brand-soft font-medium text-brand" : "text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {done ? <Check className="h-4 w-4 shrink-0" /> : <Circle className="h-4 w-4 shrink-0 text-slate-300" />}
                  <span className="truncate">{item.title}</span>
                </button>
              );
            })}
          </div>
        </aside>

        <section className="surface-card min-h-[31rem] p-5 sm:p-8">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-brand-soft px-3 py-1 text-xs font-semibold text-brand">问题 {current + 1} / {questions.length}</span>
              <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${question.required ? "bg-slate-100 text-slate-600" : "bg-emerald-50 text-emerald-700"}`}>{question.required ? "核心问题" : "可选问题"}</span>
            </div>
            <span className={`inline-flex items-center gap-1.5 text-xs ${saveState === "error" ? "text-red-600" : "text-slate-400"}`}>
              {saveState === "saving" ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : saveState === "error" ? <CircleAlert className="h-3.5 w-3.5" /> : <Save className="h-3.5 w-3.5" />}
              {saveState === "saving" ? "正在保存" : saveState === "error" ? "保存失败" : "已自动保存"}
            </span>
          </div>

          <h2 className="mt-7 text-xl font-semibold leading-8 text-slate-900 sm:text-2xl">{question.prompt}</h2>
          {question.hint ? <p className="mt-2 text-sm leading-6 text-slate-500">{question.hint}</p> : null}

          <div className="mt-7">
            {question.type === "single" ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {question.options.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setValue(option)}
                    className={`rounded-xl border px-4 py-3 text-left text-sm ${answers[question.id] === option ? "border-brand bg-brand-soft text-brand" : "border-slate-200 bg-white text-slate-700"}`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            ) : question.type === "multi" ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {question.options.map((option) => {
                  const value = answers[question.id];
                  const checked = Array.isArray(value) && value.includes(option);
                  return (
                    <button key={option} type="button" onClick={() => toggleMulti(option)} className={`rounded-xl border px-4 py-3 text-left text-sm ${checked ? "border-brand bg-brand-soft text-brand" : "border-slate-200 bg-white text-slate-700"}`}>
                      {option}
                    </button>
                  );
                })}
              </div>
            ) : (
              <textarea
                autoFocus
                value={currentValue}
                onChange={(event) => setValue(event.target.value)}
                onKeyDown={(event) => {
                  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                    event.preventDefault();
                    if (current < questions.length - 1) handleNext();
                    else void handleComplete();
                  }
                }}
                rows={8}
                placeholder={stage === "advanced" ? "描述真实情况即可；没有数字或暂时不确定，也可以直接说明……" : "请结合真实情况描述，越具体越有助于形成准确判断……"}
                className="w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3.5 text-sm leading-7 text-slate-800 outline-none transition focus:border-brand focus:ring-4 focus:ring-brand/10"
              />
            )}
            {question.type === "text" || question.type === "textarea" ? (
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
                <span>{currentValue.trim().length} 字 · Ctrl/⌘ + Enter 继续</span>
                <button type="button" onClick={handleUnsure} className="inline-flex min-h-8 items-center gap-1.5 rounded-lg bg-slate-100 px-3 font-medium text-slate-600 transition hover:bg-brand-soft hover:text-brand">
                  <HelpCircle className="h-3.5 w-3.5" />暂不确定
                </button>
              </div>
            ) : null}
            {currentNeedsDetail ? (
              <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">
                这条回答还太薄，报告会把它当作未完成。可以补一句真实对象、处理步骤、影响范围或后续验证方式。
              </p>
            ) : null}
          </div>

          {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

          <div className="mt-8 flex flex-col-reverse gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              disabled={current === 0 || generating}
              onClick={() => setCurrent((value) => Math.max(0, value - 1))}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-5 text-sm font-medium text-slate-600 disabled:opacity-35"
            >
              <ArrowLeft className="h-4 w-4" />
              上一题
            </button>
            {current < questions.length - 1 ? (
              <button
                type="button"
                onClick={handleNext}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-brand px-6 text-sm font-semibold text-white"
              >
                下一题
                <ArrowRight className="h-4 w-4" />
              </button>
            ) : (
              <button
                type="button"
                disabled={generating}
                onClick={handleComplete}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-brand px-6 text-sm font-semibold text-white disabled:opacity-60"
              >
                {generating ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {generating ? "正在生成，请稍候…" : stage === "basic" ? "生成诊断报告" : "生成最终方案"}
              </button>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
