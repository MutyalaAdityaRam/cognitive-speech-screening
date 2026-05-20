export function pollReportHistory({ endpoint, userId, onData, onError, intervalMs = 3000 }) {
  let stopped = false;

  async function tick() {
    if (stopped) return;
    try {
      const response = await fetch(`${endpoint}?route=reports&user_id=${encodeURIComponent(userId)}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      onData(await response.json());
    } catch (error) {
      if (onError) onError(error);
    } finally {
      if (!stopped) window.setTimeout(tick, intervalMs);
    }
  }

  tick();
  return () => {
    stopped = true;
  };
}

