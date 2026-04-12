'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { Lock, ArrowLeft } from 'lucide-react';

interface FeatureNotAvailableProps {
  featureName: string;
}

export function FeatureNotAvailable({ featureName }: FeatureNotAvailableProps) {
  const router = useRouter();
  const { isLoggedIn, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return <LoginForm />;
  }

  return (
    <AppLayout>
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6">
        <div className="p-4 bg-muted rounded-full">
          <Lock className="w-12 h-12 text-muted-foreground" />
        </div>
        
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">Feature Not Available</h1>
          <p className="text-muted-foreground text-lg max-w-md">
            The {featureName} feature is currently disabled in your environment.
          </p>
        </div>

        <div className="space-y-4">
          <p className="text-sm text-muted-foreground max-w-md">
            This feature can be enabled by setting the appropriate environment variable. 
            Please contact your administrator if you need access to this feature.
          </p>
          
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Go Back
          </button>
        </div>
      </div>
    </AppLayout>
  );
}
