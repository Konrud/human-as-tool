// Mock authentication service for Phase 1
// This will be replaced with real OAuth2/JWT in later phases

export interface User {
  id: string;
  email: string;
  name: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

const TOKEN_KEY = "auth_tokens";
const USER_KEY = "auth_user";

// Simulated delay for async operations
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export class AuthService {
  // Mock login - accepts any credentials
  async login(email: string, password: string): Promise<{ user: User; tokens: AuthTokens }> {
    await delay(500); // Simulate network request

    if (!email || !password) {
      throw new Error("Email and password are required");
    }

    // Generate mock tokens
    const tokens: AuthTokens = {
      accessToken: `mock_access_token_${Date.now()}`,
      refreshToken: `mock_refresh_token_${Date.now()}`,
      expiresAt: Date.now() + 25 * 60 * 1000, // 25 minutes
    };

    // Create mock user
    const user: User = {
      id: crypto.randomUUID(),
      email,
      name: email.split("@")[0],
    };

    // Store in localStorage
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    return { user, tokens };
  }

  // Mock logout
  async logout(): Promise<void> {
    await delay(200);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  // Get stored tokens
  getTokens(): AuthTokens | null {
    const tokensStr = localStorage.getItem(TOKEN_KEY);
    if (!tokensStr) return null;

    try {
      return JSON.parse(tokensStr);
    } catch {
      return null;
    }
  }

  // Get stored user
  getUser(): User | null {
    const userStr = localStorage.getItem(USER_KEY);
    if (!userStr) return null;

    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  // Check if tokens are expired
  isTokenExpired(tokens: AuthTokens): boolean {
    return Date.now() >= tokens.expiresAt;
  }

  // Mock token refresh
  async refreshTokens(): Promise<AuthTokens> {
    await delay(300);

    const newTokens: AuthTokens = {
      accessToken: `mock_access_token_${Date.now()}`,
      refreshToken: `mock_refresh_token_${Date.now()}`,
      expiresAt: Date.now() + 25 * 60 * 1000,
    };

    localStorage.setItem(TOKEN_KEY, JSON.stringify(newTokens));
    return newTokens;
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const tokens = this.getTokens();
    const user = this.getUser();

    if (!tokens || !user) return false;

    // Check if token is expired
    if (this.isTokenExpired(tokens)) {
      // In real implementation, would attempt token refresh
      return false;
    }

    return true;
  }
}

// Export singleton instance
export const authService = new AuthService();
