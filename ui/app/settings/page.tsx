'use client';

import React from 'react';
import { useAuthStore, useThemeStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { Loader2, Moon, Sun } from 'lucide-react';

function SettingsContent() {
  const { darkMode, setDarkMode } = useThemeStore();

  return (
    <div className="space-y-8 max-w-xl">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Customize your dashboard appearance</p>
      </div>

      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {darkMode ? <Moon className="w-5 h-5 text-primary" /> : <Sun className="w-5 h-5 text-yellow-500" />}
            <div>
              <h2 className="font-semibold">Theme</h2>
              <p className="text-sm text-muted-foreground">{darkMode ? 'Dark mode' : 'Light mode'}</p>
            </div>
          </div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${
              darkMode ? 'bg-primary' : 'bg-muted-foreground/30'
            }`}
          >
            <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
              darkMode ? 'translate-x-6' : 'translate-x-1'
            }`} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { isLoggedIn, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!isLoggedIn) {
    return <LoginForm />;
  }

  return (
    <AppLayout>
      <SettingsContent />
    </AppLayout>
  );
}
