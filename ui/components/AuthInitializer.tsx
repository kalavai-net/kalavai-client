'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/stores';

const ACCESS_KEY = process.env.NEXT_PUBLIC_ACCESS_KEY || null;

export function AuthInitializer() {
  const { setAccessKey } = useAuthStore();

  useEffect(() => {
    // Only run once on app initialization
    setAccessKey(ACCESS_KEY);
    
    // Clear persisted login state to force key entry on browser refresh
    // but not on navigation within the app
    const hasInitialized = sessionStorage.getItem('kalavai-auth-initialized');
    if (!hasInitialized) {
      const { signOut } = useAuthStore.getState();
      signOut();
      sessionStorage.setItem('kalavai-auth-initialized', 'true');
    }
  }, [setAccessKey]);

  return null;
}
