'use client';

import { useEffect, useState } from 'react';
import { useConnectionStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { useAuthStore } from '@/stores';
import { Cpu, Monitor, MemoryStick, Server, Briefcase, AlertCircle, Loader2 } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import kalavaiApi from '@/utils/api';

const COLORS = ['#22c55e', '#ef4444'];

interface ResourceData {
  total_cpus: number;
  online_cpus: number;
  total_gpus: number;
  online_gpus: number;
  total_ram: number;
  online_ram: number;
  total_devices: number;
  online_devices: number;
}

function GaugeCard({
  title,
  icon: Icon,
  value,
  total,
  unit,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  value: number;
  total: number;
  unit: string;
}) {
  const usedPct = total === 0 ? 0 : Math.min(100, ((total - value) / total) * 100);
  const data = [
    { name: 'Available', value: value },
    { name: 'Used', value: Math.max(0, total - value) },
  ];

  const fmt = (n: number) => parseFloat(n.toFixed(2));

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <Icon className="w-5 h-5 text-primary" />
        <h3 className="font-medium">{title}</h3>
      </div>
      
      <div className="h-48 relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              startAngle={90}
              endAngle={-270}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index]} />
              ))}
            </Pie>
            <Tooltip formatter={(v: number) => parseFloat(v.toFixed(2))} />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <span className="text-xl font-bold text-foreground">{usedPct.toFixed(1)}%</span>
        </div>
      </div>
      
      <div className="text-center mt-2">
        <span className="text-2xl font-bold">{fmt(value)}</span>
        <span className="text-muted-foreground"> / {fmt(total)} {unit}</span>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  total,
  icon: Icon,
}: {
  title: string;
  value: number;
  total: number;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-xl font-semibold">
            {parseFloat(value.toFixed(2))} <span className="text-sm text-muted-foreground">/ {parseFloat(total.toFixed(2))}</span>
          </p>
        </div>
      </div>
    </div>
  );
}

function DashboardContent() {
  const { selectedUserSpace } = useConnectionStore();
  const [isLoading, setIsLoading] = useState(true);
  const [jobCount, setJobCount] = useState(0);
  const [resources, setResources] = useState<ResourceData>({
    total_cpus: 0,
    online_cpus: 0,
    total_gpus: 0,
    online_gpus: 0,
    total_ram: 0,
    online_ram: 0,
    total_devices: 0,
    online_devices: 0,
  });

  useEffect(() => {
    loadData();
  }, [selectedUserSpace]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      console.log('Dashboard: Loading data...');
      const [resourcesData, jobDetails] = await Promise.all([
        kalavaiApi.fetchResources(),
        kalavaiApi.fetchJobDetails(selectedUserSpace ?? undefined),
      ]);

      console.log('Dashboard: Raw resources response:', resourcesData);
      console.log('Dashboard: Resources keys:', Object.keys(resourcesData || {}));
      console.log('Dashboard: Resources total:', resourcesData?.total);
      console.log('Dashboard: Resources available:', resourcesData?.available);

      setJobCount(Array.isArray(jobDetails) ? jobDetails.length : 0);

      let totalGpus = 0;
      let onlineGpus = 0;
      
      ['nvidia.com/gpu', 'amd.com/gpu'].forEach((backend) => {
        if (resourcesData.total?.[backend]) {
          totalGpus += resourcesData.total[backend];
        }
        if (resourcesData.available?.[backend]) {
          onlineGpus += resourcesData.available[backend];
        }
      });

      setResources({
        total_cpus: resourcesData.total?.cpu || 0,
        online_cpus: resourcesData.available?.cpu || 0,
        total_gpus: totalGpus,
        online_gpus: onlineGpus,
        total_ram: (resourcesData.total?.memory || 0) / 1000000000,
        online_ram: (resourcesData.available?.memory || 0) / 1000000000,
        total_devices: resourcesData.total?.n_nodes || 0,
        online_devices: resourcesData.available?.n_nodes || 0,
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Welcome!</h1>
        {selectedUserSpace && (
          <div className="text-sm text-muted-foreground">
            Space: <span className="font-medium">{selectedUserSpace}</span>
          </div>
        )}
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-4">Pool Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StatCard
            title="Devices"
            value={resources.online_devices}
            total={resources.total_devices}
            icon={Server}
          />
          <StatCard
            title="Jobs"
            value={jobCount}
            total={jobCount}
            icon={Briefcase}
          />
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-4">Resources</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <GaugeCard
            title="CPUs"
            icon={Cpu}
            value={resources.online_cpus}
            total={resources.total_cpus}
            unit="cores"
          />
          <GaugeCard
            title="GPUs"
            icon={Monitor}
            value={resources.online_gpus}
            total={resources.total_gpus}
            unit="GPUs"
          />
          <GaugeCard
            title="RAM"
            icon={MemoryStick}
            value={resources.online_ram}
            total={resources.total_ram}
            unit="GB"
          />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
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
      <DashboardContent />
    </AppLayout>
  );
}
