import { ClipboardList, Plus, Settings, Sparkles } from "lucide-react";
import { Link, Outlet } from "react-router-dom";
import ModelStatusBadge from "@/components/ModelStatusBadge";
import { appPaths } from "@/routes";

export default function DiagnosisShell() {
  return (
    <div className="relative z-10 min-h-screen">
      <header className="sticky top-0 z-40 border-b border-slate-200/60 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link to={appPaths.home} className="flex min-w-0 items-center gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand text-white">
              <Sparkles className="h-5 w-5" />
            </span>
            <span className="min-w-0">
              <strong className="block truncate text-sm text-slate-900">AI 共创官</strong>
              <small className="block truncate text-[11px] text-slate-500">AI 赋能诊断与共创平台</small>
            </span>
          </Link>
          <nav className="flex items-center gap-2">
            <div className="hidden md:block"><ModelStatusBadge /></div>
            <Link
              to={appPaths.workspace}
              className="inline-flex h-9 items-center gap-1.5 rounded-lg px-3 text-sm font-medium text-slate-600 transition hover:bg-sky-50 hover:text-brand"
            >
              <ClipboardList className="h-4 w-4" />
              <span className="hidden sm:inline">我的诊断</span>
            </Link>
            <Link
              to={appPaths.settings}
              title="系统设置"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 transition hover:bg-sky-50 hover:text-brand"
            >
              <Settings className="h-4 w-4" />
            </Link>
            <Link
              to={appPaths.start}
              className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-brand px-3.5 text-sm font-semibold text-white transition hover:brightness-95"
            >
              <Plus className="h-4 w-4" />
              新建诊断
            </Link>
          </nav>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
