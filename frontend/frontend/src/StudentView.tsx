import { useEffect, useRef, useState, type FormEvent } from 'react';
import { studentApi } from './api';
import StoryTrace, { RedactedText } from './StoryTrace';
import { DEMO_ACCESS_CODE, DEMO_TOPIC_IDEAS, IS_DEMO } from './demo/constants';
import type { Book, Difficulty, Story } from './types';

const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  too_easy: 'Too easy',
  just_right: 'Just right',
  too_hard: 'Too hard',
};

const inputClass =
  'w-full rounded-md border border-rule bg-sheet px-3 py-2.5 text-lg text-ink placeholder:text-ink-muted focus:border-accent disabled:opacity-60';
const labelClass = 'text-sm font-bold text-ink-soft';
const primaryButton =
  'inline-flex items-center justify-center gap-2 rounded-md bg-accent px-5 py-2.5 font-bold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50';
const quietButton =
  'inline-flex items-center justify-center rounded-md border border-rule bg-sheet px-4 py-2 font-bold text-ink-soft hover:border-accent hover:text-accent disabled:opacity-50';

function storyTitle(topic: string): string {
  const clean = topic.replace(/\s+/g, ' ').trim();
  return clean.charAt(0).toUpperCase() + clean.slice(1);
}

function LevelBadge({ story }: { story: Story }) {
  const [lo, hi] = story.band;
  const where = story.fit === 'in_band' ? 'in your band' : story.fit === 'too_hard' ? 'a little above your band' : 'a little below your band';
  return (
    <p className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent-soft px-3 py-1 text-sm text-accent-strong">
      <span className="font-bold tabular-nums">{story.measured_level}L</span>
      <span aria-hidden="true">·</span>
      <span>{where}, {lo} to {hi}</span>
    </p>
  );
}

