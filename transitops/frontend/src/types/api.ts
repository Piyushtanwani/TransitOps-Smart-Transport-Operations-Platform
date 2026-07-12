// NOTE: backend's `user_role` enum (docs/02-DATABASE.md) is actually
// ('fleet_manager','driver','safety_officer','financial_analyst') — there is no
// 'dispatcher' value server-side (confirmed live: dispatch@transitops.in → role:"driver").
// 'dispatcher' is kept below for backward compatibility with existing RBAC gates
// (App.tsx, AppShell.tsx, SettingsPage.tsx) that already reference it; 'driver' is
// added so real API responses type-check correctly. These two likely need
// reconciling into one canonical value by whoever owns those RBAC gates.
export type Role = 'fleet_manager' | 'dispatcher' | 'driver' | 'safety_officer' | 'financial_analyst';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active?: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
}

export interface AuthResponse extends AuthTokens {
  user: User;
}

/** Response shape of POST /auth/login and POST /auth/refresh (docs/03-API-SPEC.md §4). */
export type LoginResponse = AuthResponse;

/** Generic paginated list envelope returned by every `GET` list endpoint (docs/03-API-SPEC.md §1). */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ErrorEnvelope {
  error: {
    code: string;
    message: string;
    field?: string | null;
  };
}

/** Alias matching docs/03-API-SPEC.md §2 terminology ("error envelope") for the same shape. */
export type ApiError = ErrorEnvelope;

export type DomainErrorCode =
  | 'DUPLICATE_REGISTRATION'
  | 'DUPLICATE_LICENSE'
  | 'DUPLICATE_EMAIL'
  | 'VEHICLE_NOT_AVAILABLE'
  | 'DRIVER_NOT_AVAILABLE'
  | 'DRIVER_LICENSE_EXPIRED'
  | 'DRIVER_SUSPENDED'
  | 'CARGO_EXCEEDS_CAPACITY'
  | 'INVALID_STATUS_TRANSITION'
  | 'VEHICLE_HAS_OPEN_MAINTENANCE'
  | 'VEHICLE_HAS_HISTORY'
  | 'END_ODOMETER_LT_START'
  | 'AI_DISABLED'
  | 'AI_TOOL_FORBIDDEN'
  | 'TOKEN_EXPIRED'
  | 'INVALID_TOKEN'
  | 'INVALID_CREDENTIALS'
  | 'FORBIDDEN_ROLE'
  | 'NOT_FOUND';
