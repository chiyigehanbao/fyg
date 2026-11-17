/**
 * 公网落地页：对齐历史记录中的 page.tsx 结构（顶栏 / Hero / 三步 muted / CTA glass / FAQ / 页脚）。
 * 背景由 App.tsx 的 AppBackground 统一承载。
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3,
  Brain,
  ChevronDown,
  ChevronRight,
  FileOutput,
  FileText,
  HelpCircle,
  LogIn,
  MessageSquare,
  Sparkles,
  Target,
  UserPlus,
} from "lucide-react";
import { HeaderAuth } from "@/components/HeaderAuth";
import { industries, landing } from "@/copy/zh-CN";
import { appPaths } from "@/routes";

const INDUSTRY_ICONS = [
  Brain,
  FileText,
  FileOutput,
  BarChart3,
  MessageSquare,
  Target,
];

const FLOW_ICONS = [MessageSquare, Brain, FileOutput];

export default function HomePage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div className="relative flex min-h-screen flex-col">
      {/* 顶栏：全宽左右对齐 */}
      <header className="sticky top-0 z-50 border-b border-slate-200/50 bg-white/70 shadow-[inset_0_1px_0_0_rgba(6,182,212,0.12)] backdrop-blur-lg">
        <div className="mx-auto flex h-14 w-full items-center justify-between gap-4 px-4 sm:h-16 sm:px-6 lg:px-8">
          <Link
            to={appPaths.home}
            className="group flex min-w-0 flex-1 items-center justify-start gap-2 sm:gap-3"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#00aeef] to-blue-600 text-white shadow-md sm:h-10 sm:w-10">
              <Sparkles className="h-4 w-4 sm:h-5 sm:w-5" />
            </div>
            <div className="min-w-0 text-left">
              <span className="block truncate text-sm font-semibold text-slate-900 transition-colors group-hover:text-[#00aeef] sm:text-base">
                {landing.productName}
              </span>
              <span className="block truncate text-[11px] leading-tight text-slate-500 sm:text-xs">
                AI 赋能诊断与共创平台
              </span>
            </div>
          </Link>
          <nav className="flex shrink-0 items-center gap-2" aria-label="账户">
            <HeaderAuth />
          </nav>
        </div>
      </header>

      <main className="relative z-10 min-h-0 flex-1 px-3 py-6 sm:px-4 sm:py-10">
        <div className="mx-auto w-full max-w-4xl space-y-6 sm:space-y-8">
          {/* Hero */}
          <div className="mb-8 space-y-4 text-center sm:mb-10">
            <div className="inline-flex items-center justify-center gap-2 rounded-full bg-[hsl(var(--primary)/0.1)] px-3 py-2 text-xs font-medium text-[hsl(var(--primary))] sm:px-4 sm:text-sm">
              <Sparkles className="h-3.5 w-3.5 shrink-0 sm:h-4 sm:w-4" />
              <span className="whitespace-nowrap">{landing.tagline}</span>
            </div>

            <h1 className="title-shadow mx-auto flex w-full max-w-4xl flex-col items-center gap-1 leading-snug sm:gap-2">
              <span className="gradient-text w-full text-center text-lg font-bold sm:text-2xl md:text-3xl">
                {landing.heroTitle}
              </span>
              <span className="text-muted-fg w-full px-0.5 text-center text-xs font-medium leading-relaxed sm:text-base md:text-lg">
                {landing.heroSubtitleLead}
                <span className="whitespace-nowrap">{landing.heroSubtitleBrand}</span>
              </span>
            </h1>
          </div>

          {/* 三步 */}
          <div className="grid grid-cols-3 gap-2 py-4 sm:gap-6">
            {landing.flowSteps.map((step, i) => {
              const Icon = FLOW_ICONS[i] ?? MessageSquare;
              return (
                <div
                  key={step.title}
                  className="flex flex-col items-center gap-1 rounded-xl bg-muted-soft px-1.5 py-3 transition-colors hover-bg-primary-soft sm:gap-1.5 sm:px-2"
                >
                  <Icon className="h-5 w-5 shrink-0 text-[hsl(var(--primary))] sm:h-6 sm:w-6" />
                  <span className="whitespace-nowrap text-xs font-medium text-slate-900 sm:text-sm">
                    {step.title}
                  </span>
                  <span className="text-muted-fg whitespace-nowrap text-[11px] sm:text-xs">
                    {step.desc}
                  </span>
                </div>
              );
            })}
          </div>

          {/* CTA */}
          <div className="cta-card-hover relative">
            <div className="glass overflow-hidden rounded-xl border-0 shadow-xl">
              <div className="space-y-2 px-4 pt-4 sm:px-6 sm:pt-6">
                <div className="flex flex-wrap items-center gap-2 text-base font-semibold text-slate-900 sm:text-xl">
                  <Sparkles className="h-4 w-4 shrink-0 text-[hsl(var(--primary))] sm:h-5 sm:w-5" />
                  <span>{landing.ctaTitle}</span>
                </div>
                <p className="text-left text-sm leading-relaxed text-muted-fg sm:text-base">
                  {landing.ctaDesc}
                </p>
              </div>
              <div className="space-y-4 px-4 pb-4 pt-4 sm:px-6 sm:pb-6">
                <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
                  <Link
                    to={appPaths.start}
                    className="btn-shine inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-md bg-[hsl(var(--primary))] px-8 py-3 text-sm font-medium text-[hsl(var(--primary-foreground))] shadow-md transition-all hover:shadow-lg hover:shadow-[hsl(var(--primary)/0.25)] sm:w-auto sm:min-w-[200px]"
                  >
                    <UserPlus className="h-5 w-5 shrink-0" />
                    {landing.registerNow}
                    <ChevronRight className="h-5 w-5 shrink-0" />
                  </Link>
                  <Link
                    to={appPaths.workspace}
                    className="btn-shine inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-md bg-[hsl(var(--primary))] px-8 py-3 text-sm font-medium text-[hsl(var(--primary-foreground))] shadow-md transition-all hover:shadow-lg hover:shadow-[hsl(var(--primary)/0.25)] sm:w-auto sm:min-w-[200px]"
                  >
                    <LogIn className="h-5 w-5 shrink-0" />
                    {landing.loginNow}
                    <ChevronRight className="h-5 w-5 shrink-0" />
                  </Link>
                </div>
                <p className="text-center text-xs text-muted-fg">
                  {landing.socialProof}
                </p>
              </div>
            </div>
          </div>

          {/* FAQ */}
          <div className="py-6 text-left">
            <h3 className="text-muted-fg mb-4 flex items-center gap-2 text-sm font-semibold">
              <HelpCircle className="h-4 w-4 shrink-0" />
              {landing.faqTitle}
            </h3>
            <div className="space-y-2">
              {landing.faq.map((item, i) => (
                <div
                  key={item.q}
                  className="overflow-hidden rounded-lg border border-border-soft"
                >
                  <button
                    type="button"
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-slate-900 transition-colors hover:bg-[hsl(var(--muted)/0.5)]"
                  >
                    {item.q}
                    <ChevronDown
                      className={`h-4 w-4 shrink-0 text-muted-fg transition-transform duration-200 ${
                        openFaq === i ? "rotate-180" : ""
                      }`}
                    />
                  </button>
                  {openFaq === i ? (
                    <p className="border-t border-border-soft px-4 pb-3 pt-2 text-sm leading-relaxed text-muted-fg">
                      {item.a}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* 页脚：site-footer 三栏 */}
      <footer className="relative z-10 border-t border-slate-200/50 bg-white/80 py-8 backdrop-blur-lg sm:py-10">
        <div className="mx-auto max-w-5xl px-3 sm:px-4">
          <p className="mb-6 text-center text-xs text-slate-500">
            {landing.footerIndustriesLead}
          </p>

          <div className="mb-8 grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="flex flex-col items-center md:items-start">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 text-white">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-semibold text-slate-900">
                    {landing.productName}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {landing.footerTagline}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col items-center">
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                {landing.footerCoverTitle}
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {industries.map((label, idx) => {
                  const Icon = INDUSTRY_ICONS[idx] ?? Brain;
                  return (
                    <span
                      key={label}
                      className="inline-flex items-center gap-1 rounded-full bg-slate-100/80 px-2.5 py-1 text-xs text-slate-600 transition-colors hover:bg-[#00aeef]/10 hover:text-[#00aeef]"
                    >
                      <Icon className="h-3.5 w-3.5 shrink-0" />
                      {label}
                    </span>
                  );
                })}
              </div>
            </div>

            <div className="flex flex-col items-center gap-3 md:items-end">
              <div className="flex flex-col items-center gap-4 md:items-end">
                <p className="max-w-xs text-center text-sm leading-6 text-slate-500 md:text-right">
                  不懂 AI 也可以开始。先说清真实问题，再判断最值得验证的方向。
                </p>

                <Link
                  to={appPaths.start}
                  className="inline-flex h-10 items-center justify-center rounded-lg bg-brand px-5 text-sm font-semibold text-white transition hover:brightness-95"
                >
                  开始 AI 诊断
                </Link>
              </div>
            </div>
          </div>

          <div className="border-t border-slate-200/50 pt-6 text-center text-xs text-slate-500">
            © {new Date().getFullYear()} {landing.productName} · AI 赋能诊断与共创平台
          </div>
        </div>
      </footer>
    </div>
  );
}
