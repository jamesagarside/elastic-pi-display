import { EuiPanel, EuiText, useEuiTheme } from '@elastic/eui';
import { css } from '@emotion/react';

import type { ApmData, ApmService, SourceState } from '../types';

interface Props {
  apm: SourceState<ApmData>;
}

export function ApmServicesView({ apm }: Props) {
  const { euiTheme } = useEuiTheme();
  const services = apm.data?.services ?? [];

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
          Services
          {apm.status === 'stale' ? ' · showing last known data' : ''}
        </span>
      </EuiText>
      {services.length === 0 ? (
        <EuiText size="s" color="subdued">
          <p>No transactions in the last few minutes.</p>
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
          {services.map((service) => (
            <ServiceRow key={service.name} service={service} />
          ))}
        </div>
      )}
    </div>
  );
}

function ServiceRow({ service }: { service: ApmService }) {
  const { euiTheme } = useEuiTheme();
  const errorColor =
    service.error_rate_pct >= 5
      ? euiTheme.colors.danger
      : service.error_rate_pct > 0
        ? euiTheme.colors.warning
        : euiTheme.colors.success;

  return (
    <EuiPanel hasBorder paddingSize="s" grow={false}>
      <div
        css={css`
          display: flex;
          align-items: baseline;
          gap: ${euiTheme.size.m};
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
            {service.name}
          </span>
        </EuiText>
        <div
          css={css`
            margin-left: auto;
            display: flex;
            gap: ${euiTheme.size.m};
            font-family: ${euiTheme.font.familyCode};
            white-space: nowrap;
          `}
        >
          <EuiText size="xs" color="subdued">
            <span>{service.transactions} tx</span>
          </EuiText>
          {service.latency_ms !== null && (
            <EuiText size="xs" color="subdued">
              <span>{service.latency_ms} ms</span>
            </EuiText>
          )}
          <EuiText size="xs">
            <span css={css`color: ${errorColor}; font-weight: ${euiTheme.font.weight.bold};`}>
              {service.error_rate_pct}% err
            </span>
          </EuiText>
        </div>
      </div>
    </EuiPanel>
  );
}
