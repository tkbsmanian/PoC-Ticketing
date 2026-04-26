// ── Enums ─────────────────────────────────────────────────────────────────────

export type UserRole =
  | 'business_user'
  | 'it_manager'
  | 'it_triage'
  | 'platform_admin'
  | 'auditor'

export type TicketStatus =
  | 'Pending'
  | 'Approved'
  | 'In Review'
  | 'In Progress'
  | 'Resolved'
  | 'Closed'
  | 'Rejected'
  | 'Removed'

export type UrgencyLevel = 'Low' | 'Medium' | 'High' | 'Critical'
export type PriorityLevel = 'Low' | 'Medium' | 'High' | 'Critical'

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: number
  email: string
  display_name: string
  role: UserRole
  department_id: number | null
  department_name: string | null
}

// ── Tickets ───────────────────────────────────────────────────────────────────

export interface TicketSummary {
  id: number
  ticket_id: string
  title: string
  status: TicketStatus
  urgency: UrgencyLevel
  priority: PriorityLevel | null
  category: string | null
  department_name: string | null
  submitter_name: string
  created_at: string
  updated_at: string
  sync_failed: boolean
  jira_task_url: string | null
}

export interface TicketDetail extends TicketSummary {
  description: string
  cost: number | null
  director_approval_required: boolean
  jira_task_id: string | null
  comments: Comment[]
  attachments: Attachment[]
  history: StatusHistoryEntry[]
  approvals: Approval[]
}

export interface CreateTicketPayload {
  title: string
  description: string
  department_id: number
  urgency: UrgencyLevel
  cost?: number
  manager_id: number
}

export interface UpdateStatusPayload {
  status: TicketStatus
}

export interface UpdateCategoryPriorityPayload {
  category?: string
  priority?: PriorityLevel
}

// ── Comments ──────────────────────────────────────────────────────────────────

export interface Comment {
  id: number
  author_name: string
  author_role: UserRole
  body: string
  is_internal: boolean
  created_at: string
}

export interface CreateCommentPayload {
  body: string
  is_internal: boolean
}

// ── Attachments ───────────────────────────────────────────────────────────────

export interface Attachment {
  id: number
  original_filename: string
  mime_type: string
  file_size_bytes: number
  uploaded_by_name: string
  uploaded_at: string
}

// ── Approvals ─────────────────────────────────────────────────────────────────

export interface Approval {
  id: number
  approver_name: string
  approver_role: 'Manager' | 'Director'
  decision: 'approved' | 'rejected' | null
  comment: string | null
  decided_at: string | null
  deadline: string
}

export interface ApprovalActionPayload {
  comment?: string
}

// ── Status history ────────────────────────────────────────────────────────────

export interface StatusHistoryEntry {
  id: number
  event_type: string
  field_name: string | null
  old_value: string | null
  new_value: string | null
  actor_name: string
  created_at: string
}

// ── Notifications ─────────────────────────────────────────────────────────────

export interface Notification {
  id: number
  ticket_id: number | null
  ticket_ref: string | null
  event_type: string
  message: string
  is_read: boolean
  created_at: string
}

// ── Users & Departments ───────────────────────────────────────────────────────

export interface UserSummary {
  id: number
  email: string
  display_name: string
  role: UserRole
  department_name: string | null
  is_active: boolean
}

export interface Department {
  id: number
  name: string
  is_active: boolean
}

export interface CreateUserPayload {
  email: string
  display_name: string
  role: UserRole
  department_id: number | null
  password: string
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export interface DashboardCounts {
  by_status: Record<TicketStatus, number>
  total_open: number
}

// ── Sync health ───────────────────────────────────────────────────────────────

export interface SyncHealth {
  last_success_at: string | null
  pending_count: number
  failed_count: number
  adapter: string
}

// ── API responses ─────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ApiError {
  detail: string
}
