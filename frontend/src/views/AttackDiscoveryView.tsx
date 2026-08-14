import {
  EuiBadge,
  EuiEmptyPrompt,
  EuiFlexGroup,
  EuiFlexItem,
  EuiPanel,
  EuiText,
  EuiTitle,
  useEuiTheme,
} from '@elastic/eui';
import { css } from '@emotion/react';

import { relativeTime, windowLabel } from '../time';
import type { AttackDiscoveryData, Discovery, SourceState } from '../types';

interface Props {
  attackDiscovery: SourceState<AttackDiscoveryData>;
  /** How many discovery cards fit this layout. */
  maxCards: number;
}

export function AttackDiscoveryView({ attackDiscovery, maxCards }: Props) {
  const { euiTheme } = useEuiTheme();
  const data = attackDiscovery.data;
  const discoveries = (data?.discoveries ?? []).slice(0, maxCards);

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
          Attack Discovery{data ? ` · ${data.total} in ${windowLabel(data.window)}` : ''}
          {attackDiscovery.status === 'stale' ? ' · showing last known data' : ''}
        </span>
      </EuiText>
      {discoveries.length === 0 ? (
        <EuiEmptyPrompt
          iconType="sparkles"
          title={<h2>No attack discoveries</h2>}
          body={<p>Nothing found in {windowLabel(data?.window) || 'the current window'}.</p>}
          titleSize="s"
        />
      ) : (
        <EuiFlexGroup
          direction="column"
          gutterSize="s"
          css={css`
            flex: 1;
            min-height: 0;
            overflow: hidden;
          `}
        >
          {discoveries.map((discovery) => (
            <EuiFlexItem key={discovery.id} grow={false}>
              <DiscoveryCard discovery={discovery} />
            </EuiFlexItem>
          ))}
        </EuiFlexGroup>
      )}
    </div>
  );
}

function DiscoveryCard({ discovery }: { discovery: Discovery }) {
  const { euiTheme } = useEuiTheme();
  return (
    <EuiPanel hasBorder paddingSize="m">
      <EuiFlexGroup gutterSize="s" alignItems="center" responsive={false}>
        <EuiFlexItem>
          <EuiTitle size="xs">
            <h3
              css={css`
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
              `}
            >
              {discovery.title}
            </h3>
          </EuiTitle>
        </EuiFlexItem>
        <EuiFlexItem grow={false}>
          <EuiText size="xs" color="subdued">
            <span>{relativeTime(discovery.timestamp)}</span>
          </EuiText>
        </EuiFlexItem>
      </EuiFlexGroup>
      <div
        css={css`
          display: flex;
          flex-wrap: wrap;
          gap: ${euiTheme.size.xs};
          margin-top: ${euiTheme.size.s};
        `}
      >
        <EuiBadge color="danger">
          {discovery.alert_count} alert{discovery.alert_count === 1 ? '' : 's'}
        </EuiBadge>
        {discovery.mitre_tactics.slice(0, 3).map((tactic) => (
          <EuiBadge key={tactic} color="hollow">
            {tactic}
          </EuiBadge>
        ))}
      </div>
    </EuiPanel>
  );
}
