import { useState, useEffect } from 'react';
import { Bot, CheckCircle2, Loader2, Sparkles, X, Play, ChevronRight, AlertTriangle, Brain } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface TraceStep {
  step: number;
  tool: string;
  description: string;
  input: string;
  result: string;
  decision?: string;
  timestamp: string;
}

interface CoordinationStreamEvent {
  type: 'step' | 'complete' | 'error';
  step?: TraceStep;
  result?: {
    trace_steps?: TraceStep[];
    severity_decision?: string;
    risk_assessment?: { severity?: string };
    assigned_tasks?: unknown[];
    tasks_rationale?: string;
    agent_explanation?: string;
    planner_output?: { planning_mode?: string; validation_notes?: string[] };
  };
  message?: string;
}

interface AgentExecutionModalProps {
  isOpen: boolean;
  wardId: string;
  onClose: () => void;
  onComplete: (traceSteps: TraceStep[], taskCount: number, severity: string) => void;
}

const TOOL_COLORS: Record<string, { bg: string; color: string; label: string }> = {
  get_weather:       { bg: '#eff6ff', color: '#1d4ed8', label: 'Weather' },
  calculate_heat_risk: { bg: '#fef2f2', color: '#dc2626', label: 'Risk Calc' },
  get_vulnerability: { bg: '#fff7ed', color: '#ea580c', label: 'Vulnerability' },
  get_resources:     { bg: '#f0fdf4', color: '#16a34a', label: 'Resources' },
  candidate_sops:     { bg: '#f5f3ff', color: '#6d28d9', label: 'SOP Filter' },
  llm_operational_planner: { bg: '#eef2ff', color: '#4f46e5', label: 'LLM Planner' },
  create_action_plan:{ bg: '#faf5ff', color: '#7c3aed', label: 'Plan' },
  assign_task:       { bg: '#fffbeb', color: '#d97706', label: 'Task' },
  llm_synthesis:     { bg: '#f0f9ff', color: '#0284c7', label: 'AI Summary' },
};

const PREFLIGHT_STEPS = [
  { tool: 'get_weather', label: 'Sensing ward weather...' },
  { tool: 'calculate_heat_risk', label: 'Calculating heat risk index...' },
  { tool: 'get_vulnerability', label: 'Profiling vulnerable populations...' },
  { tool: 'get_resources', label: 'Auditing available resources...' },
  { tool: 'candidate_sops', label: 'Filtering legally eligible SOP candidates...' },
  { tool: 'llm_operational_planner', label: 'Gemini choosing SOP IDs from the approved menu...' },
  { tool: 'llm_synthesis', label: 'Generating executive summary...' },
  { tool: 'create_action_plan', label: 'Creating validated response plan...' },
  { tool: 'assign_task', label: 'Dispatching validated SOP tasks...' },
];

const TraceList = ({ traceSteps }: { traceSteps: TraceStep[] }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
    {traceSteps.map((step) => {
      const cfg = TOOL_COLORS[step.tool] || { bg: '#f8fafc', color: '#64748b', label: step.tool };
      return (
        <div key={step.step} style={{
          background: '#fafafa',
          border: '1px solid #e9edf3',
          borderLeft: `3px solid ${cfg.color}`,
          borderRadius: '9px',
          padding: '0.7rem 0.85rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#94a3b8' }}>
                STEP {step.step}
              </span>
              <span style={{ fontSize: '0.65rem', fontWeight: 700, background: cfg.bg, color: cfg.color, padding: '0.1rem 0.35rem', borderRadius: '4px', fontFamily: 'monospace' }}>
                {step.tool}
              </span>
            </div>
            <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>
              {new Date(step.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          </div>

          <p style={{ fontSize: '0.78rem', color: '#475569', marginBottom: '0.35rem' }}>{step.description}</p>

          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '0.4rem 0.6rem', fontSize: '0.72rem', fontFamily: 'monospace', marginBottom: step.decision ? '0.35rem' : 0 }}>
            <div style={{ color: '#64748b', marginBottom: '0.15rem' }}>
              <span style={{ color: '#94a3b8' }}>IN  </span>{step.input}
            </div>
            <div style={{ color: '#0f172a', fontWeight: 600 }}>
              <span style={{ color: '#16a34a' }}>OUT </span>{step.result}
            </div>
          </div>

          {step.decision && (
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.35rem', fontSize: '0.72rem', color: '#7c3aed', background: '#faf5ff', border: '1px solid #e9d5ff', borderRadius: '5px', padding: '0.3rem 0.5rem' }}>
              <ChevronRight size={11} style={{ marginTop: '1px', flexShrink: 0 }} />
              <span><strong>Decision:</strong> {step.decision}</span>
            </div>
          )}
        </div>
      );
    })}
  </div>
);

