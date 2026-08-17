import { EuiEmptyPrompt, EuiPanel, EuiText, useEuiTheme } from '@elastic/eui';
import { css } from '@emotion/react';

import { relativeTime } from '../time';
import type { ObsAlert, ObsAlertsData, SourceState } from '../types';

interface Props {
  obsAlerts: SourceState<ObsAlertsData>;
}

export function ObservabilityAlertsView({ obsAlerts }: Props) {
  const { euiTheme } = useEuiTheme();
  const data = obsAlerts.data;
  const active = data?.active ?? 0;
  const color = active > 0 ? euiTheme.colors.danger : euiTheme.colors.success;

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
          Observability alerts
          {obsAlerts.status === 'stale' ? ' · showing last known data' : ''}
        </span>
      </EuiText>
      <div
        css={css`
          display: flex;
          align-items: baseline;
          gap: ${euiTheme.size.s};
        `}
      >
        <span
          css={css`
            font-family: ${euiTheme.font.familyCode};
            font-weight: ${euiTheme.font.weight.bold};
            font-size: clamp(2.5rem, 12vh, 6rem);
            line-height: 1;
            color: ${color};
          `}
        >
          {active}
        </span>
        <EuiText size="s" color="subdued">
          <span>active</span>
        </EuiText>
      </div>
      {active === 0 ? (
        <EuiEmptyPrompt
          iconType="bell"
          title={<h2>All quiet</h2>}
          body={<p>No observability rules are firing.</p>}
          titleSize="s"
        />
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
          {(data?.recent ?? []).map((alert, i) => (
            <ObsAlertRow key={i} alert={alert} />
          ))}
        </div>
      )}
    </div>
  );
}

function ObsAlertRow({ alert }: { alert: ObsAlert }) {
  const { euiTheme } = useEuiTheme();
  return (
    <EuiPanel
      hasBorder
      paddingSize="s"
      grow={false}
      css={css`
        border-left: ${euiTheme.size.xs} solid ${euiTheme.colors.danger};
      `}
    >
      <div
        css={css`
          display: flex;
          align-items: baseline;
          gap: ${euiTheme.size.s};
        `}
      >
        <EuiText size="s">
          <span css={css`font-weight: ${euiTheme.font.weight.semiBold};`}>
            {alert.rule_name}
          </span>
        </EuiText>
        <EuiText
          size="xs"
          color="subdued"
          css={css`
            margin-left: auto;
            white-space: nowrap;
          `}
        >
          <span>{relativeTime(alert.started)}</span>
        </EuiText>
      </div>
      {alert.reason && (
        <EuiText size="xs" color="subdued">
          <span
            css={css`
              display: -webkit-box;
              -webkit-line-clamp: 2;
              -webkit-box-orient: vertical;
              overflow: hidden;
            `}
          >
            {alert.reason}
          </span>
        </EuiText>
      )}
    </EuiPanel>
  );
}
