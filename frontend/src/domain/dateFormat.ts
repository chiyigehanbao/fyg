export function formatCaseDate(value: string | null | undefined): string {
  if (!value) return "刚刚创建";

  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return "时间待校准";

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(timestamp));
}
