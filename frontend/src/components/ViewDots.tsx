import { useEuiTheme } from '@elastic/eui';
import { css } from '@emotion/react';

interface Props {
  count: number;
  active: number;
}

export function ViewDots({ count, active }: Props) {
  const { euiTheme } = useEuiTheme();
  return (
    <div
      css={css`
        display: flex;
        gap: ${euiTheme.size.xs};
        align-items: center;
      `}
      aria-label={`View ${active + 1} of ${count}`}
    >
      {Array.from({ length: count }, (_, i) => (
        <span
          key={i}
          css={css`
            width: ${euiTheme.size.s};
            height: ${euiTheme.size.s};
            border-radius: 50%;
            background: ${i === active
              ? euiTheme.colors.primary
              : euiTheme.colors.lightShade};
            transition: background 0.15s ease;
          `}
        />
      ))}
    </div>
  );
}
