import { useId, useState, type ReactNode } from 'react';
import type { TraceDraft, TraceStep } from './types';

// "How this story was made": a plain-language walk through the steps the server
// ran for this story, built only from the trace it returned. Nothing here is
// computed in the browser, so the numbers are the server's measurements.

const PII_LABELS: Record<string, string> = {
  email: 'an email address',
  url: 'a web link',
  phone: 'a phone number',
  address: 'a street address',
  id_number: 'a long number',
  name: 'a name',
};
const PII_TOKEN = /\[(email|url|phone|address|id_number|name)\]/g;

const SEEN_KEY = 'storytailor.trace-open';

// Open by default the first time; after that, remember what the reader chose.
// Storage can be unavailable (private windows, blocked site data), so every
// access is guarded and the panel still works without it.
function initialOpen(): boolean {
  try {
    const saved = localStorage.getItem(SEEN_KEY);
    return saved === null ? true : saved === '1';
  } catch {
    return true;
  }
}

function remember(open: boolean) {
  try {
    localStorage.setItem(SEEN_KEY, open ? '1' : '0');
  } catch {
    // Not saved; the panel simply opens again next time.
  }
}

function listPhrase(items: string[]): string {
  if (items.length <= 1) return items.join('');
  return `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`;
}

// Show the redacted request with each removed span marked in place.
export function RedactedText({ text }: { text: string }) {
  const parts: ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(PII_TOKEN)) {
    const at = m.index ?? 0;
    if (at > last) parts.push(text.slice(last, at));
    parts.push(
      <mark key={at} className="rounded bg-clay-soft px-1 font-bold text-clay">
        [removed<span className="sr-only">: {PII_LABELS[m[1]]}</span>]
      </mark>,
    );
    last = at + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}

function Gauge({ draft, domain }: { draft: TraceDraft; domain: [number, number] }) {
  const [lo, hi] = draft.band;
  const W = 300;
  const x = (v: number) => 8 + ((v - domain[0]) / (domain[1] - domain[0])) * (W - 16);
  const inBand = draft.fit === 'in_band';
  const mx = x(draft.measured_level);
  return (
    <svg viewBox={`0 0 ${W} 40`} className="mt-2 h-10 w-full max-w-xs" aria-hidden="true">
      <line x1="8" x2={W - 8} y1="14" y2="14" stroke="var(--color-rule)" strokeWidth="2" strokeLinecap="round" />
      <rect x={x(lo)} y="8" width={x(hi) - x(lo)} height="12" rx="4" fill="var(--color-accent-soft)" stroke="var(--color-accent)" strokeWidth="1" />
      <text x={x(lo)} y="36" fontSize="10" textAnchor="middle" fill="var(--color-ink-muted)">{lo}</text>
      <text x={x(hi)} y="36" fontSize="10" textAnchor="middle" fill="var(--color-ink-muted)">{hi}</text>
      <line x1={mx} x2={mx} y1="3" y2="25" stroke={inBand ? 'var(--color-accent-strong)' : 'var(--color-clay)'} strokeWidth="2" />
      <circle cx={mx} cy="14" r="4.5" fill={inBand ? 'var(--color-accent-strong)' : 'var(--color-clay)'} stroke="var(--color-sheet)" strokeWidth="2" />
    </svg>
  );
}

function StatusTag({ tone, children }: { tone: 'ok' | 'no' | 'plain'; children: ReactNode }) {
  const cls = tone === 'ok' ? 'bg-accent-soft text-accent-strong' : tone === 'no' ? 'bg-clay-soft text-clay' : 'bg-paper text-ink-soft';
  return <span className={`ml-2 inline-block rounded px-1.5 py-0.5 align-middle text-[11px] font-bold uppercase tracking-wide ${cls}`}>{children}</span>;
}

