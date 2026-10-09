import { X, Server, Cpu, Cloud, CheckCircle2 } from 'lucide-react';

interface ArchitectureModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ArchitectureModal = ({ isOpen, onClose }: ArchitectureModalProps) => {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(15, 23, 42, 0.65)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem'
    }}>
      <div style={{
        background: '#ffffff',
        border: '1px solid #cbd5e1',
        borderRadius: '16px',
        maxWidth: '820px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        padding: '1.5rem',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cloud size={22} color="#0284c7" />
            <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>
              HeatOps Architecture Blueprint
            </h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <p style={{ color: '#475569', fontSize: '0.85rem', marginBottom: '1.15rem', lineHeight: 1.45 }}>
          HeatOps uses a <strong>Single-Build Zero-Rewrite Architecture</strong>. Domain logic and tool contracts remain 100% identical between local development and AWS production.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
          {/* Local Development Column */}
          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '0.9rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#d97706', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Cpu size={16} />
              Local Development Stack
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.8rem', color: '#334155' }}>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                🖥️ <strong>Frontend:</strong> React + Vite TypeScript
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                ⚡ <strong>API Runtime:</strong> FastAPI (Uvicorn)
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                🧠 <strong>Orchestrator:</strong> Strands Agents SDK
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                🤖 <strong>LLM Provider:</strong> Google Gemini API
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                💾 <strong>Database:</strong> SQLite Repository
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                ⏱️ <strong>Scheduler & Alerts:</strong> Local + Console Provider
              </div>
            </div>
          </div>

          {/* AWS Production Column */}
          <div style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '10px', padding: '0.9rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0284c7', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Server size={16} />
              AWS Production Target Stack
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.8rem', color: '#0369a1' }}>
              <div style={{ background: '#ffffff', border: '1px solid #bae6fd', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                🌐 <strong>Frontend:</strong> React + S3 + CloudFront
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #bae6fd', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                ☁️ <strong>API & Runtime:</strong> API Gateway + AWS Lambda
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #bae6fd', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                🧠 <strong>Orchestrator:</strong> Strands Agents SDK
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #bae6fd', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                🤖 <strong>LLM Provider:</strong> Amazon Bedrock
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #bae6fd', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                🗄️ <strong>Database:</strong> Amazon DynamoDB
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #bae6fd', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                📡 <strong>Scheduler & Alerts:</strong> AWS EventBridge + SNS
              </div>
            </div>
          </div>
        </div>

        {/* Contract stability notice */}
        <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '0.75rem 0.85rem', borderRadius: '8px', fontSize: '0.8rem', color: '#166534', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <CheckCircle2 size={16} color="#16a34a" />
          <span>Zero-Rewrite Guarantee: Business logic, 8 logical tools, and domain models remain identical across environments.</span>
        </div>
      </div>
    </div>
  );
};
