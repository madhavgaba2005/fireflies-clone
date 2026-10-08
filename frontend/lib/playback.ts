// The playback clock is the single source of truth for "where are we in the recording".
//
// UI and transcript sync depend only on the PlaybackClock interface. Today the clock is
// simulated (there is no real audio — the PDF allows a placeholder). A real recording would
// add an `HtmlMediaClock` that wraps an <audio>/<video> element and implements the same
// interface; nothing else would change.

export interface PlaybackState {
  currentMs: number;
  durationMs: number;
  playing: boolean;
  rate: number;
}

export interface PlaybackClock {
  getSnapshot(): PlaybackState;
  subscribe(listener: () => void): () => void;
  play(): void;
  pause(): void;
  toggle(): void;
  seek(ms: number): void;
  setRate(rate: number): void;
  setDuration(ms: number): void;
  destroy(): void;
}

export const PLAYBACK_RATES = [0.75, 1, 1.25, 1.5, 2] as const;

export interface Scheduler {
  now(): number;
  request(callback: () => void): number;
  cancel(handle: number): void;
}

const browserScheduler: Scheduler = {
  now: () => performance.now(),
  request: (callback) => requestAnimationFrame(callback),
  cancel: (handle) => cancelAnimationFrame(handle),
};

/**
 * Advances time from a wall-clock anchor (not by adding frame deltas), so the position stays
 * exact even if frames are skipped or the tab is in the background.
 */
export class SimulatedClock implements PlaybackClock {
  private state: PlaybackState;
  private anchorMs = 0; // position when playback (re)started
  private anchorTime = 0; // scheduler time at that moment
  private frame: number | null = null;
  private listeners = new Set<() => void>();

  constructor(
    durationMs: number,
    private readonly scheduler: Scheduler = browserScheduler,
  ) {
    this.state = { currentMs: 0, durationMs: Math.max(0, durationMs), playing: false, rate: 1 };
  }

  getSnapshot = (): PlaybackState => this.state;

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  play = (): void => {
    if (this.state.playing || this.state.durationMs === 0) return;
    const restart = this.state.currentMs >= this.state.durationMs ? 0 : this.state.currentMs;
    this.reanchor(restart);
    this.set({ currentMs: restart, playing: true });
    this.loop();
  };

  pause = (): void => {
    if (!this.state.playing) return;
    this.set({ currentMs: this.position(), playing: false });
    this.stopLoop();
  };

  toggle = (): void => (this.state.playing ? this.pause() : this.play());

  seek = (ms: number): void => {
    const clamped = Math.min(Math.max(0, ms), this.state.durationMs);
    this.reanchor(clamped);
    this.set({ currentMs: clamped });
  };

  setRate = (rate: number): void => {
    this.reanchor(this.position());
    this.set({ rate });
  };

  setDuration = (ms: number): void => {
    const durationMs = Math.max(0, ms);
    if (durationMs === this.state.durationMs) return;
    this.set({ durationMs, currentMs: Math.min(this.state.currentMs, durationMs) });
  };

  /** Stops the frame loop. Subscribers are kept: React may re-mount (StrictMode) and resubscribe. */
  destroy = (): void => {
    this.stopLoop();
    if (this.state.playing) this.set({ playing: false });
  };

  private position(): number {
    if (!this.state.playing) return this.state.currentMs;
    const elapsed = (this.scheduler.now() - this.anchorTime) * this.state.rate;
    return Math.min(this.anchorMs + elapsed, this.state.durationMs);
  }

  private reanchor(ms: number): void {
    this.anchorMs = ms;
    this.anchorTime = this.scheduler.now();
  }

  private loop = (): void => {
    const currentMs = this.position();
    if (currentMs >= this.state.durationMs) {
      this.set({ currentMs: this.state.durationMs, playing: false });
      this.stopLoop();
      return;
    }
    this.set({ currentMs });
    this.frame = this.scheduler.request(this.loop);
  };

  private stopLoop(): void {
    if (this.frame !== null) this.scheduler.cancel(this.frame);
    this.frame = null;
  }

  private set(patch: Partial<PlaybackState>): void {
    // A new object on every change: useSyncExternalStore compares snapshots by identity.
    this.state = { ...this.state, ...patch };
    this.listeners.forEach((listener) => listener());
  }
}
