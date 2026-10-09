import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { DashboardGrid } from './components/DashboardGrid';
import { EventDetailView } from './components/EventDetailView';
import { ActionPlanPanel } from './components/ActionPlanPanel';
import { TaskMonitorPanel } from './components/TaskMonitorPanel';
import { DepartmentExecutionPanel } from './components/DepartmentExecutionPanel';
import { AgentConsole } from './components/AgentConsole';
import { ArchitectureModal } from './components/ArchitectureModal';
import { AgentExecutionModal } from './components/AgentExecutionModal';
import {
  fetchHealthCheck,
  fetchEvents,
  fetchEventDetail,
  assignTaskToDepartment,
  fetchTaskStatus,
  retryTaskDispatch,
  queryAgent,
  simulateWeatherChange,
  resetDemoData,
} from './services/api';
import type { EventDetailResponse, Task } from './types';

export function App() {
  const [health, setHealth] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [selectedWardId, setSelectedWardId] = useState<string>('ward_12');
  const [eventDetail, setEventDetail] = useState<EventDetailResponse | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);
  const [isTriggeringAgent, setIsTriggeringAgent] = useState<boolean>(false);
  const [isArchModalOpen, setIsArchModalOpen] = useState<boolean>(false);
  const [isExecModalOpen, setIsExecModalOpen] = useState<boolean>(false);

  // Load initial health & active ward events
  useEffect(() => {
    fetchHealthCheck().then(setHealth).catch(console.error);
    loadEvents();
  }, []);

  // Reload event detail and tasks when selectedWardId changes
  useEffect(() => {
    if (selectedWardId) {
      loadWardData(selectedWardId);
    }
  }, [selectedWardId]);

  const loadEvents = async () => {
    try {
      const data = await fetchEvents();
      setEvents(data);
    } catch (err) {
      console.error('Error fetching events:', err);
    }
  };

  const loadWardData = async (wardId: string) => {
    setLoadingDetail(true);
    try {
      const detail = await fetchEventDetail(wardId);
      setEventDetail(detail);
      setTasks(detail.tasks || []);
    } catch (err) {
      console.error(`Error loading data for ${wardId}:`, err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleOpenAgentExecutionModal = () => {
    setIsExecModalOpen(true);
  };

  const handleApplyAgentResponsePlan = async () => {
    if (!selectedWardId) return;
    setIsTriggeringAgent(true);
    try {
      // Modal already called the agent API — just reload the ward data
      await loadWardData(selectedWardId);
      await loadEvents();
    } catch (err) {
      console.error('Reload after agent failed:', err);
    } finally {
      setIsTriggeringAgent(false);
    }
  };

  const handleResetDemo = async () => {
    try {
      await resetDemoData();
      await loadEvents();
      await loadWardData(selectedWardId);
    } catch (err) {
      console.error('Reset demo failed:', err);
    }
  };

  const handleAssignTask = async (taskId: string, department: string) => {
    try {
      const updated = await assignTaskToDepartment(taskId, department);
      setTasks((current) => current.map((task) => task.task_id === updated.task_id ? updated : task));
    } catch (err) {
      console.error('Task assignment failed:', err);
      throw err;
    }
  };

  const handleRefreshTaskStatus = async (taskId: string) => {
    const latest = await fetchTaskStatus(taskId);
    setTasks((current) => current.map((task) => task.task_id === latest.task_id ? latest : task));
  };

  const handleRetryTask = async (taskId: string) => {
    const updated = await retryTaskDispatch(taskId);
    setTasks((current) => current.map((task) => task.task_id === updated.task_id ? updated : task));
  };

  const handleSimulateWeather = async (scenario: string) => {
    try {
      await simulateWeatherChange(selectedWardId, scenario);
      await loadEvents();
      await loadWardData(selectedWardId);
    } catch (err) {
      console.error('Weather simulation failed:', err);
    }
  };

  const handleAskAgent = async (question: string) => {
    const res = await queryAgent(question, selectedWardId);
    return res.answer;
  };

  const activeCriticalCount = events.filter((e) => e.event.severity === 'CRITICAL').length;

  return (
    <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '1.25rem' }}>
      {/* Header Bar */}
      <Header
        environment={health?.environment || 'development'}
        llmProvider={health?.llm_provider || 'gemini'}
        activeCriticalCount={activeCriticalCount}
        onOpenArchModal={() => setIsArchModalOpen(true)}
        onResetDemo={handleResetDemo}
      />

      {/* Main Ward Event Overview Grid */}
      <DashboardGrid
        events={events}
        selectedWardId={selectedWardId}
        onSelectWard={setSelectedWardId}
      />

      {/* Ward Details & Vulnerabilities */}
      <EventDetailView
        detail={eventDetail}
        loading={loadingDetail}
        onTriggerAgent={handleOpenAgentExecutionModal}
        onSimulateWeather={handleSimulateWeather}
        isTriggering={isTriggeringAgent}
      />

      {/* Response Action Plan & Live Task Tracker */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '1.25rem', alignItems: 'start' }}>
        <ActionPlanPanel
          plan={eventDetail?.action_plan || null}
          tasks={tasks}
          onRefreshStatus={handleRefreshTaskStatus}
          onRetryTask={handleRetryTask}
        />

        <TaskMonitorPanel
          tasks={tasks}
          onAssignTask={handleAssignTask}
        />
      </div>

      <DepartmentExecutionPanel
        departments={tasks.map((task) => task.responsible_team)}
      />

      {/* Agent Query Console */}
      <AgentConsole
        onAskQuestion={handleAskAgent}
        wardId={selectedWardId}
      />

      {/* Live Agent Tool Execution Modal */}
      <AgentExecutionModal
        isOpen={isExecModalOpen}
        wardId={selectedWardId}
        onClose={() => setIsExecModalOpen(false)}
        onComplete={handleApplyAgentResponsePlan}
      />

      {/* System Architecture Modal */}
      <ArchitectureModal
        isOpen={isArchModalOpen}
        onClose={() => setIsArchModalOpen(false)}
      />
    </div>
  );
}

export default App;
