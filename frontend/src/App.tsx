import { EuiProvider, useEuiTheme } from '@elastic/eui';
import { EuiThemeBorealis } from '@elastic/eui-theme-borealis';
import { css } from '@emotion/react';
import { useMemo, useState } from 'react';

import { StatusBar } from './components/StatusBar';
import { useEventStream } from './hooks/useEventStream';
import { LayoutTier, useLayoutTier } from './layout/useLayoutTier';
import { ColorMode, loadColorMode, saveColorMode } from './theme/colorMode';
import type { Snapshot } from './types';
import { AttackDiscoveryView } from './views/AttackDiscoveryView';
import { RiskView } from './views/RiskView';
import { SeverityView } from './views/SeverityView';

type ViewId = 'severity' | 'attack_discovery' | 'risk';

function availableViews(snapshot: Snapshot | null): ViewId[] {
  const views: ViewId[] = ['severity'];
  if (snapshot?.sources.attack_discovery?.status !== 'unavailable') {
    views.push('attack_discovery');
  }
  if (snapshot?.sources.risk_scores?.status !== 'unavailable') {
    views.push('risk');
  }
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
      <Display onToggleColorMode={toggleColorMode} />
    </EuiProvider>
  );
}

function Display({ onToggleColorMode }: { onToggleColorMode: () => void }) {
  const { euiTheme } = useEuiTheme();
  const { snapshot, connected } = useEventStream();
  const tier = useLayoutTier();
  const [viewIndex, setViewIndex] = useState(0);

  const views = useMemo(() => availableViews(snapshot), [snapshot]);

  // On small screens the whole display is a carousel; on medium screens the
  // severity tiles are pinned and only the secondary region cycles.
  const carousel: ViewId[] =
    tier === 'small' ? views : views.filter((v) => v !== 'severity');
  const currentView = carousel[viewIndex % Math.max(carousel.length, 1)] ?? 'severity';
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
        <Regions tier={tier} snapshot={snapshot} currentView={currentView} />
      </main>
      <StatusBar
        snapshot={snapshot}
        connected={connected}
        viewCount={cycles ? carousel.length : 0}
        viewIndex={viewIndex % Math.max(carousel.length, 1)}
      />
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
          background: transparent;
          border: none;
          cursor: none;
        `}
      />
    </div>
  );
}

function Regions({
  tier,
  snapshot,
  currentView,
}: {
  tier: LayoutTier;
  snapshot: Snapshot | null;
  currentView: ViewId;
}) {
  const alerts = snapshot?.sources.alerts ?? emptySource();
  const attackDiscovery = snapshot?.sources.attack_discovery ?? emptySource();
  const riskScores = snapshot?.sources.risk_scores ?? emptySource();

  const severity = <SeverityView alerts={alerts} compact={tier === 'small'} />;
  const secondary =
    currentView === 'risk' ? (
      <RiskView riskScores={riskScores} />
    ) : (
      <AttackDiscoveryView
        attackDiscovery={attackDiscovery}
        maxCards={tier === 'small' ? 2 : 3}
      />
    );

  if (tier === 'small') {
    return <Region grow>{currentView === 'severity' ? severity : secondary}</Region>;
  }
  if (tier === 'medium') {
    return (
      <>
        <Region grow>{severity}</Region>
        <Region grow>{secondary}</Region>
      </>
    );
  }
  return (
    <>
      <Region grow>{severity}</Region>
      <Region grow>
        <AttackDiscoveryView attackDiscovery={attackDiscovery} maxCards={3} />
      </Region>
      {riskScores.status !== 'unavailable' && (
        <Region grow>
          <RiskView riskScores={riskScores} />
        </Region>
      )}
    </>
  );
}

function Region({ children }: { children: React.ReactNode; grow?: boolean }) {
  return <div css={css`flex: 1; min-width: 0; min-height: 0;`}>{children}</div>;
}

function emptySource<T>() {
  return { status: 'pending' as const, updated_at: null, data: null as T | null, error: null };
}
