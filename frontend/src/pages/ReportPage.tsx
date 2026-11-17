import { useEffect, useState } from "react";
import {
  ArrowRight,
  BarChart3,
  Check,
  ChevronRight,
  CircleAlert,
  Download,
  Layers3,
  Lightbulb,
  LoaderCircle,
  MessageSquareText,
  PencilLine,
  Route,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import {
  type BasicReportContent,
  type DiagnosisCase,
  type DiagnosisReport,
  type FinalReportContent,
  fetchBasicReport,
  fetchDiagnosisCase,
  fetchFinalReport,
  fetchReportVersion,
  fetchReportVersions,
  generateBasicReport,
  generateFinalReport,
  reportExportUrl,
  startAdvancedInterview,
} from "@/api/diagnosis";
import { FileDownloadLink } from "@/components/FileDownloadLink";
import { scrollToTop } from "@/platform/browserEffects";
import { appPaths } from "@/routes";

type ReportPageProps = Readonly<{ stage: "basic" | "final" }>;
type LoadedReport =
  | DiagnosisReport<BasicReportContent>
  | DiagnosisReport<FinalReportContent>;

function SectionTitle({ eyebrow, title, description }: Readonly<{ eyebrow: string; title: string; description?: string }>) {
  return (
    <div className="mb-6">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand">{eyebrow}</p>
      <h2 className="mt-2 text-xl font-bold text-slate-900 sm:text-2xl">{title}</h2>
      {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{description}</p> : null}
    </div>
  );
}

function BasicReportView({ content }: Readonly<{ content: BasicReportContent }>) {
  return (
    <>
      <section className="report-section">
        <SectionTitle eyebrow="核心发现" title="真正值得优先解决的痛点" description="以下判断来自你的回答，不使用虚构数据填补未知信息。" />
        <div className="grid gap-4 md:grid-cols-3">
          {content.pain_points.map((item, index) => (
            <article key={`${item.title}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-50 text-rose-600">
                <CircleAlert className="h-4.5 w-4.5" />
              </span>
              <h3 className="mt-4 font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{item.detail}</p>
              {item.evidence ? <p className="mt-4 border-t border-slate-100 pt-3 text-xs text-slate-400">依据：{item.evidence}</p> : null}
            </article>
          ))}
        </div>
      </section>

      <section className="report-section">
        <SectionTitle eyebrow="机会地图" title="AI 最可能发挥价值的方向" description="不是功能清单，而是按验证优先级排列的机会。" />
        <div className="space-y-3">
          {content.opportunities.map((item, index) => (
            <article key={`${item.title}-${index}`} className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 sm:grid-cols-[3rem_1fr_auto] sm:items-start">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft font-bold text-brand">{index + 1}</span>
              <div>
                <h3 className="font-semibold text-slate-900">{item.title}</h3>
                <p className="mt-1.5 text-sm leading-6 text-slate-600">{item.description}</p>
                <p className="mt-2 text-xs leading-5 text-slate-400">为什么：{item.why}</p>
              </div>
              <span className="w-fit rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-brand">{item.priority}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="report-section grid gap-5 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="rounded-2xl bg-slate-900 p-6 text-white sm:p-8">
          <Lightbulb className="h-6 w-6 text-cyan-300" />
          <h2 className="mt-4 text-xl font-semibold">{content.quick_start.title}</h2>
          <ol className="mt-5 space-y-4">
            {content.quick_start.steps.map((step, index) => (
              <li key={`${step}-${index}`} className="flex gap-3 text-sm leading-6 text-slate-200">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/10 text-xs text-white">{index + 1}</span>
                {step}
              </li>
            ))}
          </ol>
        </div>
        <div className="rounded-2xl border border-brand/20 bg-brand-soft p-6 sm:p-8">
          <BarChart3 className="h-6 w-6 text-brand" />
          <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-brand">当前准备度</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">{content.readiness.level}</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">{content.readiness.detail}</p>
        </div>
      </section>

      <section className="report-section">
        <SectionTitle eyebrow="进入下一阶段前" title="还需要进一步确认的信息" />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {content.missing_information.map((item, index) => (
            <div key={`${item}-${index}`} className="flex gap-3 rounded-xl border border-slate-200 bg-white p-4 text-sm leading-6 text-slate-600">
              <Target className="mt-1 h-4 w-4 shrink-0 text-brand" />
              {item}
            </div>
          ))}
        </div>
        <p className="mt-5 text-sm leading-7 text-slate-600">{content.conclusion}</p>
      </section>
    </>
  );
}

function FinalReportView({ content }: Readonly<{ content: FinalReportContent }>) {
  return (
    <>
      <section className="report-section">
        <SectionTitle eyebrow="方案蓝图" title={content.solution.name} description={content.solution.positioning} />
        <div className="rounded-2xl border border-brand/20 bg-brand-soft p-6 sm:p-8">
          <Sparkles className="h-6 w-6 text-brand" />
          <p className="mt-4 text-sm leading-7 text-slate-700">{content.solution.description}</p>
        </div>
      </section>

      <section className="report-section">
        <SectionTitle eyebrow="能力设计" title="方案需要具备的核心能力" />
        <div className="grid gap-4 md:grid-cols-2">
          {content.capabilities.map((item, index) => (
            <article key={`${item.title}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-5">
              <Layers3 className="h-5 w-5 text-brand" />
              <h3 className="mt-3 font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{item.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="report-section grid gap-5 lg:grid-cols-2">
        <div>
          <SectionTitle eyebrow="目标流程" title="人和 AI 如何协同" />
          <ol className="space-y-3">
            {content.target_journey.map((item, index) => (
              <li key={`${item}-${index}`} className="flex gap-3 rounded-xl border border-slate-200 bg-white p-4 text-sm leading-6 text-slate-600">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-soft text-xs font-semibold text-brand">{index + 1}</span>
                {item}
              </li>
            ))}
          </ol>
        </div>
        <div>
          <SectionTitle eyebrow="数据与集成" title="落地依赖条件" />
          <div className="space-y-3">
            {content.data_and_integrations.map((item, index) => (
              <div key={`${item}-${index}`} className="flex gap-3 rounded-xl border border-slate-200 bg-white p-4 text-sm leading-6 text-slate-600">
                <Check className="mt-1 h-4 w-4 shrink-0 text-brand" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="report-section">
        <SectionTitle eyebrow="实施路径" title="先验证，再集成和扩展" />
        <div className="grid gap-4 md:grid-cols-3">
          {content.implementation_phases.map((phase, index) => (
            <article key={`${phase.name}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-5">
              <span className="text-xs font-semibold text-brand">阶段 {index + 1}</span>
              <h3 className="mt-2 font-semibold text-slate-900">{phase.name}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{phase.goal}</p>
              <ul className="mt-4 space-y-2 border-t border-slate-100 pt-4">
                {phase.deliverables.map((item) => <li key={item} className="text-xs leading-5 text-slate-500">· {item}</li>)}
              </ul>
            </article>
          ))}
        </div>
      </section>

      <section className="report-section grid gap-5 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900"><Target className="h-5 w-5 text-brand" />成功与验收</h2>
          <ul className="mt-5 space-y-3">
            {content.success_metrics.map((item, index) => <li key={`${item}-${index}`} className="flex gap-2 text-sm leading-6 text-slate-600"><Check className="mt-1 h-4 w-4 shrink-0 text-brand" />{item}</li>)}
          </ul>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900"><ShieldCheck className="h-5 w-5 text-brand" />风险与治理</h2>
          <div className="mt-5 space-y-4">
            {content.risks.map((item, index) => (
              <div key={`${item.risk}-${index}`}>
                <p className="text-sm font-medium text-slate-800">{item.risk}</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">应对：{item.mitigation}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="report-section rounded-2xl bg-slate-900 p-6 text-white sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">交付结果</p>
        <h2 className="mt-2 text-xl font-bold text-white sm:text-2xl">这套方案最终应留下什么</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {content.deliverables.map((item, index) => (
            <div key={`${item}-${index}`} className="flex items-center gap-3 rounded-xl bg-white/8 p-4 text-sm text-slate-200">
              <Check className="h-4 w-4 shrink-0 text-cyan-300" />
              {item}
            </div>
          ))}
        </div>
        <p className="mt-6 border-t border-white/10 pt-5 text-sm leading-6 text-slate-300">下一步：{content.next_action}</p>
      </section>
    </>
  );
}

export default function ReportPage({ stage }: ReportPageProps) {
  const { caseId = "" } = useParams();
  const navigate = useNavigate();
  const [diagnosis, setDiagnosis] = useState<DiagnosisCase | null>(null);
  const [report, setReport] = useState<LoadedReport | null>(null);
  const [loadingAdvanced, setLoadingAdvanced] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [revisionNote, setRevisionNote] = useState("");
  const [versions, setVersions] = useState<LoadedReport[]>([]);
  const [currentReportVersion, setCurrentReportVersion] = useState<number | null>(null);
  const [versionLoading, setVersionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const reportPromise = stage === "basic" ? fetchBasicReport(caseId) : fetchFinalReport(caseId);
    const versionsPromise = stage === "basic"
      ? fetchReportVersions(caseId, "basic")
      : fetchReportVersions(caseId, "final");
    Promise.all([fetchDiagnosisCase(caseId), reportPromise, versionsPromise])
      .then(([caseRow, reportRow, versionRows]) => {
        if (!cancelled) {
          setDiagnosis(caseRow);
          setReport(reportRow);
          setCurrentReportVersion(reportRow.version);
          setVersions(versionRows as LoadedReport[]);
        }
      })
      .catch(() => {
        if (!cancelled) setError("无法读取报告，请返回工作台后重试。");
      });
    return () => {
      cancelled = true;
    };
  }, [caseId, stage]);

  const handleAdvanced = async () => {
    setLoadingAdvanced(true);
    setError(null);
    try {
      await startAdvancedInterview(caseId);
      navigate(appPaths.advancedInterview(caseId));
    } catch {
      setError("深度共创暂时无法开始，请稍后重试。 ");
      setLoadingAdvanced(false);
    }
  };

  const handleRegenerate = async () => {
    const note = revisionNote.trim();
    if (note.length < 4) {
      setError("请简单说明希望重点调整的内容，例如更关注实施顺序、数据安全或预算边界。");
      return;
    }
    setRegenerating(true);
    setError(null);
    try {
      const nextReport = stage === "basic"
        ? await generateBasicReport(caseId, note)
        : await generateFinalReport(caseId, note);
      setReport(nextReport);
      setCurrentReportVersion(nextReport.version);
      const versionRows = stage === "basic"
        ? await fetchReportVersions(caseId, "basic")
        : await fetchReportVersions(caseId, "final");
      setVersions(versionRows as LoadedReport[]);
      setRevisionNote("");
      scrollToTop();
    } catch {
      setError("新版报告暂时没有生成完成，原版本仍然保留，可以稍后重试。");
    } finally {
      setRegenerating(false);
    }
  };

  const handleVersionSelect = async (version: number) => {
    if (!report || version === currentReportVersion || versionLoading) return;
    setVersionLoading(true);
    setError(null);
    try {
      const nextReport = await fetchReportVersion(caseId, stage, version);
      setReport(nextReport as LoadedReport);
      setCurrentReportVersion(version);
      scrollToTop();
    } catch {
      setError("暂时无法读取这个历史版本，请稍后重试。");
    } finally {
      setVersionLoading(false);
    }
  };

  if (error && (!diagnosis || !report)) {
    return <main className="mx-auto max-w-3xl px-4 py-20 text-center text-sm text-red-600">{error}</main>;
  }
  if (!diagnosis || !report) {
    return <main className="flex min-h-[70vh] items-center justify-center"><LoaderCircle className="h-6 w-6 animate-spin text-brand" /></main>;
  }

  return (
    <main className="report-page pb-16">
      {loadingAdvanced || regenerating || versionLoading ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 backdrop-blur-sm" role="status" aria-live="polite">
          <div className="w-full max-w-md rounded-3xl border border-white/10 bg-white p-7 text-center shadow-2xl sm:p-9">
            <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-soft text-brand">
              <LoaderCircle className="h-7 w-7 animate-spin" />
            </span>
            <h2 className="mt-5 text-xl font-bold text-slate-900">{versionLoading ? "正在读取历史版本" : regenerating ? "本地 AI 正在生成新版报告" : "正在定制你的进阶问题"}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-500">
              {versionLoading
                ? "系统正在从本地数据库读取已保存的旧版报告。"
                : regenerating
                ? "系统会保留原版本，并结合你的补充要求重新生成；通常需要 15–60 秒。"
                : "本地 AI 正在结合基础回答和诊断报告整理追问，通常需要 10–30 秒；如果模型超时，系统会自动使用针对当前案例的引导问题继续流程。"}
            </p>
          </div>
        </div>
      ) : null}
      <section className="border-b border-slate-200/60 bg-white/55">
        <div className="mx-auto max-w-5xl px-4 py-12 text-center sm:px-6 sm:py-16">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand text-white">
            {stage === "basic" ? <Sparkles className="h-6 w-6" /> : <Route className="h-6 w-6" />}
          </div>
          <p className="mt-5 text-xs font-semibold uppercase tracking-[0.18em] text-brand">
            {stage === "basic" ? "阶段一成果" : "阶段二成果"} · 第 {report.version} 版
          </p>
          <p className={`mx-auto mt-3 w-fit rounded-full px-3 py-1 text-xs font-medium ${
            report.content.generation_mode === "local_ai"
              ? "bg-emerald-50 text-emerald-700"
              : "bg-amber-50 text-amber-700"
          }`}>
            {report.content.generation_mode === "local_ai" ? "由本地 Ollama 模型生成" : "由本地引导引擎生成"}
          </p>
          <h1 className="mt-3 text-3xl font-bold text-slate-900 sm:text-4xl">{report.title}</h1>
          <p className="mx-auto mt-3 max-w-2xl text-sm text-slate-500">{diagnosis.scenario} · {diagnosis.challenge}</p>
          <div className="mx-auto mt-8 max-w-4xl rounded-2xl border border-brand/20 bg-brand-soft px-5 py-6 text-left sm:px-8">
            <p className="text-xs font-semibold text-brand">核心结论</p>
            <p className="mt-2 text-base font-medium leading-8 text-slate-800 sm:text-lg">{report.summary}</p>
          </div>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-4">
            <FileDownloadLink href={reportExportUrl(caseId, stage, currentReportVersion ?? report.version)} className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-brand">
              <Download className="h-4 w-4" />下载 Word 报告
            </FileDownloadLink>
            <FileDownloadLink href={reportExportUrl(caseId, stage, currentReportVersion ?? report.version, "pdf")} className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-brand">
              <Download className="h-4 w-4" />下载 PDF 报告
            </FileDownloadLink>
            <button type="button" onClick={() => navigate(stage === "basic" ? appPaths.basicInterview(caseId) : appPaths.advancedInterview(caseId))} className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-brand">
              <PencilLine className="h-4 w-4" />修改{stage === "basic" ? "基础" : "进阶"}回答
            </button>
          </div>
          {versions.length > 1 ? (
            <div className="mx-auto mt-5 flex max-w-2xl flex-wrap items-center justify-center gap-2 text-xs text-slate-500">
              <span>历史版本已保留：</span>
              {versions.map((item) => (
                <button
                  key={`${item.stage}-${item.version}`}
                  type="button"
                  disabled={versionLoading}
                  onClick={() => void handleVersionSelect(item.version)}
                  className={`rounded-full px-2.5 py-1 transition ${
                    item.version === currentReportVersion
                      ? "bg-brand-soft font-semibold text-brand"
                      : "bg-white text-slate-500 hover:text-brand"
                  } disabled:cursor-wait`}
                >
                  第 {item.version} 版
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </section>

      {error ? (
        <div className="mx-auto mt-6 max-w-5xl px-4 sm:px-6">
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
        </div>
      ) : null}

      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        {stage === "basic" ? (
          <BasicReportView content={(report as DiagnosisReport<BasicReportContent>).content} />
        ) : (
          <FinalReportView content={(report as DiagnosisReport<FinalReportContent>).content} />
        )}
      </div>

      {stage === "basic" ? (
        <section className="mx-auto mt-8 max-w-5xl px-4 sm:px-6">
          <div className="overflow-hidden rounded-2xl bg-brand px-6 py-8 text-white sm:px-10 sm:py-10">
            <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-center">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-white/70">下一阶段</p>
                <h2 className="mt-2 text-2xl font-bold">让初步方向变成你的专属落地方案</h2>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-white/80">系统会结合这份报告，进一步追问真实案例、业务规则、数据、系统、人工兜底与验收标准；已经明确的信息不会重复询问。</p>
              </div>
              <div className="flex flex-col gap-2">
                <button type="button" disabled={loadingAdvanced} onClick={handleAdvanced} className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-white px-6 text-sm font-semibold text-brand disabled:opacity-70">
                  {loadingAdvanced ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                  {loadingAdvanced ? "正在定制问题…" : "进入深度共创"}
                  {!loadingAdvanced ? <ArrowRight className="h-4 w-4" /> : null}
                </button>
                <button type="button" onClick={() => navigate(appPaths.basicInterview(caseId))} className="min-h-9 text-xs font-medium text-white/75 transition hover:text-white">先返回修改基础回答</button>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      <section className="mx-auto mt-8 max-w-5xl px-4 sm:px-6">
        <div className="surface-card overflow-hidden">
          <div className="grid gap-6 p-5 sm:p-7 lg:grid-cols-[0.75fr_1.25fr] lg:items-center">
            <div>
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-brand"><MessageSquareText className="h-5 w-5" /></span>
              <h2 className="mt-4 text-xl font-bold text-slate-900">继续打磨这份{stage === "basic" ? "诊断" : "方案"}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">原版本会保留，新结果将成为第 {Math.max(...versions.map((item) => item.version), report.version) + 1} 版。只需说明希望加强、删减或调整的重点。</p>
            </div>
            <div>
              <textarea
                value={revisionNote}
                onChange={(event) => {
                  setRevisionNote(event.target.value);
                  if (event.target.value.trim().length >= 4) setError(null);
                }}
                rows={4}
                maxLength={1200}
                placeholder={stage === "basic" ? "例如：更关注客户体验，不要默认需要开发新系统……" : "例如：把首期范围收窄到客服团队，并强化本地部署与数据脱敏要求……"}
                className="w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-800 outline-none transition focus:border-brand focus:ring-4 focus:ring-brand/10"
              />
              <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <span className="text-xs text-slate-400">{revisionNote.trim().length}/1200 字</span>
                <button type="button" disabled={regenerating} onClick={handleRegenerate} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-brand px-5 text-sm font-semibold text-white transition hover:brightness-95 disabled:opacity-50">
                  {regenerating ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                  {regenerating ? "正在生成新版…" : "生成新版报告"}
                </button>
              </div>
            </div>
          </div>
          <button type="button" onClick={() => navigate(appPaths.workspace)} className="flex min-h-12 w-full items-center justify-between border-t border-slate-100 bg-slate-50/60 px-5 text-sm font-semibold text-slate-600 transition hover:bg-brand-soft hover:text-brand">
            返回我的诊断
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </section>
    </main>
  );
}
