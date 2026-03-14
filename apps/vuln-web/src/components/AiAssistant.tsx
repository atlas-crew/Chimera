import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Bot, Minimize2, Paperclip, Globe } from 'lucide-react';
import { API_BASE_URL } from '../lib/config';
import { detectPotentialAttack, dispatchAttackLog } from '../lib/security';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const AiAssistant: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I am the Portal Support AI. How can I assist you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [urlMode, setUrlMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: `Uploading file: ${file.name}` }]);

    dispatchAttackLog('FileUpload', `${API_BASE_URL}/api/v1/genai/knowledge/upload`, `filename=${file.name}`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/genai/knowledge/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
      
      const data = await res.json();
      
      let responseText = `File uploaded successfully. Doc ID: ${data.doc_id}`;
      if (data.warning) {
        responseText += `\n\nWARNING: ${data.warning}`;
        dispatchAttackLog('FileUpload', `${API_BASE_URL}/api/v1/genai/knowledge/upload`, `filename=${file.name} [VULN TRIGGERED]`, 'allowed');
      }
      if (data.vulnerability) {
        responseText += `\n\n[System Alert]: ${data.vulnerability}`;
      }
      
      setMessages(prev => [...prev, { role: 'assistant', content: responseText }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error uploading file.' }]);
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleBrowse = async (url: string) => {
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: `Browsing: ${url}` }]);

    dispatchAttackLog('SSRF', `${API_BASE_URL}/api/v1/genai/agent/browse`, `url=${url}`);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/genai/agent/browse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      
      if (!res.ok) throw new Error(`Browse failed: ${res.status}`);
      
      const data = await res.json();
      
      let responseText = data.content || data.summary || 'Content retrieved.';
      if (data.vulnerability) {
        responseText += `\n\n[System Alert]: ${data.vulnerability}`;
        dispatchAttackLog('SSRF', `${API_BASE_URL}/api/v1/genai/agent/browse`, `url=${url} [VULN TRIGGERED]`, 'allowed');
      }

      setMessages(prev => [...prev, { role: 'assistant', content: responseText }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error browsing URL.' }]);
    } finally {
      setLoading(false);
      setUrlMode(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    if (urlMode) {
      handleBrowse(input);
      setInput('');
      return;
    }

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    // Detect potential injection attempts for logging using the new security utility
    const isPotentialAttack = detectPotentialAttack(userMsg);
    dispatchAttackLog('GenAI', `${API_BASE_URL}/api/v1/genai/chat`, userMsg, isPotentialAttack ? 'blocked' : 'allowed');

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/genai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      const data = await res.json();
      
      let responseText = data.response;
      if (data.warning) {
        responseText += `\n\n[Security Warning]: ${data.warning}`;
      }
      if (data.vulnerability) {
        responseText += `\n\n[Vulnerability Detected]: ${data.vulnerability}`;
        dispatchAttackLog('GenAI', `${API_BASE_URL}/api/v1/genai/chat`, userMsg + ' [VULN TRIGGERED]', 'allowed');
      }

      setMessages(prev => [...prev, { role: 'assistant', content: responseText }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I am having trouble connecting to the mainframe.' }]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || isMinimized) {
    return (
      <button
        onClick={() => {
          setIsOpen(true);
          setIsMinimized(false);
        }}
        aria-label="Open AI Support Chat"
        className="fixed bottom-6 right-6 p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg transition-all hover:scale-110 z-50 group"
      >
        <MessageSquare className="w-6 h-6" />
        <span className="absolute right-full mr-3 top-1/2 -translate-y-1/2 bg-slate-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          AI Support
        </span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-80 md:w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 flex flex-col overflow-hidden animate-in slide-in-from-bottom-10 fade-in duration-300">
      {/* Header */}
      <div className="p-4 bg-slate-900 text-white flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-blue-500 rounded-lg">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white">Portal Assistant</h3>
            <p className="text-[10px] text-blue-200 flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
              Online
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setIsMinimized(true)} aria-label="Minimize Chat" className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors">
            <Minimize2 className="w-4 h-4" />
          </button>
          <button onClick={() => setIsOpen(false)} aria-label="Close Chat" className="p-1 hover:bg-red-500/20 rounded text-slate-400 hover:text-red-400 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Chat Area */}
      <div className="h-96 overflow-y-auto p-4 bg-slate-50 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl p-3 text-sm ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white rounded-br-none' 
                : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none shadow-sm'
            }`}>
              {msg.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  {/* Basic markdown-like rendering for code blocks */}
                  {msg.content.split('```').map((part, i) => 
                    i % 2 === 1 ? (
                      <pre key={i} className="bg-slate-900 text-slate-100 p-2 rounded mt-2 mb-2 text-xs overflow-x-auto">
                        <code>{part.replace(/^\w+\n/, '')}</code>
                      </pre>
                    ) : (
                      <span key={i} style={{ whiteSpace: 'pre-wrap' }}>{part}</span>
                    )
                  )}
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-none p-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-slate-100">
        <div className="flex gap-1 px-3 pt-2">
           <button 
            type="button" 
            onClick={() => fileInputRef.current?.click()} 
            className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors" 
            title="Upload Knowledge Base (RAG)"
            aria-label="Upload Knowledge Base"
          >
            <Paperclip className="w-4 h-4" />
          </button>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            className="hidden" 
            aria-hidden="true"
          />
          <button 
            type="button" 
            onClick={() => {
              setUrlMode(!urlMode);
              setInput('');
            }}
            className={`p-1.5 rounded transition-colors ${urlMode ? 'text-blue-600 bg-blue-50' : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50'}`}
            title="Browse Web (Agent)"
            aria-label="Toggle URL browsing mode"
            aria-pressed={urlMode}
          >
            <Globe className="w-4 h-4" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-3 pt-1">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={urlMode ? "Enter URL to browse..." : "Ask about system status..."}
              className={`w-full pl-4 pr-10 py-3 bg-slate-50 border rounded-xl text-sm focus:outline-none focus:ring-2 transition-all ${
                urlMode 
                  ? 'border-blue-200 focus:ring-blue-500/20 focus:border-blue-500 placeholder-blue-300' 
                  : 'border-slate-200 focus:ring-slate-500/20 focus:border-slate-500'
              }`}
            />
            <button 
              type="submit" 
              disabled={!input.trim() || loading}
              aria-label={urlMode ? "Browse URL" : "Send Message"}
              className={`absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${
                urlMode ? 'bg-blue-500 hover:bg-blue-600' : 'bg-slate-900 hover:bg-slate-800'
              }`}
            >
              {urlMode ? <Globe className="w-4 h-4" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
          <p className="text-[10px] text-center text-slate-400 mt-2">
            AI responses may be inaccurate or vulnerable.
          </p>
        </form>
      </div>
    </div>
  );
};
