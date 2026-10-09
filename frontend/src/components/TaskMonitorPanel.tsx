import { useState } from 'react';
import { Activity, Clock, Users } from 'lucide-react';
import type { Task } from '../types';

interface TaskMonitorPanelProps {
  tasks: Task[];
  onAssignTask: (taskId: string, department: string) => Promise<void>;
}

const PENDING_STATUS = {
  label: 'Pending',
  color: '#64748b',
  bg: '#f8fafc',
  border: '#e2e8f0',
  icon: <Clock size={11} />,
};

const PRIORITY_DOT: Record<string, string> = {
  CRITICAL: '#dc2626',
  HIGH: '#ea580c',
  MODERATE: '#d97706',
  LOW: '#16a34a',
};

const DEPARTMENTS = [
  'Water Dept',
  'Health Dept',
  'Labour Dept',
  'Ward Officers',
  'Disaster Management',
  'Community/Volunteer Team',
];

const TaskCard = ({
  task,
  onAssignTask,
}: {
  task: Task;
  onAssignTask: (taskId: string, department: string) => Promise<void>;
}) => {
  const [department, setDepartment] = useState(task.responsible_team);
  const [assigning, setAssigning] = useState(false);
  const [error, setError] = useState('');

  const statusCfg = PENDING_STATUS;
  const dotColor = PRIORITY_DOT[task.priority] || '#64748b';
  return (
    <div style={{
      background: '#ffffff',
      border: '1px solid #e9edf3',
      borderLeft: `3.5px solid ${statusCfg.color}`,
      borderRadius: '10px',
      overflow: 'hidden',
      transition: 'all 0.2s ease',
    }}>
      {/* Main card row */}
      <div style={{ padding: '0.75rem 0.9rem' }}>
        {/* Top: priority dot + title */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.55rem', marginBottom: '0.4rem' }}>
          <span style={{
            width: '8px', height: '8px', borderRadius: '50%',
            background: dotColor, marginTop: '5px', flexShrink: 0,
          }} />
          <p style={{
            flex: 1,
            fontSize: '0.845rem',
            fontWeight: 600,
            color: '#0f172a',
            lineHeight: 1.35,
          }}>
            {task.action}
          </p>
        </div>

        {/* Meta row: status badge + team + deadline */}
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', paddingLeft: '1.3rem', marginBottom: '0.45rem' }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.22rem',
            fontSize: '0.67rem', fontWeight: 700,
            color: statusCfg.color,
            background: statusCfg.bg,
            border: `1px solid ${statusCfg.border}`,
            padding: '0.13rem 0.42rem',
            borderRadius: '5px',
            textTransform: 'uppercase',
            letterSpacing: '0.03em',
          }}>
            {statusCfg.icon}
            {statusCfg.label}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', fontSize: '0.72rem', color: '#64748b' }}>
            <Users size={11} color="#94a3b8" />
            {task.responsible_team}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', fontSize: '0.72rem', color: '#64748b' }}>
            <Clock size={11} color="#94a3b8" />
            {new Date(task.deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        {task.recommendation_reason && (
          <p style={{ margin: '0 0 0.55rem 1.3rem', color: '#64748b', fontSize: '0.73rem', lineHeight: 1.45 }}>
            {task.recommendation_reason}
          </p>
        )}

        {/* Action buttons row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap', paddingLeft: '1.3rem' }}>
          {task.status === 'PENDING' && (
            <>
              <label style={{ fontSize: '0.72rem', color: '#475569' }} htmlFor={`department-${task.task_id}`}>Assign department</label>
              <select
                id={`department-${task.task_id}`}
                value={department}
                onChange={(event) => setDepartment(event.target.value)}
                style={{ padding: '0.32rem 0.45rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.74rem' }}
              >
                {!DEPARTMENTS.includes(department) && <option value={department}>{department}</option>}
                {DEPARTMENTS.map((name) => <option key={name} value={name}>{name}</option>)}
              </select>
              <button
                className="btn-primary"
                disabled={assigning}
                style={{ fontSize: '0.73rem', padding: '0.28rem 0.65rem' }}
                onClick={async () => {
                  setAssigning(true);
                  setError('');
                  try {
                    await onAssignTask(task.task_id, department);
                  } catch (err) {
                    setError(err instanceof Error ? err.message : 'Could not notify department.');
                  } finally {
                    setAssigning(false);
                  }
                }}
              >
                {assigning ? 'Notifying…' : `Acknowledge & Notify ${department}`}
              </button>
            </>
          )}
        </div>
        {error && <p role="alert" style={{ margin: '0.45rem 0 0 1.3rem', color: '#b91c1c', fontSize: '0.73rem' }}>{error}</p>}
      </div>
    </div>
  );
};


export const TaskMonitorPanel = ({
  tasks,
  onAssignTask,
}: TaskMonitorPanelProps) => {
  const pendingTasks = tasks.filter((task) => task.status === 'PENDING');

  return (
    <div className="glass-panel" style={{ marginBottom: '1.5rem', borderRadius: '14px', padding: '1.4rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '1.05rem',
          fontWeight: 700,
          display: 'flex', alignItems: 'center', gap: '0.45rem',
          color: '#0f172a',
        }}>
          <Activity size={17} color="#0284c7" />
          Live Task Tracker
        </h2>
        {pendingTasks.length > 0 && (
          <span style={{
            fontSize: '0.72rem', fontWeight: 600, color: '#64748b',
            background: '#f1f5f9', border: '1px solid #e2e8f0',
            padding: '0.2rem 0.6rem', borderRadius: '20px',
          }}>
            {pendingTasks.length} awaiting acknowledgement
          </span>
        )}
      </div>

      {/* Empty state */}
      {pendingTasks.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '2.5rem 1rem', color: '#94a3b8',
          fontSize: '0.85rem', background: '#f8fafc',
          borderRadius: '10px', border: '1px dashed #e2e8f0',
        }}>
          <Activity size={28} color="#cbd5e1" style={{ marginBottom: '0.6rem' }} />
          <p style={{ fontWeight: 500, color: '#64748b' }}>No tasks awaiting acknowledgement</p>
          <p style={{ fontSize: '0.78rem', marginTop: '0.25rem' }}>New recommendations appear here until the central operator notifies a department.</p>
        </div>
      ) : (
        <>
          <p style={{ color: '#64748b', fontSize: '0.77rem', margin: '0 0 0.75rem' }}>
            Acknowledge an action to notify its department. It then moves to the Response Action Plan and that department's inbox.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
            {pendingTasks.map((task) => (
              <TaskCard
                key={task.task_id}
                task={task}
                onAssignTask={onAssignTask}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
};
