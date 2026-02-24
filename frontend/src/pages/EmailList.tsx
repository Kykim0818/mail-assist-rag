import { useState, useEffect } from 'react';
import api from '../api/client';

// Type definitions
interface Email {
  id: number;
  body: string;
  sender: string;
  subject: string;
  category: string;
  summary: string;
  created_at: string;
}

interface Category {
  id: number;
  name: string;
  description: string;
}

const EmailList = () => {
  // State variables
  const [emails, setEmails] = useState<Email[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);

  // Fetch categories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await api.get<Category[]>('/categories');
        setCategories(response.data);
      } catch (error) {
        console.error('Failed to fetch categories:', error);
      }
    };
    fetchCategories();
  }, []);

  // Fetch emails when category changes
  useEffect(() => {
    const fetchEmails = async () => {
      setLoading(true);
      try {
        const url = selectedCategory 
          ? `/emails?category=${encodeURIComponent(selectedCategory)}` 
          : '/emails';
        const response = await api.get<Email[]>(url);
        setEmails(response.data);
      } catch (error) {
        console.error('Failed to fetch emails:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchEmails();
  }, [selectedCategory]);

  // Helper to format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Helper to get category color
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'HR/인사': return 'bg-green-100 text-green-700 border-green-200';
      case '프로젝트': return 'bg-blue-100 text-blue-700 border-blue-200';
      case '일정': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case '공지사항': return 'bg-red-100 text-red-700 border-red-200';
      case '뉴스레터': return 'bg-purple-100 text-purple-700 border-purple-200';
      default: return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-slate-800 mb-2 tracking-tight">메일 목록</h2>
          <p className="text-slate-500">저장된 중요 메일을 한눈에 확인하세요.</p>
        </div>
        
        <div className="w-full md:w-64">
          <select 
            value={selectedCategory} 
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full p-2.5 bg-white border border-slate-300 text-slate-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block shadow-sm"
          >
            <option value="">전체 카테고리</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.name}>{cat.name}</option>
            ))}
          </select>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto pr-2">
        {loading ? (
          // Loading Skeletons
          <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 animate-pulse h-48">
                <div className="h-6 bg-slate-200 rounded w-3/4 mb-4"></div>
                <div className="h-4 bg-slate-200 rounded w-1/2 mb-6"></div>
                <div className="h-20 bg-slate-200 rounded w-full"></div>
              </div>
            ))}
          </div>
        ) : emails.length === 0 ? (
          // Empty State
          <div className="flex flex-col items-center justify-center h-64 text-slate-400 bg-slate-50/50 rounded-2xl border-2 border-dashed border-slate-200">
            <span className="text-6xl mb-4">📭</span>
            <p className="text-lg font-medium">저장된 메일이 없습니다</p>
            <p className="text-sm">새로운 메일을 분석하여 추가해보세요.</p>
          </div>
        ) : (
          // Email Grid
          <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 pb-8">
            {emails.map((email) => (
              <div 
                key={email.id} 
                onClick={() => setSelectedEmail(email)}
                className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 hover:shadow-md hover:border-blue-200 hover:-translate-y-1 transition-all cursor-pointer group flex flex-col h-full"
              >
                <div className="flex justify-between items-start mb-3 gap-2">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getCategoryColor(email.category)}`}>
                    {email.category}
                  </span>
                  <span className="text-xs text-slate-400 whitespace-nowrap pt-1">
                    {formatDate(email.created_at).split(' ')[0]}
                  </span>
                </div>
                
                <h3 className="font-bold text-lg text-slate-800 mb-1 group-hover:text-blue-600 transition-colors line-clamp-1">
                  {email.subject || "제목 없음"}
                </h3>
                
                <p className="text-sm text-slate-500 mb-4 font-medium flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
                  {email.sender}
                </p>
                
                <div className="mt-auto">
                  <p className="text-slate-600 text-sm line-clamp-3 bg-slate-50 p-3 rounded-lg border border-slate-100 group-hover:bg-blue-50/30 group-hover:border-blue-100 transition-colors">
                    {email.summary || email.body.substring(0, 100)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedEmail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm" onClick={() => setSelectedEmail(null)}>
          <div 
            className="bg-white w-full max-w-2xl max-h-[85vh] rounded-2xl shadow-2xl overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-100 flex justify-between items-start bg-slate-50/50">
              <div className="pr-8">
                <div className="flex items-center gap-3 mb-3">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getCategoryColor(selectedEmail.category)}`}>
                    {selectedEmail.category}
                  </span>
                  <span className="text-sm text-slate-500">
                    {formatDate(selectedEmail.created_at)}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-slate-800 leading-snug">
                  {selectedEmail.subject || "제목 없음"}
                </h2>
                <div className="mt-2 text-sm text-slate-600 font-medium">
                  보낸사람: <span className="text-slate-900">{selectedEmail.sender}</span>
                </div>
              </div>
              <button 
                onClick={() => setSelectedEmail(null)}
                className="text-slate-400 hover:text-slate-600 p-2 hover:bg-slate-100 rounded-full transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto custom-scrollbar">
              <div className="mb-8">
                <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <span className="text-lg">📝</span> 요약 내용
                </h4>
                <div className="bg-blue-50/50 p-5 rounded-xl border border-blue-100 text-slate-700 leading-relaxed shadow-sm">
                  {selectedEmail.summary}
                </div>
              </div>

              <div>
                <details className="group">
                  <summary className="flex items-center gap-2 cursor-pointer text-sm font-medium text-slate-500 hover:text-blue-600 transition-colors select-none">
                    <span className="group-open:rotate-90 transition-transform duration-200">▶</span>
                    원문 보기
                  </summary>
                  <div className="mt-3 p-4 bg-slate-50 rounded-xl border border-slate-200 text-sm text-slate-600 whitespace-pre-wrap font-mono leading-relaxed overflow-x-auto">
                    {selectedEmail.body}
                  </div>
                </details>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
              <button 
                onClick={() => setSelectedEmail(null)}
                className="px-5 py-2.5 bg-white border border-slate-300 text-slate-700 font-medium rounded-lg hover:bg-slate-50 hover:border-slate-400 transition-all shadow-sm"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmailList;
