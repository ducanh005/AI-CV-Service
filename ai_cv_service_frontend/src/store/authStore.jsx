import { createContext, useContext, useMemo, useState } from 'react';

import { tokenStorage } from '../utils/storage';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(tokenStorage.getUser());

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      setSession: (session) => {
        tokenStorage.setSession(session);
        setUser(session.user);
      },
      clearSession: () => {
        tokenStorage.clearSession();
        setUser(null);
      },
    }),
    [user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthStore() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthStore must be used within AuthProvider');
  }
  return context;
}
