import { EuiBadge, EuiPanel, EuiProgress, EuiText, useEuiTheme } from '@elastic/eui';
import { css } from '@emotion/react';

import type { Slo, SloData, SourceState } from '../types';

interface Props {
  slos: SourceState<SloData>;
}

const STATUS_COLORS: Record<string, string> = {
  VIOLATED: 'danger',
  DEGRADING: 'warning',
  NO_DATA: 'hollow',
  HEALTHY: 'success',
};

export function SloView({ slos }: Props) {
  const { euiTheme } = useEuiTheme();
  const list = slos.data?.slos ?? [];

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
          SLOs{slos.data ? ` · ${slos.data.total}` : ''}
          {slos.status === 'stale' ? ' · showing last known data' : ''}
        </span>
      </EuiText>
      <div
        css={css`
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: ${euiTheme.size.s};
          min-height: 0;
          overflow: hidden;
        `}
      >
        {list.map((slo) => (
          <SloRow key={slo.name ?? ''} slo={slo} />
        ))}
      </div>
    </div>
  );
}

function SloRow({ slo }: { slo: Slo }) {
  const { euiTheme } = useEuiTheme();
  const budget = slo.budget_remaining;
  const budgetPct = budget === null ? null : Math.max(0, Math.round(budget * 100));

  return (
    <EuiPanel hasBorder paddingSize="s" grow={false}>
      <div
        css={css`
          display: flex;
          align-items: center;
          gap: ${euiTheme.size.s};
        `}
      >
        <EuiText size="s">
          <span
            css={css`
              font-weight: ${euiTheme.font.weight.semiBold};
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            `}
          >
            {slo.name}
          </span>
        </EuiText>
        <div css={css`margin-left: auto;`}>
          <EuiBadge color={STATUS_COLORS[slo.status ?? ''] ?? 'hollow'}>
            {slo.status ?? 'UNKNOWN'}
          </EuiBadge>
        </div>
      </div>
      {budgetPct !== null && (
        <div css={css`margin-top: ${euiTheme.size.xs};`}>
          <div
            css={css`
              display: flex;
              justify-content: space-between;
              margin-bottom: 2px;
            `}
          >
            <EuiText size="xs" color="subdued">
              <span>error budget</span>
            </EuiText>
            <EuiText size="xs" color="subdued">
              <span>{budgetPct}% left</span>
            </EuiText>
          </div>
          <EuiProgress
            value={budgetPct}
            max={100}
            size="s"
            color={budgetPct <= 10 ? 'danger' : budgetPct <= 33 ? 'warning' : 'success'}
          />
        </div>
      )}
    </EuiPanel>
  );
}
