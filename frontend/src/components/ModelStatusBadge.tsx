import { useEffect, useState } from "react";
import { Cpu, LoaderCircle } from "lucide-react";
import { type ModelStatus, fetchModelStatus } from "@/api/diagnosis";

export default function ModelStatusBadge() {
  const [status, setStatus] = useState<ModelStatus | null>(null);

  useEffect(() => {
    fetchModelStatus().then(setStatus).catch(() => {
      setStatus({ connected: false, available: false, model: "本地模型", provider: "ollama" });
    });
  }, []);

  if (!status) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-[11px] text-slate-500">
        <LoaderCircle className="h-3 w-3 animate-spin" />检测本地 AI
      </span>
    );
  }

  const ready = status.connected && status.available;
  return (
    <span
      title={ready ? `本地 Ollama · ${status.model}` : "Ollama 未启动或所选模型未安装，报告将使用引导式兜底"}
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${
        ready ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${ready ? "bg-emerald-500" : "bg-amber-500"}`} />
      <Cpu className="h-3 w-3" />
      {ready ? `本地 AI · ${status.model}` : "本地 AI 未连接"}
    </span>
  );
}
