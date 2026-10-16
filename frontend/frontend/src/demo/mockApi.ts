// In-browser stand-in for the Flask API, used only in demo builds (VITE_DEMO=1).
//
// It mirrors the server logic closely enough to show the real product loop:
// PII redaction and the topic safety check, picking the story version that best
// fits the reader's target level, the feedback rule that moves that target by
// 50L, and leveled library recommendations from the real classroom catalog.
// Stories are pre-written samples (three leveled versions per topic, measured
// with the same Flesch-Kincaid mapping the server uses). Nothing is sent over
// the network and nothing is persisted: reloading the page resets the demo.

import catalog from '../../../../storytailor/data/books.json';
import knowledge from '../../../../storytailor/data/knowledge.json';
import samples from './stories.json';
import { DEMO_CLASS_NAME, demoRoster, demoSummary, type ReaderState } from './teacherData';
import type { Difficulty } from '../types';

interface CatalogBook {
  id: string;
  title: string;
  lexile: number;
  guided_level: string;
  tags: string[];
}

interface SampleVersion {
  text: string;
  measured_level: number;
}

interface Sample {
  key: string;
  keywords: string[];
  sources: string[];
  versions: Record<string, SampleVersion>;
}

interface DemoStory {
  id: number;
  topic: string;
  sampleKey: string;
}

// Values copied from storytailor/personalization.py and storytailor/books.py.
const LEVEL_STEP = 50;
const LEVEL_MIN = 100;
const LEVEL_MAX = 1300;
const RECENT_VOTES = 5;
const BAND_BELOW = 100;
const BAND_ABOVE = 50;

// A fictional grade 3 reader. Grade 3 starts at 600L on the server too.
const profile = {
  grade: 3,
  targetLevel: 600,
  interests: ['animals', 'science', 'adventure'],
  avoidTopics: [] as string[],
};

const stories = new Map<number, DemoStory>();
const votes: Difficulty[] = [];
const allVotes: Difficulty[] = [];
const alreadyRead = new Set<string>();
let nextStoryId = 1;

const SAMPLES = samples as Sample[];
const BOOKS = catalog as CatalogBook[];
const SOURCE_LABELS = new Map((knowledge as { id: string; source: string }[]).map(k => [k.id, k.source]));

