export type Role = 'fleet_manager' | 'dispatcher' | 'safety_officer' | 'financial_analyst';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
}

export interface AuthResponse extends AuthTokens {
  user: User;
}

export interface ErrorEnvelope {
  error: {
    code: string;
    message: string;
    field?: string;
  };
}

export type DomainErrorCode = 
  | 'DUPLICATE_REGISTRATION'
  | 'DUPLICATE_LICENSE'
  | 'VEHICLE_NOT_AVAILABLE'
  | 'DRIVER_NOT_AVAILABLE'
  | 'DRIVER_LICENSE_EXPIRED'
  | 'DRIVER_SUSPENDED'
  | 'CARGO_EXCEEDS_CAPACITY'
  | 'INVALID_STATUS_TRANSITION'
  | 'VEHICLE_HAS_OPEN_MAINTENANCE'
  | 'END_ODOMETER_LT_START'
  | 'AI_DISABLED'
  | 'AI_TOOL_FORBIDDEN'
  | 'TOKEN_EXPIRED'
  | 'INVALID_CREDENTIALS'
  | 'FORBIDDEN_ROLE'
  | 'NOT_FOUND';
