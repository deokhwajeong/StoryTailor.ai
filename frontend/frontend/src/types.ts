// Wire types shared by the student and teacher views. They mirror the JSON the
// Flask API returns (storytailor/routes/), and the demo mock returns the same shapes.

export type Difficulty = 'too_easy' | 'just_right' | 'too_hard';

export interface Source {
  id: string;
  source: string;
}

export type LevelFit = 'too_easy' | 'in_band' | 'too_hard';

// "How this story was made": one entry per pipeline step, in the order the
// server ran them. Field names mirror TRACE_FIELDS in storytailor/personalization.py
// (tests/test_demo_parity.py checks each interface below against it).
export interface TraceShelf {
  step: 'shelf';
  status: 'ok' | 'thin';
  band: [number, number];
  titles: number;
  thin_threshold: number;
}

export interface TraceRedaction {
  step: 'redaction';
  status: 'clean' | 'removed';
  kinds: string[];
  topic: string;
  learning_goal: string | null;
}

export interface TraceTopicCheck {
  step: 'topic_check';
  status: 'passed';
  word_list_size: number;
}

export interface TraceGrounding {
  step: 'grounding';
  status: 'found' | 'none';
  facts: Source[];
}

export interface TraceDraft {
  step: 'draft';
  status: 'accepted' | 'rejected';
  attempt: number;
  instruction: 'simplify' | 'enrich' | null;
  measured_level: number;
  fk_grade: number;
  words: number;
  band: [number, number];
  fit: LevelFit;
  excerpt: string;
}

export interface TraceModeration {
  step: 'moderation';
  status: 'passed';
  checks: { name: 'word_list' | 'moderation_service'; result: 'passed' | 'not_run' }[];
}

export interface TraceLibrary {
  step: 'library';
  status: 'found' | 'none';
  band: [number, number];
  books: { id: string; title: string; lexile: number; guided_level: string }[];
}

export type TraceStep = TraceShelf | TraceRedaction | TraceTopicCheck | TraceGrounding | TraceDraft | TraceModeration | TraceLibrary;

export interface Story {
  id: number;
  topic: string;
  text: string;
  target_level: number;
  measured_level: number;
  band: [number, number];
  fit: LevelFit;
  attempts: number;
  sources: Source[];
  redacted: string[];
  trace: TraceStep[];
}

export interface Book {
  id: string;
  title: string;
  lexile: number;
  guided_level: string;
  interest_matches: string[];
}

// GET /api/classrooms/<id>/students
export interface RosterStudent {
  id: string;
  grade: number;
  target_level: number;
  interests: string[];
  consent_status: string;
  last_active_at: string | null;
  stories: number;
}

// Reason codes from storytailor/insights.py, most urgent first.
export type AttentionReason = 'flagged_story' | 'struggling' | 'below_grade_level' | 'inactive' | 'ready_for_more';

export interface AttentionItem {
  student_id: string;
  target_level: number;
  reasons: AttentionReason[];
  // Newest first, at most five (the window the rules look at).
  recent_votes: Difficulty[];
}

// Titles per 100L band in the classroom library, with readers per band
// (books.class_coverage() on the server).
export interface CoverageBand {
  low: number;
  high: number;
  titles: number;
  readers: number;
  thin: boolean;
}

export interface LibraryCoverage {
  band_width: number;
  thin_threshold: number;
  total_titles: number;
  bands: CoverageBand[];
  readers_in_thin_bands: number;
}

// GET /api/classrooms/<id>/feedback-summary (fields the teacher view uses)
export interface TeacherSummary {
  library_coverage: LibraryCoverage;
  needs_attention: AttentionItem[];
  difficulty: Record<Difficulty, number>;
  levels: { avg_target: number | null; min_target: number | null; max_target: number | null };
  reading: { sessions: number; minutes: number; readers: number; average_rating: number | null };
}
