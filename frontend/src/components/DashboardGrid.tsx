import { Thermometer, Droplets, MapPin, ChevronRight } from 'lucide-react';
import type { HeatSeverity } from '../types';

interface DashboardGridProps {
  events: any[];
  selectedWardId: string;
  onSelectWard: (wardId: string) => void;
}

export const DashboardGrid = ({
  events,
  selectedWardId,
  onSelectWard,
}: DashboardGridProps) => {
  const getBadgeClass = (severity: HeatSeverity) => {
    switch (severity) {
      case 'CRITICAL': return 'badge-critical';
      case 'HIGH': return 'badge-high';
      case 'MODERATE': return 'badge-moderate';
      default: return 'badge-low';
    }
  };

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f172a' }}>
          <MapPin size={18} color="#dc2626" />
          <span>Active City Wards</span>
        </h2>
        <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Select a ward to view response details</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {events.map((item) => {
          const ev = item.event;
          const isSelected = ev.ward_id === selectedWardId;
          const badgeClass = getBadgeClass(ev.severity);

          return (
            <div
              key={ev.event_id}
              className="glass-panel"
              onClick={() => onSelectWard(ev.ward_id)}
              style={{
                cursor: 'pointer',
                borderColor: isSelected ? '#dc2626' : 'var(--border-subtle)',
                background: isSelected ? '#ffffff' : '#f8fafc',
                boxShadow: isSelected ? '0 4px 12px rgba(220, 38, 38, 0.12)' : 'none',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              {isSelected && (
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: '3px',
                  background: '#dc2626'
                }} />
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.15rem' }}>{item.ward_name}</h3>
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>ID: {ev.ward_id}</span>
                </div>
                <span className={badgeClass} style={{
                  padding: '0.2rem 0.55rem',
                  borderRadius: '10px',
                  fontSize: '0.72rem',
                }}>
                  {ev.severity}
                </span>
              </div>

              {/* Main metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', background: '#ffffff', border: '1px solid #e2e8f0', padding: '0.65rem', borderRadius: '8px', marginBottom: '0.75rem' }}>
                <div>
                  <span style={{ fontSize: '0.7rem', color: '#64748b', display: 'block' }}>Temp</span>
                  <strong style={{ fontSize: '1.05rem', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '0.15rem' }}>
                    <Thermometer size={14} />
                    {ev.temperature}°C
                  </strong>
                </div>
                <div>
                  <span style={{ fontSize: '0.7rem', color: '#64748b', display: 'block' }}>Humidity</span>
                  <strong style={{ fontSize: '1.05rem', color: '#0284c7', display: 'flex', alignItems: 'center', gap: '0.15rem' }}>
                    <Droplets size={14} />
                    {ev.humidity}%
                  </strong>
                </div>
                <div>
                  <span style={{ fontSize: '0.7rem', color: '#64748b', display: 'block' }}>Heat Index</span>
                  <strong style={{ fontSize: '1.05rem', color: '#d97706' }}>
                    {ev.heat_index}°C
                  </strong>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: '#475569' }}>
                <span>Duration: {ev.duration} hours</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: isSelected ? '#dc2626' : '#64748b', fontWeight: 600 }}>
                  View Ward <ChevronRight size={14} />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
