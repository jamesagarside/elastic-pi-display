import { EuiPanel, EuiText, useEuiTheme } from '@elastic/eui';
import { css } from '@emotion/react';

import { SEVERITY_LABELS, Severity, severityColor } from '../theme/severity';
import { relativeTime } from '../time';
import type { AlertSummary } from '../types';

interface Props {
  severity: Severity;
  count: number;
  alerts: AlertSummary[];
  onClose: () => void;
}

/**
 * Drill-down shown when a severity tile is tapped: the most recent alert
 * rule names for that severity. Tapping anywhere returns to the tiles.
 */
export function AlertList({ severity, count, alerts, onClose }: Props) {
  const { euiTheme } = useEuiTheme();
  const color = severityColor(euiTheme, severity);
  const more = count - alerts.length;

  return (
    <div
      onClick={(e) => {
        e.stopPropagation();
        onClose();
      }}
      css={css`
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: ${euiTheme.size.s};
        min-height: 0;
      `}
    >
      <EuiText size="s">
        <span
          css={css`
            font-weight: ${euiTheme.font.weight.semiBold};
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: ${color};
          `}
        >
          {SEVERITY_LABELS[severity]}
        </span>
        <span
          css={css`
            color: ${euiTheme.colors.textSubdued};
          `}
        >
          {' '}
          · {count} open · tap to go back
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
        {alerts.map((alert, i) => (
          <AlertRow key={i} alert={alert} color={color} />
        ))}
        {alerts.length === 0 && (
          <EuiText size="s" color="subdued">
            <p>No alert details available yet. The next poll will include them.</p>
          </EuiText>
        )}
        {more > 0 && (
          <EuiText size="xs" color="subdued">
            <span>and {more} more</span>
          </EuiText>
        )}
      </div>
    </div>
  );
}

function AlertRow({ alert, color }: { alert: AlertSummary; color: string }) {
  const { euiTheme } = useEuiTheme();
  const entities = [alert.host, alert.user].filter(Boolean).join(' · ');

  return (
    <EuiPanel
      hasBorder
      paddingSize="s"
      grow={false}
      css={css`
        border-left: ${euiTheme.size.xs} solid ${color};
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
          <span
            css={css`
              font-weight: ${euiTheme.font.weight.semiBold};
              display: -webkit-box;
              -webkit-line-clamp: 1;
              -webkit-box-orient: vertical;
              overflow: hidden;
            `}
          >
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
          <span>{relativeTime(alert.timestamp)}</span>
        </EuiText>
      </div>
      {entities && (
        <EuiText size="xs" color="subdued">
          <span>{entities}</span>
        </EuiText>
      )}
    </EuiPanel>
  );
}
