import { useEffect, useRef, useState, type FormEvent } from 'react';
import { SparklesIcon, BookOpenIcon, InformationCircleIcon } from '@heroicons/react/24/solid';
import { studentApi } from './api';
import { DEMO_ACCESS_CODE, DEMO_TOPIC_IDEAS, IS_DEMO } from './demo/constants';
import type { Book, Difficulty, Story } from './types';

const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  too_easy: 'Too easy',
  just_right: 'Just right',
  too_hard: 'Too hard',
};

const inputClass =
  'rounded-xl border-2 border-pink-300 bg-white px-4 py-2 text-lg text-gray-900 placeholder:text-gray-500 disabled:bg-gray-100';
const primaryButton =
  'flex items-center justify-center gap-2 rounded-full bg-pink-700 font-bold text-white shadow-lg hover:bg-pink-800 disabled:cursor-not-allowed disabled:bg-gray-400';

export default function StudentView() {
  // The access code lives only in memory: closing the tab signs the student out.
  const [code, setCode] = useState(IS_DEMO ? DEMO_ACCESS_CODE : '');
  const [topic, setTopic] = useState('');
  const [goal, setGoal] = useState('');
  const [story, setStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState<Difficulty | null>(null);
  const [levelChange, setLevelChange] = useState<{ from: number; to: number } | null>(null);
  const [showSources, setShowSources] = useState(false);
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
    setStory(null);
    setFeedback(null);
    setLevelChange(null);
    try {
      setStory(await studentApi<Story>('/api/stories', code, { topic, learning_goal: goal }));
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

  let thanks = 'Your next story will fit you even better.';
  if (levelChange && levelChange.to < levelChange.from) thanks = 'Your next story will be a little easier.';
  if (levelChange && levelChange.to > levelChange.from) thanks = 'Your next story will be a little more challenging.';

  return (
    <div className="w-full max-w-md rounded-3xl bg-white/90 p-6 shadow-xl sm:p-8">
      <h1 className="mb-1 flex items-center justify-center gap-2 text-3xl font-bold text-pink-700">
        <SparklesIcon className="h-8 w-8 text-amber-400" aria-hidden="true" />
        StoryTailor
      </h1>
      <p className="mb-6 text-center text-lg text-blue-800">A story made just for you</p>

      <form className="flex w-full flex-col gap-3" onSubmit={generate} aria-busy={loading}>
        <label className="text-sm font-semibold text-gray-700" htmlFor="code">Your reading code (from your teacher)</label>
        <input
          id="code"
          className={`${inputClass} uppercase tracking-widest`}
          value={code}
          maxLength={8}
          autoComplete="off"
          spellCheck={false}
          aria-describedby="code-help"
          onChange={e => setCode(e.target.value.toUpperCase())}
        />
        <p id="code-help" className="-mt-2 text-xs text-gray-600">8 letters and numbers.{IS_DEMO && ' The demo fills it in for you.'}</p>

        <label className="text-sm font-semibold text-gray-700" htmlFor="topic">What should the story be about?</label>
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
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Story ideas">
            {DEMO_TOPIC_IDEAS.map(idea => (
              <button
                key={idea}
                type="button"
                className="rounded-full border border-pink-300 bg-pink-50 px-2.5 py-1 text-xs text-pink-800 hover:bg-pink-100 disabled:opacity-60"
                onClick={() => setTopic(idea)}
                disabled={loading}
                aria-pressed={topic === idea}
              >
                {idea}
              </button>
            ))}
          </div>
        )}

        <label className="text-sm font-semibold text-gray-700" htmlFor="goal">What do you want to learn? (optional)</label>
        <input
          id="goal"
          className={inputClass}
          placeholder="keep trying when it is hard"
          value={goal}
          maxLength={120}
          onChange={e => setGoal(e.target.value)}
          disabled={loading}
        />
        <p id="privacy-hint" className="text-xs text-gray-600">Please do not type your name, address, or phone number.</p>
        <button type="submit" className={`${primaryButton} px-6 py-2 text-lg`} disabled={!canSubmit}>
          <SparklesIcon className="h-6 w-6" aria-hidden="true" />
          {loading ? 'Writing your story...' : 'Make my story'}
        </button>
      </form>

      <div className="mt-3 text-center">
        <button
          type="button"
          className="text-blue-800 underline underline-offset-2 hover:text-blue-900 disabled:text-gray-500 disabled:no-underline"
          onClick={loadBooks}
          disabled={code.length < 8}
        >
          Find library books for me
        </button>
      </div>

      <p className="sr-only" role="status" aria-live="polite">
        {loading ? 'Writing your story.' : story ? 'Your story is ready.' : ''}
      </p>

      {books && (
        <section className="mt-4 w-full" aria-labelledby="books-heading">
          <h2 id="books-heading" className="mb-2 text-lg font-bold text-purple-800">Books for you</h2>
          <p className="text-sm text-green-800" role="status">{loggedBook && `Great job finishing ${loggedBook}!`}</p>
          <ul className="mt-1 flex flex-col gap-2">
            {books.map(b => (
              <li key={b.id} className="flex items-center justify-between gap-2 rounded-xl bg-purple-50 px-3 py-2">
                <span>
                  <span className="font-semibold text-gray-900">{b.title}</span>
                  <span className="block text-xs text-gray-600">
                    {b.lexile}L · Level {b.guided_level}
                    {b.interest_matches.length > 0 && ` · ${b.interest_matches.join(', ')}`}
                  </span>
                </span>
                <button
                  type="button"
                  className="shrink-0 rounded-full border-2 border-green-600 px-3 py-1 text-sm text-green-900 hover:bg-green-50"
                  onClick={() => markRead(b)}
                  aria-label={`I read ${b.title}`}
                >
                  I read it
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {error && <p role="alert" className="mt-4 text-red-700">{error}</p>}

      {story && (
        <section className="mt-8 flex w-full flex-col items-center" aria-labelledby="story-heading">
          <article className="w-full rounded-2xl border-4 border-pink-200 bg-amber-50 p-6 shadow-lg">
            <BookOpenIcon className="mx-auto mb-2 h-10 w-10 text-purple-400" aria-hidden="true" />
            <h2 id="story-heading" ref={storyHeading} tabIndex={-1} className="sr-only">Your story</h2>
            <p className="whitespace-pre-line text-lg leading-relaxed text-gray-900">{story.text}</p>
          </article>

          <div className="mt-4 w-full">
            <p id="feedback-label" className="mb-2 text-sm text-gray-700">How was this story?</p>
            {feedback ? (
              <div className="flex flex-col gap-2" role="status">
                <p className="text-green-800">Thanks! {thanks}</p>
                {levelChange && levelChange.to !== levelChange.from && (
                  <p className="text-xs text-gray-600">Reading level: {levelChange.from}L to {levelChange.to}L</p>
                )}
                <button
                  type="button"
                  className={`${primaryButton} self-start px-4 py-1.5 text-sm`}
                  onClick={() => generate()}
                  disabled={!canSubmit}
                >
                  {loading ? 'Writing your story...' : 'Make my next story'}
                </button>
              </div>
            ) : (
              <div className="flex gap-2" role="group" aria-labelledby="feedback-label">
                {(Object.keys(DIFFICULTY_LABELS) as Difficulty[]).map(d => (
                  <button
                    key={d}
                    type="button"
                    className="flex-1 rounded-full border-2 border-blue-300 py-1 text-blue-900 hover:bg-blue-50"
                    onClick={() => sendFeedback(d)}
                  >
                    {DIFFICULTY_LABELS[d]}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="mt-4 w-full">
            <button
              type="button"
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-2 text-sm text-blue-800"
              aria-expanded={showSources}
              aria-controls="sources-panel"
            >
              <InformationCircleIcon className="h-5 w-5" aria-hidden="true" />
              {showSources ? 'Hide details' : 'For teachers: level and sources'}
            </button>
            <div id="sources-panel" hidden={!showSources} className="mt-2 rounded-lg bg-blue-50 p-3 text-sm text-gray-800">
              <p>Target level: {story.target_level}L, measured: about {story.measured_level}L</p>
              {story.sources.length > 0 && (
                <ul className="mt-1 list-inside list-disc">
                  {story.sources.map(s => <li key={s.id}>{s.source} ({s.id})</li>)}
                </ul>
              )}
              {story.redacted.length > 0 && <p className="mt-1">Removed before sending: {story.redacted.join(', ')}</p>}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
