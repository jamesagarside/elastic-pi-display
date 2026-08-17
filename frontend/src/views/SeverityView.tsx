import { EuiText, useEuiTheme } from '@elastic/eui';
import { css } from '@emotion/react';
import { useEffect, useState } from 'react';

import { AlertList } from '../components/AlertList';
import { SeverityTile } from '../components/SeverityTile';
import { SEVERITY_ORDER, Severity } from '../theme/severity';
import { windowLabel } from '../time';
import type { AlertsData, SourceState } from '../types';

/** Return the drill-down to the tiles if nobody taps it away. */
const DRILLDOWN_TIMEOUT_MS = 30_000;

interface Props {
  alerts: SourceState<AlertsData>;
  /** 2×2 grid on the 5" panel, single row when there's horizontal room. */
  compact: boolean;
}

export function SeverityView({ alerts, compact }: Props) {
  const { euiTheme } = useEuiTheme();
  const data = alerts.data;
  const [selected, setSelected] = useState<Severity | null>(null);

  useEffect(() => {
    if (!selected) return;
    const timer = setTimeout(() => setSelected(null), DRILLDOWN_TIMEOUT_MS);
    return () => clearTimeout(timer);
  }, [selected]);

  if (selected && data) {
    return (
      <AlertList
        severity={selected}
        count={data.counts[selected]}
        alerts={data.recent?.[selected] ?? []}
        onClose={() => setSelected(null)}
      />
    );
  }

  return (
    <div
      css={css`
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: ${euiTheme.size.s};
        min-height: 0;
      `}
    >
      <EuiText size="s" color="subdued">
        <span>
          Open alerts{data ? ` · ${windowLabel(data.window)}` : ''}
          {alerts.status === 'stale' ? ' · showing last known data' : ''}
        </span>
      </EuiText>
      <div
        css={css`
          flex: 1;
          display: grid;
          grid-template-columns: ${compact ? '1fr 1fr' : 'repeat(4, 1fr)'};
          ${compact ? 'grid-template-rows: 1fr 1fr;' : ''}
          gap: ${euiTheme.size.s};
          min-height: 0;
        `}
      >
        {SEVERITY_ORDER.map((severity) => (
          <SeverityTile
            key={severity}
            severity={severity}
            count={data?.counts[severity] ?? 0}
            onSelect={() => setSelected(severity)}
          />
        ))}
      </div>
    </div>
  );
}
