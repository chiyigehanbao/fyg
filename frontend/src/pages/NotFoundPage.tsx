import { ArrowLeft, ClipboardList, Home, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { appPaths } from "@/routes";

export default function NotFoundPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl items-center justify-center px-4 py-16 sm:px-6">
      <section className="w-full rounded-3xl border border-slate-200/80 bg-white/85 p-7 text-center shadow-xl shadow-sky-100/40 backdrop-blur sm:p-10">
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand text-white">
          <Sparkles className="h-7 w-7" />
        </span>
        <p className="mt-6 text-sm font-semibold uppercase tracking-[0.18em] text-brand">404</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-950 sm:text-3xl">这个页面暂时不存在</h1>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-500">
          可能是旧链接、手动输入错误，或本地路由已经调整。诊断数据仍保存在后端，可以回到工作台继续。
        </p>
        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <Link
            to={appPaths.workspace}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-brand px-5 text-sm font-semibold text-white transition hover:brightness-95"
          >
            <ClipboardList className="h-4 w-4" />
            返回工作台
          </Link>
          <Link
            to={appPaths.home}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            <Home className="h-4 w-4" />
            回到首页
          </Link>
        </div>
        <Link
          to={appPaths.start}
          className="mt-5 inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 transition hover:text-brand"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          重新开始一次诊断
        </Link>
      </section>
    </main>
  );
}
