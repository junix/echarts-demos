import { execFileSync } from 'node:child_process';
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

// Regression test: the calendar and theme-river series must cover the same
// civil dates in every browser timezone. Each probe re-runs the exact date
// generation from src/main.ts inside a child Node process with a pinned TZ,
// the same way a fleet browser inherits its zone from the environment.
const modulePath = fileURLToPath(new URL('../src/dates.ts', import.meta.url));
const probe = `
  import { civilDate } from ${JSON.stringify(modulePath)};
  const calendar = Array.from({length: 365}, (_, i) => civilDate(2026, 0, i + 1));
  const river = Array.from({length: 72}, (_, i) => civilDate(1960 + i, 0, 1));
  console.log(JSON.stringify({
    zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    calendar: { first: calendar[0], last: calendar.at(-1), unique: new Set(calendar).size },
    river: { first: river[0], last: river.at(-1), unique: new Set(river).size },
  }));
`;

for (const zone of ['America/Los_Angeles', 'UTC', 'Asia/Shanghai']) {
  test(`synthetic date bounds are stable in ${zone}`, () => {
    const output = JSON.parse(execFileSync(process.execPath, ['--input-type=module', '-e', probe], {
      env: { ...process.env, TZ: zone },
      encoding: 'utf8',
    }));
    assert.equal(output.zone, zone);
    assert.deepEqual(output.calendar, { first: '2026-01-01', last: '2026-12-31', unique: 365 });
    assert.deepEqual(output.river, { first: '1960-01-01', last: '2031-01-01', unique: 72 });
  });
}
