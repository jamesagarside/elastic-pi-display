// EUI loads icons via dynamic imports that Vite cannot statically bundle, so
// every icon used in the app must be pre-registered here (an offline kiosk
// cannot fall back to fetching them).
// @ts-expect-error: deep ES module path has no type declarations
import { appendIconComponentCache } from '@elastic/eui/es/components/icon/icon';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as logoSecurity } from '@elastic/eui/es/components/icon/assets/logo_security';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as sparkles } from '@elastic/eui/es/components/icon/assets/sparkles';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as storage } from '@elastic/eui/es/components/icon/assets/storage';
// @ts-expect-error: icon asset modules ship without type declarations
import { icon as user } from '@elastic/eui/es/components/icon/assets/user';

export function registerIcons(): void {
  appendIconComponentCache({
    logoSecurity,
    sparkles,
    storage,
    user,
  });
}
