/**
 * 根路由：全站背景 + 落地页 / 管理端 / 门闸。
 */

import { Navigate, Route, Routes } from "react-router-dom";
import AppBackground from "@/components/AppBackground";
import GatePage from "@/pages/GatePage";
import HomePage from "@/pages/HomePage";
import StartPage from "@/pages/StartPage";
import DiagnosisShell from "@/layouts/DiagnosisShell";
import DashboardPage from "@/pages/DashboardPage";
import InterviewPage from "@/pages/InterviewPage";
import NotFoundPage from "@/pages/NotFoundPage";
import ReportPage from "@/pages/ReportPage";
import SettingsPage from "@/pages/SettingsPage";
import { appPaths, appRoutePatterns } from "@/routes";

export default function App() {
  return (
    <div className="relative isolate min-h-screen">
      <AppBackground />
      <div className="relative z-10">
        <Routes>
          <Route path={appRoutePatterns.home} element={<HomePage />} />
          <Route path={appRoutePatterns.start} element={<StartPage />} />
          <Route path={appRoutePatterns.login} element={<GatePage />} />
          <Route path={appRoutePatterns.register} element={<GatePage />} />

          <Route element={<DiagnosisShell />}>
            <Route path={appRoutePatterns.workspace} element={<DashboardPage />} />
            <Route path={appRoutePatterns.settings} element={<SettingsPage />} />
            <Route path={appRoutePatterns.basicInterview} element={<InterviewPage stage="basic" />} />
            <Route path={appRoutePatterns.basicReport} element={<ReportPage stage="basic" />} />
            <Route path={appRoutePatterns.advancedInterview} element={<InterviewPage stage="advanced" />} />
            <Route path={appRoutePatterns.finalReport} element={<ReportPage stage="final" />} />
          </Route>

          <Route path={appRoutePatterns.legacyAdmin} element={<Navigate to={appPaths.workspace} replace />} />
          <Route path={appRoutePatterns.notFound} element={<NotFoundPage />} />
        </Routes>
      </div>
    </div>
  );
}
