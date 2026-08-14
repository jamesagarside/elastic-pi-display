import {
  EuiFlexGroup,
  EuiFlexItem,
  EuiIcon,
  EuiPanel,
  EuiProgress,
  EuiText,
  useEuiTheme,
} from '@elastic/eui';
import { css } from '@emotion/react';

import { riskLevelColor } from '../theme/severity';
import type { RiskData, RiskEntity, SourceState } from '../types';

interface Props {
  riskScores: SourceState<RiskData>;
}

export function RiskView({ riskScores }: Props) {
  const { euiTheme } = useEuiTheme();
  const data = riskScores.data;

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
          Entity risk scores
          {riskScores.status === 'stale' ? ' · showing last known data' : ''}
        </span>
      </EuiText>
      <EuiFlexGroup gutterSize="s" css={css`flex: 1; min-height: 0;`} responsive={false}>
        <EntityColumn icon="storage" title="Hosts" entities={data?.hosts ?? []} />
        <EntityColumn icon="user" title="Users" entities={data?.users ?? []} />
      </EuiFlexGroup>
    </div>
  );
}

function EntityColumn({
  icon,
  title,
  entities,
}: {
  icon: string;
  title: string;
  entities: RiskEntity[];
}) {
  const { euiTheme } = useEuiTheme();
  return (
    <EuiFlexItem>
      <EuiPanel hasBorder paddingSize="m" css={css`height: 100%;`}>
        <EuiText size="s">
          <span
            css={css`
              font-weight: ${euiTheme.font.weight.semiBold};
              display: inline-flex;
              align-items: center;
              gap: ${euiTheme.size.xs};
            `}
          >
            <EuiIcon type={icon} size="s" /> {title}
          </span>
        </EuiText>
        <div
          css={css`
            display: flex;
            flex-direction: column;
            gap: ${euiTheme.size.m};
            margin-top: ${euiTheme.size.m};
          `}
        >
          {entities.length === 0 ? (
            <EuiText size="xs" color="subdued">
              <span>No scored entities</span>
            </EuiText>
          ) : (
            entities.map((entity) => <EntityRow key={entity.name} entity={entity} />)
          )}
        </div>
      </EuiPanel>
    </EuiFlexItem>
  );
}

function EntityRow({ entity }: { entity: RiskEntity }) {
  const { euiTheme } = useEuiTheme();
  const color = riskLevelColor(euiTheme, entity.level);
  return (
    <div>
      <div
        css={css`
          display: flex;
          justify-content: space-between;
          gap: ${euiTheme.size.s};
          margin-bottom: ${euiTheme.size.xs};
        `}
      >
        <EuiText size="s">
          <span
            css={css`
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            `}
          >
            {entity.name}
          </span>
        </EuiText>
        <EuiText size="s">
          <span
            css={css`
              font-family: ${euiTheme.font.familyCode};
              font-weight: ${euiTheme.font.weight.bold};
              color: ${color};
            `}
          >
            {entity.score}
          </span>
        </EuiText>
      </div>
      <EuiProgress value={entity.score} max={100} size="s" color={color} />
    </div>
  );
}
