import type { LibraryCoverage } from './types';

// Plain-language facts for the coverage note: the densest 200L stretch of the
// shelf, and the thin bands that hold at least one reader.
export function coverageSummary(cov: LibraryCoverage) {
  const bands = cov.bands;
  let best = 0;
  for (let i = 1; i < bands.length - 1; i++) {
    if (bands[i].titles + bands[i + 1].titles > bands[best].titles + bands[best + 1].titles) best = i;
  }
  const dense = bands.length > 1 ? { low: bands[best].low, high: bands[best + 1].high, titles: bands[best].titles + bands[best + 1].titles } : null;
  const thinWithReaders = bands.filter(b => b.thin && b.readers > 0);
  return { dense, thinWithReaders };
}
