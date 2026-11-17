import { useState } from "react";
import { ArrowRight, Check, ClipboardList, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, createDiagnosisCase } from "@/api/diagnosis";
import ModelStatusBadge from "@/components/ModelStatusBadge";
import { isMeaningfulProblemDescription } from "@/domain/answerQuality";
import { scrollElementIntoView } from "@/platform/browserEffects";
import { appPaths } from "@/routes";

const SCENARIOS = [
  "流程效率",
  "客户服务",
  "内容与知识",
  "数据与决策",
  "产品与服务创新",
  "个人工作提效",
] as const;

export default function StartPage() {
  const navigate = useNavigate();
  const [scenario, setScenario] = useState<string>("");
  const [challenge, setChallenge] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scenarioError, setScenarioError] = useState(false);
  const [challengeError, setChallengeError] = useState(false);

  const handleStart = async () => {
    if (loading) return;
    const missingScenario = !scenario;
    const invalidChallenge = !isMeaningfulProblemDescription(challenge);
    setScenarioError(missingScenario);
    setChallengeError(invalidChallenge);
    if (missingScenario || invalidChallenge) {
      setError(
        missingScenario && invalidChallenge
          ? "请先选择一个场景，并用至少 8 个字描述问题。"
          : missingScenario
            ? "请先选择一个最接近的 AI 赋能场景。"
            : "请用一句完整的话描述真实问题，不能只填写数字或符号。",
      );
      scrollElementIntoView(missingScenario ? "scenario-options" : "challenge-input");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const row = await createDiagnosisCase({ scenario, challenge: challenge.trim() });
      navigate(appPaths.basicInterview(row.id));
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setChallengeError(true);
        setError(err.message || "请补充真实、具体的问题描述后再开始诊断。");
        scrollElementIntoView("challenge-input");
        return;
      }
      setError("暂时无法创建诊断，请确认后端服务已启动后重试。失去的内容仍保留在当前页面。 ");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative z-10 min-h-screen">
      <header className="border-b border-slate-200/60 bg-white/75 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link to={appPaths.home} className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand text-white">
              <Sparkles className="h-5 w-5" />
            </span>
            <span>
              <strong className="block text-sm text-slate-900">AI 共创官</strong>
              <small className="text-xs text-slate-500">AI 赋能诊断与共创平台</small>
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <div className="hidden sm:block"><ModelStatusBadge /></div>
            <span className="hidden text-sm text-slate-500 lg:block">基础诊断 · 约 5 分钟</span>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:px-6 lg:grid-cols-[0.72fr_1.28fr] lg:py-16">
        <aside className="space-y-6 lg:pt-5">
          <div className="inline-flex items-center gap-2 rounded-full bg-brand-soft px-3 py-1.5 text-xs font-semibold text-brand">
            <Sparkles className="h-3.5 w-3.5" />
            从一个真实问题开始
          </div>
          <div>
            <h1 className="text-3xl font-bold leading-tight text-slate-900 sm:text-4xl">
              先告诉我们，<br />你最想改变什么？
            </h1>
            <p className="mt-4 max-w-md text-sm leading-7 text-slate-600 sm:text-base">
              不需要提前想好技术方案。我们会通过基础问题理解现状、痛点和目标，再生成一份直击重点的 AI 机会诊断报告。
            </p>
          </div>
          <div className="space-y-3 text-sm text-slate-600">
            {["问题一题一屏，不重复追问", "答案自动保存，可随时继续", "报告底部可进入深度共创"].map((item) => (
              <div key={item} className="flex items-center gap-2.5">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-soft text-brand"><Check className="h-3 w-3" /></span>
                {item}
              </div>
            ))}
          </div>
        </aside>

        <section className="surface-card p-5 sm:p-8">
          <div className="mb-7 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand">准备阶段</p>
              <h2 className="mt-2 text-xl font-semibold text-slate-900">你的 AI 赋能场景</h2>
              <p className="mt-1 text-sm text-slate-500">选一个最接近的方向，后续还可以调整。</p>
            </div>
            <ClipboardList className="h-6 w-6 text-brand" />
          </div>

          <div
            id="scenario-options"
            className={`grid grid-cols-2 gap-3 rounded-xl sm:grid-cols-3 ${scenarioError ? "ring-2 ring-red-300 ring-offset-2" : ""}`}
          >
            {SCENARIOS.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => {
                  setScenario(item);
                  setScenarioError(false);
                  setError(null);
                }}
                className={`min-h-12 rounded-xl border px-3 py-2 text-sm transition-colors ${
                  scenario === item
                    ? "border-brand bg-brand-soft font-medium text-brand"
                    : "border-slate-200 bg-white text-slate-700 hover:border-brand/40 hover:bg-sky-50/60"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
          {scenarioError ? <p className="mt-2 text-xs font-medium text-red-600">请选择一个最接近的场景。</p> : null}

          <label className="mt-7 block">
            <span className="text-sm font-medium text-slate-800">现在最困扰你的问题是什么？</span>
            <textarea
              id="challenge-input"
              value={challenge}
              aria-invalid={challengeError}
              onChange={(event) => {
                setChallenge(event.target.value);
                if (isMeaningfulProblemDescription(event.target.value)) {
                  setChallengeError(false);
                  setError(null);
                }
              }}
              rows={5}
              placeholder="例如：每天要花大量时间整理客户反馈，但最后仍然很难判断哪些问题最值得优先解决……"
              className={`mt-2 w-full resize-none rounded-xl border bg-white px-4 py-3 text-sm leading-6 text-slate-800 outline-none transition focus:ring-4 ${
                challengeError
                  ? "border-red-400 focus:border-red-500 focus:ring-red-100"
                  : "border-slate-200 focus:border-brand focus:ring-brand/10"
              }`}
            />
            <span className={`mt-1.5 block text-xs ${challengeError ? "font-medium text-red-600" : "text-slate-400"}`}>
              {challengeError
                ? "请用一句完整的话描述真实问题，不能只填写数字或符号。"
                : `已输入 ${challenge.trim().length} 个字，建议包含现状和主要影响。`}
            </span>
          </label>

          <div className="mt-7 flex flex-col-reverse items-stretch justify-between gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:items-center">
            <p className={`text-xs ${error ? "text-red-600" : "text-slate-500"}`}>
              {error ?? "无需注册即可开始，稍后再保存报告"}
            </p>
            <button
              type="button"
              disabled={loading}
              onClick={handleStart}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-brand px-6 text-sm font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? "正在准备…" : "开始基础诊断"}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
