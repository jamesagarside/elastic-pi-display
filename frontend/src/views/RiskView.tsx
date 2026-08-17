import {
  EuiEmptyPrompt,
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

/** Entity Store types → registered icons; anything unrecognised gets gear. */
function entityIcon(type: string | null): string {
  switch ((type ?? '').toLowerCase()) {
    case 'host':
      return 'storage';
    case 'user':
      return 'user';
    default:
      return 'gear';
  }
}

export function RiskView({ riskScores }: Props) {
  const { euiTheme } = useEuiTheme();
  const entities = riskScores.data?.entities ?? [];

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
      {entities.length === 0 ? (
        <EuiEmptyPrompt
          iconType="user"
          title={<h2>No scored entities</h2>}
          body={<p>The risk engine has not scored anything yet.</p>}
          titleSize="s"
        />
      ) : (
        <EuiPanel
          hasBorder
          paddingSize="m"
          css={css`
            flex: 1;
            min-height: 0;
            overflow: hidden;
          `}
        >
          <div
            css={css`
              display: flex;
              flex-direction: column;
              gap: ${euiTheme.size.m};
            `}
          >
            {entities.map((entity) => (
              <EntityRow key={`${entity.type}:${entity.name}`} entity={entity} />
            ))}
          </div>
        </EuiPanel>
      )}
    </div>
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
          align-items: center;
          justify-content: space-between;
          gap: ${euiTheme.size.s};
          margin-bottom: ${euiTheme.size.xs};
        `}
      >
        <EuiText size="s">
          <span
            css={css`
              display: inline-flex;
              align-items: center;
              gap: ${euiTheme.size.xs};
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            `}
          >
            <EuiIcon
              type={entityIcon(entity.type)}
              size="s"
              color="subdued"
              title={entity.type ?? undefined}
            />
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
