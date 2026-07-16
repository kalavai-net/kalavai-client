'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { FeatureGate } from '@/components/FeatureGate';
import { Pagination } from '@/components/Pagination';
import kalavaiApi from '@/utils/api';
import { Loader2, Server, CheckCircle, XCircle, Trash2, Tag, Settings, RefreshCw, ToggleLeft, ToggleRight, AlertTriangle, X } from 'lucide-react';

interface DeviceStatus {
  name: string;
  ready: boolean;
  unschedulable: boolean;
  memory_pressure: boolean;
  disk_pressure: boolean;
  pid_pressure: boolean;
}

interface NodeResources {
  cpu: number;
  memory: number;
  'ephemeral-storage': number;
  gpus: Array<{
    name?: string;
    gpu_id?: string;
    vram: number;
  }>;
}

interface NodeResourceData {
  total: NodeResources;
  available: NodeResources;
}

interface ResourceItem {
  node: string;
  ready: boolean;
  unschedulable: boolean;
  memory_pressure: boolean;
  disk_pressure: boolean;
  pid_pressure: boolean;
  cpus: { total: number; available: number };
  memory: { total: number; available: number };
  storage: { total: number; available: number };
  gpus: Array<{
    name: string;
    vram: number;
  }>;
  total_gpu_vram: number;
  available_gpu_vram: number;
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

function ResourcesContent() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resources, setResources] = useState<ResourceItem[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [nodeLabels, setNodeLabels] = useState<Record<string, string>>({});
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
      // Step 1: Get all devices from backend
      const devicesResult = await kalavaiApi.fetchDevices();
      if (devicesResult?.error) {
        setError(`Error fetching devices: ${devicesResult.error}`);
        return;
      }

      const devices: DeviceStatus[] = Array.isArray(devicesResult) ? devicesResult : [];
      const deviceMap = new Map<string, DeviceStatus>();
      devices.forEach((d) => deviceMap.set(d.name, d));

      // Step 2: Get node names and fetch resources for them
      const nodeNames = devices.map((d) => d.name);
      console.log('Fetching resources for nodes:', nodeNames);
      const resourcesResult = await kalavaiApi.fetchResources(nodeNames, true);
      console.log('Resources result:', resourcesResult);
      
      if (resourcesResult?.error) {
        setError(`Error fetching resources: ${resourcesResult.error}`);
        return;
      }

      // Step 3: Cross-reference device status with resource availability
      const combined: ResourceItem[] = [];
      
      devices.forEach((device) => {
        // When node names are passed with detailed=True, the response has total/available sections keyed by node name
        const totalData = resourcesResult?.total?.[device.name] as NodeResources | undefined;
        const availableData = resourcesResult?.available?.[device.name] as NodeResources | undefined;
        
        // Calculate total and available GPU vRAM
        const totalGpuVram = totalData?.gpus?.reduce((sum: number, gpu: any) => sum + (gpu.vram || 0), 0) ?? 0;
        const availableGpuVram = availableData?.gpus?.reduce((sum: number, gpu: any) => sum + (gpu.vram || 0), 0) ?? 0;
        
        combined.push({
          node: device.name,
          ready: device.ready,
          unschedulable: device.unschedulable,
          memory_pressure: device.memory_pressure,
          disk_pressure: device.disk_pressure,
          pid_pressure: device.pid_pressure,
          cpus: {
            total: totalData?.cpu ?? 0,
            available: availableData?.cpu ?? 0,
          },
          memory: {
            total: totalData?.memory ?? 0,
            available: availableData?.memory ?? 0,
          },
          storage: {
            total: totalData?.['ephemeral-storage'] ?? 0,
            available: availableData?.['ephemeral-storage'] ?? 0,
          },
          gpus: availableData?.gpus?.map((gpu: any) => ({
            name: gpu.name || gpu.gpu_id,
            vram: gpu.vram,
          })) ?? [],
          total_gpu_vram: totalGpuVram,
          available_gpu_vram: availableGpuVram,
        });
      });

      // Sort: not-ready first, then cordoned, then ready
      combined.sort((a, b) => {
        const scoreA = (!a.ready ? 2 : 0) + (a.unschedulable ? 1 : 0);
        const scoreB = (!b.ready ? 2 : 0) + (b.unschedulable ? 1 : 0);
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
    try {
      const labelsResult = await kalavaiApi.getNodeLabels([nodeName]);
      // Labels response: { labels: { nodeName: { key: value, ... } } }
      setNodeLabels(labelsResult?.labels?.[nodeName] ?? {});
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
        <button onClick={() => loadResources()} className="flex items-center gap-2 px-3 py-2 border border-border rounded-md text-sm hover:bg-accent">
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

      {/* Consolidated Resources Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {resources.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">No resources found in the pool.</div>
        ) : (
          <table className="w-full">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Node</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Available resources</th>
                <th className="px-4 py-3 text-left text-sm font-medium">GPUs</th>
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
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    <div className="space-y-1">
                      <div className="text-xs">
                        <span className="font-medium">CPU:</span> {resource.cpus.available} / {resource.cpus.total}
                      </div>
                      <div className="text-xs">
                        <span className="font-medium">Memory:</span> {formatBytes(resource.memory.available)} / {formatBytes(resource.memory.total)}
                      </div>
                      <div className="text-xs">
                        <span className="font-medium">Storage:</span> {formatBytes(resource.storage.available)} / {formatBytes(resource.storage.total)}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {resource.gpus.length > 0 ? (
                      <div className="space-y-2">
                        <div className="space-y-1">
                          {resource.gpus.map((gpu, idx) => (
                            <div key={idx} className="text-xs text-muted-foreground">
                              {gpu.name}
                            </div>
                          ))}
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>vRAM</span>
                            <span>{formatBytes(resource.total_gpu_vram - resource.available_gpu_vram)} / {formatBytes(resource.total_gpu_vram)}</span>
                          </div>
                          <div className="w-full bg-muted rounded-full h-2">
                            <div 
                              className="bg-primary h-2 rounded-full transition-all"
                              style={{ width: `${resource.total_gpu_vram > 0 ? ((resource.total_gpu_vram - resource.available_gpu_vram) / resource.total_gpu_vram) * 100 : 0}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
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
                      {resource.unschedulable && <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">Cordoned</span>}
                      {resource.memory_pressure && <span className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded">Memory Pressure</span>}
                      {resource.disk_pressure && <span className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded">Disk Pressure</span>}
                      {resource.pid_pressure && <span className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded">PID Pressure</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center gap-1">
                      <button onClick={() => loadNodeDetails(resource.node)} className="p-1.5 hover:bg-accent rounded" title="View details">
                        <Settings className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleCordonToggle(resource.node, resource.unschedulable)} className="p-1.5 hover:bg-accent rounded" title={resource.unschedulable ? 'Uncordon' : 'Cordon'}>
                        {resource.unschedulable ? <ToggleLeft className="w-4 h-4 text-yellow-500" /> : <ToggleRight className="w-4 h-4 text-green-500" />}
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
    <FeatureGate feature="SHOW_RESOURCES" featureName="Resources">
      <AppLayout>
        <ResourcesContent />
      </AppLayout>
    </FeatureGate>
  );
}
