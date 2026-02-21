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
  total_jobs: number;
  online_jobs: number;
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
  const data = [
    { name: 'Available', value: value },
    { name: 'Used', value: Math.max(0, total - value) },
  ];

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <Icon className="w-5 h-5 text-primary" />
        <h3 className="font-medium">{title}</h3>
      </div>
      
      <div className="h-48">
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
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      
      <div className="text-center mt-2">
        <span className="text-2xl font-bold">{value}</span>
        <span className="text-muted-foreground"> / {total} {unit}</span>
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
            {value} <span className="text-sm text-muted-foreground">/ {total}</span>
          </p>
        </div>
      </div>
    </div>
  );
}

function DashboardContent() {
  const { selectedUserSpace } = useConnectionStore();
  const [isLoading, setIsLoading] = useState(true);
  const [resources, setResources] = useState<ResourceData>({
    total_cpus: 0,
    online_cpus: 0,
    total_gpus: 0,
    online_gpus: 0,
    total_ram: 0,
    online_ram: 0,
    total_jobs: 0,
    online_jobs: 0,
    total_devices: 0,
    online_devices: 0,
  });

  useEffect(() => {
    loadData();
  }, [selectedUserSpace]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [resourcesData, jobNames] = await Promise.all([
        kalavaiApi.fetchResources(),
        kalavaiApi.fetchJobNames(),
      ]);

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
        total_jobs: jobNames?.length || 0,
        online_jobs: jobNames?.length || 0,
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Devices"
            value={resources.online_devices}
            total={resources.total_devices}
            icon={Server}
          />
          <StatCard
            title="Jobs"
            value={resources.online_jobs}
            total={resources.total_jobs}
            icon={Briefcase}
          />
          <StatCard
            title="CPUs"
            value={resources.online_cpus}
            total={resources.total_cpus}
            icon={Cpu}
          />
          <StatCard
            title="GPUs"
            value={resources.online_gpus}
            total={resources.total_gpus}
            icon={Monitor}
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
            value={Math.round(resources.online_ram)}
            total={Math.round(resources.total_ram)}
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
