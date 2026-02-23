'use client';

import React, { useState } from 'react';
import { useAuthStore, useThemeStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { Loader2, Moon, Sun, RefreshCw, Database, AlertTriangle, CheckCircle } from 'lucide-react';
import { kalavaiApi } from '@/utils/api';

function SettingsContent() {
  const { darkMode, setDarkMode } = useThemeStore();
  const [isUpdatingRepos, setIsUpdatingRepos] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const showMsg = (type: 'success' | 'error', text: string) => {
    setActionMsg({ type, text });
    setTimeout(() => setActionMsg(null), 4000);
  };

  const handleUpdateRepositories = async () => {
    setIsUpdatingRepos(true);
    try {
      const result = await kalavaiApi.updateRepositories();
      if (result?.error) {
        showMsg('error', `Failed to update repositories: ${result.error}`);
      } else {
        showMsg('success', 'Repositories updated successfully');
      }
    } catch (err) {
      showMsg('error', `Failed to update repositories: ${err}`);
    } finally {
      setIsUpdatingRepos(false);
    }
  };

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

      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="w-5 h-5 text-primary" />
            <div>
              <h2 className="font-semibold">Repositories</h2>
              <p className="text-sm text-muted-foreground">Update pool repositories</p>
            </div>
          </div>
          <button
            onClick={handleUpdateRepositories}
            disabled={isUpdatingRepos}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isUpdatingRepos ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Updating...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                Update Repositories
              </>
            )}
          </button>
        </div>
      </div>

      {/* Toast */}
      {actionMsg && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium border ${actionMsg.type === 'success' ? 'bg-green-100 text-green-800 border-green-200' : 'bg-red-100 text-red-800 border-red-200'}`}>
          {actionMsg.type === 'success' ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
          {actionMsg.text}
        </div>
      )}
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
