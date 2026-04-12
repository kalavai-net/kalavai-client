'use client';

import { useEffect, useState } from 'react';
import { useAuthStore, useConnectionStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { 
  BarChart3, 
  Cpu, 
  MemoryStick, 
  Monitor, 
  Loader2, 
  ChevronDown
} from 'lucide-react';
import kalavaiApi from '@/utils/api';

interface UsageData {
  cpu_hours: number;
  memory_hours: number;
  gpu_hours: number;
}

interface NodeLabel {
  key: string;
  value: string;
  displayString: string;
}

function UsageStatCard({
  title,
  value,
  icon: Icon,
  unit
}: {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  unit: string;
}) {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <h3 className="font-medium text-sm text-muted-foreground">{title}</h3>
      </div>
      <div className="text-2xl font-bold">
        {value.toFixed(2)}
        <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>
      </div>
    </div>
  );
}

function UserSpaceSelector({
  selectedUserSpace,
  onUserSpaceChange,
  userSpaces,
  isLoading
}: {
  selectedUserSpace: string | null;
  onUserSpaceChange: (userSpace: string | null) => void;
  userSpaces: string[];
  isLoading: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (userSpace: string | null) => {
    onUserSpaceChange(userSpace);
    setIsOpen(false);
  };

  const selectedLabel = selectedUserSpace || 'Select user space';

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="flex items-center gap-2 px-3 py-1.5 bg-card border border-border rounded-lg hover:bg-accent transition-colors text-sm disabled:opacity-50"
      >
        <span>{selectedLabel}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-48 bg-card border border-border rounded-lg shadow-lg z-50">
          <div className="p-2">
            {userSpaces.map((userSpace) => (
              <button
                key={userSpace}
                onClick={() => handleSelect(userSpace)}
                className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                  selectedUserSpace === userSpace
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                }`}
              >
                {userSpace}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TimeRangeFilter({
  selectedTimeRange,
  onTimeRangeChange,
}: {
  selectedTimeRange: string;
  onTimeRangeChange: (timeRange: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  
  const timeRanges = [
    { value: '24h', label: 'Last 24 hours' },
    { value: '3d', label: 'Last 3 days' },
    { value: '7d', label: 'Last week' },
    { value: '15d', label: 'Last 2 weeks' },
  ];

  const selectedRange = timeRanges.find(range => range.value === selectedTimeRange);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-card border border-border rounded-lg hover:bg-accent transition-colors"
      >
        <Monitor className="w-4 h-4" />
        <span className="text-sm">{selectedRange?.label || 'Select time range'}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-48 bg-card border border-border rounded-lg shadow-lg z-50">
          <div className="p-2">
            {timeRanges.map((range) => (
              <button
                key={range.value}
                onClick={() => {
                  onTimeRangeChange(range.value);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                  selectedTimeRange === range.value
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function LabelFilter({
  selectedLabels,
  onSelectionChange,
  isLoading
}: {
  selectedLabels: Record<string, string>;
  onSelectionChange: (labels: Record<string, string>) => void;
  isLoading: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [availableLabels, setAvailableLabels] = useState<NodeLabel[]>([]);

  useEffect(() => {
    if (isOpen) {
      loadNodeLabels();
    }
  }, [isOpen]);

  const loadNodeLabels = async () => {
    try {
      console.log('=== LOAD NODE LABELS FOR DROPDOWN ===');
      const response = await kalavaiApi.getNodeLabels();
      console.log('Raw node labels response:', response);
      
      const labelsDict = response.labels || {};
      console.log('Labels dictionary:', labelsDict);
      
      // Extract unique labels from all nodes
      const uniqueLabels = new Set<string>();
      Object.values(labelsDict).forEach((nodeLabels: any) => {
        if (nodeLabels && typeof nodeLabels === 'object') {
          Object.entries(nodeLabels).forEach(([key, value]) => {
            uniqueLabels.add(`${key}=${value}`);
          });
        }
      });

      console.log('Unique labels set:', Array.from(uniqueLabels));

      // Convert to array of NodeLabel objects
      const labelsArray = Array.from(uniqueLabels).map(labelString => {
        const [key, value] = labelString.split('=');
        return {
          key,
          value,
          displayString: labelString
        };
      }).sort((a, b) => a.displayString.localeCompare(b.displayString));

      console.log('Processed labels array:', labelsArray);
      setAvailableLabels(labelsArray);
    } catch (error: any) {
      console.error('Error loading node labels:', error);
      console.error('Error details:', error.response?.data || error.message);
      setAvailableLabels([]);
    }
  };

  const handleToggle = (label: NodeLabel) => {
    // Single selection mode: replace current selection
    const labelKey = `${label.key}=${label.value}`;
    
    if (selectedLabels[labelKey]) {
      // If clicking the same label, deselect it
      onSelectionChange({});
    } else {
      // Select only this label (single selection mode)
      onSelectionChange({ [labelKey]: label.value });
    }
  };

  const handleSelectAll = () => {
    // In single selection mode, select all doesn't make sense
    // Let's select the first label instead
    if (availableLabels.length > 0) {
      const firstLabel = availableLabels[0];
      const labelKey = `${firstLabel.key}=${firstLabel.value}`;
      onSelectionChange({ [labelKey]: firstLabel.value });
    }
  };

  const handleClearAll = () => {
    onSelectionChange({});
  };

  const selectedLabelKey = Object.keys(selectedLabels)[0]; // Get the single selected label
  const isAllSelected = availableLabels.length > 0 && availableLabels.length === 1 && 
    selectedLabelKey === `${availableLabels[0].key}=${availableLabels[0].value}`;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="flex items-center gap-2 px-4 py-2 bg-card border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50"
      >
        <BarChart3 className="w-4 h-4" />
        <span className="text-sm">
          {Object.keys(selectedLabels).length === 0 
            ? 'Select label' 
            : `1 label selected`
          }
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-card border border-border rounded-lg shadow-lg z-50">
          <div className="p-3 border-b border-border">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-sm">Filter by Node Label (Single Selection)</h3>
              <div className="flex gap-2">
                <button
                  onClick={handleSelectAll}
                  className="text-xs px-2 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors"
                >
                  First
                </button>
                <button
                  onClick={handleClearAll}
                  className="text-xs px-2 py-1 bg-muted text-muted-foreground rounded hover:bg-muted/80 transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
          
          <div className="max-h-60 overflow-y-auto p-2">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            ) : availableLabels.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No labels available</p>
            ) : (
              <div className="space-y-1">
                {availableLabels.map((label) => {
                  const labelKey = `${label.key}=${label.value}`;
                  return (
                    <label
                      key={labelKey}
                      className="flex items-center gap-2 p-2 rounded hover:bg-accent cursor-pointer"
                    >
                      <input
                        type="radio"
                        name="label-selection"
                        checked={!!selectedLabels[labelKey]}
                        onChange={() => handleToggle(label)}
                        className="rounded border-border"
                      />
                      <span className="text-sm flex-1">{label.displayString}</span>
                    </label>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function UsagePanel({ 
  data, 
  isLoading, 
  timePeriod, 
  selectedUserSpace,
  onUserSpaceChange,
  userSpaces 
}: { 
  data: UsageData; 
  isLoading: boolean; 
  timePeriod: string;
  selectedUserSpace: string | null;
  onUserSpaceChange: (userSpace: string | null) => void;
  userSpaces: string[];
}) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Resource Usage</h2>
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  const getTimePeriodLabel = (timeRange: string) => {
    switch (timeRange) {
      case '3d': return 'Last 3 days';
      case '7d': return 'Last week';
      case '15d': return 'Last 2 weeks';
      case '24h':
      default: return 'Last 24 hours';
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Resource Usage</h2>
        <div className="flex items-center gap-3">
          <UserSpaceSelector
            selectedUserSpace={selectedUserSpace}
            onUserSpaceChange={onUserSpaceChange}
            userSpaces={userSpaces}
            isLoading={isLoading}
          />
          <span className="text-sm text-muted-foreground">{getTimePeriodLabel(timePeriod)}</span>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <UsageStatCard
          title="CPU Usage"
          value={data.cpu_hours}
          icon={Cpu}
          unit="hours"
        />
        <UsageStatCard
          title="Memory Usage"
          value={data.memory_hours}
          icon={MemoryStick}
          unit="GB-hours"
        />
        <UsageStatCard
          title="GPU Usage"
          value={data.gpu_hours}
          icon={Monitor}
          unit="hours"
        />
      </div>
    </div>
  );
}

function UsageContent() {
  const { userSpaces, selectedUserSpace, loadConnectionState } = useConnectionStore();
  const [selectedLabels, setSelectedLabels] = useState<Record<string, string>>({});
  const [appliedLabels, setAppliedLabels] = useState<Record<string, string>>({});
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>('24h');
  const [appliedTimeRange, setAppliedTimeRange] = useState<string>('24h');
  const [selectedUserSpaceForPanel, setSelectedUserSpaceForPanel] = useState<string | null>(selectedUserSpace);
  const [isLoadingLabels, setIsLoadingLabels] = useState(false);
  const [isLoadingUsage, setIsLoadingUsage] = useState(false);
  const [usageData, setUsageData] = useState<UsageData>({
    cpu_hours: 0,
    memory_hours: 0,
    gpu_hours: 0
  });

  useEffect(() => {
    // Load connection state to get user spaces
    loadConnectionState();
    // Auto-load labels when page loads
    loadNodeLabels();
  }, []);

  useEffect(() => {
    // Set default user space to selected user space when available
    if (selectedUserSpace && !selectedUserSpaceForPanel) {
      setSelectedUserSpaceForPanel(selectedUserSpace);
    }
  }, [selectedUserSpace, selectedUserSpaceForPanel]);

  useEffect(() => {
    // Auto-apply filters when user space changes (if labels are selected)
    if (selectedUserSpaceForPanel && Object.keys(selectedLabels).length > 0) {
      setAppliedLabels({ ...selectedLabels });
      setAppliedTimeRange(selectedTimeRange);
    }
  }, [selectedUserSpaceForPanel, selectedLabels, selectedTimeRange]);

  useEffect(() => {
    // Load data only when filters are applied and user space is selected
    if (selectedUserSpaceForPanel) {
      loadUsageData();
    }
  }, [appliedLabels, appliedTimeRange, selectedUserSpaceForPanel]);

  const loadNodeLabels = async () => {
    setIsLoadingLabels(true);
    try {
      console.log('=== AUTO LOAD NODE LABELS ===');
      const response = await kalavaiApi.getNodeLabels();
      console.log('Raw node labels response:', response);
      
      const labelsDict = response.labels || {};
      console.log('Labels dictionary:', labelsDict);
      
      // Extract unique labels from all nodes
      const uniqueLabels = new Set<string>();
      Object.values(labelsDict).forEach((nodeLabels: any) => {
        if (nodeLabels && typeof nodeLabels === 'object') {
          Object.entries(nodeLabels).forEach(([key, value]) => {
            uniqueLabels.add(`${key}=${value}`);
          });
        }
      });

      console.log('Unique labels set:', Array.from(uniqueLabels));

      // Convert to array of NodeLabel objects
      const labelsArray = Array.from(uniqueLabels).map(labelString => {
        const [key, value] = labelString.split('=');
        return {
          key,
          value,
          displayString: labelString
        };
      }).sort((a, b) => a.displayString.localeCompare(b.displayString));

      console.log('Processed labels array:', labelsArray);
      
      // Default to no labels selected (as requested)
      console.log('Defaulting to no labels selected');
      setSelectedLabels({});
      
      // Auto-apply with no labels (initial load)
      if (selectedUserSpaceForPanel) {
        setAppliedLabels({});
        setAppliedTimeRange(selectedTimeRange);
      }
    } catch (error: any) {
      console.error('Error loading node labels:', error);
      console.error('Error details:', error.response?.data || error.message);
    } finally {
      setIsLoadingLabels(false);
    }
  };

  const loadUsageData = async () => {
    if (!selectedUserSpaceForPanel) {
      console.log('No user space selected, skipping data load');
      return;
    }

    setIsLoadingUsage(true);
    try {
      console.log('=== LOAD USAGE DATA ===');
      console.log('Applied labels:', appliedLabels);
      console.log('Time range:', { start_time: appliedTimeRange, end_time: 'now' });
      console.log('User space:', selectedUserSpaceForPanel);

      // Convert selected labels to the format expected by the API
      // Since we only allow one label at a time, this is simple
      const nodeLabelsForApi: Record<string, string> = {};
      Object.entries(appliedLabels).forEach(([key, value]) => {
        const [labelKey, labelValue] = key.split('=');
        nodeLabelsForApi[labelKey] = labelValue;
      });
      
      console.log('Converted node labels for API:', nodeLabelsForApi);

      const requestPayload: any = {
        start_time: appliedTimeRange,
        end_time: 'now',
        node_labels: Object.keys(nodeLabelsForApi).length > 0 ? nodeLabelsForApi : undefined,
        namespaces: [selectedUserSpaceForPanel],
        step_seconds: 3600
      };
      
      console.log('API request payload:', JSON.stringify(requestPayload, null, 2));

      const response = await kalavaiApi.getComputeUsage(requestPayload);

      console.log('API response:', response);
      console.log('Response type:', typeof response);
      console.log('Response keys:', response ? Object.keys(response) : 'null/undefined');

      // Convert usage data
      const cpuValue = response?.cpu ?? 0;
      const ramValue = response?.ram ?? 0;
      const gpusValue = response?.gpus ?? 0;

      const usage = {
        cpu_hours: parseFloat(cpuValue.toFixed(2)),
        memory_hours: parseFloat((ramValue / (1024 * 1024 * 1024)).toFixed(2)),
        gpu_hours: parseFloat(gpusValue.toFixed(2))
      };

      console.log('Converted usage values:', usage);

      setUsageData(usage);
    } catch (error: any) {
      console.error('Error loading usage data:', error);
      console.error('Error details:', error.response?.data || error.message);
    } finally {
      setIsLoadingUsage(false);
    }
  };

  const handleApplyFilters = () => {
    setAppliedLabels({ ...selectedLabels });
    setAppliedTimeRange(selectedTimeRange);
  };

  const hasPendingChanges = 
    JSON.stringify(Object.keys(selectedLabels).sort()) !== JSON.stringify(Object.keys(appliedLabels).sort()) ||
    selectedTimeRange !== appliedTimeRange;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Usage</h1>
      </div>

      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Filters</h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Labels:</span>
            <LabelFilter
              selectedLabels={selectedLabels}
              onSelectionChange={setSelectedLabels}
              isLoading={isLoadingLabels}
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Time Range:</span>
            <TimeRangeFilter
              selectedTimeRange={selectedTimeRange}
              onTimeRangeChange={setSelectedTimeRange}
            />
          </div>
          <button
            onClick={handleApplyFilters}
            disabled={!hasPendingChanges || isLoadingUsage}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            {isLoadingUsage ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Applying...
              </div>
            ) : (
              'Apply Filters'
            )}
          </button>
        </div>
      </div>

      <div className="space-y-6">
        <UsagePanel 
          data={usageData} 
          isLoading={isLoadingUsage} 
          timePeriod={appliedTimeRange}
          selectedUserSpace={selectedUserSpaceForPanel}
          onUserSpaceChange={setSelectedUserSpaceForPanel}
          userSpaces={userSpaces}
        />
      </div>
    </div>
  );
}

export default function UsagePage() {
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
      <UsageContent />
    </AppLayout>
  );
}
