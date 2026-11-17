export function defer(callback: () => void, delayMs = 0): number {
  return window.setTimeout(callback, delayMs);
}

export function cancelDeferred(handle: number): void {
  window.clearTimeout(handle);
}

export function scrollToTop(): void {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

export function scrollElementIntoView(elementId: string): void {
  defer(() => {
    document.getElementById(elementId)?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
}
