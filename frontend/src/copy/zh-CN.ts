/**
 * 业务可见中文文案。
 */

/**
 * 公网 Landing 全文案（与设计稿 `docs/assets/首页.png` 对齐；禁用「演示/Demo/样例」等用语）。
 */
export const landing = {
  productName: "AI 共创官",
  headerLogin: "我的诊断",
  headerRegister: "开始诊断",
  tagline: "找到最值得落地的 AI 机会",
  heroTitle: "把难题说清，让 AI 真正落地",
  /** 副标题拆行：末尾品牌词 nowrap */
  heroSubtitleLead: "从业务痛点到可执行方案，两阶段完成你的专属",
  heroSubtitleBrand: "AI 赋能诊断",
  flowSteps: [
    { title: "说出难题", desc: "描述真实困境" },
    { title: "机会诊断", desc: "定位 AI 切入点" },
    { title: "专属方案", desc: "形成落地路径" },
  ],
  ctaTitle: "先看清问题，再决定 AI 怎么做。",
  ctaDesc: "用几分钟完成基础诊断，先获得一份直击痛点的 AI 机会报告。",
  registerNow: "开始免费诊断",
  loginNow: "查看我的诊断",
  socialProof: "不限行业、不限团队规模，从一个真实问题开始",
  faqTitle: "常见问题",
  faq: [
    {
      q: "需要准备什么？",
      a: "不需要先懂 AI。只要描述正在发生的业务问题、目前的处理方式和希望改善的结果。",
    },
    {
      q: "AI 如何帮我？",
      a: "系统会先定位真正的痛点和高价值机会，再判断更适合知识问答、内容生成、流程自动化、数据分析、客户服务还是决策辅助。",
    },
    {
      q: "为什么分成两个阶段？",
      a: "基础阶段帮助你快速看清方向；确认值得继续后，再通过深度共创收集流程、数据、系统和约束，生成专属落地方案。",
    },
  ],
  footerTagline: "从真实痛点出发的 AI 赋能诊断",
  footerIndustriesLead: "覆盖组织运营、客户服务、内容知识、数据决策与个人效率",
  footerCoverTitle: "AI 机会方向",
} as const;

/** 页脚行业栅格（与设计稿图标文案一致） */
export const industries = [
  "知识问答",
  "内容生成",
  "流程自动化",
  "数据分析",
  "客户服务",
  "决策辅助",
] as const;
