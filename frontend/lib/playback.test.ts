import { beforeEach, describe, expect, it } from "vitest";

import { type Scheduler, SimulatedClock } from "./playback";

/** A controllable scheduler: time only moves when the test says so. */
class FakeScheduler implements Scheduler {
  time = 0;
  private callbacks = new Map<number, () => void>();
  private nextHandle = 1;

  now = () => this.time;
  request = (callback: () => void) => {
    const handle = this.nextHandle++;
    this.callbacks.set(handle, callback);
    return handle;
  };
  cancel = (handle: number) => {
    this.callbacks.delete(handle);
  };
  /** Advance time and run one animation frame. */
  advance(ms: number) {
    this.time += ms;
    const pending = [...this.callbacks.values()];
    this.callbacks.clear();
    pending.forEach((callback) => callback());
  }
  get scheduled() {
    return this.callbacks.size;
  }
}

describe("SimulatedClock", () => {
  let scheduler: FakeScheduler;
  let clock: SimulatedClock;

  beforeEach(() => {
    scheduler = new FakeScheduler();
    clock = new SimulatedClock(10_000, scheduler);
  });

  it("starts paused at zero", () => {
    expect(clock.getSnapshot()).toEqual({
      currentMs: 0,
      durationMs: 10_000,
      playing: false,
      rate: 1,
    });
  });

  it("advances with real elapsed time while playing", () => {
    clock.play();
    scheduler.advance(1500);
    expect(clock.getSnapshot().currentMs).toBe(1500);
    scheduler.advance(500);
    expect(clock.getSnapshot()).toMatchObject({ currentMs: 2000, playing: true });
  });

  it("pause freezes the position and stops scheduling frames", () => {
    clock.play();
    scheduler.advance(1000);
    clock.pause();
    scheduler.time += 5000;
    expect(clock.getSnapshot()).toMatchObject({ currentMs: 1000, playing: false });
    expect(scheduler.scheduled).toBe(0);
  });

  it("seek moves the position while paused and while playing", () => {
    clock.seek(4000);
    expect(clock.getSnapshot().currentMs).toBe(4000);
    clock.play();
    scheduler.advance(100);
    clock.seek(8000);
    scheduler.advance(250);
    expect(clock.getSnapshot().currentMs).toBe(8250);
  });

  it("clamps seeks to the recording", () => {
    clock.seek(-50);
    expect(clock.getSnapshot().currentMs).toBe(0);
    clock.seek(99_999);
    expect(clock.getSnapshot().currentMs).toBe(10_000);
  });

  it("playback rate scales elapsed time", () => {
    clock.setRate(2);
    clock.play();
    scheduler.advance(1000);
    expect(clock.getSnapshot()).toMatchObject({ currentMs: 2000, rate: 2 });
  });

  it("changing rate mid-play keeps the current position", () => {
    clock.play();
    scheduler.advance(1000);
    clock.setRate(1.5);
    scheduler.advance(1000);
    expect(clock.getSnapshot().currentMs).toBe(2500);
  });

  it("stops at the end, and play restarts from the beginning", () => {
    clock.play();
    scheduler.advance(12_000);
    expect(clock.getSnapshot()).toMatchObject({ currentMs: 10_000, playing: false });
    clock.play();
    expect(clock.getSnapshot()).toMatchObject({ currentMs: 0, playing: true });
  });

  it("toggle switches between play and pause", () => {
    clock.toggle();
    expect(clock.getSnapshot().playing).toBe(true);
    clock.toggle();
    expect(clock.getSnapshot().playing).toBe(false);
  });

  it("cannot play an empty recording", () => {
    const empty = new SimulatedClock(0, scheduler);
    empty.play();
    expect(empty.getSnapshot().playing).toBe(false);
  });

  it("notifies subscribers with a new snapshot object on every change", () => {
    const seen: unknown[] = [];
    const unsubscribe = clock.subscribe(() => seen.push(clock.getSnapshot()));
    const before = clock.getSnapshot();
    clock.seek(100);
    expect(seen).toHaveLength(1);
    expect(clock.getSnapshot()).not.toBe(before);
    unsubscribe();
    clock.seek(200);
    expect(seen).toHaveLength(1);
  });

  it("setDuration clamps the position and ignores no-op updates", () => {
    clock.seek(9000);
    clock.setDuration(5000);
    expect(clock.getSnapshot()).toMatchObject({ currentMs: 5000, durationMs: 5000 });
    const snapshot = clock.getSnapshot();
    clock.setDuration(5000);
    expect(clock.getSnapshot()).toBe(snapshot);
  });

  it("destroy cancels the frame loop and pauses", () => {
    clock.play();
    clock.destroy();
    expect(scheduler.scheduled).toBe(0);
    expect(clock.getSnapshot().playing).toBe(false);
  });
});