export default function StudentView() {
  // The access code lives only in memory: closing the tab signs the student out.
  const [code, setCode] = useState(IS_DEMO ? DEMO_ACCESS_CODE : '');
  const [topic, setTopic] = useState('');
  const [goal, setGoal] = useState('');
  const [story, setStory] = useState<Story | null>(null);
  const [composing, setComposing] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState<Difficulty | null>(null);
  const [levelChange, setLevelChange] = useState<{ from: number; to: number } | null>(null);
  const [books, setBooks] = useState<Book[] | null>(null);
  const [loggedBook, setLoggedBook] = useState('');
  const storyHeading = useRef<HTMLHeadingElement>(null);

  const canSubmit = !loading && topic.trim().length > 0 && code.length === 8;

  // Move focus to the new story so keyboard and screen reader users land on it.
  useEffect(() => {
    if (story) storyHeading.current?.focus();
  }, [story]);

  const loadBooks = async () => {
    setError('');
    try {
      const data = await studentApi<{ books: Book[] }>('/api/books/recommendations', code);
      setBooks(data.books);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load books.');
    }
  };

  const markRead = async (book: Book) => {
    try {
      await studentApi('/api/books/log', code, { book_id: book.id, completed: true });
      setLoggedBook(book.title);
      await loadBooks();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save.');
    }
  };

  const generate = async (e?: FormEvent) => {
    e?.preventDefault();
    if (!canSubmit) return;
    setLoading(true);
    setError('');
    setFeedback(null);
    setLevelChange(null);
    try {
      setStory(await studentApi<Story>('/api/stories', code, { topic, learning_goal: goal }));
      setComposing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  const sendFeedback = async (difficulty: Difficulty) => {
    if (!story) return;
    try {
      const res = await studentApi<{ target_level?: number }>(`/api/stories/${story.id}/feedback`, code, { difficulty });
      if (typeof res.target_level === 'number') {
        setLevelChange({ from: story.target_level, to: res.target_level });
      }
      setFeedback(difficulty);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not send feedback.');
    }
  };

  let thanks = 'Your next story will stay at this level.';
  if (levelChange && levelChange.to < levelChange.from) thanks = 'Your next story will be a little easier.';
  if (levelChange && levelChange.to > levelChange.from) thanks = 'Your next story will be a little more challenging.';

  const form = (
    <form className="flex flex-col gap-4" onSubmit={generate} aria-busy={loading}>
      <div className="flex flex-col gap-1.5">
        <label className={labelClass} htmlFor="topic">What should the story be about?</label>
        <input
          id="topic"
          className={inputClass}
          placeholder="an octopus who loves puzzles"
          value={topic}
          maxLength={120}
          onChange={e => setTopic(e.target.value)}
          disabled={loading}
          aria-describedby="privacy-hint"
        />
        {IS_DEMO && (
          <div className="mt-1 flex flex-wrap gap-2" role="group" aria-label="Story ideas">
            {DEMO_TOPIC_IDEAS.map(idea => (
              <button
                key={idea}
                type="button"
                className={`rounded-md border px-2.5 py-1 text-sm ${topic === idea ? 'border-accent bg-accent-soft text-accent-strong' : 'border-rule bg-sheet text-ink-soft hover:border-accent'} disabled:opacity-60`}
                onClick={() => setTopic(idea)}
                disabled={loading}
                aria-pressed={topic === idea}
              >
                {idea}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-[1fr_12rem]">
        <div className="flex flex-col gap-1.5">
          <label className={labelClass} htmlFor="goal">Something to learn <span className="font-normal text-ink-muted">(optional)</span></label>
          <input
            id="goal"
            className={inputClass}
            placeholder="keep trying when it is hard"
            value={goal}
            maxLength={120}
            onChange={e => setGoal(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className={labelClass} htmlFor="code">Reading code</label>
          <input
            id="code"
            className={`${inputClass} font-bold uppercase tracking-[0.2em]`}
            value={code}
            maxLength={8}
            autoComplete="off"
            spellCheck={false}
            aria-describedby="code-help"
            onChange={e => setCode(e.target.value.toUpperCase())}
          />
          <p id="code-help" className="text-xs text-ink-muted">From your teacher.{IS_DEMO && ' Filled in for the demo.'}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p id="privacy-hint" className="text-sm text-ink-muted">Please leave out your name, address, and phone number.</p>
        <button type="submit" className={primaryButton} disabled={!canSubmit}>
          {loading ? 'Writing your story...' : 'Write my story'}
        </button>
      </div>
    </form>
  );

  return (
    <div className="flex flex-col gap-6">
      <p className="sr-only" role="status" aria-live="polite">
        {loading ? 'Writing your story.' : story ? 'Your story is ready.' : ''}
      </p>

      {composing || !story ? (
        <section className="mx-auto w-full max-w-2xl rounded-lg border border-rule bg-sheet p-5 sm:p-7" aria-labelledby="ask-heading">
          <h1 id="ask-heading" className="font-serif text-2xl text-ink sm:text-3xl">A story written for you</h1>
          <p className="mb-5 mt-1 text-ink-soft">
            Pick a topic. Your story is checked for safety and measured so it matches your reading level.
          </p>
          {form}
          {story && (
            <button type="button" className="mt-4 text-sm text-accent underline underline-offset-2" onClick={() => setComposing(false)}>
              Back to my story
            </button>
          )}
        </section>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-rule bg-sheet px-4 py-3">
          <p className="text-sm text-ink-soft">
            You asked for: <span className="font-bold text-ink"><RedactedText text={story.topic} /></span>
          </p>
          <button type="button" className={quietButton} onClick={() => setComposing(true)}>Write a different story</button>
        </div>
      )}

      {error && <p role="alert" className="mx-auto w-full max-w-2xl rounded-md border border-clay/30 bg-clay-soft px-4 py-3 text-clay">{error}</p>}

      {story && (
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_24rem]">
          <section aria-labelledby="story-heading" className="flex flex-col gap-5">
            <article className="rounded-lg border border-rule bg-sheet px-6 py-8 shadow-[0_1px_0_var(--color-rule),0_12px_32px_-20px_rgba(38,34,30,0.35)] sm:px-12 sm:py-12">
              <div className="mx-auto max-w-[36rem]">
                <h2 id="story-heading" ref={storyHeading} tabIndex={-1} className="font-serif text-3xl leading-tight text-ink sm:text-4xl">
                  <RedactedText text={storyTitle(story.topic)} />
                </h2>
                <div className="mb-8 mt-4"><LevelBadge story={story} /></div>
                <div className="flex flex-col gap-5 text-[1.25rem] leading-[1.8] text-ink">
                  {story.text.split(/\n\s*\n/).map((para, i) => <p key={i}>{para}</p>)}
                </div>
                <p className="mt-10 text-center text-ink-muted" aria-hidden="true">· · ·</p>
              </div>
            </article>

            <div className="rounded-lg border border-rule bg-sheet px-5 py-4">
              <p id="feedback-label" className="font-bold text-ink">How did this story feel?</p>
              {feedback ? (
                <div className="mt-2 flex flex-col items-start gap-3" role="status">
                  <p className="text-ink-soft">
                    Thanks, you said <span className="font-bold text-ink">{DIFFICULTY_LABELS[feedback].toLowerCase()}</span>. {thanks}
                    {levelChange && levelChange.to !== levelChange.from && (
                      <span className="block text-sm text-ink-muted">Your level moved from {levelChange.from}L to {levelChange.to}L.</span>
                    )}
                  </p>
                  <button type="button" className={primaryButton} onClick={() => generate()} disabled={!canSubmit}>
                    {loading ? 'Writing your story...' : 'Write my next story'}
                  </button>
                </div>
              ) : (
                <div className="mt-3 grid grid-cols-3 gap-2" role="group" aria-labelledby="feedback-label">
                  {(Object.keys(DIFFICULTY_LABELS) as Difficulty[]).map(d => (
                    <button key={d} type="button" className={quietButton} onClick={() => sendFeedback(d)}>
                      {DIFFICULTY_LABELS[d]}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </section>

          <aside className="flex flex-col gap-6 lg:sticky lg:top-4" aria-label="About this story">
            <StoryTrace key={story.id} trace={story.trace} />
          </aside>
        </div>
      )}

      <section className="rounded-lg border border-rule bg-sheet px-5 py-4" aria-labelledby="books-heading">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 id="books-heading" className="font-bold text-ink">Books from your class library</h2>
            <p className="text-sm text-ink-muted">Real books at your level, picked for what you like.</p>
          </div>
          <button type="button" className={quietButton} onClick={loadBooks} disabled={code.length < 8}>
            {books ? 'Refresh' : 'Find books for me'}
          </button>
        </div>
        <p className="text-sm text-accent-strong" role="status">{loggedBook && `Nice work finishing ${loggedBook}.`}</p>
        {books && (
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {books.map(b => (
              <li key={b.id} className="flex items-center justify-between gap-3 rounded-md border border-rule px-3 py-2">
                <span>
                  <span className="font-bold text-ink">{b.title}</span>
                  <span className="block text-xs text-ink-muted">
                    {b.lexile}L · level {b.guided_level}
                    {b.interest_matches.length > 0 && ` · ${b.interest_matches.join(', ')}`}
                  </span>
                </span>
                <button
                  type="button"
                  className="shrink-0 rounded-md border border-accent px-3 py-1 text-sm font-bold text-accent hover:bg-accent-soft"
                  onClick={() => markRead(b)}
                  aria-label={`I read ${b.title}`}
                >
                  I read it
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
