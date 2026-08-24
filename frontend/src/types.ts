export interface ActionItem {
  task: string;
  owner: string | null;
  due_iso: string | null;
  priority: string;
  confidence: number;
}

export interface Decision {
  decision: string;
  context: string;
}

export interface Conflict {
  previous_decision: string;
  new_decision: string;
  reason: string;
  evidence: string;
}

export interface ClarificationQuestion {
  commitment: string;
  missing_info: string;
  question: string;
  options: string[];
}

export interface DashboardMetrics {
  decisions: number;
  decisions_requiring_review: number;
  active_commitments: number;
  overdue_commitments: number;
}

