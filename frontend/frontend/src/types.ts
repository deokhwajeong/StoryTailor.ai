// Wire types shared by the student and teacher views. They mirror the JSON the
// Flask API returns (storytailor/routes/), and the demo mock returns the same shapes.

export type Difficulty = 'too_easy' | 'just_right' | 'too_hard';

export interface Source {
  id: string;
  source: string;
}

export interface Story {
  id: number;
  topic: string;
  text: string;
  target_level: number;
  measured_level: number;
  sources: Source[];
  redacted: string[];
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
}

// GET /api/classrooms/<id>/feedback-summary (fields the teacher view uses)
export interface TeacherSummary {
  needs_attention: AttentionItem[];
  difficulty: Record<Difficulty, number>;
  levels: { avg_target: number | null; min_target: number | null; max_target: number | null };
  reading: { sessions: number; minutes: number; readers: number; average_rating: number | null };
}
