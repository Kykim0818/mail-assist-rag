import { useState } from 'react';
import api from '../api/client';

interface EmailResult {
  id: number;
  body: string;
  sender: string | null;
  subject: string | null;
  category: string;
  summary: string;
  created_at: string;
}

const EmailInput = () => {
  const [body, setBody] = useState('');
  const [sender, setSender] = useState('');
  const [subject, setSubject] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EmailResult | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!body.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.post<EmailResult>('/emails', {
        body,
        sender: sender.trim() || undefined,
        subject: subject.trim() || undefined,
      });
      setResult(response.data);
    } catch (err) {
      console.error('Failed to process email:', err);
      setError('메일 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setBody('');
    setSender('');
    setSubject('');
    setResult(null);
    setError(null);
  };

  if (result) {
    return (
      <div className="max-w-3xl mx-auto p-6 space-y-6">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-slate-800">분석 결과</h2>
            <span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-sm font-medium border border-slate-200">
              #{result.category}
            </span>
          </div>

          <div className="space-y-6">
            {result.subject && (
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-1">제목</h3>
                <p className="text-lg text-slate-800 font-medium">{result.subject}</p>
              </div>
            )}

            <div>
              <h3 className="text-sm font-medium text-slate-400 mb-2">요약</h3>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-slate-700 leading-relaxed whitespace-pre-wrap">
                {result.summary}
              </div>
            </div>

            <div className="pt-6 border-t border-slate-100 flex justify-end">
              <button
                onClick={handleReset}
                className="bg-slate-800 text-white px-6 py-3 rounded-xl hover:bg-slate-700 active:bg-slate-900 transition-colors font-medium shadow-md hover:shadow-lg flex items-center gap-2"
              >
                <span>✨</span> 새 메일 입력
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
        <header className="mb-8">
          <h2 className="text-3xl font-bold text-slate-800 mb-2 tracking-tight">메일 입력</h2>
          <p className="text-slate-500">분석하거나 요약할 메일 내용을 입력해주세요.</p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="sender" className="block text-sm font-medium text-slate-700 mb-1">
                보낸 사람 <span className="text-slate-400 font-normal">(선택)</span>
              </label>
              <input
                id="sender"
                type="text"
                value={sender}
                onChange={(e) => setSender(e.target.value)}
                placeholder="홍길동 <hong@example.com>"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-slate-500 focus:ring-2 focus:ring-slate-200 outline-none transition-all placeholder:text-slate-400"
                disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="subject" className="block text-sm font-medium text-slate-700 mb-1">
                제목 <span className="text-slate-400 font-normal">(선택)</span>
              </label>
              <input
                id="subject"
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="프로젝트 진행 상황 공유"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-slate-500 focus:ring-2 focus:ring-slate-200 outline-none transition-all placeholder:text-slate-400"
                disabled={loading}
              />
            </div>
          </div>

          <div>
            <label htmlFor="body" className="block text-sm font-medium text-slate-700 mb-1">
              내용 <span className="text-red-500">*</span>
            </label>
            <textarea
              id="body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="메일 내용을 붙여넣으세요..."
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-slate-500 focus:ring-2 focus:ring-slate-200 outline-none transition-all min-h-[300px] resize-y placeholder:text-slate-400 leading-relaxed"
              required
              disabled={loading}
            />
            <div className="mt-2 flex justify-between text-xs text-slate-400">
              <span>{body.length.toLocaleString()} 자</span>
              {body.length > 50000 && (
                <span className="text-amber-500 font-medium">⚠️ 내용이 너무 깁니다 (50,000자 권장)</span>
              )}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-xl text-sm border border-red-100 flex items-center gap-2">
              <span>⚠️</span>
              {error}
            </div>
          )}

          <div className="flex justify-end pt-4">
            <button
              type="submit"
              disabled={loading || !body.trim()}
              className="bg-slate-800 text-white px-8 py-3.5 rounded-xl hover:bg-slate-700 active:bg-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-md hover:shadow-lg flex items-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>분석 중...</span>
                </>
              ) : (
                <>
                  <span>🔍</span>
                  <span>분석하기</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EmailInput;
