'use client';

import { useState, useEffect } from 'react';
import { useAuthStore, useConnectionStore } from '@/stores';
import { Loader2, Key, AlertCircle } from 'lucide-react';

interface LoginFormProps {
  accessKey?: string;
}

export function LoginForm({ accessKey }: LoginFormProps) {
  const [userKey, setUserKey] = useState('');
  const { authorize, setUserKey: saveUserKey, isLoading, loginErrorMessage, isLoggedIn } = useAuthStore();
  const { loadConnectionState } = useConnectionStore();

  // Auto-login if accessKey is provided
  useEffect(() => {
    if (accessKey && !isLoggedIn && !isLoading) {
      saveUserKey(accessKey);
      authorize(accessKey);
    }
  }, [accessKey, isLoggedIn, isLoading, saveUserKey, authorize]);

  useEffect(() => {
    if (isLoggedIn) {
      loadConnectionState();
    }
  }, [isLoggedIn, loadConnectionState]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    saveUserKey(userKey);
    await authorize(accessKey || '');
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-muted-foreground">Verifying user key...</p>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      <div className="w-full max-w-md">
        <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-semibold">Enter your user key</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Required for accessing the dashboard
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                User Key
              </label>
              <div className="relative">
                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="password"
                  value={userKey}
                  onChange={(e) => setUserKey(e.target.value)}
                  placeholder={accessKey ? 'Key pre-configured' : 'Enter your user key'}
                  disabled={!!accessKey}
                  className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                />
              </div>
            </div>

            {loginErrorMessage && (
              <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 p-3 rounded-md">
                <AlertCircle className="w-4 h-4" />
                {loginErrorMessage}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary text-primary-foreground py-2 rounded-md font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              Verify Key
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
