import { useState } from 'react';
import { Bot, Send, Sparkles, MessageSquare } from 'lucide-react';

interface AgentConsoleProps {
  onAskQuestion: (question: string) => Promise<string>;
  wardId: string;
}

const PRESET_QUESTIONS = [
  "Why is Ward 12 critical?",
  "What actions are pending?",
  "Which ward should we prioritize?",
  "Why was the water supply task escalated?",
];

export const AgentConsole = ({ onAskQuestion }: AgentConsoleProps) => {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'agent'; text: string }>>([
    {
      sender: 'agent',
      text: 'Hello. I am the HeatOps AI Agent. I track weather forecasts, risk levels, vulnerable populations, and task status. Ask me any question about the heat response.',
    },
  ]);
  const [isAsking, setIsAsking] = useState(false);

  const handleSend = async (queryText?: string) => {
    const q = queryText || question;
    if (!q.trim() || isAsking) return;

    setMessages((prev) => [...prev, { sender: 'user', text: q }]);
    if (!queryText) setQuestion('');
    setIsAsking(true);

    try {
      const answer = await onAskQuestion(q);
      setMessages((prev) => [...prev, { sender: 'agent', text: answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: 'agent', text: 'Apologies, an error occurred querying system data.' },
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="glass-panel" style={{ marginBottom: '1.5rem', borderRadius: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f172a' }}>
          <Bot size={18} color="#0284c7" />
          <span>Ask HeatOps AI Agent</span>
        </h2>
        <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <Sparkles size={12} color="#0284c7" /> Grounded in Database & Tools
        </span>
      </div>

      {/* Preset Question Chips */}
      <div style={{ display: 'flex', gap: '0.45rem', flexWrap: 'wrap', marginBottom: '0.85rem' }}>
        {PRESET_QUESTIONS.map((pq, idx) => (
          <button
            key={idx}
            className="btn-secondary"
            onClick={() => handleSend(pq)}
            disabled={isAsking}
            style={{ fontSize: '0.78rem', padding: '0.3rem 0.65rem', borderRadius: '14px' }}
          >
            <MessageSquare size={12} style={{ opacity: 0.7 }} />
            <span>{pq}</span>
          </button>
        ))}
      </div>

      {/* Messages Stream */}
      <div style={{
        background: '#f8fafc',
        borderRadius: '8px',
        padding: '0.85rem',
        minHeight: '140px',
        maxHeight: '220px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        marginBottom: '0.85rem',
        border: '1px solid #e2e8f0'
      }}>
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              background: m.sender === 'user' ? '#0284c7' : '#ffffff',
              color: m.sender === 'user' ? '#ffffff' : '#0f172a',
              padding: '0.55rem 0.85rem',
              borderRadius: m.sender === 'user' ? '10px 10px 0 10px' : '10px 10px 10px 0',
              fontSize: '0.825rem',
              lineHeight: 1.4,
              border: m.sender === 'agent' ? '1px solid #e2e8f0' : 'none'
            }}
          >
            {m.text}
          </div>
        ))}
        {isAsking && (
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontStyle: 'italic' }}>
            HeatOps Agent querying database facts...
          </div>
        )}
      </div>

      {/* Question Input Box */}
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask HeatOps agent a question..."
          style={{
            flex: 1,
            background: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            padding: '0.55rem 0.85rem',
            color: '#0f172a',
            fontSize: '0.825rem',
            outline: 'none'
          }}
        />
        <button className="btn-primary" onClick={() => handleSend()} disabled={isAsking} style={{ background: '#0284c7' }}>
          <Send size={14} />
          <span>Ask</span>
        </button>
      </div>
    </div>
  );
};
