export type HeatSeverity = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
export type TaskStatus = 'PENDING' | 'NOTIFIED' | 'ACKNOWLEDGED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'OVERDUE' | 'ESCALATED';
export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type EscalationStatus = 'NONE' | 'PENDING' | 'ESCALATED' | 'RESOLVED';

export interface Ward {
  ward_id: string;
  name: string;
  city: string;
  population: number;
  risk_metadata?: Record<string, any>;
}

export interface VulnerabilityProfile {
  ward_id: string;
  elderly_count: number;
  children_count: number;
  outdoor_worker_count: number;
  high_risk_population: number;
  vulnerability_score: number;
}

export interface Resource {
  resource_id: string;
  ward_id: string;
  type: string;
  name: string;
  capacity: number;
  availability: number;
  contact_owner: string;
}

export interface HeatEvent {
  event_id: string;
  ward_id: string;
  timestamp: string;
  temperature: number;
  humidity: number;
  heat_index: number;
  severity: HeatSeverity;
  duration: number;
}

export interface ActionPlan {
  plan_id: string;
  event_id: string;
  created_at: string;
  priority: Priority;
  status: string;
  summary?: string;
}

export interface Task {
  task_id: string;
  plan_id: string;
  action: string;
  responsible_team: string;
  priority: Priority;
  deadline: string;
  status: TaskStatus;
  created_at: string;
  completed_at?: string;
  escalation_status: EscalationStatus;
  recommendation_reason?: string;
  assigned_by?: string;
  updated_at?: string;
  updated_by?: string;
  failure_reason?: string;
}

export interface Escalation {
  escalation_id: string;
  task_id: string;
  reason: string;
  created_at: string;
  severity: Priority;
  status: string;
}

export interface EventDetailResponse {
  event: HeatEvent;
  ward: Ward;
  vulnerability: VulnerabilityProfile;
  resources: Resource[];
  action_plan?: ActionPlan;
  tasks: Task[];
  previous_completed_tasks?: Task[];
}