// Same patterns as storytailor/privacy.py, in the same order.
const PII_PATTERNS: [string, RegExp][] = [
  ['email', /\b[\w.+-]+@[\w-]+\.[\w.-]+\b/g],
  ['url', /\bhttps?:\/\/\S+|\bwww\.\S+/gi],
  ['phone', /(?:\+?1[\s.-]?)?\(?\b\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b/g],
  ['address', /\b\d{1,5}\s+(?:[A-Z][a-z]+\s){1,3}(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Way|Blvd|Boulevard)\b\.?/g],
  ['id_number', /\b\d{6,}\b/g],
  ['name', /\b((?:my name is|my name's|i'm called)\s+)[a-z]+/gi],
];

// Same word list as storytailor/safety.py.
const BLOCKED_TERMS = [
  'kill', 'killed', 'killing', 'murder', 'blood', 'bloody', 'gun', 'guns', 'knife',
  'weapon', 'drug', 'drugs', 'alcohol', 'beer', 'wine', 'cigarette', 'vape',
  'war', 'suicide', 'horror', 'gore', 'sexy', 'dead body',
];
const BLOCKED_RE = new RegExp(`\\b(${BLOCKED_TERMS.join('|')})\\b`, 'gi');

export class DemoApiError extends Error {}

function redact(text: string): [string, string[]] {
  const found: string[] = [];
  let out = text;
  for (const [kind, pattern] of PII_PATTERNS) {
    const replaced = out.replace(pattern, (...m) => (kind === 'name' ? `${m[1]}[name]` : `[${kind}]`));
    if (replaced !== out) found.push(kind);
    out = replaced;
  }
  return [out, found];
}

function blockedTerms(text: string): string[] {
  return [...new Set([...text.matchAll(BLOCKED_RE)].map(m => m[1].toLowerCase()))].sort();
}

function words(text: string): string[] {
  return (text.toLowerCase().match(/[a-z]+/g) ?? []).map(w => (w.length > 3 && w.endsWith('s') ? w.slice(0, -1) : w));
}

function hash(text: string): number {
  let h = 0;
  for (const ch of text) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return h;
}

// Pick the sample whose keywords best match the request. With no match, pick
// one deterministically from the topic text so the same request is stable.
function pickSample(topic: string, goal: string): Sample {
  const asked = new Set(words(`${topic} ${goal}`));
  const allowed = SAMPLES.filter(s => !profile.avoidTopics.includes(s.key));
  const pool = allowed.length > 0 ? allowed : SAMPLES;
  const scored = pool.map(s => ({ s, score: s.keywords.filter(k => asked.has(words(k)[0])).length }));
  const best = Math.max(...scored.map(x => x.score));
  if (best > 0) return scored.find(x => x.score === best)!.s;
  return pool[hash(topic.toLowerCase()) % pool.length];
}

// The server measures each draft and retries once if it reads above target.
// Here every topic has three pre-measured drafts, so take the closest fit.
function pickVersion(sample: Sample): SampleVersion {
  return Object.values(sample.versions).reduce((best, v) =>
    Math.abs(v.measured_level - profile.targetLevel) < Math.abs(best.measured_level - profile.targetLevel) ? v : best,
  );
}

// Port of adjust_level() in storytailor/personalization.py.
function adjustLevel(current: number, recent: Difficulty[]): number {
  if (recent.length === 0) return current;
  const hard = recent.filter(v => v === 'too_hard').length;
  const easy = recent.filter(v => v === 'too_easy').length;
  let level = current;
  if (hard > easy && hard * 2 >= recent.length) level -= LEVEL_STEP;
  else if (easy > hard && easy * 2 >= recent.length) level += LEVEL_STEP;
  return Math.max(LEVEL_MIN, Math.min(LEVEL_MAX, level));
}

// Port of recommend() in storytailor/books.py.
function recommend(k = 5) {
  const target = profile.targetLevel;
  const interests = new Set(profile.interests);
  const unread = BOOKS.filter(b => !alreadyRead.has(b.id));
  let band: CatalogBook[] = [];
  for (const widen of [0, 50, 100, 200]) {
    const lo = target - BAND_BELOW - widen;
    const hi = target + BAND_ABOVE + widen;
    band = unread.filter(b => b.lexile >= lo && b.lexile <= hi);
    if (band.length >= k) break;
  }
  const overlap = (b: CatalogBook) => b.tags.filter(t => interests.has(t)).length;
  return [...band]
    .sort((a, b) =>
      overlap(b) - overlap(a)
      || Math.abs(a.lexile - target) - Math.abs(b.lexile - target)
      || (a.title < b.title ? -1 : a.title > b.title ? 1 : 0))
    .slice(0, k)
    .map(b => ({
      ...b,
      interest_matches: b.tags.filter(t => interests.has(t)).sort(),
      lexile_difference: b.lexile - target,
    }));
}

function createStory(body: { topic?: string; learning_goal?: string }) {
  const [topic, topicPii] = redact(String(body.topic ?? '').trim().slice(0, 120));
  const [goal, goalPii] = redact(String(body.learning_goal ?? '').trim().slice(0, 120));
  if (!topic) throw new DemoApiError('topic is required.');
  const hits = blockedTerms(`${topic} ${goal}`);
  if (hits.length > 0) throw new DemoApiError(`Topic not allowed for this classroom: ${hits.join(', ')}`);

  const sample = pickSample(topic, goal);
  const version = pickVersion(sample);
  const id = nextStoryId++;
  stories.set(id, { id, topic, sampleKey: sample.key });
  return {
    id,
    topic,
    text: version.text,
    target_level: profile.targetLevel,
    measured_level: version.measured_level,
    sources: sample.sources.map(sid => ({ id: sid, source: SOURCE_LABELS.get(sid) ?? 'curated' })),
    attempts: 1,
    redacted: [...new Set([...topicPii, ...goalPii])].sort(),
  };
}

function storyFeedback(storyId: number, body: { difficulty?: Difficulty; flag?: string }) {
  const story = stories.get(storyId);
  if (!story) throw new DemoApiError('Story not found.');
  if (body.difficulty) {
    votes.unshift(body.difficulty);
    allVotes.push(body.difficulty);
    votes.length = Math.min(votes.length, RECENT_VOTES);
  }
  if (body.flag === 'inappropriate' && !profile.avoidTopics.includes(story.sampleKey)) {
    profile.avoidTopics.push(story.sampleKey);
  }
  profile.targetLevel = adjustLevel(profile.targetLevel, votes);
  return { ok: true, target_level: profile.targetLevel };
}

function logBook(body: { book_id?: string }) {
  if (!BOOKS.some(b => b.id === body.book_id)) throw new DemoApiError('Unknown book_id.');
  alreadyRead.add(body.book_id!);
  return { ok: true };
}

function readerState(): ReaderState {
  return {
    targetLevel: profile.targetLevel,
    interests: profile.interests,
    recentVotes: [...votes],
    allVotes: [...allVotes],
    stories: stories.size,
    booksRead: alreadyRead.size,
  };
}

// The demo has one fictional classroom (id 1). Any non-empty teacher token works.
function teacherRequest(path: string, token: string) {
  if (!token.trim()) throw new DemoApiError('Missing or invalid teacher token.');
  const m = path.match(/^\/api\/classrooms\/(\d+)\/(students|feedback-summary)$/);
  if (!m) throw new DemoApiError('This action is not available in the demo.');
  if (m[1] !== '1') throw new DemoApiError('Classroom not found.');
  return m[2] === 'students' ? demoRoster(readerState()) : { classroom: DEMO_CLASS_NAME, ...demoSummary(readerState()) };
}

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function demoTeacherApi(path: string, token: string): Promise<unknown> {
  await delay(250);
  return teacherRequest(path, token);
}

export async function demoApi(path: string, code: string, body?: unknown): Promise<unknown> {
  if (code.length !== 8) throw new DemoApiError('Missing or unknown access code.');
  const data = (body ?? {}) as Record<string, never>;

  if (path === '/api/stories' && body !== undefined) {
    // Give the reader a moment of "writing" so the flow feels like the real app.
    await delay(900);
    return createStory(data);
  }
  const feedback = path.match(/^\/api\/stories\/(\d+)\/feedback$/);
  if (feedback) {
    await delay(150);
    return storyFeedback(Number(feedback[1]), data);
  }
  if (path === '/api/books/recommendations') {
    await delay(200);
    return {
      target_level: profile.targetLevel,
      band: [profile.targetLevel - BAND_BELOW, profile.targetLevel + BAND_ABOVE],
      books: recommend(),
    };
  }
  if (path === '/api/books/log') {
    await delay(150);
    return logBook(data);
  }
  throw new DemoApiError('This action is not available in the demo.');
}
