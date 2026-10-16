import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { teacherApi } from './api';
import { IS_DEMO } from './demo/constants';
import CoverageChart from './CoverageChart';
import { coverageSummary } from './coverage';
import { displayNames } from './pseudonym';
import type { AttentionItem, AttentionReason, Difficulty, RosterStudent, TeacherSummary } from './types';

// Plain-language labels and a next step for each reason in storytailor/insights.py,
// in the same order (most urgent first).
const REASON_TEXT: Record<AttentionReason, { label: string; action: string }> = {
  flagged_story: { label: 'A story was flagged', action: 'Review the flagged story together.' },
  struggling: { label: 'Finding stories too hard', action: 'Check in. The target level is already stepping down.' },
  below_grade_level: { label: 'Well below the grade starting level', action: 'Consider small-group or read-aloud support.' },
  inactive: { label: 'No reading in 14+ days', action: 'Encourage a short session this week.' },
  ready_for_more: { label: 'Says stories are too easy', action: 'Offer a stretch book from the library.' },
};
const REASON_ORDER = Object.keys(REASON_TEXT) as AttentionReason[];

const VOTE_STYLE: Record<Difficulty, { label: string; pill: string; bar: string }> = {
  too_hard: { label: 'Too hard', pill: 'bg-clay-soft text-clay', bar: 'bg-clay' },
  just_right: { label: 'Just right', pill: 'bg-accent-soft text-accent-strong', bar: 'bg-accent' },
  too_easy: { label: 'Too easy', pill: 'bg-slate-soft text-slate', bar: 'bg-slate' },
};
const VOTE_ORDER: Difficulty[] = ['too_hard', 'just_right', 'too_easy'];

const GRADE_START: Record<number, number> = { 0: 150, 1: 300, 2: 450, 3: 600, 4: 740, 5: 840, 6: 920, 7: 980, 8: 1030 };
const BUCKET = 50;

interface Props {
  token: string;
  classroomId: string;
  onCredentials: (token: string, classroomId: string) => void;
  readerId?: string;
}

function lastActive(iso: string | null): string {
  if (!iso) return 'never';
  const days = Math.floor((Date.now() - Date.parse(iso)) / 86_400_000);
  if (days <= 0) return 'today';
  return days === 1 ? 'yesterday' : `${days} days ago`;
}

function levelBuckets(levels: number[]) {
  const lo = Math.floor(Math.min(...levels) / BUCKET) * BUCKET;
  const hi = Math.floor(Math.max(...levels) / BUCKET) * BUCKET;
  const buckets: { from: number; count: number }[] = [];
  for (let from = lo; from <= hi; from += BUCKET) {
    buckets.push({ from, count: levels.filter(l => l >= from && l < from + BUCKET).length });
  }
  return buckets;
}

