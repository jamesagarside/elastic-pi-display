import { EuiPanel, EuiProgress, EuiText, useEuiTheme } from '@elastic/eui';
import { css } from '@emotion/react';

import type { HostMetrics, HostsData, SourceState } from '../types';

interface Props {
  hosts: SourceState<HostsData>;
}

export function HostsView({ hosts }: Props) {
  const { euiTheme } = useEuiTheme();
  const list = hosts.data?.hosts ?? [];

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
          Hosts
          {hosts.status === 'stale' ? ' · showing last known data' : ''}
        </span>
      </EuiText>
      {list.length === 0 ? (
        <EuiText size="s" color="subdued">
          <p>No host metrics in the last few minutes.</p>
        </EuiText>
      ) : (
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
          {list.map((host) => (
            <HostRow key={host.name} host={host} />
          ))}
        </div>
      )}
    </div>
  );
}

function usageColor(euiTheme: ReturnType<typeof useEuiTheme>['euiTheme'], pct: number | null) {
  if (pct === null) return euiTheme.colors.textSubdued;
  if (pct >= 90) return euiTheme.colors.danger;
  if (pct >= 75) return euiTheme.colors.warning;
  return euiTheme.colors.success;
}

function HostRow({ host }: { host: HostMetrics }) {
  const { euiTheme } = useEuiTheme();
  return (
    <EuiPanel hasBorder paddingSize="s" grow={false}>
      <EuiText size="s">
        <span css={css`font-weight: ${euiTheme.font.weight.semiBold};`}>{host.name}</span>
      </EuiText>
      <div
        css={css`
          display: flex;
          gap: ${euiTheme.size.m};
          margin-top: ${euiTheme.size.xs};
        `}
      >
        <Meter label="CPU" pct={host.cpu_pct} />
        <Meter label="MEM" pct={host.memory_pct} />
      </div>
    </EuiPanel>
  );
}

function Meter({ label, pct }: { label: string; pct: number | null }) {
  const { euiTheme } = useEuiTheme();
  const color = usageColor(euiTheme, pct);
  return (
    <div css={css`flex: 1; min-width: 0;`}>
      <div
        css={css`
          display: flex;
          justify-content: space-between;
          margin-bottom: 2px;
        `}
      >
        <EuiText size="xs" color="subdued">
          <span>{label}</span>
        </EuiText>
        <EuiText size="xs">
          <span
            css={css`
              font-family: ${euiTheme.font.familyCode};
              font-weight: ${euiTheme.font.weight.bold};
              color: ${color};
            `}
          >
            {pct === null ? 'n/a' : `${pct}%`}
          </span>
        </EuiText>
      </div>
      <EuiProgress value={pct ?? 0} max={100} size="s" color={color} />
    </div>
  );
}
