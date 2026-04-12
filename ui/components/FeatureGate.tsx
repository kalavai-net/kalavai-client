'use client';

import React from 'react';
import { getFeatureFlag, FeatureFlags } from '@/utils/featureFlags';
import { FeatureNotAvailable } from './FeatureNotAvailable';

interface FeatureGateProps {
  feature: keyof FeatureFlags;
  featureName: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function FeatureGate({ feature, featureName, children, fallback }: FeatureGateProps) {
  const isEnabled = getFeatureFlag(feature);
  
  if (isEnabled) {
    return <>{children}</>;
  }
  
  if (fallback) {
    return <>{fallback}</>;
  }
  
  return <FeatureNotAvailable featureName={featureName} />;
}
