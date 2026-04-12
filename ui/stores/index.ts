import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import kalavaiApi from '@/utils/api';

// Helper function to convert Kubernetes memory units to GB
function convertK8sMemoryToGB(memoryStr: string): number {
  if (!memoryStr || memoryStr === '0') return 0;
  
  // Remove any whitespace
  const cleanStr = memoryStr.trim();
  
  // Extract number and unit
  const match = cleanStr.match(/^(\d+(?:\.\d+)?)([KMG]i)?$/);
  if (!match) return parseInt(cleanStr.replace(/\D/g, '')) || 0;
  
  const value = parseFloat(match[1]);
  const unit = match[2] || '';
  
  switch (unit) {
    case 'Ki': return value / (1024 * 1024);  // KiB to GB
    case 'Mi': return value / 1024;           // MiB to GB  
    case 'Gi': return value;                   // GiB to GB
    default: return value / (1024 * 1024 * 1024); // Bytes to GB
  }
}

// Helper function to convert Kubernetes CPU units to cores
function convertK8sCpuToCores(cpuStr: string): number {
  if (!cpuStr || cpuStr === '0') return 0;
  
  // Remove any whitespace
  const cleanStr = cpuStr.trim();
  
  // Extract number and unit
  const match = cleanStr.match(/^(\d+(?:\.\d+)?)(m)?$/);
  if (!match) return parseInt(cleanStr.replace(/\D/g, '')) || 0;
  
  const value = parseFloat(match[1]);
  const unit = match[2] || '';
  
  switch (unit) {
    case 'm': return value / 1000;  // millicores to cores
    default: return value;          // cores to cores
  }
}

interface AuthState {
  isLoggedIn: boolean;
  isLoading: boolean;
  loginErrorMessage: string;
  userKey: string;
  accessKey: string | null;
  
  // Actions
  setUserKey: (key: string) => void;
  authorize: (typedKey: string) => Promise<boolean>;
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
      
      authorize: async (typedKey: string) => {
        set({ isLoading: true, loginErrorMessage: '' });
        
        const { accessKey } = get();
        const isValid = typedKey === accessKey;
        
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
      console.log('[STORE DEBUG] Quota response:', quota);
      
      // Handle the structured response from API
      if (quota && typeof quota === 'object' && quota.quota && quota.used) {
        const hard = quota.quota || {};
        const used = quota.used || {};
        
        console.log('[STORE DEBUG] Processing quota - hard:', hard, 'used:', used);
        console.log('[STORE DEBUG] Available hard fields:', Object.keys(hard));
        console.log('[STORE DEBUG] Available used fields:', Object.keys(used));
        
        // Try different possible field names
        const cpuUsed = used['limits.cpu'] || used['cpu'] || '0';
        const cpuHard = hard['limits.cpu'] || hard['cpu'] || '0';
        const memoryUsed = used['limits.memory'] || used['memory'] || '0';
        const memoryHard = hard['limits.memory'] || hard['memory'] || '0';
        const gpuUsed = used['limits.nvidia.com/gpu'] || used['nvidia.com/gpu'] || '0';
        const gpuHard = hard['limits.nvidia.com/gpu'] || hard['nvidia.com/gpu'] || '0';
        
        console.log('[STORE DEBUG] Parsed values:', {
          cpuUsed, cpuHard, memoryUsed, memoryHard, gpuUsed, gpuHard
        });
        
        set({
          usedCpuQuota: convertK8sCpuToCores(cpuUsed),
          maxCpuQuota: convertK8sCpuToCores(cpuHard),
          usedGpuQuota: parseInt(gpuUsed),
          maxGpuQuota: parseInt(gpuHard),
          usedMemoryQuota: convertK8sMemoryToGB(memoryUsed),
          maxMemoryQuota: convertK8sMemoryToGB(memoryHard),
          userSpaceHasQuota: true,
        });
      } else if (Array.isArray(quota) && quota.length > 0) {
        // Fallback for array response (backward compatibility)
        const q = quota[0];
        const used = q.status?.used || {};
        const hard = q.status?.hard || {};
        
        set({
          usedCpuQuota: convertK8sCpuToCores(used['limits.cpu'] || '0'),
          maxCpuQuota: convertK8sCpuToCores(hard['limits.cpu'] || '0'),
          usedGpuQuota: parseInt(used['limits.nvidia.com/gpu'] || '0'),
          maxGpuQuota: parseInt(hard['limits.nvidia.com/gpu'] || '0'),
          usedMemoryQuota: convertK8sMemoryToGB(used['limits.memory'] || '0'),
          maxMemoryQuota: convertK8sMemoryToGB(hard['limits.memory'] || '0'),
          userSpaceHasQuota: true,
        });
      } else {
        console.log('[STORE DEBUG] No quota data found, setting userSpaceHasQuota to false');
        set({ userSpaceHasQuota: false });
      }
    } catch (error) {
      console.error('Error loading quota:', error);
      set({ userSpaceHasQuota: false });
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
        userSpaces: Array.isArray(spaces) ? spaces : [],
      });
      
      if (Array.isArray(spaces) && spaces.length > 0 && !get().selectedUserSpace) {
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
