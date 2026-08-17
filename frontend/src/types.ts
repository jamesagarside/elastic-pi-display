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

export interface ObsAlert {
  rule_name: string;
  category: string | null;
  reason: string;
  started: string | null;
}

export interface ObsAlertsData {
  active: number;
  recent: ObsAlert[];
}

export interface Slo {
  name: string | null;
  status: string | null;
  sli: number | null;
  target: number | null;
  budget_remaining: number | null;
}

export interface SloData {
  total: number;
  slos: Slo[];
}

export interface HostMetrics {
  name: string;
  cpu_pct: number | null;
  memory_pct: number | null;
}

export interface HostsData {
  hosts: HostMetrics[];
  window: string;
}

export interface ApmService {
  name: string;
  transactions: number;
  error_rate_pct: number;
  latency_ms: number | null;
}

export interface ApmData {
  services: ApmService[];
  window: string;
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
    observability_alerts?: SourceState<ObsAlertsData>;
    slos?: SourceState<SloData>;
    hosts?: SourceState<HostsData>;
    apm_services?: SourceState<ApmData>;
  };
  meta: {
    space?: string;
    deployment_type?: string;
    version?: string;
    elastic_reachable?: boolean;
  };
  generated_at: number;
}
