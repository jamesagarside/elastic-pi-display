// EUI loads icons via dynamic imports that Vite cannot statically bundle, so
// every icon used in the app must be pre-registered here (an offline kiosk
// cannot fall back to fetching them).
// @ts-expect-error: deep ES module path has no type declarations
import { appendIconComponentCache } from '@elastic/eui/es/components/icon/icon';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as bell } from '@elastic/eui/es/components/icon/assets/bell';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as gear } from '@elastic/eui/es/components/icon/assets/gear';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as logoObservability } from '@elastic/eui/es/components/icon/assets/logo_observability';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as logoSecurity } from '@elastic/eui/es/components/icon/assets/logo_security';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as moon } from '@elastic/eui/es/components/icon/assets/moon';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as sparkles } from '@elastic/eui/es/components/icon/assets/sparkles';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as storage } from '@elastic/eui/es/components/icon/assets/storage';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as sun } from '@elastic/eui/es/components/icon/assets/sun';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as user } from '@elastic/eui/es/components/icon/assets/user';

export function registerIcons(): void {
  appendIconComponentCache({
    bell,
    gear,
    logoObservability,
    logoSecurity,
    moon,
    sparkles,
    storage,
    sun,
    user,
  });
}
