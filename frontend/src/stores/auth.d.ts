declare module '@/stores/auth' {
  interface User {
    is_super_admin: boolean;
    is_manager: boolean;
  }

  interface AuthStore {
    user: User | null;
  }

  export function useAuthStore(): AuthStore;
} 