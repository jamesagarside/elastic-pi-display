const STORAGE_KEY = 'esd:colorMode';

export type ColorMode = 'light' | 'dark';

export function loadColorMode(): ColorMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    // localStorage unavailable: fall through to default
  }
  return 'dark';
}

export function saveColorMode(mode: ColorMode): void {
  try {
    localStorage.setItem(STORAGE_KEY, mode);
  } catch {
    // best effort only
  }
}
