'use client';

declare global {
  interface Window {
    env?: Record<string, string | undefined>;
  }
}

export interface FeatureFlags {
  SHOW_RESOURCES: boolean;
  SHOW_MONITORING: boolean;
  SHOW_USER_SPACES: boolean;
}

const DEFAULT_FEATURE_FLAGS: FeatureFlags = {
  SHOW_RESOURCES: true,
  SHOW_MONITORING: true,
  SHOW_USER_SPACES: true,
};

export function getFeatureFlag(flag: keyof FeatureFlags): boolean {
  // Check if we're in a browser environment
  if (typeof window === 'undefined') {
    return DEFAULT_FEATURE_FLAGS[flag];
  }

  // Get environment variable from window or process
  const envValue = window.env?.[flag] || process.env[flag];
  
  if (envValue === undefined) {
    return DEFAULT_FEATURE_FLAGS[flag];
  }

  // Parse boolean values
  if (typeof envValue === 'string') {
    return envValue.toLowerCase() === 'true';
  }

  return Boolean(envValue);
}

export function getAllFeatureFlags(): FeatureFlags {
  return {
    SHOW_RESOURCES: getFeatureFlag('SHOW_RESOURCES'),
    SHOW_MONITORING: getFeatureFlag('SHOW_MONITORING'),
    SHOW_USER_SPACES: getFeatureFlag('SHOW_USER_SPACES'),
  };
}
