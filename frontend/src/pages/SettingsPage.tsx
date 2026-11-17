import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Database,
  Download,
  RefreshCw,
  Server,
  Settings,
} from "lucide-react";
import { type SystemStatus, fetchSystemStatus, systemBackupUrl } from "@/api/diagnosis";
import { FileDownloadLink } from "@/components/FileDownloadLink";

type StatusCardProps = {
  title: string;
  detail: string;
  connected: boolean;
  icon: ReactNode;
  meta?: string[];
};

function StatusCard({ title, detail, connected, icon, meta }: StatusCardProps) {
  return (
    <section className="surface-card p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <span
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
              connected ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
            }`}
          >
            {icon}
          </span>
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-slate-950">{title}</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">{detail}</p>
            {meta?.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {meta.map((item) => (
                  <span
                    key={item}
                    className="rounded-md bg-slate-50 px-2 py-1 text-xs text-slate-500"
                  >
                    {item}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        </div>
        {connected ? (
          <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
        ) : (
          <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600" />
        )}
      </div>
    </section>
  );
}

function modelErrorText(error?: string | null): string {
  if (!error) return "模型状态正常。";
  const messages: Record<string, string> = {
    connect_error: "无法连接 Ollama，请确认 Ollama 已启动。",
    timeout: "Ollama 状态检查超时，请稍后重试或检查本机负载。",
    invalid_response: "Ollama 返回异常，请检查服务版本或代理配置。",
    model_not_found: "Ollama 已连接，但未找到当前配置的模型。",
  };
  if (error.startsWith("http_")) return `Ollama 状态接口返回 ${error.replace("http_", "HTTP ")}。`;
  return messages[error] ?? error;
}

const requiredApiCapabilities = ["model_status_error", "report_pdf_export"];

export default function SettingsPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setStatus(await fetchSystemStatus());
    } catch (err) {
      setStatus(null);
      setError(err instanceof Error ? err.message : "无法连接后端 API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    fetchSystemStatus()
      .then((nextStatus) => {
        if (!cancelled) {
          setStatus(nextStatus);
          setError("");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setStatus(null);
          setError(err instanceof Error ? err.message : "无法连接后端 API");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const readiness = useMemo(() => {
    if (!status) {
      return {
        label: "待检测",
        detail: "正在读取系统依赖状态。",
        ready: false,
        actions: ["确认后端服务已启动：.\\scripts\\start-local.ps1 -CheckOnly"],
      };
    }
    const missingCapabilities = requiredApiCapabilities.filter(
      (capability) => !(status.api.capabilities ?? []).includes(capability),
    );
    const requiredBlockers = [
      !status.api.connected ? "API" : "",
      missingCapabilities.length > 0 ? "API 能力版本" : "",
      !status.database.connected ? "数据库" : "",
    ].filter(Boolean);
    const modelReady = status.model.connected && status.model.available;
    if (requiredBlockers.length > 0) {
      return {
        label: "存在阻塞",
        detail: `${requiredBlockers.join("、")} 尚未就绪，访谈、报告和备份能力可能不可用。`,
        ready: false,
        actions: [
          "检查本地服务：.\\scripts\\start-local.ps1 -CheckOnly",
          ...(missingCapabilities.length > 0 ? ["当前 API 可能是旧进程，请重启后端以加载最新代码。"] : []),
          "检查数据库：.\\scripts\\verify-local.ps1 -SkipFrontend -CheckDatabase",
        ],
      };
    }
    if (!modelReady) {
      return {
        label: "降级可用",
        detail: "API 和数据库正常；本地 AI 未就绪，报告会使用引导式兜底内容，适合继续演示和录入真实案例。",
        ready: true,
        actions: [
          `启动 Ollama 并安装模型：ollama pull ${status.config.ollama_model}`,
          "验证模型：.\\scripts\\verify-local.ps1 -SkipFrontend -CheckModel",
        ],
      };
    }
    return {
      label: "可用于本地交付",
      detail: "API、数据库和本地 AI 均已连接，可以继续访谈、生成报告和导出文档。",
      ready: true,
      actions: ["建议交付前导出一次本地备份，并保留当前 .env 与启动脚本配置。"],
    };
  }, [status]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:py-10">
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-brand">运行状态</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">系统设置</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            检查 API、数据库和本地大模型，方便把诊断平台从本地原型推进到可交付产品。
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-wait disabled:opacity-70"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          重新检测
        </button>
      </div>

      {error ? (
        <section className="mb-5 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          后端 API 未连接：{error}
        </section>
      ) : null}

      <section className={`mb-5 rounded-xl border bg-white/80 p-5 ${readiness.ready ? "border-emerald-200" : "border-amber-200"}`}>
        <div className="flex items-start gap-3">
          <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${readiness.ready ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
            <Settings className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-slate-950">{readiness.label}</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">{readiness.detail}</p>
            <div className="mt-4 grid gap-2">
              {readiness.actions.map((item) => (
                <code key={item} className="rounded-lg bg-slate-950 px-3 py-2 text-xs leading-5 text-slate-100">
                  {item}
                </code>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        <StatusCard
          title="后端 API"
          detail={
            status?.api.connected
              ? "FastAPI 服务正在响应前端请求。"
              : "前端暂时无法读取后端状态。"
          }
          connected={Boolean(status?.api.connected)}
          icon={<Server className="h-5 w-5" />}
          meta={
            status
              ? [
                  `状态：${status.api.status}`,
                  status.api.service ?? "unknown-service",
                  `能力：${status.api.capabilities?.length ?? 0}`,
                  `CORS：${status.config.cors_allowed_origins?.length ?? 0} 个来源`,
                  status.config.frontend_dist_dir ? "Web 构建：已托管" : "Web 构建：未检测",
                  ...requiredApiCapabilities
                    .filter((capability) => !(status.api.capabilities ?? []).includes(capability))
                    .map((capability) => `缺少：${capability}`),
                ]
              : undefined
          }
        />
        <StatusCard
          title="数据库"
          detail={
            status?.database.connected
              ? "数据库连接可用，诊断案例和报告可以持久化。"
              : "数据库 ping 失败，请检查 DATABASE_URL 或本地服务。"
          }
          connected={Boolean(status?.database.connected)}
          icon={<Database className="h-5 w-5" />}
          meta={
            status
              ? [
                  status.database.driver,
                  status.database.host ?? "unknown",
                  status.database.name ?? "default",
                  `${status.data.cases} 个案例`,
                  `${status.data.reports} 份报告`,
                  `${status.data.report_revisions} 个历史版本`,
                  ...(status.database.error ? [status.database.error] : []),
                ]
              : undefined
          }
        />
        <StatusCard
          title="本地大模型"
          detail={
            status?.model.connected && status.model.available
              ? "Ollama 已连接，所选模型可用于生成诊断报告。"
              : "Ollama 未连接或模型未安装，系统会使用引导式兜底内容。"
          }
          connected={Boolean(status?.model.connected && status.model.available)}
          icon={<Cpu className="h-5 w-5" />}
          meta={
            status
                ? [
                  status.config.ollama_base_url,
                  status.config.ollama_model,
                  `keep_alive ${status.config.ollama_keep_alive}`,
                  modelErrorText(status.model.error),
                ]
              : undefined
          }
        />
      </div>

      <section className="mt-5 rounded-xl border border-slate-200 bg-white/80 p-5">
        <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-center">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-sky-50 text-brand">
              <Download className="h-5 w-5" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-950">本地数据备份</h2>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">
                导出案例、访谈、报告和历史版本为 JSON 文件，适合在升级、迁移 PostgreSQL 或交付客户环境前留存快照。
              </p>
            </div>
          </div>
          <FileDownloadLink
            href={systemBackupUrl()}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-brand px-4 text-sm font-semibold text-white shadow-sm transition hover:brightness-95"
          >
            <Download className="h-4 w-4" />
            下载备份
          </FileDownloadLink>
        </div>
      </section>
    </main>
  );
}
