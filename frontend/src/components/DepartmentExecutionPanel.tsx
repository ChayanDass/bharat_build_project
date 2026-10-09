import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, Users, XCircle } from 'lucide-react';
import { fetchDepartmentTasks, updateDepartmentTaskStatus } from '../services/api';
import type { Task, TaskStatus } from '../types';

const DEPARTMENTS = [
  'Water Dept',
  'Health Dept',
  'Labour Dept',
  'Ward Officers',
  'Disaster Management',
  'Community/Volunteer Team',
];

interface DepartmentExecutionPanelProps {
  departments: string[];
  lockedDepartment?: string;
}

const statusLabel: Record<TaskStatus, string> = {
  PENDING: 'Awaiting central assignment',
  NOTIFIED: 'Notified',
  ACKNOWLEDGED: 'Acknowledged',
  IN_PROGRESS: 'Work initiated',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
  OVERDUE: 'Overdue',
  ESCALATED: 'Escalated',
};

export const DepartmentExecutionPanel = ({ departments, lockedDepartment }: DepartmentExecutionPanelProps) => {
  const [selectedDepartment, setSelectedDepartment] = useState(lockedDepartment || DEPARTMENTS[0]);
  const [departmentTasks, setDepartmentTasks] = useState<Task[]>([]);
  const [failureReasons, setFailureReasons] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [busyTaskId, setBusyTaskId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const availableDepartments = lockedDepartment
    ? [lockedDepartment]
    : [...new Set([...DEPARTMENTS, ...departments])];

  const refresh = async () => {
    setLoading(true);
    try {
      setDepartmentTasks(await fetchDepartmentTasks(selectedDepartment));
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load department assignments.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, [selectedDepartment]);

  const setStatus = async (task: Task, status: TaskStatus) => {
    setBusyTaskId(task.task_id);
    try {
      const updated = await updateDepartmentTaskStatus(
        task.task_id,
        selectedDepartment,
        status,
        failureReasons[task.task_id],
      );
      setDepartmentTasks((current) => current.map((item) => item.task_id === updated.task_id ? updated : item));
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not update task status.');
    } finally {
      setBusyTaskId(null);
    }
  };

  const activeTasks = departmentTasks.filter((task) => task.status !== 'COMPLETED');
  const completedTasks = departmentTasks.filter((task) => task.status === 'COMPLETED');

  return (
    <section className="glass-panel" style={{ marginBottom: '1.5rem', borderRadius: '14px', padding: '1.4rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', marginBottom: '0.7rem' }}>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#0f172a', margin: 0 }}>
          <Activity size={17} color="#0284c7" />
          Department Task Interfaces
        </h2>
        <button className="btn-secondary" onClick={() => void refresh()} disabled={loading} style={{ fontSize: '0.75rem' }}>
          {loading ? 'Refreshing…' : 'Refresh department inbox'}
        </button>
      </div>

      <p style={{ color: '#64748b', fontSize: '0.76rem', margin: '0 0 0.85rem', lineHeight: 1.5 }}>
        {lockedDepartment
          ? 'Only tasks assigned to your authenticated department are shown here.'
          : 'Select a department to view only its notified assignments. In demo mode, departments share this interface.'}
      </p>

      {!lockedDepartment && (
        <div role="tablist" aria-label="Department inbox" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.9rem' }}>
          {availableDepartments.map((department) => (
            <button
              key={department}
              role="tab"
              aria-selected={selectedDepartment === department}
              className={selectedDepartment === department ? 'btn-primary' : 'btn-secondary'}
              onClick={() => setSelectedDepartment(department)}
              style={{ fontSize: '0.74rem', padding: '0.35rem 0.65rem' }}
            >
              {department}
            </button>
          ))}
        </div>
      )}

      {error && <p role="alert" style={{ color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '7px', padding: '0.6rem 0.75rem', fontSize: '0.78rem' }}>{error}</p>}

      {loading ? (
        <p style={{ margin: 0, padding: '1rem', color: '#64748b', fontSize: '0.8rem' }}>Loading {selectedDepartment} assignments…</p>
      ) : activeTasks.length === 0 && completedTasks.length === 0 ? (
        <p style={{ margin: 0, padding: '1rem', borderRadius: '9px', background: '#f8fafc', color: '#64748b', fontSize: '0.8rem' }}>
          No tasks have been notified to {selectedDepartment}.
        </p>
      ) : (
        <>
          {activeTasks.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {activeTasks.map((task) => (
                <article key={task.task_id} style={{
                  padding: '0.8rem 0.9rem',
                  borderRadius: '9px',
                  border: `1px solid ${task.status === 'FAILED' || task.status === 'ESCALATED' || task.status === 'OVERDUE' ? '#fecaca' : '#e2e8f0'}`,
                  background: '#ffffff',
                }}>
                  <strong style={{ display: 'block', fontSize: '0.83rem', color: '#0f172a', lineHeight: 1.4, marginBottom: '0.45rem' }}>{task.action}</strong>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.8rem', color: '#64748b', fontSize: '0.72rem', marginBottom: '0.6rem' }}>
                    <span><Users size={11} style={{ verticalAlign: 'middle' }} /> {selectedDepartment}</span>
                    <span><strong>Priority:</strong> {task.priority}</span>
                    <span><strong>Status:</strong> {statusLabel[task.status]}</span>
                    <span>Deadline: {new Date(task.deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    {task.assigned_by && <span>Assigned by: {task.assigned_by}</span>}
                    {task.updated_at && <span>Updated {new Date(task.updated_at).toLocaleString()} by {task.updated_by || 'department operator'}</span>}
                  </div>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {task.status === 'NOTIFIED' && (
                      <button className="btn-secondary" disabled={busyTaskId === task.task_id} onClick={() => void setStatus(task, 'ACKNOWLEDGED')}>
                        Acknowledge request
                      </button>
                    )}
                    {task.status === 'ACKNOWLEDGED' && (
                      <button className="btn-secondary" disabled={busyTaskId === task.task_id} onClick={() => void setStatus(task, 'IN_PROGRESS')}>
                        <Activity size={12} /> Work Initiated
                      </button>
                    )}
                    {task.status === 'IN_PROGRESS' && (
                      <>
                        <button className="btn-secondary" disabled={busyTaskId === task.task_id} onClick={() => void setStatus(task, 'COMPLETED')}>
                          <CheckCircle2 size={12} /> Report Completed
                        </button>
                        <input
                          aria-label={`Failure reason for ${task.action}`}
                          placeholder="Failure reason (required)"
                          value={failureReasons[task.task_id] || ''}
                          onChange={(event) => setFailureReasons((current) => ({ ...current, [task.task_id]: event.target.value }))}
                          style={{ minWidth: '200px', padding: '0.35rem 0.5rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.75rem' }}
                        />
                        <button
                          className="btn-danger"
                          disabled={busyTaskId === task.task_id || !(failureReasons[task.task_id] || '').trim()}
                          onClick={() => void setStatus(task, 'FAILED')}
                        >
                          <XCircle size={12} /> Report Failure
                        </button>
                      </>
                    )}
                    {(task.status === 'FAILED' || task.status === 'OVERDUE' || task.status === 'ESCALATED') && (
                      <div style={{ color: '#b91c1c', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <AlertTriangle size={12} />
                        {task.failure_reason || 'Central HeatOps must reassign or re-notify this task.'}
                      </div>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}

          {completedTasks.length > 0 && (
            <details style={{ marginTop: '0.85rem' }}>
              <summary style={{ cursor: 'pointer', color: '#166534', fontSize: '0.78rem', fontWeight: 700 }}>
                Completed assignments ({completedTasks.length})
              </summary>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.55rem' }}>
                {completedTasks.map((task) => (
                  <div key={task.task_id} style={{ padding: '0.55rem 0.7rem', borderRadius: '7px', background: '#f0fdf4', color: '#14532d', fontSize: '0.77rem' }}>
                    <CheckCircle2 size={13} style={{ verticalAlign: 'middle', marginRight: '0.35rem' }} />
                    {task.action} · updated {task.updated_at ? new Date(task.updated_at).toLocaleString() : 'time unavailable'}
                  </div>
                ))}
              </div>
            </details>
          )}
        </>
      )}
    </section>
  );
};
