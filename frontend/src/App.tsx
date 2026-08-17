import { EuiIcon, EuiProvider, useEuiTheme } from '@elastic/eui';
import { EuiThemeBorealis } from '@elastic/eui-theme-borealis';
import { css } from '@emotion/react';
import { useEffect, useMemo, useState } from 'react';

import { StatusBar } from './components/StatusBar';
import { useEventStream } from './hooks/useEventStream';
import { LayoutTier, useLayoutTier } from './layout/useLayoutTier';
import { ColorMode, loadColorMode, saveColorMode } from './theme/colorMode';
import { DisplayMode, loadDisplayMode, saveDisplayMode } from './theme/displayMode';
import type { Snapshot } from './types';
import { ApmServicesView } from './views/ApmServicesView';
import { AttackDiscoveryView } from './views/AttackDiscoveryView';
import { HostsView } from './views/HostsView';
import { ObservabilityAlertsView } from './views/ObservabilityAlertsView';
import { RiskView } from './views/RiskView';
import { SeverityView } from './views/SeverityView';
import { SloView } from './views/SloView';

type ViewId =
  | 'severity'
  | 'attack_discovery'
  | 'risk'
  | 'obs_alerts'
  | 'slos'
  | 'hosts'
  | 'apm';

function sourceAvailable(snapshot: Snapshot | null, name: keyof Snapshot['sources']): boolean {
  return snapshot?.sources[name]?.status !== 'unavailable' && !!snapshot?.sources[name];
}

function availableViews(mode: DisplayMode, snapshot: Snapshot | null): ViewId[] {
  if (mode === 'security') {
    const views: ViewId[] = ['severity'];
    if (snapshot?.sources.attack_discovery?.status !== 'unavailable') {
      views.push('attack_discovery');
    }
    if (snapshot?.sources.risk_scores?.status !== 'unavailable') {
      views.push('risk');
    }
    return views;
  }
  const views: ViewId[] = [];
  if (sourceAvailable(snapshot, 'observability_alerts')) views.push('obs_alerts');
  if (sourceAvailable(snapshot, 'hosts')) views.push('hosts');
  if (sourceAvailable(snapshot, 'slos')) views.push('slos');
  if (sourceAvailable(snapshot, 'apm_services')) views.push('apm');
  return views;
}

export default function App() {
  const [colorMode, setColorMode] = useState<ColorMode>(loadColorMode);

  const toggleColorMode = () => {
    const next = colorMode === 'dark' ? 'light' : 'dark';
    setColorMode(next);
    saveColorMode(next);
  };

  return (
    <EuiProvider theme={EuiThemeBorealis} colorMode={colorMode}>
      <Display colorMode={colorMode} onToggleColorMode={toggleColorMode} />
    </EuiProvider>
  );
}

function Display({
  colorMode,
  onToggleColorMode,
}: {
  colorMode: ColorMode;
  onToggleColorMode: () => void;
}) {
  const { euiTheme } = useEuiTheme();
  const { snapshot, connected } = useEventStream();
  const tier = useLayoutTier();
  const [mode, setMode] = useState<DisplayMode>(loadDisplayMode);
  const [viewIndex, setViewIndex] = useState(0);

  const observabilityAvailable = useMemo(
    () => availableViews('observability', snapshot).length > 0,
    [snapshot],
  );
  // A stored observability preference on a deployment without observability
  // data falls back to security rather than an empty screen.
  const effectiveMode: DisplayMode =
    mode === 'observability' && !observabilityAvailable ? 'security' : mode;

  const toggleMode = () => {
    const next: DisplayMode = effectiveMode === 'security' ? 'observability' : 'security';
    setMode(next);
    saveDisplayMode(next);
  };

  useEffect(() => setViewIndex(0), [effectiveMode]);

  const views = useMemo(
    () => availableViews(effectiveMode, snapshot),
    [effectiveMode, snapshot],
  );

  // Small screens carousel every view; medium pins the primary view and only
  // cycles the rest; large shows everything side by side.
  const primary = views[0] ?? 'severity';
  const carousel: ViewId[] = tier === 'small' ? views : views.filter((v) => v !== primary);
  const currentView = carousel[viewIndex % Math.max(carousel.length, 1)] ?? primary;
  const cycles = tier !== 'large' && carousel.length > 1;

  const cycleView = () => {
    if (cycles) setViewIndex((i) => (i + 1) % carousel.length);
  };

  return (
    <div
      css={css`
        height: 100%;
        display: flex;
        flex-direction: column;
        background: ${euiTheme.colors.body};
      `}
    >
      <main
        onClick={cycleView}
        css={css`
          flex: 1;
          min-height: 0;
          padding: ${tier === 'small' ? euiTheme.size.s : euiTheme.size.m};
          display: flex;
          gap: ${euiTheme.size.m};
        `}
      >
        <Regions
          tier={tier}
          snapshot={snapshot}
          views={views}
          primary={primary}
          currentView={currentView}
        />
      </main>
      <StatusBar
        snapshot={snapshot}
        connected={connected}
        mode={effectiveMode}
        viewCount={cycles ? carousel.length : 0}
        viewIndex={viewIndex % Math.max(carousel.length, 1)}
      />
      {observabilityAvailable && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            toggleMode();
          }}
          aria-label="Switch between security and observability"
          css={css`
            position: fixed;
            top: 0;
            left: 0;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: flex-start;
            justify-content: flex-start;
            padding: ${euiTheme.size.s};
            background: transparent;
            border: none;
            cursor: none;
            opacity: 0.5;
          `}
        >
          <EuiIcon
            type={effectiveMode === 'security' ? 'logoObservability' : 'logoSecurity'}
            size="s"
          />
        </button>
      )}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggleColorMode();
        }}
        aria-label="Toggle light/dark mode"
        css={css`
          position: fixed;
          top: 0;
          right: 0;
          width: 48px;
          height: 48px;
          display: flex;
          align-items: flex-start;
          justify-content: flex-end;
          padding: ${euiTheme.size.s};
          background: transparent;
          border: none;
          cursor: none;
          /* Visible but unobtrusive on a wall display */
          opacity: 0.5;
        `}
      >
        <EuiIcon
          type={colorMode === 'dark' ? 'sun' : 'moon'}
          size="s"
          color="subdued"
        />
      </button>
    </div>
  );
}

