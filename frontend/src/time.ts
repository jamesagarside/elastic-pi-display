/** Compact relative time for glanceable cards: "just now", "5m ago", "3h ago". */
export function relativeTime(input: string | number | null): string {
  if (input === null || input === undefined) return '';
  const then = typeof input === 'number' ? input * 1000 : Date.parse(input);
  if (Number.isNaN(then)) return '';
  const seconds = Math.max(0, (Date.now() - then) / 1000);
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

/** "now-24h" → "last 24h" for tile captions. */
export function windowLabel(window: string | undefined): string {
  if (!window) return '';
  const match = /^now-(\d+[smhdw])$/.exec(window);
  return match ? `last ${match[1]}` : window;
}