function Marker({ tone, n }: { tone: 'ok' | 'no'; n: number }) {
  return (
    <span
      className={`absolute left-0 top-0 flex h-7 w-7 items-center justify-center rounded-full border-2 text-xs font-bold ${tone === 'ok' ? 'border-accent bg-sheet text-accent' : 'border-clay bg-clay-soft text-clay'}`}
      aria-hidden="true"
    >
      {tone === 'ok' ? n : '×'}
    </span>
  );
}

function draftText(d: TraceDraft, draftCount: number) {
  const band = `${d.band[0]} to ${d.band[1]}L`;
  if (d.status === 'rejected') {
    return d.fit === 'too_hard'
      ? `Too hard for your band (${band}). Rejected, and the writer was asked for shorter sentences and simpler words.`
      : d.fit === 'too_easy'
        ? `Too easy for your band (${band}). Rejected, and the writer was asked for richer words.`
        : `In your band, but another draft was kept.`;
  }
  if (d.fit === 'in_band') {
    return d.attempt === 1
      ? `In your band (${band}) on the first try. Accepted.`
      : `In your band (${band}). Accepted: this is the story you are reading.`;
  }
  const side = d.fit === 'too_hard' ? 'a little above' : 'a little below';
  return `Closest of the ${draftCount} drafts, ${side} your band (${band}). Kept so you still get a story; your feedback will tune the next one.`;
}

