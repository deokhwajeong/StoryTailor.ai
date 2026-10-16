import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { teacherApi } from './api';
import { IS_DEMO } from './demo/constants';
import type { AttentionReason, Difficulty, RosterStudent, TeacherSummary } from './types';

// Plain-language labels and a next step for each reason in storytailor/insights.py.
const REASON_TEXT: Record<AttentionReason, { label: string; action: string }> = {
  flagged_story: { label: 'A story was flagged', action: 'Review the flagged story with the student.' },
  struggling: { label: 'Finding stories too hard', action: 'Check in. The target level is already stepping down.' },
  below_grade_level: { label: 'Well below the grade starting level', action: 'Consider small-group or read-aloud support.' },
  inactive: { label: 'No reading in 14+ days', action: 'Encourage a short session this week.' },
  ready_for_more: { label: 'Says stories are too easy', action: 'Offer a stretch book from the library.' },
};

const DIFFICULTY_STYLE: Record<Difficulty, { label: string; bar: string }> = {
  too_hard: { label: 'Too hard', bar: 'bg-amber-500' },
  just_right: { label: 'Just right', bar: 'bg-emerald-600' },
  too_easy: { label: 'Too easy', bar: 'bg-sky-600' },
};

const GRADE_START: Record<number, number> = { 0: 150, 1: 300, 2: 450, 3: 600, 4: 740, 5: 840, 6: 920, 7: 980, 8: 1030 };

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