const StepProgressList = ({
  traceSteps,
  completedThrough,
  phase,
}: {
  traceSteps: TraceStep[];
  completedThrough: number;
  phase: 'loading' | 'done' | 'error';
}) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
    {PREFLIGHT_STEPS.map((step, idx) => {
      const done = idx <= completedThrough;
      const active = phase !== 'done' && idx === completedThrough + 1;
      const cfg = TOOL_COLORS[step.tool] || { bg: '#f8fafc', color: '#64748b', label: step.tool };
      const stepDetails = traceSteps.filter((traceStep) => traceStep.tool === step.tool);
      const rowStyle = {
        display: 'flex',
        alignItems: 'center',
        gap: '0.65rem',
        padding: '0.55rem 0.8rem',
        borderRadius: '8px',
        background: done ? '#f0fdf4' : active ? '#f8fafc' : '#ffffff',
        border: `1px solid ${done ? '#bbf7d0' : active ? '#94a3b8' : '#f1f5f9'}`,
        opacity: done || active ? 1 : 0.4,
        transition: 'all 0.3s ease',
      } as const;

      const statusIcon = done
        ? <CheckCircle2 size={15} color="#16a34a" />
        : active && phase === 'loading'
          ? <Loader2 size={15} color="#0284c7" style={{ animation: 'spin 1s linear infinite' }} />
          : active && phase === 'error'
            ? <AlertTriangle size={15} color="#dc2626" />
            : <div style={{ width: 15, height: 15, borderRadius: '50%', border: '2px solid #e2e8f0' }} />;

      const rowContent = (
        <>
          {statusIcon}
          <span style={{ fontFamily: 'monospace', background: cfg.bg, color: cfg.color, padding: '0.1rem 0.35rem', borderRadius: '4px', fontSize: '0.67rem', fontWeight: 700 }}>
            {cfg.label}
          </span>
          <span style={{ fontSize: '0.8rem', color: done ? '#166534' : '#475569', fontWeight: active ? 600 : 400 }}>
            {step.label}
          </span>
        </>
      );

      return done && stepDetails.length > 0 ? (
        <details key={step.tool} style={{ borderRadius: '8px' }}>
          <summary style={{ ...rowStyle, cursor: 'pointer', listStylePosition: 'inside' }}>
            {rowContent}
            <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: '#64748b' }}>View details</span>
          </summary>
          <div style={{ padding: '0.6rem 0 0 1.5rem' }}>
            <TraceList traceSteps={stepDetails} />
          </div>
        </details>
      ) : (
        <div key={step.tool} style={rowStyle}>
          {rowContent}
        </div>
      );
    })}
  </div>
);

