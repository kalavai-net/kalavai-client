'use client';

import { useEffect } from 'react';
import { useConnectionStore } from '@/stores';
import { Cpu, Monitor, MemoryStick, Layers, Infinity } from 'lucide-react';

function QuotaMeter({
  label,
  used,
  max,
  unit,
  icon: Icon,
  color,
}: {
  label: string;
  used: number;
  max: number;
  unit: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  const ratio = max === 0 ? 0 : Math.min(100, Math.round((used / max) * 100));
  const isHigh = ratio >= 80;
  const isMed = ratio >= 50;

  const barColor = isHigh
    ? 'bg-red-500'
    : isMed
    ? 'bg-yellow-400'
    : color;

  const textColor = isHigh
    ? 'text-red-400'
    : isMed
    ? 'text-yellow-400'
    : 'text-primary';

  return (
    <div className="flex-1 min-w-0 bg-muted/40 rounded-xl p-4 flex flex-col gap-3 border border-border/50">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className={`p-1.5 rounded-lg bg-primary/10`}>
            <Icon className="w-3.5 h-3.5 text-primary" />
          </div>
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {label}
          </span>
        </div>
        <span className={`text-xs font-bold tabular-nums ${textColor}`}>
          {ratio}%
        </span>
      </div>

      <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-1.5 rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${ratio}%` }}
        />
      </div>

      <div className="flex items-baseline gap-1">
        <span className="text-lg font-bold tabular-nums leading-none">{used}</span>
        <span className="text-xs text-muted-foreground">/ {max} {unit}</span>
      </div>
    </div>
  );
}

export function UserSpaceQuota() {
  const {
    userSpaces,
    selectedUserSpace,
    userSpaceHasQuota,
    usedCpuQuota,
    maxCpuQuota,
    usedGpuQuota,
    maxGpuQuota,
    usedMemoryQuota,
    maxMemoryQuota,
    setUserSpace,
    loadConnectionState,
  } = useConnectionStore();

  useEffect(() => {
    loadConnectionState();
  }, []);

  if (userSpaces.length === 0) {
    return null;
  }

  return (
    <div className="w-full bg-card border border-border rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2 min-w-0">
          <div className="p-1.5 rounded-lg bg-primary/10 shrink-0">
            <Layers className="w-4 h-4 text-primary" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold leading-none mb-0.5">
              User Space
            </p>
            <p className="text-sm font-semibold break-all">
              {selectedUserSpace ?? '—'}
            </p>
          </div>
        </div>

        <select
          value={selectedUserSpace ?? ''}
          onChange={(e) => setUserSpace(e.target.value)}
          className="text-xs bg-muted border border-border rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary text-foreground cursor-pointer min-w-0 max-w-[200px] truncate"
        >
          {userSpaces.map((space) => (
            <option key={space} value={space}>
              {space}
            </option>
          ))}
        </select>
      </div>

      {userSpaceHasQuota ? (
        <div className="flex gap-3">
          <QuotaMeter
            label="CPU"
            used={usedCpuQuota}
            max={maxCpuQuota}
            unit="cores"
            icon={Cpu}
            color="bg-primary"
          />
          <QuotaMeter
            label="GPU"
            used={usedGpuQuota}
            max={maxGpuQuota}
            unit="GPUs"
            icon={Monitor}
            color="bg-primary"
          />
          <QuotaMeter
            label="RAM"
            used={usedMemoryQuota}
            max={maxMemoryQuota}
            unit="GB"
            icon={MemoryStick}
            color="bg-primary"
          />
        </div>
      ) : (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Infinity className="w-4 h-4 shrink-0" />
          <span className="text-sm">Unlimited resources in this space</span>
        </div>
      )}
    </div>
  );
}
