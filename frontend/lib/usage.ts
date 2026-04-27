import { Plan, getLimit } from './plans';

const STORAGE_KEY = 'lex-aureon-user';

export type LocalUser = {
  user_id: string;
  email: string;
  plan: Plan;
  usage_count: number;
  usage_date: string;
};

export function getTodayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export function getOrCreateUser(): LocalUser {
  if (typeof window === 'undefined') {
    return {
      user_id: 'server-anon',
      email: 'anon@lexaureon.ai',
      plan: 'free',
      usage_count: 0,
      usage_date: getTodayISO()
    };
  }

  const existing = window.localStorage.getItem(STORAGE_KEY);
  if (existing) {
    const parsed = JSON.parse(existing) as LocalUser;
    if (parsed.usage_date !== getTodayISO()) {
      parsed.usage_date = getTodayISO();
      parsed.usage_count = 0;
      persistUser(parsed);
    }
    return parsed;
  }

  const user: LocalUser = {
    user_id: crypto.randomUUID(),
    email: 'founder@demo.lexaureon.ai',
    plan: 'free',
    usage_count: 0,
    usage_date: getTodayISO()
  };
  persistUser(user);
  return user;
}

export function persistUser(user: LocalUser): void {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  }
}

export function canRun(plan: Plan, usageCount: number): boolean {
  return usageCount < getLimit(plan);
}