function VotePills({ votes }: { votes: Difficulty[] }) {
  if (votes.length === 0) return <span className="text-xs text-ink-muted">No recent votes</span>;
  return (
    <ul className="flex flex-wrap gap-1" aria-label="Recent votes, newest first">
      {votes.map((v, i) => (
        <li key={i} className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${VOTE_STYLE[v].pill}`}>{VOTE_STYLE[v].label}</li>
      ))}
    </ul>
  );
}

// Students per 50L band, as a hand-drawn SVG histogram (no chart library).
function LevelChart({ levels, gradeStart, readerLevel }: { levels: number[]; gradeStart?: number; readerLevel?: number }) {
  const buckets = levelBuckets(levels);
  const max = Math.max(1, ...buckets.map(b => b.count));
  const W = 360, H = 170, left = 8, right = 8, top = 18, bottom = 34;
  const slot = (W - left - right) / buckets.length;
  const barW = Math.max(4, slot - 2);
  const y = (c: number) => top + (H - top - bottom) * (1 - c / max);
  const xOf = (level: number) => left + ((level - buckets[0].from) / BUCKET) * slot;
  const labelEvery = buckets.length > 8 ? 2 : 1;
  return (
    <figure>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-labelledby="level-chart-title">
        <title id="level-chart-title">
          {`Students per 50L band: ${buckets.filter(b => b.count).map(b => `${b.from} to ${b.from + BUCKET - 1}L, ${b.count}`).join('; ')}.`}
        </title>
        <line x1={left} x2={W - right} y1={H - bottom} y2={H - bottom} stroke="var(--color-rule)" strokeWidth="1" />
        {buckets.map((b, i) => {
          const x = left + i * slot + 1;
          const hasReader = readerLevel !== undefined && readerLevel >= b.from && readerLevel < b.from + BUCKET;
          return (
            <g key={b.from}>
              <title>{`${b.from} to ${b.from + BUCKET - 1}L: ${b.count} ${b.count === 1 ? 'student' : 'students'}${hasReader ? ', including the demo reader' : ''}`}</title>
              {/* Full-height hit area so the tooltip is easy to reach. */}
              <rect x={x - 1} y={top} width={slot} height={H - top - bottom} fill="transparent" />
              {b.count > 0 && (
                <path
                  d={`M${x},${H - bottom} V${y(b.count) + 4} q0,-4 4,-4 h${barW - 8} q4,0 4,4 V${H - bottom} Z`}
                  fill={hasReader ? 'var(--color-accent-strong)' : 'var(--color-accent)'}
                  opacity={hasReader ? 1 : 0.78}
                />
              )}
              {b.count > 0 && (
                <text x={x + barW / 2} y={y(b.count) - 4} textAnchor="middle" fontSize="10" fill="var(--color-ink-soft)">{b.count}</text>
              )}
              {i % labelEvery === 0 && (
                <text x={x + barW / 2} y={H - bottom + 13} textAnchor="middle" fontSize="9.5" fill="var(--color-ink-muted)">{b.from}</text>
              )}
            </g>
          );
        })}
        {gradeStart !== undefined && gradeStart >= buckets[0].from && gradeStart <= buckets[buckets.length - 1].from + BUCKET && (
          <g>
            <line x1={xOf(gradeStart)} x2={xOf(gradeStart)} y1={top - 6} y2={H - bottom} stroke="var(--color-ink-soft)" strokeWidth="1.5" strokeDasharray="3 3" />
            <text x={xOf(gradeStart)} y={H - 6} textAnchor="middle" fontSize="10" fontWeight="700" fill="var(--color-ink-soft)">grade start {gradeStart}L</text>
          </g>
        )}
      </svg>
    </figure>
  );
}

export default function TeacherView({ token, classroomId, onCredentials, readerId }: Props) {
  const [roster, setRoster] = useState<RosterStudent[] | null>(null);
  const [summary, setSummary] = useState<(TeacherSummary & { classroom?: string }) | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [draftToken, setDraftToken] = useState(token);
  const [draftClass, setDraftClass] = useState(classroomId);

  const load = useCallback(async (t: string, c: string) => {
    setLoading(true);
    setError('');
    try {
      const [r, s] = await Promise.all([
        teacherApi<RosterStudent[]>(`/api/classrooms/${c}/students`, t),
        teacherApi<TeacherSummary>(`/api/classrooms/${c}/feedback-summary`, t),
      ]);
      setRoster(r);
      setSummary(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load the class.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Reload whenever the view opens with credentials, so the demo reflects the
  // votes the reader just gave in the student tab.
  useEffect(() => {
    if (token && classroomId) void load(token, classroomId);
  }, [token, classroomId, load]);

  const names = useMemo(() => displayNames(roster?.map(s => s.id) ?? []), [roster]);
  const nameOf = (id: string) => names.get(id) ?? id;

  const submit = (e: FormEvent) => {
    e.preventDefault();
    onCredentials(draftToken.trim(), draftClass.trim());
  };

  const totalVotes = summary ? Object.values(summary.difficulty).reduce((a, b) => a + b, 0) : 0;
  const pct = (n: number) => (totalVotes ? Math.round((n / totalVotes) * 100) : 0);
  const grade = roster?.[0]?.grade;
  const gradeStart = grade === undefined ? undefined : GRADE_START[grade];
  const readerLevel = roster?.find(s => s.id === readerId)?.target_level;
  const groups = summary
    ? REASON_ORDER.map(r => ({ reason: r, items: summary.needs_attention.filter(i => i.reasons.includes(r)) })).filter(g => g.items.length > 0)
    : [];

  const studentName = (id: string) => (
    <span className="font-bold text-ink" title={`Pseudonymous id: ${id}`}>
      {nameOf(id)}
      {id === readerId && <span className="ml-1.5 rounded bg-accent-soft px-1.5 py-0.5 text-[11px] font-bold text-accent-strong">demo reader</span>}
    </span>
  );

  const card = 'rounded-lg border border-rule bg-sheet';

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-serif text-2xl text-ink sm:text-3xl">{summary?.classroom ?? 'Class overview'}</h1>
        <p className="mt-1 max-w-3xl text-ink-soft">
          Who may need a check-in and why, how stories are landing, and where the class reads.
          Students appear under generated display names; the real pseudonymous id is in each name&apos;s tooltip and in the roster. No real names, no scores.
          {IS_DEMO && ' Fictional students; the demo reader from the Student tab updates live.'}
        </p>
      </div>

      {!IS_DEMO && (
        <form className={`${card} flex flex-wrap items-end gap-3 p-4`} onSubmit={submit}>
          <div className="flex flex-col gap-1">
            <label htmlFor="teacher-token" className="text-sm font-bold text-ink-soft">Teacher token</label>
            <input id="teacher-token" type="password" autoComplete="off" value={draftToken}
                   onChange={e => setDraftToken(e.target.value)}
                   className="rounded-md border border-rule bg-sheet px-3 py-2" />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="classroom-id" className="text-sm font-bold text-ink-soft">Classroom ID</label>
            <input id="classroom-id" inputMode="numeric" value={draftClass}
                   onChange={e => setDraftClass(e.target.value)}
                   className="w-28 rounded-md border border-rule bg-sheet px-3 py-2" />
          </div>
          <button type="submit" disabled={!draftToken.trim() || !draftClass.trim()}
                  className="rounded-md bg-accent px-4 py-2 font-bold text-white hover:bg-accent-strong disabled:opacity-50">
            Load class
          </button>
        </form>
      )}

      <p className="sr-only" role="status" aria-live="polite">{loading ? 'Loading class.' : ''}</p>
      {error && <p role="alert" className="rounded-md border border-clay/30 bg-clay-soft px-4 py-3 text-clay">{error}</p>}

      {summary && roster && (
        <>
          <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              ['Students', String(roster.length)],
              ['Average level', summary.levels.avg_target === null ? 'n/a' : `${Math.round(summary.levels.avg_target)}L`],
              ['Level range', summary.levels.min_target === null ? 'n/a' : `${summary.levels.min_target} to ${summary.levels.max_target}L`],
              ['May need a check-in', String(summary.needs_attention.length)],
            ].map(([label, value]) => (
              <div key={label} className={`${card} px-4 py-3`}>
                <dt className="text-xs text-ink-muted">{label}</dt>
                <dd className="mt-0.5 text-xl font-bold tabular-nums text-ink">{value}</dd>
              </div>
            ))}
          </dl>

          <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_24rem]">
            <section aria-labelledby="attention-heading" className="flex flex-col gap-3">
              <div>
                <h2 id="attention-heading" className="text-lg font-bold text-ink">Who may need a check-in</h2>
                <p className="text-sm text-ink-muted">Grouped by reason. Simple stated rules, meant to start a conversation, not to grade a child.</p>
              </div>
              {groups.length === 0 ? (
                <p className={`${card} px-4 py-3 text-ink-soft`}>Nobody right now.</p>
              ) : groups.map(({ reason, items }) => (
                <div key={reason} className={card}>
                  <div className="flex items-baseline justify-between gap-3 border-b border-rule px-4 py-3">
                    <div>
                      <h3 className="font-bold text-ink">{REASON_TEXT[reason].label}</h3>
                      <p className="text-sm text-ink-muted">{REASON_TEXT[reason].action}</p>
                    </div>
                    <span className="shrink-0 rounded-full bg-paper px-2.5 py-0.5 text-sm font-bold tabular-nums text-ink-soft" aria-label={`${items.length} students`}>
                      {items.length}
                    </span>
                  </div>
                  <ul>
                    {items.map((item: AttentionItem) => (
                      <li key={item.student_id} className={`flex flex-wrap items-center justify-between gap-x-4 gap-y-1.5 border-b border-rule px-4 py-2.5 last:border-0 ${item.student_id === readerId ? 'bg-accent-soft/50' : ''}`}>
                        <span className="flex items-baseline gap-3">
                          {studentName(item.student_id)}
                          <span className="text-sm tabular-nums text-ink-muted">{item.target_level}L</span>
                          {item.reasons.length > 1 && (
                            <span className="text-xs text-ink-muted">
                              also: {item.reasons.filter(r => r !== reason).map(r => REASON_TEXT[r].label.toLowerCase()).join('; ')}
                            </span>
                          )}
                        </span>
                        <VotePills votes={item.recent_votes} />
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </section>

            <div className="flex flex-col gap-6">
              <section aria-labelledby="spread-heading" className={`${card} px-4 py-4`}>
                <h2 id="spread-heading" className="font-bold text-ink">Reading levels in the class</h2>
                <p className="mb-2 text-sm text-ink-muted">Students per 50L band{readerLevel !== undefined && '; the darker bar holds the demo reader'}.</p>
                <LevelChart levels={roster.map(s => s.target_level)} gradeStart={gradeStart} readerLevel={readerLevel} />
              </section>

              <section aria-labelledby="fit-heading" className={`${card} px-4 py-4`}>
                <h2 id="fit-heading" className="font-bold text-ink">How stories are landing</h2>
                <p className="text-sm text-ink-muted">Recent one-tap votes, {totalVotes} in total.</p>
                <div className="mt-3 flex h-3 gap-0.5 overflow-hidden rounded-full" aria-hidden="true">
                  {VOTE_ORDER.map(d => (
                    <div key={d} className={VOTE_STYLE[d].bar} style={{ width: `${pct(summary.difficulty[d])}%` }} />
                  ))}
                </div>
                <ul className="mt-3 flex flex-col gap-1 text-sm text-ink-soft">
                  {VOTE_ORDER.map(d => (
                    <li key={d} className="flex items-center gap-2">
                      <span className={`inline-block h-2.5 w-2.5 rounded-sm ${VOTE_STYLE[d].bar}`} aria-hidden="true" />
                      {VOTE_STYLE[d].label}
                      <span className="ml-auto tabular-nums">{summary.difficulty[d]} ({pct(summary.difficulty[d])}%)</span>
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          </div>

          {(() => {
            const cov = summary.library_coverage;
            const { dense, thinWithReaders } = coverageSummary(cov);
            const n = cov.readers_in_thin_bands;
            return (
              <section aria-labelledby="coverage-heading" id="library-coverage" className={`${card} px-4 py-4 sm:px-6`}>
                <h2 id="coverage-heading" className="font-bold text-ink">Class library coverage</h2>
                <p className="mt-1 max-w-3xl text-sm text-ink-soft">
                  {cov.total_titles} cataloged titles.
                  {dense && ` ${dense.titles} of them (${Math.round((dense.titles / cov.total_titles) * 100)}%) sit in ${dense.low} to ${dense.high}L.`}
                  {' '}A band with fewer than {cov.thin_threshold} titles is marked thin; generated stories fill the gap there.
                </p>
                <p className="mt-2 text-sm font-bold text-clay">
                  {n === 0
                    ? `No readers are in bands with fewer than ${cov.thin_threshold} books on the shelf right now.`
                    : `${n} ${n === 1 ? 'reader is' : 'readers are'} in bands with fewer than ${cov.thin_threshold} books on the shelf: `
                      + thinWithReaders.map(b => `${b.low} to ${b.high}L (${b.titles} ${b.titles === 1 ? 'title' : 'titles'}, ${b.readers} ${b.readers === 1 ? 'reader' : 'readers'})`).join('; ') + '.'}
                </p>
                <div className="mt-3">
                  <CoverageChart
                    coverage={cov}
                    readers={roster.map(s => ({ id: s.id, name: nameOf(s.id), level: s.target_level, isDemoReader: s.id === readerId }))}
                  />
                </div>
              </section>
            );
          })()}

          <section aria-labelledby="roster-heading">
            <h2 id="roster-heading" className="text-lg font-bold text-ink">Roster</h2>
            <p className="text-sm text-ink-muted">Display names are generated from each pseudonymous id. The teacher keeps the real name list offline.</p>
            <div className={`${card} mt-2 max-h-96 overflow-auto`} tabIndex={0} role="region" aria-labelledby="roster-heading">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-paper text-ink-soft">
                  <tr>
                    <th scope="col" className="px-4 py-2">Student</th>
                    <th scope="col" className="px-4 py-2 text-right">Level</th>
                    <th scope="col" className="hidden px-4 py-2 text-right sm:table-cell">Stories</th>
                    <th scope="col" className="px-4 py-2">Last active</th>
                  </tr>
                </thead>
                <tbody>
                  {roster.map(s => (
                    <tr key={s.id} className={`border-t border-rule ${s.id === readerId ? 'bg-accent-soft/50' : ''}`}>
                      <th scope="row" className="px-4 py-2 font-normal">
                        {studentName(s.id)}
                        <span className="block font-mono text-[11px] text-ink-muted">{s.id}</span>
                      </th>
                      <td className="px-4 py-2 text-right tabular-nums text-ink">{s.target_level}L</td>
                      <td className="hidden px-4 py-2 text-right tabular-nums text-ink sm:table-cell">{s.stories}</td>
                      <td className="whitespace-nowrap px-4 py-2 text-ink-soft">{lastActive(s.last_active_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
