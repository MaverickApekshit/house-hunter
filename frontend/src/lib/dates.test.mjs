// Dependency-free unit test (Node built-in runner):
//   node --test src/lib/dates.test.mjs
// Guards the Safari-safe date normalization used by the "Newly Listed" sort.
import { test } from "node:test";
import assert from "node:assert/strict";
import { listingTime } from "./dates.mjs";

test("SQLite space form is normalized to ISO (Safari would NaN the raw form)", () => {
  const t = listingTime("2026-07-08 18:52:57");
  // Equals the ISO parse -> proves it does not depend on lenient engine parsing.
  assert.equal(t, new Date("2026-07-08T18:52:57").getTime());
  assert.ok(!Number.isNaN(t));
});

test("ISO / offset (cloud) form passes through unchanged", () => {
  assert.equal(
    listingTime("2026-07-08T18:52:57+00:00"),
    new Date("2026-07-08T18:52:57+00:00").getTime(),
  );
});

test("ordering is preserved: newer > older", () => {
  assert.ok(listingTime("2026-07-08 18:52:57") > listingTime("2026-05-15 13:52:39"));
});

test("missing / unparseable input returns 0 (no NaN in the comparator)", () => {
  assert.equal(listingTime(""), 0);
  assert.equal(listingTime(null), 0);
  assert.equal(listingTime(undefined), 0);
  assert.equal(listingTime("not-a-date"), 0);
});
