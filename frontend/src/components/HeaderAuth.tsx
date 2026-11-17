/**
 * 顶栏右侧：本地工作台入口 + 新建诊断入口。
 */

import { Link } from "react-router-dom";
import { ClipboardList, Sparkles } from "lucide-react";
import { landing } from "@/copy/zh-CN";
import { appPaths } from "@/routes";

export type HeaderAuthProps = {
  loading?: boolean;
};

export function HeaderAuth({
  loading = false,
}: Readonly<HeaderAuthProps>) {
  if (loading) {
    return (
      <div className="h-9 w-16 animate-pulse rounded-md bg-slate-200/80" />
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Link
        to={appPaths.workspace}
        className="inline-flex h-9 items-center justify-center gap-1.5 rounded-md px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-[#00aeef]/10 hover:text-[#00aeef]"
      >
        <ClipboardList className="h-4 w-4 shrink-0" />
        {landing.headerLogin}
      </Link>
      <Link
        to={appPaths.start}
        className="inline-flex h-9 items-center justify-center gap-1.5 rounded-md bg-[#00aeef] px-4 text-sm font-medium text-white shadow-sm transition-opacity hover:opacity-95"
      >
        <Sparkles className="h-4 w-4 shrink-0" />
        {landing.headerRegister}
      </Link>
    </div>
  );
}
