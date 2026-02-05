
import { useState } from 'react';
import { SparklesIcon, BookOpenIcon, InformationCircleIcon } from '@heroicons/react/24/solid';

const API_URL = 'http://localhost:8000/generate_story'; // FastAPI 서버 주소에 맞게 수정

interface StoryData {
  story: string;
  sources: string[];
  fact_checked: boolean;
  confidence_score: number;
  rag_context: string[];
}

function App() {
  const [topic, setTopic] = useState('');
  const [storyData, setStoryData] = useState<StoryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showRagInfo, setShowRagInfo] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setStoryData(null);
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          age: 7, // 샘플값, UI 확장 가능
          preferences: [topic],
          learning_goal: '',
          use_rag: true // RAG 사용 활성화
        })
      });
      if (!res.ok) throw new Error('이야기 생성 실패');
      const data: StoryData = await res.json();
      setStoryData(data);
    } catch (e: unknown) {
      if (e instanceof Error) {
        setError(e.message);
      } else {
        setError('오류 발생');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-100 via-blue-100 to-green-100 flex flex-col items-center justify-center">
      <div className="w-full max-w-md bg-white/80 rounded-3xl shadow-xl p-8 flex flex-col items-center">
        <h1 className="text-3xl font-bold text-pink-400 mb-4 drop-shadow-lg flex items-center gap-2">
          <SparklesIcon className="w-8 h-8 text-yellow-300 animate-bounce" />
          StoryTailor.ai
        </h1>
        <p className="text-lg text-blue-400 mb-8">아동을 위한 AI 동화 생성 플랫폼</p>
        <div className="w-full flex flex-col gap-4">
          <input
            className="rounded-xl border-2 border-pastelPink px-4 py-2 text-lg focus:outline-none focus:ring-2 focus:ring-pastelBlue bg-pink-50 placeholder:text-pastelPurple"
            placeholder="동화에 들어갈 소재를 입력해보세요! (예: 용감한 토끼)"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            disabled={loading}
          />
          <button
            className="flex items-center justify-center gap-2 bg-pastelPink hover:bg-pastelBlue text-white font-bold py-2 px-6 rounded-full shadow-lg transition-all text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleGenerate}
            disabled={loading || !topic.trim()}
          >
            <SparklesIcon className="w-6 h-6 text-yellow-200" />
            {loading ? '생성 중...' : '동화 만들기'}
          </button>
        </div>
        {error && <div className="mt-4 text-red-500">{error}</div>}
        {storyData && (
          <div className="mt-8 w-full flex flex-col items-center">
            <div className="relative w-full max-w-xs bg-pastelYellow rounded-2xl shadow-lg p-6 border-4 border-pastelPink flex flex-col items-center book-effect">
              <BookOpenIcon className="w-10 h-10 text-pastelPurple mb-2" />
              <div className="text-gray-700 whitespace-pre-line text-lg font-sans text-center">
                {storyData.story}
              </div>
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-24 h-2 bg-pastelPink rounded-full opacity-30 blur-sm" />
            </div>
            
            {/* RAG Information Section */}
            <div className="mt-4 w-full max-w-xs">
              <button
                onClick={() => setShowRagInfo(!showRagInfo)}
                className="flex items-center gap-2 text-sm text-blue-500 hover:text-blue-700"
              >
                <InformationCircleIcon className="w-5 h-5" />
                {showRagInfo ? 'RAG 정보 숨기기' : 'RAG 정보 보기'}
              </button>
              
              {showRagInfo && (
                <div className="mt-2 p-3 bg-blue-50 rounded-lg text-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold">신뢰도:</span>
                    <span className={`px-2 py-1 rounded ${
                      storyData.confidence_score >= 0.7 ? 'bg-green-100 text-green-700' :
                      storyData.confidence_score >= 0.5 ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {Math.round(storyData.confidence_score * 100)}%
                    </span>
                  </div>
                  <div className="mb-2">
                    <span className="font-semibold">사실 확인:</span>
                    <span className={`ml-2 ${storyData.fact_checked ? 'text-green-600' : 'text-gray-500'}`}>
                      {storyData.fact_checked ? '✓ 확인됨' : '미확인'}
                    </span>
                  </div>
                  {storyData.sources.length > 0 && (
                    <div className="mb-2">
                      <span className="font-semibold">참고 출처:</span>
                      <ul className="list-disc list-inside ml-2 text-gray-600">
                        {storyData.sources.map((source, idx) => (
                          <li key={idx}>{source}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      <footer className="mt-8 text-xs text-gray-400">© 2026 StoryTailor.ai</footer>
    </div>
  );
}

export default App;
