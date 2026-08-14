import { useEffect, useState } from 'react';

/**
 * small  — 5" panels (800×480): one view at a time, tap to cycle
 * medium — ~10" screens: severity + attack discovery side by side
 * large  — monitors/TVs: all regions at once
 */
export type LayoutTier = 'small' | 'medium' | 'large';

function tierFor(width: number): LayoutTier {
  if (width < 1024) return 'small';
  if (width < 1600) return 'medium';
  return 'large';
}

export function useLayoutTier(): LayoutTier {
  const [tier, setTier] = useState<LayoutTier>(() => tierFor(window.innerWidth));

  useEffect(() => {
    const onResize = () => setTier(tierFor(window.innerWidth));
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return tier;
}
