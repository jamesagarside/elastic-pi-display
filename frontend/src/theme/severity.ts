import type { UseEuiTheme } from '@elastic/eui';

export type Severity = 'critical' | 'high' | 'medium' | 'low';

export const SEVERITY_ORDER: Severity[] = ['critical', 'high', 'medium', 'low'];

export const SEVERITY_LABELS: Record<Severity, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

/**
 * Map alert severities to the Borealis semantic severity palette (the same
 * tokens Elastic Security uses), falling back to the classic semantic
 * colours if a future EUI version reshapes the palette.
 */
export function severityColor(euiTheme: UseEuiTheme['euiTheme'], severity: Severity): string {
  const palette = (euiTheme.colors as Record<string, any>).severity ?? {};
  switch (severity) {
    case 'critical':
      return palette.danger ?? euiTheme.colors.danger;
    case 'high':
      return palette.risk ?? euiTheme.colors.warning;
    case 'medium':
      return palette.warning ?? euiTheme.colors.warning;
    case 'low':
      return palette.neutral ?? euiTheme.colors.primary;
  }
}

/** Risk-engine levels (Unknown/Low/Moderate/High/Critical) → severity palette. */
export function riskLevelColor(euiTheme: UseEuiTheme['euiTheme'], level: string | null): string {
  switch ((level ?? '').toLowerCase()) {
    case 'critical':
      return severityColor(euiTheme, 'critical');
    case 'high':
      return severityColor(euiTheme, 'high');
    case 'moderate':
      return severityColor(euiTheme, 'medium');
    case 'low':
      return severityColor(euiTheme, 'low');
    default:
      return euiTheme.colors.textSubdued;
  }
}
