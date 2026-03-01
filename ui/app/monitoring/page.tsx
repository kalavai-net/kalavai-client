'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { 
  BarChart3, 
  Cpu, 
  MemoryStick, 
  Monitor, 
  Loader2, 
  ChevronDown,
  Check,
  X
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import kalavaiApi from '@/utils/api';

interface Device {
  name: string;
  status: string;
  [key: string]: any;
}

interface UsageData {
  cpu_hours: number;
  memory_hours: number;
  gpu_hours: number;
}

interface TimeSeriesData {
  timestamp: string[];
  total_resources: number[];
  used_resources: number[];
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

function ResourceFilter({
  selectedResource,
  onResourceChange,
}: {
  selectedResource: string;
  onResourceChange: (resource: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  
  const resources = [
    { value: 'gpus', label: 'GPUs' },
    { value: 'cpus', label: 'CPUs' },
  ];

  const selectedRes = resources.find(res => res.value === selectedResource);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-card border border-border rounded-lg hover:bg-accent transition-colors"
      >
        <Cpu className="w-4 h-4" />
        <span className="text-sm">{selectedRes?.label || 'Select resource'}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-40 bg-card border border-border rounded-lg shadow-lg z-50">
          <div className="p-2">
            {resources.map((resource) => (
              <button
                key={resource.value}
                onClick={() => {
                  onResourceChange(resource.value);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                  selectedResource === resource.value
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                }`}
              >
                {resource.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DeviceFilter({
  devices,
  selectedDevices,
  onSelectionChange,
  isLoading
}: {
  devices: Device[];
  selectedDevices: string[];
  onSelectionChange: (devices: string[]) => void;
  isLoading: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = (deviceName: string) => {
    if (selectedDevices.includes(deviceName)) {
      onSelectionChange(selectedDevices.filter(d => d !== deviceName));
    } else {
      onSelectionChange([...selectedDevices, deviceName]);
    }
  };

  const handleSelectAll = () => {
    onSelectionChange(devices.map(d => d.name));
  };

  const handleClearAll = () => {
    onSelectionChange([]);
  };

  const isAllSelected = selectedDevices.length === devices.length && devices.length > 0;
  const isPartiallySelected = selectedDevices.length > 0 && selectedDevices.length < devices.length;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="flex items-center gap-2 px-4 py-2 bg-card border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50"
      >
        <BarChart3 className="w-4 h-4" />
        <span className="text-sm">
          {selectedDevices.length === 0 
            ? 'Select devices' 
            : `${selectedDevices.length} device${selectedDevices.length > 1 ? 's' : ''} selected`
          }
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-card border border-border rounded-lg shadow-lg z-50">
          <div className="p-3 border-b border-border">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-sm">Filter by Devices</h3>
              <div className="flex gap-2">
                <button
                  onClick={handleSelectAll}
                  className="text-xs px-2 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors"
                >
                  All
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
            ) : devices.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No devices available</p>
            ) : (
              <div className="space-y-1">
                {devices.map((device) => (
                  <label
                    key={device.name}
                    className="flex items-center gap-2 p-2 rounded hover:bg-accent cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedDevices.includes(device.name)}
                      onChange={() => handleToggle(device.name)}
                      className="rounded border-border"
                    />
                    <span className="text-sm flex-1">{device.name}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      device.status === 'online' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {device.status}
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
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

function OverallUsagePanel({ data, isLoading, timePeriod }: { data: UsageData; isLoading: boolean; timePeriod: string }) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Overall Usage</h2>
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
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Overall Usage</h2>
        <span className="text-sm text-muted-foreground">{getTimePeriodLabel(timePeriod)}</span>
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

function TimeSeriesPanel({ data, isLoading, timePeriod, resourceType }: { data: TimeSeriesData | null; isLoading: boolean; timePeriod: string; resourceType: string }) {
  const getTimePeriodLabel = (timeRange: string) => {
    switch (timeRange) {
      case '3d': return 'Last 3 days';
      case '7d': return 'Last week';
      case '15d': return 'Last 2 weeks';
      case '24h':
      default: return 'Last 24 hours';
    }
  };

  const getResourceLabels = (resource: string) => {
    if (resource === 'gpus') {
      return {
        title: 'GPU Usage Over Time',
        availableName: 'GPUs Available',
        usedName: 'GPUs Used',
        availableLegend: 'Total GPUs available',
        usedLegend: 'GPUs actually used by jobs'
      };
    } else {
      return {
        title: 'CPU Usage Over Time',
        availableName: 'CPUs Available',
        usedName: 'CPUs Used',
        availableLegend: 'Total CPUs available',
        usedLegend: 'CPUs actually used by jobs'
      };
    }
  };

  const labels = getResourceLabels(resourceType);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">{labels.title}</h2>
          <span className="text-sm text-muted-foreground">{getTimePeriodLabel(timePeriod)}</span>
        </div>
        <div className="flex items-center justify-center h-80">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (!data || !data.timestamp || data.timestamp.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">{labels.title}</h2>
          <span className="text-sm text-muted-foreground">{getTimePeriodLabel(timePeriod)}</span>
        </div>
        <div className="flex items-center justify-center h-80">
          <p className="text-muted-foreground">No time series data available</p>
        </div>
      </div>
    );
  }

  // Transform the data for the chart
  const chartData = data.timestamp.map((timestamp, index) => ({
    time: new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    availableResources: data.total_resources[index] || 0,
    usedResources: data.used_resources[index] || 0,
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{labels.title}</h2>
        <span className="text-sm text-muted-foreground">{getTimePeriodLabel(timePeriod)}</span>
      </div>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis 
              dataKey="time" 
              tick={{ fontSize: 12 }}
              tickLine={false}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              tickLine={false}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px'
              }}
            />
            <Legend />
            {/* Available GPU resources with lighter shade */}
            <Line 
              type="monotone" 
              dataKey="availableResources" 
              stroke="#60a5fa" 
              strokeWidth={2}
              fill="#60a5fa"
              fillOpacity={0.3}
              dot={false}
              name={labels.availableName}
            />
            {/* Used GPU resources with darker shade */}
            <Line 
              type="monotone" 
              dataKey="usedResources" 
              stroke="#2563eb" 
              strokeWidth={2}
              fill="#2563eb"
              fillOpacity={0.4}
              dot={false}
              name={labels.usedName}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-600 rounded"></div>
          <span>{labels.usedLegend}</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <div className="w-3 h-3 bg-blue-400 rounded"></div>
          <span>{labels.availableLegend}</span>
        </div>
      </div>
    </div>
  );
}


function MonitoringContent() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevices, setSelectedDevices] = useState<string[]>([]);
  const [appliedDevices, setAppliedDevices] = useState<string[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>('24h');
  const [appliedTimeRange, setAppliedTimeRange] = useState<string>('24h');
  const [selectedResource, setSelectedResource] = useState<string>('gpus');
  const [appliedResource, setAppliedResource] = useState<string>('gpus');
  const [isLoadingDevices, setIsLoadingDevices] = useState(true);
  const [isLoadingUsage, setIsLoadingUsage] = useState(true);
  const [isLoadingTimeSeries, setIsLoadingTimeSeries] = useState(true);
  const [usageData, setUsageData] = useState<UsageData>({
    cpu_hours: 0,
    memory_hours: 0,
    gpu_hours: 0
  });
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData | null>(null);

  useEffect(() => {
    loadDevices();
  }, []);

  useEffect(() => {
    if (appliedDevices.length > 0) {
      loadUsageData();
      loadTimeSeriesData();
    }
  }, [appliedDevices, appliedTimeRange, appliedResource]);

  const loadDevices = async () => {
    setIsLoadingDevices(true);
    try {
      const devicesData = await kalavaiApi.fetchDevices();
      setDevices(devicesData || []);
      const deviceNames = devicesData?.map((d: Device) => d.name) || [];
      setSelectedDevices(deviceNames);
      setAppliedDevices(deviceNames);
    } catch (error) {
      console.error('Error loading devices:', error);
      setDevices([]);
    } finally {
      setIsLoadingDevices(false);
    }
  };

  const getTimeRangeFromSelection = (timeRange: string) => {
    const now = new Date();
    const endTime = now.toISOString();
    let startTime: Date;
    
    switch (timeRange) {
      case '3d':
        startTime = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
        break;
      case '7d':
        startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '15d':
        startTime = new Date(now.getTime() - 15 * 24 * 60 * 60 * 1000);
        break;
      case '24h':
      default:
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
    }
    
    return {
      start_time: startTime.toISOString(),
      end_time: endTime
    };
  };

  const loadUsageData = async () => {
    setIsLoadingUsage(true);
    try {
      const { start_time, end_time } = getTimeRangeFromSelection(appliedTimeRange);

      console.log('Loading usage data for devices:', appliedDevices);
      console.log('Time range:', { start_time, end_time });

      const usageResponse = await kalavaiApi.getComputeUsage({
        start_time,
        end_time,
        node_names: appliedDevices
      });

      console.log('Raw API response:', usageResponse);

      // Convert raw values to hours and round to 2 decimal places
      const cpuHours = parseFloat((usageResponse.cpu / 3600).toFixed(2));
      const memoryHours = parseFloat(((usageResponse.ram / (1024 * 1024 * 1024)) / 3600).toFixed(2)); // Convert bytes to GB then to hours
      const gpuHours = parseFloat((usageResponse.gpus).toFixed(2));

      console.log('Converted values:', { cpuHours, memoryHours, gpuHours });

      setUsageData({
        cpu_hours: cpuHours,
        memory_hours: memoryHours,
        gpu_hours: gpuHours
      });
    } catch (error) {
      console.error('Error loading usage data:', error);
      // Keep mock data as fallback
    } finally {
      setIsLoadingUsage(false);
    }
  };

  const loadTimeSeriesData = async () => {
    setIsLoadingTimeSeries(true);
    try {
      const { start_time, end_time } = getTimeRangeFromSelection(appliedTimeRange);
      
      // Get the resources list based on selection
      const resources = appliedResource === 'gpus' 
        ? ['amd_com_gpu', 'nvidia_com_gpu'] 
        : ['cpu'];
      
      console.log('Loading time series data for devices:', appliedDevices);
      console.log('Time range:', { start_time, end_time });
      console.log('Resources:', resources);

      const metricsResponse = await kalavaiApi.fetchNodesMetrics({
        start_time,
        end_time,
        node_names: appliedDevices,
        resources,
        aggregate_results: true
      });

      console.log('Raw time series API response:', metricsResponse);
      setTimeSeriesData(metricsResponse);
    } catch (error) {
      console.error('Error loading time series data:', error);
      setTimeSeriesData(null);
    } finally {
      setIsLoadingTimeSeries(false);
    }
  };

  const handleApplyFilters = () => {
    setAppliedDevices([...selectedDevices]);
    setAppliedTimeRange(selectedTimeRange);
    setAppliedResource(selectedResource);
  };

  const hasPendingChanges = 
    JSON.stringify(selectedDevices.sort()) !== JSON.stringify(appliedDevices.sort()) ||
    selectedTimeRange !== appliedTimeRange ||
    selectedResource !== appliedResource;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Monitoring</h1>
      </div>

      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Filters</h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Devices:</span>
            <DeviceFilter
              devices={devices}
              selectedDevices={selectedDevices}
              onSelectionChange={setSelectedDevices}
              isLoading={isLoadingDevices}
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Time Range:</span>
            <TimeRangeFilter
              selectedTimeRange={selectedTimeRange}
              onTimeRangeChange={setSelectedTimeRange}
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Resource:</span>
            <ResourceFilter
              selectedResource={selectedResource}
              onResourceChange={setSelectedResource}
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
        <OverallUsagePanel data={usageData} isLoading={isLoadingUsage} timePeriod={appliedTimeRange} />
        <TimeSeriesPanel data={timeSeriesData} isLoading={isLoadingTimeSeries} timePeriod={appliedTimeRange} resourceType={appliedResource} />
      </div>
    </div>
  );
}

export default function MonitoringPage() {
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
      <MonitoringContent />
    </AppLayout>
  );
}
