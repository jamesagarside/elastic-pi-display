import { EuiText, useEuiTheme } from '@elastic/eui';
import { css } from '@emotion/react';

import { SeverityTile } from '../components/SeverityTile';
import { SEVERITY_ORDER } from '../theme/severity';
import { windowLabel } from '../time';
import type { AlertsData, SourceState } from '../types';

interface Props {
  alerts: SourceState<AlertsData>;
  /** 2×2 grid on the 5" panel, single row when there's horizontal room. */
  compact: boolean;
}

export function SeverityView({ alerts, compact }: Props) {
  const { euiTheme } = useEuiTheme();
  const data = alerts.data;

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
          />
        ))}
      </div>
    </div>
  );
}
