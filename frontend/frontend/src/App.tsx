import { useState } from 'react';
import { SparklesIcon, BookOpenIcon, InformationCircleIcon } from '@heroicons/react/24/solid';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:5000';

interface Source {
  id: string;
  source: string;
}

interface Story {
  id: number;
  topic: string;
  text: string;
  target_level: number;
  measured_level: number;
  sources: Source[];
  redacted: string[];
}

type Difficulty = 'too_easy' | 'just_right' | 'too_hard';

const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  too_easy: 'Too easy',
  just_right: 'Just right',
  too_hard: 'Too hard',
};

async function api<T>(path: string, code: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Student-Code': code },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error ?? 'Something went wrong.');
  return data as T;
}

function App() {
  // The access code lives only in memory: closing the tab signs the student out.
  const [code, setCode] = useState('');
  const [topic, setTopic] = useState('');
  const [goal, setGoal] = useState('');
  const [story, setStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [showSources, setShowSources] = useState(false);

  const generate = async () => {
    setLoading(true);
    setError('');
    setStory(null);
    setFeedbackSent(false);
    try {
      setStory(await api<Story>('/api/stories', code, { topic, learning_goal: goal }));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  const sendFeedback = async (difficulty: Difficulty) => {
    if (!story) return;
    try {
      await api(`/api/stories/${story.id}/feedback`, code, { difficulty });
      setFeedbackSent(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not send feedback.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-100 via-blue-100 to-green-100 flex flex-col items-center justify-center p-4">
      <main className="w-full max-w-md bg-white/80 rounded-3xl shadow-xl p-8 flex flex-col items-center">
        <h1 className="text-3xl font-bold text-pink-400 mb-2 flex items-center gap-2">
          <SparklesIcon className="w-8 h-8 text-yellow-300" aria-hidden="true" />
          StoryTailor
        </h1>
        <p className="text-lg text-blue-500 mb-6">A story made just for you</p>

        <div className="w-full flex flex-col gap-3">
          <label className="text-sm text-gray-600" htmlFor="code">Your reading code (from your teacher)</label>
          <input
            id="code"
            className="rounded-xl border-2 border-pink-200 px-4 py-2 text-lg tracking-widest uppercase"
            value={code}
            maxLength={8}
            autoComplete="off"
            onChange={e => setCode(e.target.value.toUpperCase())}
          />
          <label className="text-sm text-gray-600" htmlFor="topic">What should the story be about?</label>
          <input
            id="topic"
            className="rounded-xl border-2 border-pink-200 px-4 py-2 text-lg"
            placeholder="an octopus who loves puzzles"
            value={topic}
            maxLength={120}
            onChange={e => setTopic(e.target.value)}
            disabled={loading}
          />
          <label className="text-sm text-gray-600" htmlFor="goal">What do you want to learn? (optional)</label>
          <input
            id="goal"
            className="rounded-xl border-2 border-pink-200 px-4 py-2 text-lg"
            placeholder="keep trying when it is hard"
            value={goal}
            maxLength={120}
            onChange={e => setGoal(e.target.value)}
            disabled={loading}
          />
          <p className="text-xs text-gray-500">Please do not type your name, address, or phone number.</p>
          <button
            className="flex items-center justify-center gap-2 bg-pink-300 hover:bg-blue-300 text-white font-bold py-2 px-6 rounded-full shadow-lg text-lg disabled:opacity-50"
            onClick={generate}
            disabled={loading || !topic.trim() || code.length < 8}
          >
            <SparklesIcon className="w-6 h-6" aria-hidden="true" />
            {loading ? 'Writing your story...' : 'Make my story'}
          </button>
        </div>

        {error && <p role="alert" className="mt-4 text-red-600">{error}</p>}

        {story && (
          <section className="mt-8 w-full flex flex-col items-center" aria-live="polite">
            <article className="w-full bg-yellow-50 rounded-2xl shadow-lg p-6 border-4 border-pink-200">
              <BookOpenIcon className="w-10 h-10 text-purple-300 mx-auto mb-2" aria-hidden="true" />
              <p className="text-gray-800 whitespace-pre-line text-lg leading-relaxed">{story.text}</p>
            </article>

            <div className="mt-4 w-full">
              <p className="text-sm text-gray-600 mb-2">How was this story?</p>
              {feedbackSent ? (
                <p className="text-green-600">Thanks! Your next story will fit you even better.</p>
              ) : (
                <div className="flex gap-2">
                  {(Object.keys(DIFFICULTY_LABELS) as Difficulty[]).map(d => (
                    <button
                      key={d}
                      className="flex-1 rounded-full border-2 border-blue-200 py-1 hover:bg-blue-100"
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
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-2 text-sm text-blue-600"
                aria-expanded={showSources}
                aria-controls="sources-panel"
              >
                <InformationCircleIcon className="w-5 h-5" aria-hidden="true" />
                {showSources ? 'Hide details' : 'For teachers: level and sources'}
              </button>
              {showSources && (
                <div id="sources-panel" className="mt-2 p-3 bg-blue-50 rounded-lg text-sm text-gray-700">
                  <p>Target level: {story.target_level}L, measured: about {story.measured_level}L</p>
                  {story.sources.length > 0 && (
                    <ul className="list-disc list-inside mt-1">
                      {story.sources.map(s => <li key={s.id}>{s.source} ({s.id})</li>)}
                    </ul>
                  )}
                  {story.redacted.length > 0 && (
                    <p className="mt-1">Removed before sending: {story.redacted.join(', ')}</p>
                  )}
                </div>
              )}
            </div>
          </section>
        )}
      </main>
      <footer className="mt-8 text-xs text-gray-500">StoryTailor 2026</footer>
    </div>
  );
}

export default App;
