import { useRef, useState, type KeyboardEvent } from 'react';
import StudentView from './StudentView';
import TeacherView from './TeacherView';
import { DEMO_CLASSROOM_ID, DEMO_TEACHER_TOKEN, IS_DEMO } from './demo/constants';

type View = 'student' | 'teacher';
const VIEWS: { id: View; label: string }[] = [
  { id: 'student', label: 'Student' },
  { id: 'teacher', label: 'Teacher' },
];

// Must match DEMO_READER_ID in demo/teacherData.ts (kept here so the normal
// build does not import demo code).
const DEMO_READER_ID = 'stu_demo_reader';

function Wordmark() {
  return (
    <span className="flex items-center gap-2 text-lg font-bold tracking-tight text-ink">
      <svg viewBox="0 0 24 24" className="h-6 w-6 text-accent" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round">
        <path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5Z" />
        <path d="M12 6.5v13" />
      </svg>
      StoryTailor
    </span>
  );
}

function App() {
  const [view, setView] = useState<View>('student');
  const [teacherToken, setTeacherToken] = useState(IS_DEMO ? DEMO_TEACHER_TOKEN : '');
  const [classroomId, setClassroomId] = useState(IS_DEMO ? DEMO_CLASSROOM_ID : '');
  const tabs = useRef<Record<View, HTMLButtonElement | null>>({ student: null, teacher: null });

  // Arrow keys move between tabs (WAI-ARIA tabs pattern, automatic activation).
  const onTabKey = (e: KeyboardEvent) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
    e.preventDefault();
    const i = VIEWS.findIndex(v => v.id === view);
    const next = e.key === 'Home' ? 0 : e.key === 'End' ? VIEWS.length - 1
      : (i + (e.key === 'ArrowRight' ? 1 : VIEWS.length - 1)) % VIEWS.length;
    setView(VIEWS[next].id);
    tabs.current[VIEWS[next].id]?.focus();
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-rule bg-sheet">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Wordmark />
          <div role="tablist" aria-label="Choose a view" className="flex" onKeyDown={onTabKey}>
            {VIEWS.map(v => (
              <button
                key={v.id}
                ref={el => { tabs.current[v.id] = el; }}
                id={`tab-${v.id}`}
                role="tab"
                type="button"
                aria-selected={view === v.id}
                aria-controls={`panel-${v.id}`}
                tabIndex={view === v.id ? 0 : -1}
                onClick={() => setView(v.id)}
                className={`-mb-px border-b-2 px-3 py-4 text-sm font-bold sm:px-4 ${view === v.id ? 'border-accent text-accent' : 'border-transparent text-ink-muted hover:text-ink'}`}
              >
                {v.label}
              </button>
            ))}
          </div>
        </div>
      </header>
      {IS_DEMO && (
        <p role="note" className="mx-auto w-full max-w-6xl px-4 pt-3 text-xs text-ink-muted sm:px-6">
          Demo: sample stories and fictional students. Nothing you type leaves your browser.
        </p>
      )}

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
        {/* The student panel stays mounted so a story in progress survives a tab switch. */}
        <div id="panel-student" role="tabpanel" aria-labelledby="tab-student" hidden={view !== 'student'}>
          <StudentView />
        </div>
        {view === 'teacher' && (
          <div id="panel-teacher" role="tabpanel" aria-labelledby="tab-teacher">
            <TeacherView
              token={teacherToken}
              classroomId={classroomId}
              onCredentials={(t, c) => { setTeacherToken(t); setClassroomId(c); }}
              readerId={IS_DEMO ? DEMO_READER_ID : undefined}
            />
          </div>
        )}
      </main>
      <footer className="border-t border-rule px-4 py-5 text-center text-xs text-ink-muted">StoryTailor · open source, MIT licensed</footer>
    </div>
  );
}

export default App;
