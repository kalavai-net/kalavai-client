'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { Pagination } from '@/components/Pagination';
import kalavaiApi from '@/utils/api';
import { Loader2, Server, CheckCircle, XCircle, Trash2, Tag, Settings, RefreshCw, ToggleLeft, ToggleRight, AlertTriangle, X } from 'lucide-react';

interface Device {
  name: string;
  ready: boolean;
  unschedulable: boolean;
  memory_pressure: boolean;
  disk_pressure: boolean;
  pid_pressure: boolean;
}

interface GpuInfo {
  node: string;
  models: string[];
  total: number;
  available: number;
  ready: boolean;
}

interface ResourceItem {
  node: string;
  models: string;
  used: number;
  total: number;
  issues: string;
  disabled: boolean;
  ready: boolean;
}

const RESOURCES_SHOWN = ['cpu', 'memory', 'nvidia.com/gpu', 'amd.com/gpu'];

function ResourcesContent() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resources, setResources] = useState<ResourceItem[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [nodeLabels, setNodeLabels] = useState<Record<string, string>>({});
  const [nodeResources, setNodeResources] = useState<Record<string, { available: string; total: string }>>({});
  const [nodeDetailLoading, setNodeDetailLoading] = useState(false);
  const [newLabelKey, setNewLabelKey] = useState('');
  const [newLabelValue, setNewLabelValue] = useState('');
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 10;

  const showMsg = (type: 'success' | 'error', text: string) => {
    setActionMsg({ type, text });
    setTimeout(() => setActionMsg(null), 4000);
  };

  useEffect(() => {
    loadResources();
  }, []);

  const loadResources = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [devicesResult, gpusResult] = await Promise.all([
        kalavaiApi.fetchDevices(),
        kalavaiApi.fetchGpus(),
      ]);

      if (devicesResult?.error) { setError(`Error fetching devices: ${devicesResult.error}`); return; }
      if (gpusResult?.error) { setError(`Error fetching GPUs: ${gpusResult.error}`); return; }

      const devices: Device[] = Array.isArray(devicesResult) ? devicesResult : [];
      const gpus: GpuInfo[] = Array.isArray(gpusResult) ? gpusResult : [];

      const deviceMap = new Map<string, Device>();
      devices.forEach((d) => deviceMap.set(d.name, d));

      const combined: ResourceItem[] = [];
      const gpuNodesSeen = new Set<string>();

      gpus.forEach((gpu) => {
        gpuNodesSeen.add(gpu.node);
        const device = deviceMap.get(gpu.node);
        const used = gpu.total > 0 ? 100 - Math.round((gpu.available / gpu.total) * 100) : 0;
        const issues: string[] = [];
        if (device?.memory_pressure) issues.push('memory_pressure');
        if (device?.disk_pressure) issues.push('disk_pressure');
        if (device?.pid_pressure) issues.push('pid_pressure');
        const modelList = Array.isArray(gpu.models) ? gpu.models : [];
        combined.push({
          node: gpu.node,
          models: modelList.join('\n') || '-',
          used,
          total: gpu.total,
          issues: issues.join(', '),
          disabled: device?.unschedulable ?? false,
          ready: device?.ready ?? gpu.ready,
        });
      });

      devices.forEach((device) => {
        if (gpuNodesSeen.has(device.name)) return;
        const issues: string[] = [];
        if (device.memory_pressure) issues.push('memory_pressure');
        if (device.disk_pressure) issues.push('disk_pressure');
        if (device.pid_pressure) issues.push('pid_pressure');
        combined.push({
          node: device.name,
          models: '-',
          used: 0,
          total: 0,
          issues: issues.join(', '),
          disabled: device.unschedulable,
          ready: device.ready,
        });
      });

      // Sort: not-ready first, then cordoned, then ready
      combined.sort((a, b) => {
        const scoreA = (!a.ready ? 2 : 0) + (a.disabled ? 1 : 0);
        const scoreB = (!b.ready ? 2 : 0) + (b.disabled ? 1 : 0);
        return scoreB - scoreA;
      });
      setResources(combined);
    } catch (err) {
      setError(`Failed to load resources: ${err}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCordonToggle = async (node: string, isDisabled: boolean) => {
    try {
      const result = isDisabled
        ? await kalavaiApi.uncordonNodes([node])
        : await kalavaiApi.cordonNodes([node]);
      if (result?.error) { showMsg('error', result.error); }
      else { showMsg('success', isDisabled ? `${node} uncordoned` : `${node} cordoned`); await loadResources(); }
    } catch (err) { showMsg('error', `Failed: ${err}`); }
  };

  const handleDelete = async (node: string) => {
    try {
      const result = await kalavaiApi.deleteNodes([node]);
      if (result?.error) { showMsg('error', result.error); }
      else {
        showMsg('success', `Node ${node} deleted`);
        setDeleteConfirm(null);
        if (selectedNode === node) setSelectedNode(null);
        await loadResources();
      }
    } catch (err) { showMsg('error', `Failed: ${err}`); }
  };

  const loadNodeDetails = async (nodeName: string) => {
    setSelectedNode(nodeName);
    setNodeDetailLoading(true);
    setNodeLabels({});
    setNodeResources({});
    try {
      const [labelsResult, resourcesResult] = await Promise.all([
        kalavaiApi.getNodeLabels([nodeName]),
        kalavaiApi.fetchResources([nodeName]),
      ]);

      // Labels response: { labels: { nodeName: { key: value, ... } } }
      setNodeLabels(labelsResult?.labels?.[nodeName] ?? {});

      // Resources response: { total: { cpu: x, memory: y, ... }, available: { ... } }
      if (!resourcesResult?.error) {
        const resMap: Record<string, { available: string; total: string }> = {};
        RESOURCES_SHOWN.forEach((key) => {
          const t = resourcesResult?.total?.[key];
          const a = resourcesResult?.available?.[key];
          if (t !== undefined || a !== undefined) {
            resMap[key] = { available: String(a ?? 0), total: String(t ?? 0) };
          }
        });
        setNodeResources(resMap);
      }
    } catch (err) {
      showMsg('error', `Failed to load node details: ${err}`);
    } finally {
      setNodeDetailLoading(false);
    }
  };

  const handleAddLabel = async () => {
    if (!selectedNode || !newLabelKey || !newLabelValue) return;
    try {
      const result = await kalavaiApi.addNodeLabels(selectedNode, { [newLabelKey]: newLabelValue });
      if (result?.error) { showMsg('error', result.error); }
      else {
        showMsg('success', 'Label added');
        setNewLabelKey('');
        setNewLabelValue('');
        await loadNodeDetails(selectedNode);
      }
    } catch (err) { showMsg('error', `Failed: ${err}`); }
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
        <div>
          <h1 className="text-3xl font-bold">Resources</h1>
          <p className="text-muted-foreground">Available resources the pool is managing</p>
        </div>
        <button onClick={loadResources} className="flex items-center gap-2 px-3 py-2 border border-border rounded-md text-sm hover:bg-accent">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {actionMsg && (
        <div className={`px-4 py-3 rounded-md text-sm font-medium ${actionMsg.type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-red-100 text-red-800 border border-red-200'}`}>
          {actionMsg.text}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Node detail modal */}
      {selectedNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setSelectedNode(null)}>
          <div className="bg-card border border-border rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <div className="flex items-center gap-2">
                <Server className="w-5 h-5 text-primary" />
                <h2 className="font-semibold">{selectedNode}</h2>
              </div>
              <button onClick={() => setSelectedNode(null)} className="p-1 hover:bg-accent rounded">
                <X className="w-4 h-4" />
              </button>
            </div>

            {nodeDetailLoading ? (
              <div className="flex justify-center py-10">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
              </div>
            ) : (
              <div className="overflow-y-auto flex-1 p-5 space-y-5">
                <div>
                  <h3 className="text-xs font-semibold uppercase text-muted-foreground mb-2">Available Resources</h3>
                  {Object.keys(nodeResources).length === 0 ? (
                    <p className="text-sm text-muted-foreground">No resource data</p>
                  ) : (
                    <div className="space-y-1">
                      {Object.entries(nodeResources).map(([key, val]) => (
                        <div key={key} className="text-sm bg-muted px-3 py-1.5 rounded flex justify-between">
                          <span className="font-medium">{key}</span>
                          <span className="text-muted-foreground">{val.available} / {val.total}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h3 className="text-xs font-semibold uppercase text-muted-foreground mb-2 flex items-center gap-1">
                    <Tag className="w-3 h-3" /> Device Labels
                  </h3>
                  {Object.keys(nodeLabels).length === 0 ? (
                    <p className="text-sm text-muted-foreground">No labels</p>
                  ) : (
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {Object.entries(nodeLabels).map(([key, value]) => (
                        <div key={key} className="text-xs bg-muted px-3 py-1.5 rounded flex gap-2">
                          <span className="font-medium shrink-0">{key}:</span>
                          <span className="text-muted-foreground break-all">{value}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="mt-3 space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">Add new label</p>
                    <input type="text" placeholder="Key" value={newLabelKey} onChange={(e) => setNewLabelKey(e.target.value)}
                      className="w-full px-2 py-1.5 border border-border rounded text-sm bg-background" />
                    <input type="text" placeholder="Value" value={newLabelValue} onChange={(e) => setNewLabelValue(e.target.value)}
                      className="w-full px-2 py-1.5 border border-border rounded text-sm bg-background" />
                    <button onClick={handleAddLabel} className="w-full px-3 py-1.5 bg-primary text-primary-foreground rounded text-sm font-medium hover:bg-primary/90">
                      Add Label
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="bg-card border border-border rounded-lg overflow-hidden">
            {resources.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">No resources found in the pool.</div>
            ) : (
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium">Node</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">GPU Models</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">GPU Used</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {resources.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE).map((resource) => (
                    <tr
                      key={resource.node}
                      className="hover:bg-muted/50"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Server className="w-4 h-4 text-muted-foreground shrink-0" />
                          <span className="font-medium text-sm">{resource.node}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm whitespace-pre-line text-muted-foreground">{resource.models}</td>
                      <td className="px-4 py-3">
                        {resource.total > 0 ? (
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                              <div className="h-full bg-primary rounded-full" style={{ width: `${resource.used}%` }} />
                            </div>
                            <span className="text-xs text-muted-foreground">{resource.used}%</span>
                          </div>
                        ) : <span className="text-xs text-muted-foreground">—</span>}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1 flex-wrap">
                          {resource.ready ? (
                            <span className="flex items-center gap-1 text-xs text-green-700 bg-green-100 px-2 py-0.5 rounded">
                              <CheckCircle className="w-3 h-3" /> Ready
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-xs text-red-700 bg-red-100 px-2 py-0.5 rounded">
                              <XCircle className="w-3 h-3" /> Not Ready
                            </span>
                          )}
                          {resource.disabled && <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">Cordoned</span>}
                          {resource.issues && <span className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded" title={resource.issues}>Issues</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-1">
                          <button onClick={() => loadNodeDetails(resource.node)} className="p-1.5 hover:bg-accent rounded" title="View details">
                            <Settings className="w-4 h-4" />
                          </button>
                          <button onClick={() => handleCordonToggle(resource.node, resource.disabled)} className="p-1.5 hover:bg-accent rounded" title={resource.disabled ? 'Uncordon' : 'Cordon'}>
                            {resource.disabled ? <ToggleLeft className="w-4 h-4 text-yellow-500" /> : <ToggleRight className="w-4 h-4 text-green-500" />}
                          </button>
                          {deleteConfirm === resource.node ? (
                            <div className="flex items-center gap-1">
                              <button onClick={() => handleDelete(resource.node)} className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700">Confirm</button>
                              <button onClick={() => setDeleteConfirm(null)} className="px-2 py-1 text-xs border border-border rounded hover:bg-accent">Cancel</button>
                            </div>
                          ) : (
                            <button onClick={() => setDeleteConfirm(resource.node)} className="p-1.5 hover:bg-accent rounded" title="Delete node">
                              <Trash2 className="w-4 h-4 text-red-500" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <Pagination page={page} pageSize={PAGE_SIZE} total={resources.length} onPageChange={setPage} />
      </div>
    </div>
  );
}

export default function ResourcesPage() {
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
      <ResourcesContent />
    </AppLayout>
  );
}
