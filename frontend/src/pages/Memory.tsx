import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';

type Message = {
  id: string;
  role: 'user' | 'ai';
  content: string;
  sources?: { title: string, type: string }[];
};

export default function Memory() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Math.random().toString(),
      role: 'user',
      content: input.trim()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/memory/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: userMessage.content
        })
      });
      
      if (!res.ok) throw new Error("Failed to get answer");
      
      const data = await res.json();
      setConversationId(data.conversation_id);
      
      const aiMessage: Message = {
        id: Math.random().toString(),
        role: 'ai',
        content: data.answer,
        sources: data.sources
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { id: Math.random().toString(), role: 'ai', content: "An error occurred while searching organizational memory." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-8 pb-4 max-w-4xl mx-auto w-full">
        <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">Organizational Memory</h1>
        <p className="text-gray-500 mt-1 text-sm">Ask about what your organization decided, why it decided it, and what happened next.</p>
      </div>

      <div className="flex-1 overflow-y-auto px-8 w-full max-w-4xl mx-auto space-y-6 pb-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-6 border border-blue-100">
              <Bot className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">How can I help?</h2>
            <p className="text-gray-500 max-w-md">I can search through past meetings, extract decisions, and help you understand why certain choices were made.</p>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className="flex flex-col">
              <div className="flex items-start">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-1 ${msg.role === 'ai' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
                  {msg.role === 'ai' ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
                </div>
                <div className="ml-4 flex-1 bg-white p-5 rounded-2xl shadow-sm border border-gray-100 text-gray-800 leading-relaxed text-sm">
                  <div className="font-semibold text-xs uppercase tracking-wider mb-2 text-gray-400">
                    {msg.role === 'ai' ? 'AI Assistant' : 'You'}
                  </div>
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Sources</div>
                      <div className="flex flex-wrap gap-2">
                        {msg.sources.map((src, i) => (
                          <Link key={i} to="/meetings" className="inline-flex items-center px-3 py-1.5 rounded bg-gray-50 border border-gray-200 text-xs font-medium text-gray-700 hover:border-blue-300 hover:bg-blue-50 transition-colors">
                            <FileText className="w-3.5 h-3.5 mr-1.5 text-gray-400" />
                            {src.title}
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        
        {loading && (
          <div className="flex items-start">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center flex-shrink-0 mt-1">
              <Bot className="w-5 h-5" />
            </div>
            <div className="ml-4 bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex items-center">
              <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              <span className="ml-3 text-sm text-gray-500 font-medium">Searching organizational memory...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-8 pt-4 max-w-4xl mx-auto w-full">
        <form onSubmit={handleSend} className="relative">
          <input
            type="text"
            className="w-full pl-5 pr-14 py-4 bg-white border border-gray-300 rounded-xl shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900"
            placeholder="Ask about your organization..."
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-2 top-2 bottom-2 aspect-square flex items-center justify-center rounded-lg bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-50 transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
