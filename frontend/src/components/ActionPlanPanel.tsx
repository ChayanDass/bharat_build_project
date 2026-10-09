import { useState } from 'react';
import { ListChecks, Clock, UserCheck, RefreshCw, RotateCcw } from 'lucide-react';
import type { ActionPlan, Task } from '../types';

interface ActionPlanPanelProps {
  plan: ActionPlan | null;
  tasks: Task[];
  onRefreshStatus: (taskId: string) => Promise<void>;
  onRetryTask: (taskId: string) => Promise<void>;
}

export const ActionPlanPanel = ({ plan, tasks, onRefreshStatus, onRetryTask }: ActionPlanPanelProps) => {
  const [refreshingTask, setRefreshingTask] = useState<string | null>(null);
  const [retryingTask, setRetryingTask] = useState<string | null>(null);
  const [taskError, setTaskError] = useState('');
  const assignedTasks = tasks.filter((task) => task.status !== 'PENDING');

  const refresh = async (taskId: string) => {
    setRefreshingTask(taskId);
    setTaskError('');
    try {
      await onRefreshStatus(taskId);
    } catch (cause) {
      setTaskError(cause instanceof Error ? cause.message : 'Could not refresh task status.');
    } finally {
      setRefreshingTask(null);
    }
  };

  const retry = async (taskId: string) => {
    setRetryingTask(taskId);
    setTaskError('');
    try {
      await onRetryTask(taskId);
    } catch (cause) {
      setTaskError(cause instanceof Error ? cause.message : 'Could not re-notify the department.');
    } finally {
      setRetryingTask(null);
    }
  };

  if (!plan && assignedTasks.length === 0) {
    return (
      <div className="glass-panel" style={{ marginBottom: '1.5rem', textAlign: 'center', color: '#64748b', padding: '2rem' }}>
        No active action plan generated yet. Click "Trigger Agent Response Workflow" to generate one.
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ marginBottom: '1.5rem', borderRadius: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f172a' }}>
          <ListChecks size={18} color="#d97706" />
          <span>Response Action Plan</span>
        </h2>
        {plan && (
          <span style={{ fontSize: '0.75rem', color: '#64748b', background: '#f1f5f9', padding: '0.15rem 0.5rem', borderRadius: '8px' }}>
            Plan ID: {plan.plan_id}
          </span>
        )}
      </div>

      {plan?.summary && (
        <p style={{ fontSize: '0.825rem', color: '#475569', marginBottom: '0.85rem', background: '#fffbeb', borderLeft: '3px solid #d97706', padding: '0.5rem 0.75rem', borderRadius: '0 6px 6px 0' }}>
          {plan.summary}
        </p>
      )}

      <p style={{ fontSize: '0.76rem', color: '#64748b', margin: '0 0 0.65rem' }}>
        Department status is a stored snapshot. Use Refresh Status to check for the latest department update.
      </p>
      {taskError && <p role="alert" style={{ color: '#b91c1c', fontSize: '0.75rem' }}>{taskError}</p>}
      {assignedTasks.length === 0 ? (
        <p style={{ margin: 0, padding: '0.8rem', borderRadius: '8px', background: '#f8fafc', color: '#64748b', fontSize: '0.8rem' }}>
          No response actions have been acknowledged and assigned yet.
        </p>
      ) : (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {assignedTasks.map((task) => (
          <div
            key={task.task_id}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              padding: '0.65rem 0.85rem',
              flexWrap: 'wrap',
              gap: '0.5rem'
            }}
          >
            <div style={{ flex: 1, minWidth: '220px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.15rem' }}>
                <span className={`badge-${task.priority.toLowerCase()}`} style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem', borderRadius: '6px' }}>
                  {task.priority}
                </span>
                <strong style={{ fontSize: '0.85rem', color: '#0f172a' }}>{task.action}</strong>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.85rem', fontSize: '0.75rem', color: '#64748b' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                  <UserCheck size={12} color="#0284c7" /> {task.responsible_team}
                </span>
                <strong style={{ color: '#334155' }}>
                  {task.status === 'IN_PROGRESS' ? 'WORK INITIATED' : task.status.replace('_', ' ')}
                </strong>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                  <Clock size={12} color="#d97706" /> Deadline: {new Date(task.deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                {task.updated_at && (
                  <span>Updated {new Date(task.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}{task.updated_by ? ` by ${task.updated_by}` : ''}</span>
                )}
                {task.recommendation_reason && <span>{task.recommendation_reason}</span>}
                {task.failure_reason && <span style={{ color: '#b91c1c' }}>Failure: {task.failure_reason}</span>}
              </div>
            </div>
            <button
              className="btn-secondary"
              onClick={() => void refresh(task.task_id)}
              disabled={refreshingTask === task.task_id}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.72rem' }}
            >
              <RefreshCw size={12} style={{ animation: refreshingTask === task.task_id ? 'spin 1s linear infinite' : 'none' }} />
              Refresh Status
            </button>
            {(task.status === 'FAILED' || task.status === 'OVERDUE' || task.status === 'ESCALATED') && (
              <button
                className="btn-secondary"
                onClick={() => void retry(task.task_id)}
                disabled={retryingTask === task.task_id}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.72rem' }}
              >
                <RotateCcw size={12} style={{ animation: retryingTask === task.task_id ? 'spin 1s linear infinite' : 'none' }} />
                {retryingTask === task.task_id ? 'Notifying…' : 'Retry & Notify'}
              </button>
            )}
          </div>
        ))}
      </div>
      )}
    </div>
  );
};
