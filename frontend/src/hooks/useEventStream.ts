import { useEffect, useRef, useState } from 'react';

import type { Snapshot } from '../types';

// If neither a state event nor a heartbeat arrives for this long, treat the
// backend as gone (the backend heartbeats every 15s).
const STALE_AFTER_MS = 60_000;
const WATCHDOG_TICK_MS = 5_000;

export interface EventStream {
  snapshot: Snapshot | null;
  connected: boolean;
}

export function useEventStream(): EventStream {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const lastSeenRef = useRef<number>(Date.now());

  useEffect(() => {
    // Initial paint from the REST snapshot so the UI never waits on the stream.
    fetch('/api/state')
      .then((r) => (r.ok ? r.json() : null))
      .then((snap) => {
        if (snap) {
          setSnapshot(snap);
          lastSeenRef.current = Date.now();
        }
      })
      .catch(() => undefined);

    const source = new EventSource('/api/events');

    source.addEventListener('state', (event) => {
      lastSeenRef.current = Date.now();
      setConnected(true);
      try {
        setSnapshot(JSON.parse((event as MessageEvent).data));
      } catch {
        // malformed frame: keep last good snapshot
      }
    });

    source.addEventListener('heartbeat', () => {
      lastSeenRef.current = Date.now();
      setConnected(true);
    });

    // EventSource reconnects automatically; onerror just updates the pill.
    source.onerror = () => setConnected(false);

    const watchdog = window.setInterval(() => {
      if (Date.now() - lastSeenRef.current > STALE_AFTER_MS) {
        setConnected(false);
      }
    }, WATCHDOG_TICK_MS);

    return () => {
      source.close();
      window.clearInterval(watchdog);
    };
  }, []);

  return { snapshot, connected };
}
