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
    <div className="flex min-h-screen flex-col items-center bg-gradient-to-br from-pink-100 via-blue-100 to-green-100 px-4 py-6">
      {IS_DEMO && (
        <p role="note" className="mb-3 max-w-md rounded-full border border-gray-300 bg-white/80 px-4 py-1.5 text-center text-xs text-gray-700">
          Demo mode: sample stories and fictional students, no data leaves your browser
        </p>
      )}
      <div role="tablist" aria-label="Choose a view" className="mb-4 flex rounded-full bg-white/80 p-1 shadow" onKeyDown={onTabKey}>
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
            className={`rounded-full px-5 py-1.5 text-sm font-semibold ${view === v.id ? 'bg-pink-700 text-white' : 'text-gray-800 hover:bg-pink-50'}`}
          >
            {v.label}
          </button>
        ))}
      </div>

      <main className="flex w-full justify-center">
        {/* The student panel stays mounted so a story in progress survives a tab switch. */}
        <div id="panel-student" role="tabpanel" aria-labelledby="tab-student" hidden={view !== 'student'} className="flex w-full justify-center">
          <StudentView />
        </div>
        {view === 'teacher' && (
          <div id="panel-teacher" role="tabpanel" aria-labelledby="tab-teacher" className="flex w-full justify-center">
            <TeacherView
              token={teacherToken}
              classroomId={classroomId}
              onCredentials={(t, c) => { setTeacherToken(t); setClassroomId(c); }}
              readerId={IS_DEMO ? DEMO_READER_ID : undefined}
            />
          </div>
        )}
      </main>
      <footer className="mt-8 text-xs text-gray-700">StoryTailor · open source, MIT licensed</footer>
    </div>
  );
}

export default App;
