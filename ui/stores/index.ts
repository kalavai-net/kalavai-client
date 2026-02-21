import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import kalavaiApi from '@/utils/api';

interface AuthState {
  isLoggedIn: boolean;
  isLoading: boolean;
  loginErrorMessage: string;
  userKey: string;
  accessKey: string | null;
  
  // Actions
  setUserKey: (key: string) => void;
  authorize: (accessKey: string) => Promise<boolean>;
  signOut: () => void;
  setAccessKey: (key: string | null) => void;
}

interface ConnectionState {
  isConnected: boolean;
  agentRunning: boolean;
  isServer: boolean;
  userSpaces: string[];
  selectedUserSpace: string | null;
  userSpaceHasQuota: boolean;
  
  // Quota values
  usedCpuQuota: number;
  maxCpuQuota: number;
  usedGpuQuota: number;
  maxGpuQuota: number;
  usedMemoryQuota: number;
  maxMemoryQuota: number;
  
  // Computed
  cpuQuotaRatio: () => number;
  gpuQuotaRatio: () => number;
  memoryQuotaRatio: () => number;
  
  // Actions
  setUserSpace: (space: string) => Promise<void>;
  loadConnectionState: () => Promise<void>;
  refreshStatus: () => Promise<void>;
  updateConnected: (state: boolean) => void;
}

interface ThemeState {
  accentColor: string;
  grayColor: string;
  radius: string;
  scaling: string;
  darkMode: boolean;
  
  // Actions
  setAccentColor: (color: string) => void;
  setGrayColor: (color: string) => void;
  setRadius: (radius: string) => void;
  setScaling: (scaling: string) => void;
  setDarkMode: (dark: boolean) => void;
}

// Auth Store
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isLoggedIn: false,
      isLoading: false,
      loginErrorMessage: '',
      userKey: '',
      accessKey: null,
      
      setUserKey: (key: string) => set({ userKey: key }),
      
      setAccessKey: (key: string | null) => set({ accessKey: key }),
      
      authorize: async (accessKey: string) => {
        set({ isLoading: true, loginErrorMessage: '' });
        
        const { userKey } = get();
        const isValid = userKey === accessKey;
        
        set({
          isLoggedIn: isValid || !accessKey,
          loginErrorMessage: isValid || !accessKey ? '' : 'Invalid user key',
          isLoading: false,
        });
        
        return isValid || !accessKey;
      },
      
      signOut: () => {
        set({
          isLoggedIn: false,
          loginErrorMessage: '',
          userKey: '',
        });
      },
    }),
    {
      name: 'kalavai-auth-storage',
    }
  )
);

// Connection Store
export const useConnectionStore = create<ConnectionState>()((set, get) => ({
  isConnected: false,
  agentRunning: false,
  isServer: false,
  userSpaces: [],
  selectedUserSpace: null,
  userSpaceHasQuota: false,
  
  usedCpuQuota: 0,
  maxCpuQuota: 0,
  usedGpuQuota: 0,
  maxGpuQuota: 0,
  usedMemoryQuota: 0,
  maxMemoryQuota: 0,
  
  cpuQuotaRatio: () => {
    const { maxCpuQuota, usedCpuQuota } = get();
    return maxCpuQuota === 0 ? 0 : Math.round((usedCpuQuota / maxCpuQuota) * 100);
  },
  
  gpuQuotaRatio: () => {
    const { maxGpuQuota, usedGpuQuota } = get();
    return maxGpuQuota === 0 ? 0 : Math.round((usedGpuQuota / maxGpuQuota) * 100);
  },
  
  memoryQuotaRatio: () => {
    const { maxMemoryQuota, usedMemoryQuota } = get();
    return maxMemoryQuota === 0 ? 0 : Math.round((usedMemoryQuota / maxMemoryQuota) * 100);
  },
  
  setUserSpace: async (space: string) => {
    set({ selectedUserSpace: space, userSpaceHasQuota: false });
    
    try {
      const quota = await kalavaiApi.getUserSpaceQuota(space);
      
      if (Array.isArray(quota) && quota.length > 0) {
        const q = quota[0];
        const used = q.status?.used || {};
        const hard = q.status?.hard || {};
        
        set({
          usedCpuQuota: parseInt(used['limits.cpu'] || '0'),
          maxCpuQuota: parseInt(hard['limits.cpu'] || '0'),
          usedGpuQuota: parseInt(used['limits.nvidia.com/gpu'] || '0'),
          maxGpuQuota: parseInt(hard['limits.nvidia.com/gpu'] || '0'),
          usedMemoryQuota: parseInt((used['limits.memory'] || '0').replace(/\D/g, '')),
          maxMemoryQuota: parseInt((hard['limits.memory'] || '0').replace(/\D/g, '')),
          userSpaceHasQuota: true,
        });
      }
    } catch (error) {
      console.error('Error loading quota:', error);
    }
  },
  
  loadConnectionState: async () => {
    try {
      const [isConnected, spaces] = await Promise.all([
        kalavaiApi.isConnected(),
        kalavaiApi.getAvailableUserSpaces(),
      ]);
      
      set({
        isConnected,
        userSpaces: spaces || [],
      });
      
      if (spaces && spaces.length > 0 && !get().selectedUserSpace) {
        await get().setUserSpace(spaces[0]);
      }
    } catch (error) {
      console.error('Error loading connection state:', error);
    }
  },
  
  refreshStatus: async () => {
    try {
      const [agentRunning, connectedToServer, isServer] = await Promise.all([
        kalavaiApi.isAgentRunning(),
        kalavaiApi.isConnected(),
        kalavaiApi.isServer(),
      ]);
      
      set({
        agentRunning,
        isConnected: connectedToServer,
        isServer,
      });
    } catch (error) {
      console.error('Error refreshing status:', error);
    }
  },
  
  updateConnected: (state: boolean) => set({ isConnected: state }),
}));

function applyDarkMode(dark: boolean) {
  if (typeof document !== 'undefined') {
    if (dark) {
      document.documentElement.classList.remove('light');
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.classList.add('light');
    }
  }
}

// Theme Store
export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      accentColor: 'grass',
      grayColor: 'gray',
      radius: 'large',
      scaling: '100%',
      darkMode: true,
      
      setAccentColor: (color: string) => set({ accentColor: color }),
      setGrayColor: (color: string) => set({ grayColor: color }),
      setRadius: (radius: string) => set({ radius }),
      setScaling: (scaling: string) => set({ scaling }),
      setDarkMode: (dark: boolean) => {
        applyDarkMode(dark);
        set({ darkMode: dark });
      },
    }),
    {
      name: 'kalavai-theme-storage',
      onRehydrateStorage: () => (state) => {
        if (state) applyDarkMode(state.darkMode);
      },
    }
  )
);
