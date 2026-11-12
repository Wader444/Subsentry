export interface User {
  id: string
  email: string
  full_name: string | null
  role: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface Subscription {
  id: string
  user_id: string
  merchant: string
  plan_name: string
  category: string | null
  price_monthly_usd: number
  currency: string
  status: string
  paypal_subscription_id: string | null
  started_on: string | null
  next_billing_on: string | null
  last_used_days_ago: number | null
  created_at: string
  updated_at: string
}

export interface EnrichedSubscription {
  id: string
  merchant: string
  plan_name: string
  category: string | null
  price_monthly_usd: number
  currency: string
  status: string
  started_on: string | null
  next_billing_on: string | null
  last_used_days_ago: number | null
  live_status: string | null
  waste_score: number
  flagged: boolean
  reason: string | null
}

export interface ProposeResponse {
  flagged: EnrichedSubscription[]
  kept: EnrichedSubscription[]
  monthly_saving_usd: number
  annual_saving_usd: number
  total_monthly_usd: number
}

export interface ApproveResponse {
  approved: string[]
}

export interface BlockedCancel {
  id: string
  reason: string
}

export interface CancelResponse {
  cancelled: string[]
  blocked: BlockedCancel[]
  monthly_saving_usd: number
  annual_saving_usd: number
  still_active: string[]
}

export interface ReportResponse {
  cancelled: string[]
  still_active: string[]
  monthly_saving_usd: number
  annual_saving_usd: number
  total_monthly_usd: number
}

export interface AskResponse {
  question: string
  answer: string
}

export interface NotificationItem {
  id: string
  user_id: string
  title: string
  body: string
  is_read: boolean
  created_at: string
}

export interface NotificationsResponse {
  notifications: NotificationItem[]
}

export interface DuplicateGroup {
  merchant: string
  subscription_ids: string[]
  subscriptions: EnrichedSubscription[]
  reason: string
}

export interface DuplicatesResponse {
  groups: DuplicateGroup[]
}

export interface AuditEntry {
  id: string
  user_id: string
  action: string
  entity_type: string
  entity_id: string | null
  detail: string | null
  created_at: string
}

export interface AuditResponse {
  entries: AuditEntry[]
}

export interface AdminUser {
  id: string
  email: string
  full_name: string | null
  role: string
}

export interface AdminUsersResponse {
  users: AdminUser[]
}

export interface AdminStats {
  total_users: number
  total_subscriptions: number
  active_subscriptions: number
  cancelled_subscriptions: number
  total_monthly_usd: number
}

export interface HealthResponse {
  status: string
  mode: string
  db: string
}

export interface CreateSubscriptionPayload {
  merchant: string
  plan_name: string
  category?: string
  price_monthly_usd: number
  started_on?: string
  next_billing_on?: string
  last_used_days_ago?: number
  paypal_subscription_id?: string
}
