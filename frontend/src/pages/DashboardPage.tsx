import { useEffect, useState } from "react";
import { ArrowRight, CalendarDays, Copy, LoaderCircle, Plus, Sparkles, Trash2, X } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import {
  caseExportUrl,
  type DiagnosisCase,
  deleteDiagnosisCase,
  duplicateDiagnosisCase,
  fetchDiagnosisCases,
} from "@/api/diagnosis";
import { FileDownloadLink } from "@/components/FileDownloadLink";
import { formatCaseDate } from "@/domain/dateFormat";
import { appPaths, casePathByStatus } from "@/routes";

const STATUS_LABEL: Record<DiagnosisCase["status"], string> = {
  basic_collecting: "基础诊断进行中",
  basic_generating: "正在生成初步报告",
  basic_report_ready: "初步报告已就绪",
  advanced_collecting: "深度共创进行中",
  final_generating: "正在生成最终方案",
  final_report_ready: "最终方案已就绪",
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const [cases, setCases] = useState<DiagnosisCase[] | null>(null);
  const [error, setError] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<DiagnosisCase | null>(null);

  useEffect(() => {
    fetchDiagnosisCases().then(setCases).catch(() => setError(true));
  }, []);

  const handleDuplicate = async (row: DiagnosisCase) => {
    if (busyId) return;
    setBusyId(row.id);
    setActionError(null);
    try {
      const cloned = await duplicateDiagnosisCase(row.id);
      setCases((current) => current ? [cloned, ...current] : [cloned]);
      navigate(casePathByStatus(cloned));
    } catch {
      setActionError("复制诊断失败，请稍后重试。");
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async () => {
    const row = deleteTarget;
    if (!row) return;
    if (busyId) return;
    setBusyId(row.id);
    setActionError(null);
    try {
      await deleteDiagnosisCase(row.id);
      setCases((current) => current ? current.filter((item) => item.id !== row.id) : current);
      setDeleteTarget(null);
    } catch {
      setActionError("删除诊断失败，请稍后重试。");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
      {deleteTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="delete-case-title">
          <div className="w-full max-w-md rounded-2xl border border-white/70 bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-500">
                <Trash2 className="h-5 w-5" />
              </span>
              <button
                type="button"
                onClick={() => setDeleteTarget(null)}
                className="rounded-lg p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
                aria-label="关闭删除确认"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <h2 id="delete-case-title" className="mt-4 text-lg font-bold text-slate-900">删除这次诊断？</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              这会同时删除访谈回答、报告和历史版本。这个操作完成后不能在应用内恢复。
            </p>
            <FileDownloadLink
              href={caseExportUrl(deleteTarget.id)}
              className="mt-3 inline-flex text-sm font-semibold text-brand transition hover:brightness-90"
            >
              先下载这次诊断备份
            </FileDownloadLink>
            <div className="mt-4 rounded-xl bg-slate-50 p-3">
              <p className="text-xs font-medium text-slate-400">{deleteTarget.scenario}</p>
              <p className="mt-1 line-clamp-2 text-sm font-semibold leading-6 text-slate-800">{deleteTarget.challenge}</p>
            </div>
            <div className="mt-5 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                disabled={busyId === deleteTarget.id}
                onClick={() => setDeleteTarget(null)}
                className="inline-flex min-h-10 items-center justify-center rounded-lg border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
              >
                取消
              </button>
              <button
                type="button"
                disabled={busyId === deleteTarget.id}
                onClick={() => void handleDelete()}
                className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg bg-red-500 px-4 text-sm font-semibold text-white transition hover:bg-red-600 disabled:opacity-50"
              >
                {busyId === deleteTarget.id ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                确认删除
              </button>
            </div>
          </div>
        </div>
      ) : null}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand">我的诊断</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">继续探索值得落地的 AI 机会</h1>
          <p className="mt-2 text-sm text-slate-500">所有阶段都会自动保存，你可以随时返回继续。</p>
        </div>
        <Link to={appPaths.start} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-brand px-5 text-sm font-semibold text-white">
          <Plus className="h-4 w-4" />新建诊断
        </Link>
      </div>

      {error ? <p className="mt-10 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">暂时无法加载诊断记录，请稍后刷新。</p> : null}
      {actionError ? <p className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{actionError}</p> : null}
      {!cases && !error ? <div className="flex min-h-64 items-center justify-center"><LoaderCircle className="h-6 w-6 animate-spin text-brand" /></div> : null}

      {cases?.length === 0 ? (
        <section className="surface-card mt-10 px-5 py-14 text-center">
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-soft text-brand"><Sparkles className="h-6 w-6" /></span>
          <h2 className="mt-4 text-xl font-semibold text-slate-900">还没有开始诊断</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">从一个正在困扰你的真实问题开始，先得到方向，再决定是否深入。</p>
          <Link to={appPaths.start} className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-lg bg-brand px-5 text-sm font-semibold text-white">开始第一次诊断<ArrowRight className="h-4 w-4" /></Link>
        </section>
      ) : null}

      {cases && cases.length > 0 ? (
        <div className="mt-9 grid gap-4 md:grid-cols-2">
          {cases.map((row) => (
            <article key={row.id} className="group surface-card p-5 transition hover:-translate-y-0.5 hover:border-brand/30 sm:p-6">
              <div className="flex items-start justify-between gap-4">
                <span className="rounded-full bg-brand-soft px-3 py-1 text-xs font-semibold text-brand">{STATUS_LABEL[row.status]}</span>
                <Link to={casePathByStatus(row)} aria-label="继续诊断" className="rounded-lg p-1 text-slate-300 transition hover:bg-brand-soft hover:text-brand">
                  <ArrowRight className="h-5 w-5 transition group-hover:translate-x-1" />
                </Link>
              </div>
              <p className="mt-5 text-xs font-medium text-slate-400">{row.scenario}</p>
              <Link to={casePathByStatus(row)} className="mt-2 block">
                <h2 className="line-clamp-2 text-lg font-semibold leading-7 text-slate-900">{row.challenge}</h2>
              </Link>
              <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4 text-xs text-slate-400">
                <span className="inline-flex items-center gap-1.5"><CalendarDays className="h-3.5 w-3.5" />{formatCaseDate(row.updated_at)}</span>
                {row.status === "final_report_ready" ? <span className="inline-flex items-center gap-1 text-brand"><Sparkles className="h-3.5 w-3.5" />方案已完成</span> : null}
              </div>
              <div className="mt-4 flex gap-2">
                <button
                  type="button"
                  disabled={busyId === row.id}
                  onClick={() => void handleDuplicate(row)}
                  className="inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 transition hover:border-brand/30 hover:text-brand disabled:opacity-50"
                >
                  {busyId === row.id ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : <Copy className="h-3.5 w-3.5" />}
                  复制
                </button>
                <button
                  type="button"
                  disabled={busyId === row.id}
                  onClick={() => setDeleteTarget(row)}
                  className="inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-red-100 bg-white px-3 text-xs font-semibold text-red-500 transition hover:border-red-200 hover:bg-red-50 disabled:opacity-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  删除
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </main>
  );
}
