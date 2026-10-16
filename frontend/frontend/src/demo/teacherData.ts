// Teacher view data for the demo build: a fictional grade 3 class plus the demo
// reader from the student tab, summarized with a port of storytailor/insights.py.
//
// Every student here is generated from a fixed seed. Pseudonyms, levels, votes,
// and activity are synthetic and are not results from any classroom.

import type { AttentionReason, Difficulty, RosterStudent, TeacherSummary } from '../types';

// Values copied from storytailor/insights.py and storytailor/personalization.py.
// tests/test_demo_parity.py fails if they drift.
const RECENT_VOTES = 5;
const MIN_VOTES = 2;
const INACTIVE_DAYS = 14;
const BELOW_GRADE_MARGIN = 150;
const GRADE = 3;
const GRADE_START_LEVEL = 600;
const REASONS = ['flagged_story', 'struggling', 'below_grade_level', 'inactive', 'ready_for_more'] as const;

type Reason = AttentionReason;

export const DEMO_CLASS_NAME = 'Demo · Grade 3 · Room 101';
export const DEMO_READER_ID = 'stu_demo_reader';

interface SyntheticStudent extends RosterStudent {
  recent_votes: Difficulty[];
  flags: number;
  minutes: number;
  sessions: number;
}

// mulberry32: tiny seeded PRNG so the class is identical on every load.
function prng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const INTERESTS = ['animals', 'science', 'fantasy', 'humor', 'sports', 'mystery', 'community', 'adventure'];
const DAY_MS = 86_400_000;

function daysAgo(days: number, now: number): string {
  return new Date(now - days * DAY_MS).toISOString().replace(/\.\d{3}Z$/, '+00:00');
}

function syntheticClass(now: number): SyntheticStudent[] {
  const rand = prng(2026);
  const pick = <T,>(xs: T[]) => xs[Math.floor(rand() * xs.length)];
  const students: SyntheticStudent[] = [];
  for (let i = 0; i < 24; i++) {
    const id = 'stu_' + Array.from({ length: 12 }, () => '0123456789abcdef'[Math.floor(rand() * 16)]).join('');
    // Same spread as storytailor/demo.py: grade start level plus or minus 150L, in 10L steps.
    const level = GRADE_START_LEVEL + Math.floor((rand() * 300 - 150) / 10) * 10;
    // Readers further from the middle lean toward one side of the difficulty scale.
    const lean = (level - GRADE_START_LEVEL) / 150;
    const voteCount = Math.floor(rand() * 6);
    const votes: Difficulty[] = Array.from({ length: voteCount }, () => {
      const r = rand() + lean * 0.3;
      return r < 0.16 ? 'too_hard' : r > 0.88 ? 'too_easy' : 'just_right';
    });
    const inactive = rand() < 0.12;
    const sessions = inactive ? Math.floor(rand() * 2) : 1 + Math.floor(rand() * 6);
    students.push({
      id,
      grade: GRADE,
      target_level: level,
      interests: [pick(INTERESTS), pick(INTERESTS)].filter((v, j, a) => a.indexOf(v) === j),
      consent_status: 'school_authorized',
      last_active_at: inactive ? (rand() < 0.5 ? null : daysAgo(15 + Math.floor(rand() * 10), now)) : daysAgo(Math.floor(rand() * 6), now),
      stories: voteCount + Math.floor(rand() * 3),
      recent_votes: votes,
      flags: rand() < 0.06 ? 1 : 0,
      minutes: sessions * (10 + Math.floor(rand() * 15)),
      sessions,
    });
  }
  return students;
}

// Port of attention_reasons() in storytailor/insights.py.
export function attentionReasons(s: { grade: number; target_level: number; recent_votes: Difficulty[]; flags: number; last_active_at: string | null }, now: number): Reason[] {
  const reasons = new Set<Reason>();
  if (s.flags > 0) reasons.add('flagged_story');
  const votes = s.recent_votes.slice(0, RECENT_VOTES);
  if (votes.length >= MIN_VOTES) {
    const hard = votes.filter(v => v === 'too_hard').length;
    const easy = votes.filter(v => v === 'too_easy').length;
    if (hard > easy && hard * 2 >= votes.length) reasons.add('struggling');
    else if (easy > hard && easy * 2 >= votes.length) reasons.add('ready_for_more');
  }
  if (s.grade === GRADE && s.target_level <= GRADE_START_LEVEL - BELOW_GRADE_MARGIN) reasons.add('below_grade_level');
  if (s.last_active_at === null || Date.parse(s.last_active_at) < now - INACTIVE_DAYS * DAY_MS) reasons.add('inactive');
  return REASONS.filter(r => reasons.has(r));
}

export interface ReaderState {
  targetLevel: number;
  interests: string[];
  recentVotes: Difficulty[];
  allVotes: Difficulty[];
  stories: number;
  booksRead: number;
}

// Generated once per page load so "last active" stays relative to today.
const loadedAt = Date.now();
const CLASS = syntheticClass(loadedAt);

function withReader(reader: ReaderState): SyntheticStudent[] {
  return [
    {
      id: DEMO_READER_ID,
      grade: GRADE,
      target_level: reader.targetLevel,
      interests: reader.interests,
      consent_status: 'school_authorized',
      last_active_at: daysAgo(0, loadedAt),
      stories: reader.stories,
      recent_votes: reader.recentVotes,
      flags: 0,
      minutes: reader.booksRead * 15,
      sessions: reader.booksRead,
    },
    ...CLASS,
  ];
}

export function demoRoster(reader: ReaderState): RosterStudent[] {
  return withReader(reader).map(s => ({
    id: s.id,
    grade: s.grade,
    target_level: s.target_level,
    interests: s.interests,
    consent_status: s.consent_status,
    last_active_at: s.last_active_at,
    stories: s.stories,
  }));
}

export function demoSummary(reader: ReaderState): TeacherSummary {
  const students = withReader(reader);
  const levels = students.map(s => s.target_level);
  const difficulty = { too_easy: 0, just_right: 0, too_hard: 0 };
  for (const v of [...CLASS.flatMap(s => s.recent_votes), ...reader.allVotes]) difficulty[v] += 1;
  const needs = students
    .map(s => ({ student_id: s.id, target_level: s.target_level, reasons: attentionReasons(s, loadedAt) }))
    .filter(r => r.reasons.length > 0)
    .sort((a, b) =>
      b.reasons.length - a.reasons.length
      || REASONS.indexOf(a.reasons[0]) - REASONS.indexOf(b.reasons[0])
      || (a.student_id < b.student_id ? -1 : 1));
  const readers = students.filter(s => s.sessions > 0);
  return {
    needs_attention: needs,
    difficulty,
    levels: {
      avg_target: levels.reduce((a, b) => a + b, 0) / levels.length,
      min_target: Math.min(...levels),
      max_target: Math.max(...levels),
    },
    reading: {
      sessions: students.reduce((a, s) => a + s.sessions, 0),
      minutes: students.reduce((a, s) => a + s.minutes, 0),
      readers: readers.length,
      average_rating: null,
    },
  };
}