function levelBuckets(roster: RosterStudent[], width = 50) {
  const levels = roster.map(s => s.target_level);
  const lo = Math.floor(Math.min(...levels) / width) * width;
  const hi = Math.floor(Math.max(...levels) / width) * width;
  const buckets: { from: number; count: number }[] = [];
  for (let from = lo; from <= hi; from += width) {
    buckets.push({ from, count: levels.filter(l => l >= from && l < from + width).length });
  }
  return buckets;
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

  const submit = (e: FormEvent) => {
    e.preventDefault();
    onCredentials(draftToken.trim(), draftClass.trim());
  };

  const totalVotes = summary ? Object.values(summary.difficulty).reduce((a, b) => a + b, 0) : 0;
  const pct = (n: number) => (totalVotes ? Math.round((n / totalVotes) * 100) : 0);
  const grade = roster?.[0]?.grade;
  const gradeStart = grade === undefined ? undefined : GRADE_START[grade];
  const buckets = roster && roster.length > 0 ? levelBuckets(roster) : [];
  const maxBucket = Math.max(1, ...buckets.map(b => b.count));
  const studentLabel = (id: string) => (id === readerId ? `${id} (demo reader)` : id);

  return (
    <div className="w-full max-w-3xl rounded-3xl bg-white/95 p-4 shadow-xl sm:p-8">
      <h1 className="text-2xl font-bold text-pink-700">Class overview</h1>
      <p className="mt-1 text-sm text-gray-700">
        {summary?.classroom ? `${summary.classroom}.` : 'Reading levels, difficulty fit, and who may need a check-in.'}
        {IS_DEMO && ' Fictional, generated students. The demo reader from the Student tab is included and updates live.'}
      </p>

      {!IS_DEMO && (
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={submit}>
          <div className="flex flex-col">
            <label htmlFor="teacher-token" className="text-sm font-semibold text-gray-700">Teacher token</label>
            <input id="teacher-token" type="password" autoComplete="off" value={draftToken}
                   onChange={e => setDraftToken(e.target.value)}
                   className="rounded-lg border-2 border-pink-300 px-3 py-1.5" />
          </div>
          <div className="flex flex-col">
            <label htmlFor="classroom-id" className="text-sm font-semibold text-gray-700">Classroom ID</label>
            <input id="classroom-id" inputMode="numeric" value={draftClass}
                   onChange={e => setDraftClass(e.target.value)}
                   className="w-28 rounded-lg border-2 border-pink-300 px-3 py-1.5" />
          </div>
          <button type="submit" disabled={!draftToken.trim() || !draftClass.trim()}
                  className="rounded-full bg-pink-700 px-4 py-2 font-bold text-white hover:bg-pink-800 disabled:bg-gray-400">
            Load class
          </button>
        </form>
      )}

      <p className="sr-only" role="status" aria-live="polite">{loading ? 'Loading class.' : ''}</p>
      {error && <p role="alert" className="mt-4 text-red-700">{error}</p>}

      {summary && roster && (
        <>
          <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              ['Students', String(roster.length)],
              ['Average level', summary.levels.avg_target === null ? 'n/a' : `${Math.round(summary.levels.avg_target)}L`],
              ['Level range', summary.levels.min_target === null ? 'n/a' : `${summary.levels.min_target} to ${summary.levels.max_target}L`],
              ['Need a check-in', String(summary.needs_attention.length)],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl bg-pink-50 px-3 py-2">
                <dt className="text-xs text-gray-700">{label}</dt>
                <dd className="text-xl font-bold text-gray-900">{value}</dd>
              </div>
            ))}
          </dl>

          <section className="mt-6" aria-labelledby="attention-heading">
            <h2 id="attention-heading" className="text-lg font-bold text-gray-900">Who may need a check-in</h2>
            <p className="text-xs text-gray-600">Simple rules with a stated reason, meant to start a conversation, not to grade a child.</p>
            {summary.needs_attention.length === 0 ? (
              <p className="mt-2 text-sm text-gray-700">Nobody right now.</p>
            ) : (
              <ul className="mt-2 flex flex-col gap-2">
                {summary.needs_attention.map(item => (
                  <li key={item.student_id} className={`rounded-xl border px-3 py-2 ${item.student_id === readerId ? 'border-pink-400 bg-pink-50' : 'border-gray-200 bg-white'}`}>
                    <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                      <span className="font-mono text-sm font-semibold text-gray-900">{studentLabel(item.student_id)}</span>
                      <span className="text-sm text-gray-700">{item.target_level}L</span>
                    </div>
                    <ul className="mt-1 flex flex-col gap-0.5">
                      {item.reasons.map(r => (
                        <li key={r} className="text-sm text-gray-800">
                          <span className="font-semibold">{REASON_TEXT[r].label}.</span> {REASON_TEXT[r].action}
                        </li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <div className="mt-6 grid gap-6 sm:grid-cols-2">
            <section aria-labelledby="fit-heading">
              <h2 id="fit-heading" className="text-lg font-bold text-gray-900">Difficulty fit</h2>
              <p className="text-xs text-gray-600">Recent one-tap votes, {totalVotes} in total.</p>
              <div className="mt-2 flex h-4 overflow-hidden rounded-full bg-gray-200" aria-hidden="true">
                {(Object.keys(DIFFICULTY_STYLE) as Difficulty[]).map(d => (
                  <div key={d} className={DIFFICULTY_STYLE[d].bar} style={{ width: `${pct(summary.difficulty[d])}%` }} />
                ))}
              </div>
              <ul className="mt-2 flex flex-col gap-1 text-sm text-gray-800">
                {(Object.keys(DIFFICULTY_STYLE) as Difficulty[]).map(d => (
                  <li key={d} className="flex items-center gap-2">
                    <span className={`inline-block h-3 w-3 rounded-sm ${DIFFICULTY_STYLE[d].bar}`} aria-hidden="true" />
                    {DIFFICULTY_STYLE[d].label}: {summary.difficulty[d]} ({pct(summary.difficulty[d])}%)
                  </li>
                ))}
              </ul>
            </section>

            <section aria-labelledby="spread-heading">
              <h2 id="spread-heading" className="text-lg font-bold text-gray-900">Level spread</h2>
              <p className="text-xs text-gray-600">
                Students per 50L band{gradeStart !== undefined && `; grade ${grade} starts at ${gradeStart}L`}.
              </p>
              <ul className="mt-2 flex flex-col gap-1">
                {buckets.map(b => (
                  <li key={b.from} className="flex items-center gap-2 text-sm">
                    <span className={`w-20 shrink-0 tabular-nums ${gradeStart !== undefined && gradeStart >= b.from && gradeStart < b.from + 50 ? 'font-bold text-gray-900' : 'text-gray-700'}`}>
                      {b.from}-{b.from + 49}L
                    </span>
                    <span className="h-3 rounded-sm bg-purple-600" style={{ width: `${(b.count / maxBucket) * 100}%`, minWidth: b.count ? '0.5rem' : 0 }} aria-hidden="true" />
                    <span className="tabular-nums text-gray-800">{b.count}</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>

          <section className="mt-6" aria-labelledby="roster-heading">
            <h2 id="roster-heading" className="text-lg font-bold text-gray-900">Roster</h2>
            <p className="text-xs text-gray-600">Pseudonyms only. The teacher keeps the name list offline.</p>
            <div className="mt-2 max-h-80 overflow-auto rounded-xl border border-gray-200" tabIndex={0} role="region" aria-labelledby="roster-heading">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-gray-100 text-gray-800">
                  <tr>
                    <th scope="col" className="px-3 py-2">Student</th>
                    <th scope="col" className="px-3 py-2 text-right">Level</th>
                    <th scope="col" className="hidden px-3 py-2 text-right sm:table-cell">Stories</th>
                    <th scope="col" className="px-3 py-2">Last active</th>
                  </tr>
                </thead>
                <tbody>
                  {roster.map(s => (
                    <tr key={s.id} className={`border-t border-gray-100 ${s.id === readerId ? 'bg-pink-50' : ''}`}>
                      <th scope="row" className="px-3 py-1.5 font-mono font-normal text-gray-900">{studentLabel(s.id)}</th>
                      <td className="px-3 py-1.5 text-right tabular-nums">{s.target_level}L</td>
                      <td className="hidden px-3 py-1.5 text-right tabular-nums sm:table-cell">{s.stories}</td>
                      <td className="px-3 py-1.5 whitespace-nowrap">{lastActive(s.last_active_at)}</td>
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
