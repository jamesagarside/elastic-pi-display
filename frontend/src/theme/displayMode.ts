const STORAGE_KEY = 'esd:displayMode';

export type DisplayMode = 'security' | 'observability';

export function loadDisplayMode(): DisplayMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'security' || stored === 'observability') return stored;
  } catch {
    // localStorage unavailable: fall through to default
  }
  return 'security';
}

export function saveDisplayMode(mode: DisplayMode): void {
  try {
    localStorage.setItem(STORAGE_KEY, mode);
  } catch {
    // best effort only
  }
}
