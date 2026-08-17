export type SourceStatus = 'pending' | 'ok' | 'stale' | 'unavailable';

export interface SeverityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface AlertSummary {
  rule_name: string;
  timestamp: string | null;
  host: string | null;
  user: string | null;
}

export interface AlertsData {
  counts: SeverityCounts;
  /** Most recent alerts per severity, for the tile drill-down. */
  recent?: {
    critical: AlertSummary[];
    high: AlertSummary[];
    medium: AlertSummary[];
    low: AlertSummary[];
  };
  total_open: number;
  window: string;
}

export interface Discovery {
  id: string;
  title: string;
  summary: string;
  timestamp: string | null;
  alert_count: number;
  risk_score: number | null;
  mitre_tactics: string[];
  workflow_status: string | null;
}

export interface AttackDiscoveryData {
  total: number;
  discoveries: Discovery[];
  window: string;
}

export interface RiskEntity {
  name: string;
  /** Entity Store type: "Host", "User", "Service", ... (null on old data). */
  type: string | null;
  score: number;
  level: string | null;
}

export interface RiskData {
  entities: RiskEntity[];
}

export interface SourceState<T> {
  status: SourceStatus;
  updated_at: number | null;
  data: T | null;
  error: string | null;
}

export interface Snapshot {
  sources: {
    alerts?: SourceState<AlertsData>;
    attack_discovery?: SourceState<AttackDiscoveryData>;
    risk_scores?: SourceState<RiskData>;
  };
  meta: {
    space?: string;
    deployment_type?: string;
    version?: string;
    elastic_reachable?: boolean;
  };
  generated_at: number;
}
