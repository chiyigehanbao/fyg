/**
 * 全站背景：渐变 + 网格 + 顶条 + 光晕 + 浮动点。
 */

const FLOAT_DOTS: { top: string; left?: string; right?: string }[] = [
  { top: "20%", left: "15%" },
  { top: "65%", right: "12%" },
  { top: "40%", right: "25%" },
];

export default function AppBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 z-0" aria-hidden>
      {/* 浅蓝向中心收束为亮白，与设计稿门户背景一致 */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_85%_65%_at_50%_45%,#ffffff_0%,#f0f9fc_42%,#e0f4fb_100%)]" />
      <div className="absolute inset-0 bg-gradient-to-b from-sky-100/50 via-transparent to-cyan-50/40" />
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.45]" />
      <div
        className="absolute left-0 right-0 top-0 h-1 bg-gradient-to-r from-brand via-sky-400 to-blue-500"
        style={{ transformOrigin: "left" }}
      />
      <div className="absolute -left-40 top-1/3 h-80 w-80 rounded-full bg-brand/20 blur-3xl" />
      <div className="absolute -right-40 bottom-1/3 h-96 w-96 rounded-full bg-sky-400/16 blur-3xl" />
      {FLOAT_DOTS.map((dot, i) => (
        <div
          key={`${dot.top}-${dot.left ?? ""}-${dot.right ?? ""}`}
          className="animate-float absolute h-2.5 w-2.5 rounded-full bg-brand/35 shadow-[0_0_14px_4px_rgba(0,174,239,0.35)]"
          style={{
            top: dot.top,
            left: dot.left,
            right: dot.right,
            animationDelay: `${i * 0.5}s`,
          }}
        />
      ))}
    </div>
  );
}
