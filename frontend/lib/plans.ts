export type Plan = 'free' | 'pro' | 'enterprise';

export const PLAN_LIMITS: Record<Plan, number> = {
  free: 10,
  pro: 500,
  enterprise: 100000
};

export const PLAN_LABELS: Record<Plan, string> = {
  free: 'Free',
  pro: 'Pro',
  enterprise: 'Enterprise'
};

export function getLimit(plan: Plan): number {
  return PLAN_LIMITS[plan];
}
