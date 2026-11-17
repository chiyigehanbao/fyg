/**
 * 本地模式兼容入口：旧登录/注册链接直接进入工作台。
 */

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { appPaths } from "@/routes";

export default function GatePage() {
  const navigate = useNavigate();

  useEffect(() => {
    navigate(appPaths.workspace, { replace: true });
  }, [navigate]);

  return (
    <div className="relative z-10 flex min-h-screen items-center justify-center p-8">
      <p className="text-app-body">本地模式无需登录，正在进入工作台…</p>
    </div>
  );
}
