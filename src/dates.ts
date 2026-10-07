// Civil-date strings for the synthetic time series. Local Date constructors
// combined with toISOString shift the UTC date by the timezone offset (a
// +08:00 browser renders 2026-01-01 as 2025-12-31), so both series build
// their dates from Date.UTC to keep calendar bounds identical everywhere.
export const civilDate = (year: number, month: number, day: number): string =>
  new Date(Date.UTC(year, month, day)).toISOString().slice(0, 10);
