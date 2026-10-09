import { Users, Play, Building2, Droplet, HeartPulse, CloudSun } from 'lucide-react';
import type { EventDetailResponse } from '../types';

interface EventDetailViewProps {
  detail: EventDetailResponse | null;
  loading: boolean;
  onTriggerAgent: () => void;
  onSimulateWeather: (scenario: string) => void;
  isTriggering: boolean;
}

export const EventDetailView = ({
  detail,
  loading,
  onTriggerAgent,
  onSimulateWeather,
  isTriggering,
}: EventDetailViewProps) => {
  if (loading) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
        Loading ward information...
      </div>
    );
  }

  if (!detail) return null;

  const { event, ward, vulnerability, resources } = detail;
  const hasPlan = Boolean(detail.action_plan);
  const isWard12 = event.ward_id === 'ward_12';

  return (
    <div className="glass-panel" style={{ marginBottom: '1.5rem', borderRadius: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>
              {ward?.name || event.ward_id}
            </h2>
            <span className={`badge-${event.severity.toLowerCase()}`} style={{ padding: '0.15rem 0.55rem', borderRadius: '8px', fontSize: '0.72rem' }}>
              {event.severity} SEVERITY
            </span>
          </div>
          <p style={{ color: '#64748b', fontSize: '0.8rem', marginTop: '0.15rem' }}>
            City: {ward?.city} | Total Population: {ward?.population?.toLocaleString()}
          </p>
        </div>

        {/* Trigger Agent Workflow Action */}
        <button
          className="btn-primary"
          onClick={onTriggerAgent}
          disabled={isTriggering}
        >
          <Play size={15} />
          <span>{hasPlan ? 'Re-check & Re-plan Response' : 'Trigger Agent Response Workflow'}</span>
        </button>
      </div>

      {isWard12 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.75rem',
          flexWrap: 'wrap',
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '8px',
          padding: '0.65rem 0.8rem',
          marginBottom: '1rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#475569', fontSize: '0.78rem', fontWeight: 700 }}>
            <CloudSun size={15} color="#d97706" />
            Simulate changed afternoon conditions before replanning
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button className="btn-secondary" onClick={() => onSimulateWeather('afternoon_relief')} style={{ fontSize: '0.76rem', padding: '0.42rem 0.7rem' }}>
              Afternoon Relief
            </button>
            <button className="btn-secondary" onClick={() => onSimulateWeather('renewed_heat_spike')} style={{ fontSize: '0.76rem', padding: '0.42rem 0.7rem' }}>
              Renewed Heat Spike
            </button>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))', gap: '1rem' }}>
        {/* Vulnerable Population Card */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.85rem' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#dc2626', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Users size={15} />
            Vulnerable Populations
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem', fontSize: '0.825rem' }}>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.5rem', borderRadius: '6px' }}>
              <span style={{ color: '#64748b', fontSize: '0.72rem', display: 'block' }}>Outdoor Workers</span>
              <strong style={{ fontSize: '1rem', color: '#0f172a' }}>{vulnerability?.outdoor_worker_count?.toLocaleString()}</strong>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.5rem', borderRadius: '6px' }}>
              <span style={{ color: '#64748b', fontSize: '0.72rem', display: 'block' }}>Elderly</span>
              <strong style={{ fontSize: '1rem', color: '#0f172a' }}>{vulnerability?.elderly_count?.toLocaleString()}</strong>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.5rem', borderRadius: '6px' }}>
              <span style={{ color: '#64748b', fontSize: '0.72rem', display: 'block' }}>Children</span>
              <strong style={{ fontSize: '1rem', color: '#0f172a' }}>{vulnerability?.children_count?.toLocaleString()}</strong>
            </div>

            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', padding: '0.5rem', borderRadius: '6px' }}>
              <span style={{ color: '#dc2626', fontSize: '0.72rem', display: 'block', fontWeight: 600 }}>Total At-Risk</span>
              <strong style={{ fontSize: '1rem', color: '#dc2626' }}>{vulnerability?.high_risk_population?.toLocaleString()}</strong>
            </div>
          </div>
        </div>

        {/* Resources Card */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.85rem' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0284c7', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Building2 size={15} />
            Ward Response Resources
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', maxHeight: '140px', overflowY: 'auto' }}>
            {resources.map((r) => (
              <div key={r.resource_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.45rem 0.65rem', borderRadius: '6px', fontSize: '0.78rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  {r.type === 'cooling_centre' && <Building2 size={13} color="#0284c7" />}
                  {r.type === 'water_point' && <Droplet size={13} color="#2563eb" />}
                  {r.type === 'health_centre' && <HeartPulse size={13} color="#db2777" />}
                  <span style={{ fontWeight: 600, color: '#0f172a' }}>{r.name}</span>
                </div>
                <span style={{ color: '#64748b', fontSize: '0.72rem' }}>
                  Cap: {r.availability}/{r.capacity}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
