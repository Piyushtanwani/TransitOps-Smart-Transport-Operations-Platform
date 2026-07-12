import type { AuthResponse, Role } from '../../types/api';

const MOCK_USERS = {
  fleet_manager: { id: 'user-fm-1', email: 'manager@transitops.in', full_name: 'Alex Manager', role: 'fleet_manager' as Role },
  dispatcher: { id: 'user-d-1', email: 'dispatch@transitops.in', full_name: 'Raven K.', role: 'dispatcher' as Role },
  safety_officer: { id: 'user-so-1', email: 'safety@transitops.in', full_name: 'Sam Officer', role: 'safety_officer' as Role },
  financial_analyst: { id: 'user-fa-1', email: 'finance@transitops.in', full_name: 'Fin Analyst', role: 'financial_analyst' as Role },
};

export async function mockLogin(email: string, password: string): Promise<AuthResponse> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 600));

  let roleKey = Object.keys(MOCK_USERS).find(
    k => MOCK_USERS[k as keyof typeof MOCK_USERS].email === email
  );

  if (!roleKey) {
    // Fallback: Check if they just typed the role name instead of full email
    roleKey = Object.keys(MOCK_USERS).find(k => k === email || email.startsWith(k));
  }

  if (!roleKey || password.length < 8) {
    throw {
      response: {
        status: 401,
        data: {
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid credentials. Please check your email and password.',
          }
        }
      }
    };
  }

  const user = MOCK_USERS[roleKey as keyof typeof MOCK_USERS];

  return {
    access_token: `mock_access_token_${user.id}_${Date.now()}`,
    refresh_token: `mock_refresh_token_${user.id}_${Date.now()}`,
    token_type: 'bearer',
    user
  };
}

export async function mockRefresh(refreshToken: string): Promise<{ access_token: string, refresh_token: string }> {
  await new Promise(resolve => setTimeout(resolve, 300));
  
  if (!refreshToken || !refreshToken.startsWith('mock_refresh_token_')) {
    throw { response: { status: 401 } };
  }

  return {
    access_token: `mock_access_token_refreshed_${Date.now()}`,
    refresh_token: `mock_refresh_token_refreshed_${Date.now()}`
  };
}