export const AgentExecutionModal = ({
  isOpen,
  wardId,
  onClose,
  onComplete,
}: AgentExecutionModalProps) => {
  const [phase, setPhase] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const [completedThrough, setCompletedThrough] = useState(-1);
  const [traceSteps, setTraceSteps] = useState<TraceStep[]>([]);
  const [severity, setSeverity] = useState('');
  const [taskCount, setTaskCount] = useState(0);
  const [rationale, setRationale] = useState('');
  const [agentSummary, setAgentSummary] = useState('');
  const [plannerMode, setPlannerMode] = useState('');
  const [plannerNotes, setPlannerNotes] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!isOpen) {
      setPhase('idle');
      setCompletedThrough(-1);
      setTraceSteps([]);
      setSeverity('');
      setTaskCount(0);
      setRationale('');
      setAgentSummary('');
      setPlannerMode('');
      setPlannerNotes([]);
      setErrorMsg('');
    }
  }, [isOpen]);

  const runAgent = async () => {
    setPhase('loading');
    setTraceSteps([]);
    setCompletedThrough(-1);
    setAgentSummary('');

    try {
      const res = await fetch(`${API_BASE}/api/agent/coordinate/${wardId}/stream`, {
        method: 'POST',
        headers: { 'X-HeatOps-Role': 'central' },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (!res.body) throw new Error('Agent progress stream is unavailable.');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let completed = false;
      while (true) {
        const { done, value } = await reader.read();
        buffer += decoder.decode(value, { stream: !done });
        const frames = buffer.split('\n\n');
        buffer = frames.pop() || '';
        for (const frame of frames) {
          const payload = frame.split('\n').find((line) => line.startsWith('data: '))?.slice(6);
          if (!payload) continue;
          const event = JSON.parse(payload) as CoordinationStreamEvent;
          if (event.type === 'step' && event.step) {
            setTraceSteps((current) => [...current, event.step!]);
            const index = PREFLIGHT_STEPS.findIndex((item) => item.tool === event.step?.tool);
            if (index >= 0 && event.step.tool !== 'assign_task') {
              setCompletedThrough((current) => Math.max(current, index));
            }
          } else if (event.type === 'complete' && event.result) {
            const data = event.result;
            setSeverity(data.severity_decision || data.risk_assessment?.severity || '');
            setTaskCount(data.assigned_tasks?.length || 0);
            setRationale(data.tasks_rationale || '');
            setAgentSummary(data.agent_explanation || '');
            setPlannerMode(data.planner_output?.planning_mode || 'unknown');
            setPlannerNotes(data.planner_output?.validation_notes || []);
            setCompletedThrough(PREFLIGHT_STEPS.length - 1);
            setPhase('done');
            completed = true;
          } else if (event.type === 'error') {
            throw new Error(event.message || 'Agent execution failed');
          }
        }
        if (done) break;
      }
      if (!completed) throw new Error('Agent progress stream ended before execution completed.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Agent call failed');
      setPhase('error');
    }
  };

  if (!isOpen) return null;

  const severityColor = severity === 'CRITICAL' ? '#dc2626'
    : severity === 'HIGH' ? '#ea580c'
    : severity === 'MODERATE' ? '#d97706'
    : '#16a34a';
  const isFallbackPlan = plannerMode !== 'llm_planned';
  const plannerLabel = plannerMode === 'llm_planned'
    ? 'Gemini-planned SOP selection'
    : plannerMode === 'backend_validated_fallback'
      ? 'Backend fallback SOP selection'
      : 'Planner mode unknown';

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(15, 23, 42, 0.6)',
      backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: '1rem',
    }}>
      <div style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '18px',
        maxWidth: '700px',
        width: '100%',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 50px -12px rgba(0,0,0,0.18)',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '1.1rem 1.4rem',
          borderBottom: '1px solid #f1f5f9',
          background: '#fafafa',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div style={{ background: '#fef2f2', padding: '0.45rem', borderRadius: '10px', display: 'flex' }}>
              <Bot size={22} color="#dc2626" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0f172a' }}>
                HeatOps Agent — Live Reasoning Trace
              </h3>
              <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
                {wardId.replace(/_/g, ' ').toUpperCase()} · Real-time tool call execution
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '0.25rem' }}>
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.2rem 1.4rem' }}>

          {/* IDLE: Start button */}
          {phase === 'idle' && (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem' }}>
              <div style={{ width: '64px', height: '64px', background: '#fef2f2', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem' }}>
                <Brain size={32} color="#dc2626" />
              </div>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
                Ready to Execute
              </h4>
              <p style={{ fontSize: '0.83rem', color: '#64748b', maxWidth: '380px', margin: '0 auto 1.5rem', lineHeight: 1.6 }}>
                The agent will sense weather, calculate risk, audit resources, and dynamically
                assign only the tasks appropriate for this ward's severity level.
              </p>
              <button className="btn-primary" onClick={runAgent} style={{ fontSize: '0.9rem', padding: '0.65rem 1.5rem' }}>
                <Play size={15} /> Run Agent Workflow
              </button>
            </div>
          )}

          {(phase === 'loading' || phase === 'error') && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {phase === 'loading' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <Loader2 size={16} color="#dc2626" style={{ animation: 'spin 1s linear infinite' }} />
                  <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#475569' }}>
                    Agent executing tool calls...
                  </span>
                </div>
              )}
              <StepProgressList
                traceSteps={traceSteps}
                completedThrough={completedThrough}
                phase={phase}
              />
            </div>
          )}

          {/* ERROR */}
          {phase === 'error' && (
            <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
              <AlertTriangle size={36} color="#dc2626" style={{ marginBottom: '0.75rem' }} />
              <p style={{ color: '#dc2626', fontWeight: 700, marginBottom: '0.5rem' }}>Agent execution failed</p>
              <p style={{ fontSize: '0.8rem', color: '#64748b' }}>{errorMsg}</p>
            </div>
          )}

          {/* DONE: Real trace steps */}
          {phase === 'done' && (
            <>
              {/* Severity outcome banner */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: '0.75rem',
                background: `${severityColor}10`,
                border: `1.5px solid ${severityColor}40`,
                borderRadius: '10px',
                padding: '0.8rem 1rem',
                marginBottom: '1.1rem',
              }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: severityColor, flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '0.82rem', fontWeight: 700, color: severityColor }}>
                    {severity} Severity — {taskCount} Task{taskCount !== 1 ? 's' : ''} Assigned
                  </p>
                  {rationale && (
                    <p style={{ fontSize: '0.74rem', color: '#475569', marginTop: '0.15rem' }}>{rationale}</p>
                  )}
                </div>
                <Sparkles size={16} color={severityColor} />
              </div>

              <div style={{
                background: isFallbackPlan ? '#fffbeb' : '#eef2ff',
                border: `1px solid ${isFallbackPlan ? '#fcd34d' : '#c7d2fe'}`,
                borderRadius: '10px',
                padding: '0.7rem 0.85rem',
                marginBottom: '1rem',
              }}>
                <p style={{
                  fontSize: '0.78rem',
                  fontWeight: 800,
                  color: isFallbackPlan ? '#92400e' : '#3730a3',
                  marginBottom: plannerNotes.length ? '0.25rem' : 0,
                }}>
                  {plannerLabel}
                </p>
                {plannerNotes.length > 0 && (
                  <p style={{ fontSize: '0.72rem', color: '#475569', lineHeight: 1.45 }}>
                    {plannerNotes.join(' ')}
                  </p>
                )}
              </div>

              <StepProgressList
                traceSteps={traceSteps}
                completedThrough={completedThrough}
                phase="done"
              />

              {agentSummary && (
                <div style={{
                  background: '#f0f9ff',
                  border: '1px solid #bae6fd',
                  borderRadius: '10px',
                  padding: '0.85rem 1rem',
                  marginTop: '1rem',
                }}>
                  <p style={{ fontSize: '0.78rem', fontWeight: 800, color: '#0369a1', marginBottom: '0.35rem' }}>
                    AI Summary
                  </p>
                  <p style={{ fontSize: '0.8rem', color: '#334155', lineHeight: 1.55 }}>
                    {agentSummary}
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '0.9rem 1.4rem',
          borderTop: '1px solid #f1f5f9',
          background: '#fafafa',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', color: '#64748b' }}>
            <Sparkles size={13} color="#dc2626" />
            <span>
              {phase === 'idle' && 'Click "Run Agent Workflow" to start'}
              {phase === 'loading' && 'Showing live workflow progress...'}
              {phase === 'done' && `Workflow complete — ${plannerLabel}`}
              {phase === 'error' && 'Agent execution failed'}
            </span>
          </div>

          {phase === 'done' && (
            <button
              className="btn-primary"
              onClick={() => {
                onComplete(traceSteps, taskCount, severity);
                onClose();
              }}
              style={{ fontSize: '0.85rem', padding: '0.55rem 1.2rem' }}
            >
              <Play size={14} />
              Apply Response Plan
            </button>
          )}
          {phase === 'idle' && (
            <button onClick={onClose} className="btn-secondary" style={{ fontSize: '0.82rem' }}>
              Cancel
            </button>
          )}
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
