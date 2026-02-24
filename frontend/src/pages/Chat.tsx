import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent, ChangeEvent } from 'react';
import api from '../api/client';

type Source = {
  email_id: number;
  sender: string;
  subject: string;
  summary: string;
};

type Message = {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
};

type ChatResponse = {
  answer: string;
  source_ids: number[];
  sources: Source[];
};

const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();
    const newMessages: Message[] = [
      ...messages,
      { role: 'user', content: question },
    ];

    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      // Build chat history for API (exclude sources, keep only role and content)
      const chatHistory = messages.map(({ role, content }) => ({ role, content }));
      
      const response = await api.post<ChatResponse>('/chat', {
        question,
        chat_history: chatHistory,
      });

      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: response.data.answer,
          sources: response.data.sources,
        },
      ]);
    } catch (error) {
      console.error('Chat API Error:', error);
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: '죄송합니다. 답변을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleExampleClick = (example: string) => {
    setInput(example);
    // Optional: auto-send or just set input
    // Let's just set input to let user confirm
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
      {/* Header */}
      <header className="p-6 border-b border-slate-50 bg-slate-50/50 flex-none">
        <h2 className="text-xl font-bold text-slate-800">Q&A 채팅</h2>
        <p className="text-sm text-slate-500">메일 내용에 대해 자유롭게 질문하세요</p>
      </header>

      {/* Messages Area */}
      <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-slate-50/30">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-6 opacity-80">
            <div className="text-6xl mb-2">💬</div>
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-slate-700">무엇이 궁금하신가요?</h3>
              <p className="text-slate-500">저장된 메일을 기반으로 답변해드립니다.</p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 max-w-lg">
              {['최근 프로젝트 마감일이 언제야?', 'HR 관련 메일 요약해줘', '김철수님이 보낸 파일 찾아줘'].map((ex) => (
                <button
                  key={ex}
                  onClick={() => handleExampleClick(ex)}
                  className="px-4 py-2 bg-white border border-slate-200 rounded-full text-sm text-slate-600 hover:border-slate-400 hover:text-slate-800 transition-colors shadow-sm"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${
                  msg.role === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-2xl shadow-sm whitespace-pre-wrap leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-slate-800 text-white rounded-tr-none shadow-slate-200'
                      : 'bg-white border border-slate-100 text-slate-800 rounded-tl-none'
                  }`}
                >
                  {msg.content}
                </div>
                
                {/* Sources Section */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 ml-1 space-y-2 max-w-[80%]">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1">참고한 메일</p>
                    <div className="grid gap-2">
                      {msg.sources.map((source) => (
                        <div 
                          key={source.email_id}
                          className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow cursor-default text-left"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-lg">📧</span>
                            <span className="font-medium text-slate-800 text-sm truncate">
                              {source.subject || '(제목 없음)'}
                            </span>
                          </div>
                          <div className="text-xs text-slate-500 pl-7">
                            <span className="font-medium">From:</span> {source.sender || '(발신자 없음)'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-100 p-4 rounded-2xl rounded-tl-none shadow-sm flex items-center space-x-2">
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-100 bg-white flex-none">
        <div className="flex gap-2 relative">
          <input
            type="text"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="질문을 입력하세요..."
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-800/20 focus:border-slate-800 transition-all bg-slate-50 focus:bg-white disabled:bg-slate-50 disabled:text-slate-400"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="bg-slate-800 text-white px-6 py-3 rounded-xl hover:bg-slate-700 active:scale-95 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 shadow-lg shadow-slate-200"
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;