function SingleView({ view, snapshot }: { view: ViewId; snapshot: Snapshot | null }) {
  const alerts = snapshot?.sources.alerts ?? emptySource();
  switch (view) {
    case 'severity':
      return <SeverityView alerts={alerts} compact />;
    case 'attack_discovery':
      return (
        <AttackDiscoveryView
          attackDiscovery={snapshot?.sources.attack_discovery ?? emptySource()}
          maxCards={2}
        />
      );
    case 'risk':
      return <RiskView riskScores={snapshot?.sources.risk_scores ?? emptySource()} />;
    case 'obs_alerts':
      return (
        <ObservabilityAlertsView
          obsAlerts={snapshot?.sources.observability_alerts ?? emptySource()}
        />
      );
    case 'slos':
      return <SloView slos={snapshot?.sources.slos ?? emptySource()} />;
    case 'hosts':
      return <HostsView hosts={snapshot?.sources.hosts ?? emptySource()} />;
    case 'apm':
      return <ApmServicesView apm={snapshot?.sources.apm_services ?? emptySource()} />;
  }
}

function Regions({
  tier,
  snapshot,
  views,
  primary,
  currentView,
}: {
  tier: LayoutTier;
  snapshot: Snapshot | null;
  views: ViewId[];
  primary: ViewId;
  currentView: ViewId;
}) {
  if (tier === 'small') {
    return (
      <Region>
        <SingleView view={currentView} snapshot={snapshot} />
      </Region>
    );
  }
  if (tier === 'medium') {
    // The cycling region disappears entirely when the primary view is the
    // only one available, letting it take the full width.
    return (
      <>
        <Region>
          <WideView view={primary} snapshot={snapshot} />
        </Region>
        {currentView !== primary && (
          <Region>
            <SingleView view={currentView} snapshot={snapshot} />
          </Region>
        )}
      </>
    );
  }
  return (
    <>
      {views.map((view) => (
        <Region key={view}>
          <WideView view={view} snapshot={snapshot} />
        </Region>
      ))}
    </>
  );
}

/** Same as SingleView but with roomier variants where a view supports them. */
function WideView({ view, snapshot }: { view: ViewId; snapshot: Snapshot | null }) {
  if (view === 'severity') {
    return <SeverityView alerts={snapshot?.sources.alerts ?? emptySource()} compact={false} />;
  }
  if (view === 'attack_discovery') {
    return (
      <AttackDiscoveryView
        attackDiscovery={snapshot?.sources.attack_discovery ?? emptySource()}
        maxCards={3}
      />
    );
  }
  return <SingleView view={view} snapshot={snapshot} />;
}

function Region({ children }: { children: React.ReactNode }) {
  return <div css={css`flex: 1; min-width: 0; min-height: 0;`}>{children}</div>;
}

function emptySource<T>() {
  return { status: 'pending' as const, updated_at: null, data: null as T | null, error: null };
}
