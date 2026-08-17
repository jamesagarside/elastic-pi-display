import { EuiPanel, EuiText, useEuiTheme } from '@elastic/eui';
import { css } from '@emotion/react';

import { SEVERITY_LABELS, Severity, severityColor } from '../theme/severity';

interface Props {
  severity: Severity;
  count: number;
  /** Called on tap when the tile has alerts to show. */
  onSelect?: () => void;
}

export function SeverityTile({ severity, count, onSelect }: Props) {
  const { euiTheme } = useEuiTheme();
  const color = severityColor(euiTheme, severity);
  const active = count > 0;

  return (
    <EuiPanel
      hasBorder
      paddingSize="m"
      onClick={
        active && onSelect
          ? (e: React.MouseEvent) => {
              // Keep the tap from also cycling views.
              e.stopPropagation();
              onSelect();
            }
          : undefined
      }
      css={css`
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border-top: ${euiTheme.size.xs} solid ${color};
        min-height: 0;
      `}
    >
      <EuiText size="s">
        <span
          css={css`
            font-weight: ${euiTheme.font.weight.semiBold};
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: ${euiTheme.colors.textSubdued};
          `}
        >
          {SEVERITY_LABELS[severity]}
        </span>
      </EuiText>
      <div
        css={css`
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: flex-end;
          font-family: ${euiTheme.font.familyCode};
          font-weight: ${euiTheme.font.weight.bold};
          /* Numerals dominate the tile on every screen size */
          font-size: clamp(3rem, 18vh, 11rem);
          line-height: 1;
          color: ${active ? color : euiTheme.colors.textSubdued};
        `}
      >
        {count}
      </div>
    </EuiPanel>
  );
}
