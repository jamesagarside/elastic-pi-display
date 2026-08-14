import { EuiBadge, EuiIcon, EuiText, useEuiTheme } from '@elastic/eui';
import { css } from '@emotion/react';

import { relativeTime } from '../time';
import type { Snapshot } from '../types';
import { ViewDots } from './ViewDots';

interface Props {
  snapshot: Snapshot | null;
  connected: boolean;
  viewCount: number;
  viewIndex: number;
}

export function StatusBar({ snapshot, connected, viewCount, viewIndex }: Props) {
  const { euiTheme } = useEuiTheme();

  const lastUpdated = snapshot
    ? Math.max(
        ...Object.values(snapshot.sources)
          .map((s) => s?.updated_at ?? 0)
          .concat(0),
      )
    : 0;

  const reachable = snapshot?.meta.elastic_reachable !== false;
  const pill = !connected
    ? { color: 'danger', label: 'Display offline' }
    : !reachable
      ? { color: 'warning', label: 'Elastic unreachable' }
      : { color: 'success', label: 'Live' };

  return (
    <div
      css={css`
        display: flex;
        align-items: center;
        gap: ${euiTheme.size.s};
        padding: ${euiTheme.size.s} ${euiTheme.size.m};
        border-top: ${euiTheme.border.thin};
        background: ${euiTheme.colors.body};
      `}
    >
      <EuiIcon type="logoSecurity" size="m" />
      <EuiText size="xs">
        <span css={css`font-weight: ${euiTheme.font.weight.semiBold};`}>
          Elastic Security
        </span>
      </EuiText>
      {snapshot?.meta.space && snapshot.meta.space !== 'default' && (
        <EuiBadge color="hollow">{snapshot.meta.space}</EuiBadge>
      )}
      <div css={css`flex: 1; display: flex; justify-content: center;`}>
        {viewCount > 1 && <ViewDots count={viewCount} active={viewIndex} />}
      </div>
      {lastUpdated > 0 && (
        <EuiText size="xs" color="subdued">
          <span>updated {relativeTime(lastUpdated)}</span>
        </EuiText>
      )}
      <EuiBadge color={pill.color}>{pill.label}</EuiBadge>
    </div>
  );
}