export default function StoryTrace({ trace }: { trace: TraceStep[] }) {
  const [open, setOpen] = useState(initialOpen);
  const panelId = useId();
  const drafts = trace.filter((s): s is TraceDraft => s.step === 'draft');
  const rejected = drafts.filter(d => d.status === 'rejected').length;
  const levels = drafts.flatMap(d => [d.measured_level, ...d.band]);
  const domain: [number, number] = [Math.min(...levels) - 60, Math.max(...levels) + 60];

  const toggle = () => {
    setOpen(!open);
    remember(!open);
  };

  const items = trace.map((s, i) => {
    const n = i + 1;
    let tone: 'ok' | 'no' = 'ok';
    let title: ReactNode;
    let body: ReactNode;
    switch (s.step) {
      case 'shelf':
        title = (
          <>
            Looked at your class shelf
            {s.status === 'thin' && <StatusTag tone="plain">Few books</StatusTag>}
          </>
        );
        body = s.status === 'thin'
          ? <p>Your band, {s.band[0]} to {s.band[1]}L, has only {s.titles} {s.titles === 1 ? 'book' : 'books'} on the class shelf, so a new story helps here.</p>
          : <p>Your band, {s.band[0]} to {s.band[1]}L, has {s.titles} books on the class shelf. A story adds one more, just for you.</p>;
        break;
      case 'redaction':
        title = 'Checked your request for personal details';
        body = (
          <>
            <p>{s.status === 'removed'
              ? `Removed ${listPhrase(s.kinds.map(k => PII_LABELS[k] ?? k))} before anything else saw it.`
              : 'Nothing personal found.'}</p>
            <p className="mt-1.5 rounded bg-paper px-2 py-1 text-ink-soft">
              <span className="sr-only">Request as it was sent on: </span>
              &ldquo;<RedactedText text={s.topic} />&rdquo;
              {s.learning_goal && <>, goal &ldquo;<RedactedText text={s.learning_goal} />&rdquo;</>}
            </p>
          </>
        );
        break;
      case 'topic_check':
        title = 'Checked the topic is right for school';
        body = <p>Passed. None of the {s.word_list_size} words on the classroom block list appear.</p>;
        break;
      case 'grounding':
        title = 'Looked up real facts';
        body = s.facts.length > 0 ? (
          <>
            <p>Found {s.facts.length} {s.facts.length === 1 ? 'fact' : 'facts'} so real-world details stay accurate:</p>
            <ul className="mt-1 list-inside list-disc text-ink-soft">
              {s.facts.map(f => <li key={f.id}>{f.source}</li>)}
            </ul>
          </>
        ) : <p>No matching facts, so the story stays fully made up.</p>;
        break;
      case 'draft':
        tone = s.status === 'rejected' ? 'no' : 'ok';
        title = (
          <>
            Draft {s.attempt}: measured {s.measured_level}L
            <StatusTag tone={s.status === 'accepted' ? 'ok' : 'no'}>{s.status === 'accepted' ? 'Accepted' : 'Rejected'}</StatusTag>
          </>
        );
        body = (
          <>
            <p>{draftText(s, drafts.length)}</p>
            <Gauge draft={s} domain={domain} />
            <p className="text-xs text-ink-muted">
              Flesch-Kincaid grade {s.fk_grade.toFixed(1)} · {s.words} words
              {s.instruction && ` · rewritten to ${s.instruction === 'simplify' ? 'simplify' : 'enrich'}`}
            </p>
            <details className="mt-1 text-xs">
              <summary className="cursor-pointer text-accent underline underline-offset-2">How this draft began</summary>
              <p className="mt-1 italic text-ink-soft">{s.excerpt}</p>
            </details>
          </>
        );
        break;
      case 'moderation': {
        const service = s.checks.find(c => c.name === 'moderation_service');
        title = 'Checked the finished story';
        body = (
          <p>
            Classroom word list: passed.{' '}
            {service?.result === 'passed'
              ? 'Moderation service: passed.'
              : 'A moderation service is not used in this setup (offline or demo), so only the word list ran.'}
          </p>
        );
        break;
      }
      case 'library':
        title = 'Matched books from your class library';
        body = s.books.length > 0 ? (
          <>
            <p>{s.books.length} books in your band ({s.band[0]} to {s.band[1]}L):</p>
            <ul className="mt-1 flex flex-col gap-1">
              {s.books.map(b => (
                <li key={b.id} className="flex items-baseline justify-between gap-3 border-b border-dotted border-rule pb-1 last:border-0">
                  <span className="text-ink">{b.title}</span>
                  <span className="shrink-0 tabular-nums text-xs text-ink-muted">{b.lexile}L · level {b.guided_level}</span>
                </li>
              ))}
            </ul>
          </>
        ) : <p>No unread books in your band right now.</p>;
        break;
    }
    return (
      <li key={i} className="relative pb-5 pl-10 last:pb-0">
        {i < trace.length - 1 && <span className="absolute bottom-0 left-[13px] top-7 w-0.5 bg-rule" aria-hidden="true" />}
        <Marker tone={tone} n={n} />
        <h3 className="pt-0.5 font-bold text-ink">{title}</h3>
        <div className="mt-1 text-sm leading-relaxed text-ink-soft">{body}</div>
      </li>
    );
  });

  return (
    <section className="rounded-lg border border-rule bg-sheet" aria-labelledby={`${panelId}-h`}>
      <h2 id={`${panelId}-h`} className="m-0">
        <button
          type="button"
          onClick={toggle}
          aria-expanded={open}
          aria-controls={panelId}
          className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left"
        >
          <span>
            <span className="block font-bold text-ink">How this story was made</span>
            <span className="block text-xs text-ink-muted">
              {trace.length} steps · {drafts.length} {drafts.length === 1 ? 'draft' : 'drafts'}
              {rejected > 0 && `, ${rejected} rejected for level`}
            </span>
          </span>
          <svg viewBox="0 0 20 20" className={`h-5 w-5 shrink-0 text-ink-muted transition-transform ${open ? 'rotate-180' : ''}`} aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m5 8 5 5 5-5" />
          </svg>
        </button>
      </h2>
      <div id={panelId} hidden={!open} className="border-t border-rule px-5 py-5 lg:max-h-[calc(100vh-7.5rem)] lg:overflow-y-auto" tabIndex={-1}>
        <ol>{items}</ol>
      </div>
    </section>
  );
}
