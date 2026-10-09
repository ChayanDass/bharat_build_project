import { Flame, ShieldAlert, Cpu, Layers, RotateCcw } from 'lucide-react';

interface HeaderProps {
  environment: string;
  llmProvider: string;
  activeCriticalCount: number;
  onOpenArchModal: () => void;
  onResetDemo: () => void;
}

export const Header = ({
  environment,
  llmProvider,
  activeCriticalCount,
  onOpenArchModal,
  onResetDemo,
}: HeaderProps) => {
  return (
    <header className="glass-panel" style={{ marginBottom: '1.5rem', borderRadius: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            background: '#dc2626',
            padding: '0.5rem',
            borderRadius: '10px',
            display: 'flex',
            color: '#ffffff'
          }}>
            <Flame size={24} />
          </div>
          <div>
            <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.4rem', fontWeight: 800, color: '#0f172a' }}>
              HeatOps — Heatwave Response System
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem', fontWeight: 500 }}>
              City Heatwave Monitoring & Action Coordination
            </p>
          </div>
        </div>

        {/* System Meta Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Active Alert Banner */}
          <div className="badge-critical" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.4rem 0.8rem',
            borderRadius: '16px',
            fontSize: '0.8rem'
          }}>
            <span className="pulse-dot"></span>
            <ShieldAlert size={15} />
            <span>{activeCriticalCount} Critical Ward Alert</span>
          </div>

          {/* Environment Pill */}
          <div style={{
            background: '#f1f5f9',
            border: '1px solid #e2e8f0',
            padding: '0.4rem 0.75rem',
            borderRadius: '16px',
            fontSize: '0.78rem',
            color: '#475569',
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem'
          }}>
            <Cpu size={14} color="#0284c7" />
            <span>ENV: <strong>{environment.toUpperCase()}</strong></span>
            <span style={{ opacity: 0.3 }}>|</span>
            <span>LLM: <strong style={{ color: '#0284c7' }}>{llmProvider.toUpperCase()}</strong></span>
          </div>

          {/* Reset Demo Button */}
          <button
            className="btn-secondary"
            onClick={onResetDemo}
            title="Reset database to clean initial demo state (0 tasks)"
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <RotateCcw size={14} color="#dc2626" />
            <span>Reset Demo Data</span>
          </button>

          {/* Architecture Modal Button */}
          <button className="btn-secondary" onClick={onOpenArchModal} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Layers size={14} color="#d97706" />
            <span>Architecture Blueprint</span>
          </button>
        </div>
      </div>
    </header>
  );
};
