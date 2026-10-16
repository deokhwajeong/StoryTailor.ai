import type { LibraryCoverage } from './types';

// "Class library coverage": real titles per 100L band from the classroom
// catalog (computed by the server, or the demo mock, from books.json), with
// each student's current level as a dot underneath. Hand-drawn SVG, no library.

interface Reader {
  id: string;
  name: string;
  level: number;
  isDemoReader: boolean;
}

const DOT_BIN = 20;

export default function CoverageChart({ coverage, readers }: { coverage: LibraryCoverage; readers: Reader[] }) {
  const { bands, band_width: width, thin_threshold: thin } = coverage;
  const first = bands[0].low;
  const span = bands[bands.length - 1].low + width - first;
  const W = 720, left = 8, right = 56, top = 22, plotH = 120;
  const plotW = W - left - right;
  const axisY = top + plotH;
  const maxTitles = Math.max(thin, ...bands.map(b => b.titles));
  const xOf = (level: number) => left + ((level - first) / span) * plotW;
  const yOf = (n: number) => top + plotH * (1 - n / maxTitles);

  // Stack reader dots in 20L bins so nobody hides behind a neighbor.
  const stacks = new Map<number, number>();
  const dots = [...readers].sort((a, b) => a.level - b.level).map(r => {
    const bin = Math.floor(r.level / DOT_BIN);
    const row = stacks.get(bin) ?? 0;
    stacks.set(bin, row + 1);
    const band = bands.find(b => r.level >= b.low && r.level <= b.high);
    return { ...r, row, cx: xOf((bin + 0.5) * DOT_BIN), inThin: band?.thin ?? true };
  });
  const rows = Math.max(1, ...[...stacks.values()]);
  const stripTop = axisY + 30;
  const H = stripTop + rows * 10 + 10;

  return (
    <figure>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-labelledby="coverage-title">
        <title id="coverage-title">
          {`Library titles per ${width}L band: ${bands.map(b => `${b.low} to ${b.high}L, ${b.titles} titles, ${b.readers} readers`).join('; ')}.`}
        </title>
        {bands.map(b => {
          const x0 = xOf(b.low) + 1;
          const w = xOf(b.low + width) - xOf(b.low) - 2;
          return (
            <g key={b.low}>
              <title>{`${b.low} to ${b.high}L: ${b.titles} ${b.titles === 1 ? 'title' : 'titles'} on the shelf, ${b.readers} ${b.readers === 1 ? 'reader' : 'readers'}${b.thin ? ` (fewer than ${thin})` : ''}`}</title>
              {b.thin && <rect x={x0 - 1} y={top - 14} width={w + 2} height={plotH + 14} fill="var(--color-clay-soft)" opacity="0.6" rx="4" />}
              {b.titles > 0 && (
                <path
                  d={`M${x0},${axisY} V${yOf(b.titles) + 4} q0,-4 4,-4 h${w - 8} q4,0 4,4 V${axisY} Z`}
                  fill={b.thin ? 'var(--color-clay)' : 'var(--color-accent)'}
                  opacity={b.thin ? 0.9 : 0.78}
                />
              )}
              <text x={x0 + w / 2} y={yOf(b.titles) - 5} textAnchor="middle" fontSize="11" fontWeight="700" fill="var(--color-ink-soft)">{b.titles}</text>
              <text x={x0 + w / 2} y={axisY + 15} textAnchor="middle" fontSize="10.5" fill="var(--color-ink-muted)">{b.low}</text>
            </g>
          );
        })}
        <line x1={left} x2={left + plotW} y1={axisY} y2={axisY} stroke="var(--color-ink-muted)" strokeWidth="1" />
        <line x1={left} x2={left + plotW} y1={yOf(thin)} y2={yOf(thin)} stroke="var(--color-clay)" strokeWidth="1" strokeDasharray="4 3" />
        <text x={left + plotW + 6} y={yOf(thin) + 4} fontSize="10.5" fill="var(--color-clay)">{thin} titles</text>
        <text x={left + plotW + 6} y={axisY + 15} fontSize="10.5" fill="var(--color-ink-muted)">Lexile</text>
        <text x={left + plotW + 6} y={stripTop + 4} fontSize="10.5" fill="var(--color-ink-muted)">readers</text>
        {dots.map(d => (
          <circle
            key={d.id}
            cx={d.cx}
            cy={stripTop + d.row * 10}
            r="4"
            fill={d.inThin ? 'var(--color-clay)' : 'var(--color-ink-soft)'}
            stroke={d.isDemoReader ? 'var(--color-accent)' : 'var(--color-sheet)'}
            strokeWidth={d.isDemoReader ? 2.5 : 1.5}
          >
            <title>{`${d.name}: ${d.level}L${d.isDemoReader ? ' (demo reader)' : ''}`}</title>
          </circle>
        ))}
      </svg>
      <figcaption className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5"><span className="inline-block h-2.5 w-2.5 rounded-sm bg-accent opacity-80" aria-hidden="true" />Titles on the shelf per {width}L band</span>
        <span className="flex items-center gap-1.5"><span className="inline-block h-2.5 w-2.5 rounded-sm bg-clay" aria-hidden="true" />Fewer than {thin} titles</span>
        <span className="flex items-center gap-1.5"><span className="inline-block h-2.5 w-2.5 rounded-full bg-ink-soft" aria-hidden="true" />One student&apos;s current level</span>
      </figcaption>
      <table className="sr-only">
        <caption>Library titles and readers per {width}L band</caption>
        <thead><tr><th scope="col">Band</th><th scope="col">Titles</th><th scope="col">Readers</th></tr></thead>
        <tbody>
          {bands.map(b => <tr key={b.low}><th scope="row">{b.low} to {b.high}L</th><td>{b.titles}</td><td>{b.readers}</td></tr>)}
        </tbody>
      </table>
    </figure>
  );
}
