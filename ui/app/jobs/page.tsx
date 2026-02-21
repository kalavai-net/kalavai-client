'use client';

import { useEffect, useState, useRef } from 'react';
import { useAuthStore, useConnectionStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { Pagination } from '@/components/Pagination';
import kalavaiApi from '@/utils/api';
import { Loader2, ExternalLink, Trash2, Plus, X, RefreshCw, ChevronLeft, ChevronRight, AlertTriangle, CheckCircle, Info, Filter } from 'lucide-react';

interface Job {
  job_id: string;
  name: string;
  owner: string;
  status: string;
  workers: string;
  host_nodes: string;
  endpoint: Record<string, { address: string; port: string } | string>;
  spec?: Record<string, unknown>;
  conditions?: Record<string, unknown>;
}

interface Template { name: string; }

interface TemplateParam {
  name: string; type: string; default: unknown;
  description: string; required: boolean; options?: string[];
}

interface TemplateData {
  values: Record<string, unknown>;
  schema: { properties?: Record<string, { type: string; description?: string; enum?: unknown[] }>; required?: string[] };
  metadata: { name?: string; description?: string; icon?: string; sources?: string[]; version?: string };
}

function parseEndpointUrl(ep: { address: string; port: string } | string): string {
  if (typeof ep === 'string') return ep;
  return `http://${ep.address}:${ep.port}`;
}

function buildParams(data: TemplateData): Record<string, TemplateParam> {
  const params: Record<string, TemplateParam> = {};
  const required = data.schema?.required || [];
  Object.entries(data.values || {}).forEach(([name, value]) => {
    const schema = data.schema?.properties?.[name];
    if (!schema) return;
    if (schema.type === 'object' || schema.type === 'array') return;
    if (value !== null && typeof value === 'object') return;
    params[name] = {
      name, default: value,
      type: schema.enum ? 'enum' : schema.type,
      description: schema.description || '',
      required: required.includes(name),
      options: schema.enum as string[] | undefined,
    };
  });
  return params;
}

function statusBadge(status: string) {
  const cls = status === 'Running' ? 'bg-green-100 text-green-800' :
    status === 'Pending' ? 'bg-yellow-100 text-yellow-800' :
    status === 'Error' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800';
  return <span className={`px-2 py-0.5 rounded text-xs font-medium ${cls}`}>{status || '—'}</span>;
}

function ParamField({ param, value, onChange }: { param: TemplateParam; value: unknown; onChange: (v: unknown) => void }) {
  const base = 'w-full px-3 py-2 border border-border rounded-md text-sm bg-background';
  if (param.type === 'enum' && param.options) {
    return <select className={base} value={String(value ?? param.default ?? '')} onChange={e => onChange(e.target.value)}>
      {param.options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>;
  }
  if (param.type === 'integer' || param.type === 'number') {
    return <input type="number" className={base} value={String(value ?? param.default ?? '')}
      onChange={e => onChange(e.target.value === '' ? '' : Number(e.target.value))} />;
  }
  if (param.type === 'boolean') {
    return <label className="flex items-center gap-2 cursor-pointer">
      <input type="checkbox" checked={Boolean(value ?? param.default)} onChange={e => onChange(e.target.checked)} className="w-4 h-4" />
      <span className="text-sm">{String(value ?? param.default)}</span>
    </label>;
  }
  return <input type="text" className={base} value={String(value ?? param.default ?? '')} onChange={e => onChange(e.target.value)} />;
}

function ExpandableNodes({ nodes }: { nodes: string }) {
  const [expanded, setExpanded] = useState(false);
  const nodeList = nodes.split('\n').filter(Boolean);

  return (
    <span className="text-xs text-muted-foreground">
      <span className="font-medium text-foreground/60">nodes:</span>{' '}
      <button
        onClick={() => setExpanded(v => !v)}
        className="text-primary hover:underline"
      >
        {expanded ? 'hide' : `${nodeList.length} node${nodeList.length !== 1 ? 's' : ''}`}
      </button>
      {expanded && (
        <span className="block mt-0.5 space-y-0.5">
          {nodeList.map((n, i) => <span key={i} className="block">{n}</span>)}
        </span>
      )}
    </span>
  );
}

function JobsContent() {
  const { userSpaces, selectedUserSpace, loadConnectionState } = useConnectionStore();

  // Namespace filter: null means "all", otherwise the selected space name
  // undefined = not yet initialised (don't fetch yet)
  const [namespaceFilter, setNamespaceFilter] = useState<string | null | undefined>(undefined);
  const initialised = useRef(false);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 10;

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkDeleteConfirm, setBulkDeleteConfirm] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);

  // Service logs modal
  const [serviceLogsOpen, setServiceLogsOpen] = useState(false);
  const [serviceLogs, setServiceLogs] = useState('');
  const [serviceLogsLoading, setServiceLogsLoading] = useState(false);
  const [serviceLogTail, setServiceLogTail] = useState(100);

  // Deploy modal
  const [deployOpen, setDeployOpen] = useState(false);
  const [deployStep, setDeployStep] = useState(0);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [templateData, setTemplateData] = useState<TemplateData | null>(null);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [params, setParams] = useState<Record<string, TemplateParam>>({});
  const [formValues, setFormValues] = useState<Record<string, unknown>>({});
  const [jobName, setJobName] = useState('');
  const [deploying, setDeploying] = useState(false);
  const [availableLabels, setAvailableLabels] = useState<string[]>([]);
  const [selectedLabels, setSelectedLabels] = useState<Record<string, string[]>>({});
  const [labelMode, setLabelMode] = useState<'AND' | 'OR'>('AND');

  // Logs modal
  const [logsJob, setLogsJob] = useState<Job | null>(null);
  const [logsTab, setLogsTab] = useState<'job' | 'status' | 'logs'>('job');
  const [jobLogs, setJobLogs] = useState<Record<string, string>>({});
  const [jobMeta, setJobMeta] = useState('');
  const [jobStatus, setJobStatus] = useState('');
  const [logsLoading, setLogsLoading] = useState(false);
  const [logTail, setLogTail] = useState(100);

  const allSelected = jobs.length > 0 && selectedIds.size === jobs.length;
  const toggleSelectAll = () => setSelectedIds(allSelected ? new Set() : new Set(jobs.map(j => j.job_id)));
  const toggleSelect = (id: string) => setSelectedIds(prev => { const s = new Set(prev); s.has(id) ? s.delete(id) : s.add(id); return s; });

  const handleBulkDelete = async () => {
    setBulkDeleting(true);
    const toDelete = jobs.filter(j => selectedIds.has(j.job_id));
    const errors: string[] = [];
    for (const job of toDelete) {
      try {
        const result = await kalavaiApi.deleteJob(job.name, job.owner);
        if (result?.error) errors.push(`${job.name}: ${result.error}`);
      } catch (err) { errors.push(`${job.name}: ${err}`); }
    }
    setBulkDeleting(false); setBulkDeleteConfirm(false); setSelectedIds(new Set());
    if (errors.length) showMsg('error', `Some deletions failed: ${errors.join('; ')}`);
    else showMsg('success', `Deleted ${toDelete.length} job(s)`);
    await loadJobs(namespaceFilter ?? null);
  };

  const loadServiceLogs = async () => {
    setServiceLogsLoading(true);
    try {
      const data = await kalavaiApi.fetchServiceLogs(serviceLogTail);
      if (!data || typeof data !== 'object') {
        setServiceLogs('No logs available');
        return;
      }
      if (data.error) { setServiceLogs(`Error: ${data.error}`); return; }
      const entries = Object.entries(data as Record<string, { logs?: string; pod?: { spec?: { node_name?: string } } }>);
      if (entries.length === 0) {
        setServiceLogs('No service pod found (label: app=kalavai-watcher-service in namespace kalavai).\nThe Kalavai watcher service may not be running in this environment.');
        return;
      }
      const lines: string[] = [];
      for (const [name, info] of entries) {
        const node = info?.pod?.spec?.node_name ?? 'unknown';
        lines.push('------');
        lines.push(`--> Service: ${name} in ${node}`);
        lines.push('------');
        lines.push(info?.logs ?? '(no log output)');
        lines.push('');
      }
      setServiceLogs(lines.join('\n'));
    } catch (err) { setServiceLogs(`Error: ${err}`); }
    finally { setServiceLogsLoading(false); }
  };

  const openServiceLogs = async () => {
    setServiceLogsOpen(true);
    await loadServiceLogs();
  };

  const showMsg = (type: 'success' | 'error', text: string) => {
    setActionMsg({ type, text });
    setTimeout(() => setActionMsg(null), 4000);
  };

  // On mount: load connection state so userSpaces / selectedUserSpace are populated
  useEffect(() => {
    loadConnectionState();
  }, []);

  // Once selectedUserSpace is known, set it as the default filter exactly once.
  // If the store has loaded but there are no user spaces, fall back to "all" (null).
  const { isConnected } = useConnectionStore();
  useEffect(() => {
    if (initialised.current) return;
    if (selectedUserSpace) {
      initialised.current = true;
      setNamespaceFilter(selectedUserSpace);
    } else if (isConnected && userSpaces.length === 0) {
      initialised.current = true;
      setNamespaceFilter(null);
    }
  }, [selectedUserSpace, userSpaces, isConnected]);

  // Fetch jobs whenever namespaceFilter transitions from undefined to a real value,
  // or whenever the user changes it. Skip while still undefined (not yet initialised).
  useEffect(() => {
    if (namespaceFilter === undefined) return;
    setPage(1);
    loadJobs(namespaceFilter);
  }, [namespaceFilter]);

  const loadJobs = async (ns: string | null) => {
    setIsLoading(true); setError(null);
    try {
      const details = await kalavaiApi.fetchJobDetails(ns ?? undefined);
      if (details?.error) { setError(details.error); return; }
      const formatted: Job[] = (Array.isArray(details) ? details : []).map((job: Job) => ({
        ...job,
        endpoint: Object.fromEntries(
          Object.entries(job.endpoint || {}).map(([n, ep]) => [n, parseEndpointUrl(ep as { address: string; port: string } | string)])
        ),
      }));
      setJobs(formatted);
    } catch (err) { setError(`Failed to load jobs: ${err}`); }
    finally { setIsLoading(false); }
  };

  const openDeployModal = async () => {
    setDeployOpen(true); setDeployStep(0); setSelectedTemplate('');
    setTemplateData(null); setParams({}); setFormValues({});
    setJobName(''); setSelectedLabels({});
    setTemplatesLoading(true);
    try {
      const data = await kalavaiApi.fetchJobTemplates();
      console.log('[fetchJobTemplates] raw response:', data);
      if (data?.error) {
        showMsg('error', `Failed to load templates: ${data.error}`);
        setTemplates([]);
      } else {
        setTemplates(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('[fetchJobTemplates] error:', err);
      showMsg('error', `Failed to load templates: ${err}`);
      setTemplates([]);
    }
    finally { setTemplatesLoading(false); }
    try {
      const devices = await kalavaiApi.fetchDevices();
      const nodeNames = (Array.isArray(devices) ? devices : []).map((d: { name: string }) => d.name);
      if (nodeNames.length > 0) {
        const labelsResult = await kalavaiApi.getNodeLabels(nodeNames);
        const labelSet = new Set<string>();
        Object.values(labelsResult?.labels || {}).forEach((nl) => {
          Object.entries(nl as Record<string, string>).forEach(([k, v]) => labelSet.add(`${k}: ${v}`));
        });
        setAvailableLabels(Array.from(labelSet).sort());
      }
    } catch { setAvailableLabels([]); }
  };

  const loadTemplateDetails = async (name: string) => {
    setSelectedTemplate(name); setTemplateData(null); setParams({});
    setTemplateLoading(true);
    try {
      const data = await kalavaiApi.fetchTemplateAll(name);
      setTemplateData(data);
      const p = buildParams(data);
      setParams(p);
      const defaults: Record<string, unknown> = {};
      Object.entries(p).forEach(([k, v]) => { defaults[k] = v.default; });
      setFormValues(defaults);
    } catch (err) { showMsg('error', `Failed to load template: ${err}`); }
    finally { setTemplateLoading(false); }
  };

  const addTargetLabel = (encoded: string) => {
    const idx = encoded.indexOf(':');
    if (idx < 0) return;
    const key = encoded.slice(0, idx).trim();
    const value = encoded.slice(idx + 1).trim();
    setSelectedLabels(prev => ({ ...prev, [key]: [...(prev[key] || []), value] }));
  };

  const handleDeploy = async () => {
    if (!jobName.trim() || !selectedTemplate) return;
    setDeploying(true);
    try {
      const payload: Parameters<typeof kalavaiApi.deployJob>[0] = {
        name: jobName.toLowerCase().trim(),
        template_name: selectedTemplate,
        values: formValues,
        force_namespace: namespaceFilter ?? undefined,
      };
      if (Object.keys(selectedLabels).length > 0) {
        payload.target_labels = selectedLabels;
        payload.target_labels_ops = labelMode;
      }
      const result = await kalavaiApi.deployJob(payload);
      if (result?.error) { showMsg('error', result.error); }
      else { showMsg('success', `Job "${jobName}" submitted`); setDeployOpen(false); await loadJobs(namespaceFilter ?? null); }
    } catch (err) { showMsg('error', `Deploy failed: ${err}`); }
    finally { setDeploying(false); }
  };

  const handleDelete = async (job: Job) => {
    try {
      const result = await kalavaiApi.deleteJob(job.name, job.owner);
      if (result?.error) { showMsg('error', result.error); }
      else { showMsg('success', `Job "${job.name}" deleted`); setDeleteConfirm(null); await loadJobs(namespaceFilter ?? null); }
    } catch (err) { showMsg('error', `Delete failed: ${err}`); }
  };

  const openLogs = async (job: Job) => {
    setLogsJob(job); setLogsTab('job'); setJobLogs({});
    setJobMeta(job.spec ? JSON.stringify(job.spec, null, 2) : 'Job spec pending...');
    setJobStatus(job.conditions ? JSON.stringify(job.conditions, null, 2) : 'Status pending...');
    setLogsLoading(true);
    try {
      const data = await kalavaiApi.fetchJobLogs(job.job_id, job.owner, undefined, logTail);
      if (data?.error) { setJobLogs({ error: data.error }); return; }
      const parsed: Record<string, string> = {};
      Object.values(data || {}).forEach((group) => {
        Object.entries(group as Record<string, { logs?: string }>).forEach(([pod, info]) => {
          parsed[pod] = info?.logs ?? 'Logs not ready yet';
        });
      });
      setJobLogs(parsed);
    } catch (err) { setJobLogs({ error: String(err) }); }
    finally { setLogsLoading(false); }
  };

  const refreshLogs = async () => {
    if (!logsJob) return;
    setLogsLoading(true);
    try {
      const data = await kalavaiApi.fetchJobLogs(logsJob.job_id, logsJob.owner, undefined, logTail);
      if (data?.error) { setJobLogs({ error: data.error }); return; }
      const parsed: Record<string, string> = {};
      Object.values(data || {}).forEach((group) => {
        Object.entries(group as Record<string, { logs?: string }>).forEach(([pod, info]) => {
          parsed[pod] = info?.logs ?? 'Logs not ready yet';
        });
      });
      setJobLogs(parsed);
    } catch (err) { setJobLogs({ error: String(err) }); }
    finally { setLogsLoading(false); }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const requiredParams = Object.values(params).filter(p => p.required);
  const optionalParams = Object.values(params).filter(p => !p.required);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold">Job Deployments</h1>
          <p className="text-muted-foreground">Manage AI workloads deployed across your pool.</p>
        </div>
        <div className="flex gap-2 items-center">
          <button onClick={() => loadJobs(namespaceFilter ?? null)} className="flex items-center gap-2 px-3 py-2 border border-border rounded-md text-sm hover:bg-accent" title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={openServiceLogs} className="flex items-center gap-2 px-3 py-2 border border-border rounded-md text-sm hover:bg-accent" title="Kalavai service logs">
            <Info className="w-4 h-4" />
          </button>
          {selectedIds.size > 0 && (
            <button onClick={() => setBulkDeleteConfirm(true)}
              className="flex items-center gap-2 px-3 py-2 border border-red-500 text-red-500 rounded-md text-sm hover:bg-red-500/10">
              <Trash2 className="w-4 h-4" /> Delete ({selectedIds.size})
            </button>
          )}
          <button onClick={openDeployModal} className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90">
            <Plus className="w-4 h-4" /> Deploy Job
          </button>
        </div>
      </div>

      {/* Namespace filter */}
      {userSpaces.length > 0 && (
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground shrink-0">
            <Filter className="w-3.5 h-3.5" />
            <span className="font-medium">Namespace:</span>
          </div>
          <button
            onClick={() => setNamespaceFilter(null)}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors shrink-0 ${
              namespaceFilter === null
                ? 'bg-primary text-primary-foreground border-primary'
                : 'border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'
            }`}
          >
            All
          </button>
          <select
            value={namespaceFilter ?? ''}
            onChange={(e) => setNamespaceFilter(e.target.value || null)}
            className={`text-xs border rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer transition-colors ${
              namespaceFilter !== null
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-muted border-border text-muted-foreground'
            }`}
          >
            <option value="">Select namespace…</option>
            {userSpaces.map((space) => (
              <option key={space} value={space}>{space}</option>
            ))}
          </select>
        </div>
      )}

      {/* Toast */}
      {actionMsg && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium border ${actionMsg.type === 'success' ? 'bg-green-100 text-green-800 border-green-200' : 'bg-red-100 text-red-800 border-red-200'}`}>
          {actionMsg.type === 'success' ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
          {actionMsg.text}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Jobs table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {jobs.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">No jobs deployed yet. Click "Deploy Job" to get started.</div>
        ) : (
          <table className="w-full">
            <thead className="bg-muted">
              <tr>
                <th className="px-3 py-3 w-8">
                  <input type="checkbox" checked={allSelected} onChange={toggleSelectAll}
                    className="w-4 h-4 rounded accent-primary cursor-pointer" />
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium">Job</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Endpoints</th>
                <th className="px-4 py-3 text-left text-sm font-medium w-24">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {jobs.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE).map((job) => (
                <tr key={job.job_id} className={`hover:bg-muted/50 ${selectedIds.has(job.job_id) ? 'bg-primary/5' : ''}`}>
                  <td className="px-3 py-3">
                    <input type="checkbox" checked={selectedIds.has(job.job_id)} onChange={() => toggleSelect(job.job_id)}
                      className="w-4 h-4 rounded accent-primary cursor-pointer" />
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => openLogs(job)} className="font-medium text-sm text-primary hover:underline text-left">{job.name}</button>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1">
                      <span className="text-xs text-muted-foreground">
                        <span className="font-medium text-foreground/60">ns:</span> {job.owner}
                      </span>
                      {job.host_nodes && (
                        <ExpandableNodes nodes={job.host_nodes} />
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="space-y-1">
                      {statusBadge(job.status)}
                      {job.workers && (
                        <p className="text-xs text-muted-foreground mt-1">
                          <span className="font-medium text-foreground/60">workers:</span> {job.workers}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {Object.keys(job.endpoint || {}).length === 0 ? (
                      <span className="text-xs text-muted-foreground">—</span>
                    ) : (
                      <div className="space-y-1">
                        {Object.entries(job.endpoint).map(([name, url]) => (
                          <a key={name} href={String(url)} target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-1 text-sm text-primary hover:underline">
                            {name} <ExternalLink className="w-3 h-3" />
                          </a>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      {deleteConfirm === job.job_id ? (
                        <>
                          <button onClick={() => handleDelete(job)} className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700">Confirm</button>
                          <button onClick={() => setDeleteConfirm(null)} className="px-2 py-1 text-xs border border-border rounded hover:bg-accent">Cancel</button>
                        </>
                      ) : (
                        <button onClick={() => setDeleteConfirm(job.job_id)} className="p-1.5 hover:bg-accent rounded" title="Delete job">
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
        <Pagination page={page} pageSize={PAGE_SIZE} total={jobs.length} onPageChange={setPage} />
      </div>

      {/* ── Deploy Modal (3 steps) ── */}
      {deployOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setDeployOpen(false)}>
          <div className="bg-card border border-border rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] flex flex-col" onClick={e => e.stopPropagation()}>
            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <div>
                <h2 className="font-semibold text-lg">Deploy your job</h2>
                <div className="flex items-center gap-2 mt-1">
                  {['Template', 'Targets', 'Parameters'].map((label, i) => (
                    <span key={i} className={`text-xs px-2 py-0.5 rounded-full ${deployStep === i ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>
                      {i + 1}. {label}
                    </span>
                  ))}
                </div>
              </div>
              <button onClick={() => setDeployOpen(false)} className="p-1 hover:bg-accent rounded"><X className="w-4 h-4" /></button>
            </div>

            <div className="overflow-y-auto flex-1 px-6 py-5">

              {/* Step 0: Select template */}
              {deployStep === 0 && (
                <div className="space-y-4">
                  <p className="text-sm font-medium">Select the template you want to deploy</p>
                  {templatesLoading ? (
                    <div className="flex justify-center py-6"><Loader2 className="w-5 h-5 animate-spin text-primary" /></div>
                  ) : (
                    <select className="w-full px-3 py-2 border border-border rounded-md text-sm bg-background"
                      value={selectedTemplate} onChange={e => { if (e.target.value) loadTemplateDetails(e.target.value); }}>
                      <option value="">Select model engine…</option>
                      {templates.map(t => <option key={t.name} value={t.name}>{t.name}</option>)}
                    </select>
                  )}
                  {templateLoading && <div className="flex justify-center py-4"><Loader2 className="w-5 h-5 animate-spin text-primary" /></div>}
                  {templateData?.metadata && !templateLoading && (
                    <div className="bg-muted rounded-lg p-4 flex gap-4 items-start">
                      {templateData.metadata.icon && (
                        <img
                          src={templateData.metadata.icon}
                          alt={templateData.metadata.name}
                          className="w-16 h-16 rounded-md object-contain shrink-0 bg-background p-1"
                          onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                        />
                      )}
                      <div className="space-y-1 min-w-0">
                        <p className="font-medium">{templateData.metadata.name}</p>
                        <p className="text-sm text-muted-foreground">{templateData.metadata.description}</p>
                        {templateData.metadata.version && <p className="text-xs text-muted-foreground">Version: {templateData.metadata.version}</p>}
                        {templateData.metadata.sources && (
                          <a href={templateData.metadata.sources[0]} target="_blank" rel="noopener noreferrer"
                            className="text-xs text-primary hover:underline flex items-center gap-1">
                            Docs <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Step 1: Select targets */}
              {deployStep === 1 && (
                <div className="space-y-4">
                  <p className="text-sm font-medium">Select deployment targets <span className="text-muted-foreground font-normal">(leave blank for auto deploy)</span></p>
                  {Object.keys(selectedLabels).length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-xs text-muted-foreground">Selected labels:</p>
                      {Object.entries(selectedLabels).map(([k, vals]) => (
                        <div key={k} className="text-xs bg-muted px-3 py-1.5 rounded">{k}: {vals.join(', ')}</div>
                      ))}
                      <div className="flex items-center gap-3 pt-1">
                        <span className="text-xs text-muted-foreground">Label operator:</span>
                        {(['AND', 'OR'] as const).map(mode => (
                          <label key={mode} className="flex items-center gap-1 text-sm cursor-pointer">
                            <input type="radio" name="labelMode" value={mode} checked={labelMode === mode} onChange={() => setLabelMode(mode)} />
                            {mode}
                          </label>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No labels selected</p>
                  )}
                  <div className="flex gap-2">
                    <select className="flex-1 px-3 py-2 border border-border rounded-md text-sm bg-background"
                      defaultValue="" onChange={e => { if (e.target.value) addTargetLabel(e.target.value); }}>
                      <option value="">Select target label…</option>
                      {availableLabels.map(l => <option key={l} value={l}>{l}</option>)}
                    </select>
                    <button onClick={() => setSelectedLabels({})} className="px-3 py-2 border border-border rounded-md text-sm hover:bg-accent">Clear</button>
                  </div>
                </div>
              )}

              {/* Step 2: Parameters */}
              {deployStep === 2 && (
                <div className="space-y-4">
                  <p className="text-sm font-medium">Populate template values</p>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">Job name <span className="text-red-500">*</span></label>
                    <input type="text" className="w-full px-3 py-2 border border-border rounded-md text-sm bg-background"
                      placeholder="my-job" value={jobName} onChange={e => setJobName(e.target.value)} />
                  </div>
                  {requiredParams.length > 0 && (
                    <div className="space-y-3">
                      <p className="text-xs font-semibold uppercase text-muted-foreground">Parameters</p>
                      {requiredParams.map(p => (
                        <div key={p.name}>
                          <label className="block text-sm font-medium mb-1">{p.name} <span className="text-red-500">*</span></label>
                          <ParamField param={p} value={formValues[p.name]} onChange={v => setFormValues(prev => ({ ...prev, [p.name]: v }))} />
                          {p.description && <p className="text-xs text-muted-foreground mt-1">{p.description}</p>}
                        </div>
                      ))}
                    </div>
                  )}
                  {optionalParams.length > 0 && (
                    <details className="border border-border rounded-md">
                      <summary className="px-3 py-2 text-sm font-medium cursor-pointer hover:bg-muted">Advanced parameters</summary>
                      <div className="px-3 pb-3 space-y-3 pt-2">
                        {optionalParams.map(p => (
                          <div key={p.name}>
                            <label className="block text-sm font-medium mb-1">{p.name}</label>
                            <ParamField param={p} value={formValues[p.name]} onChange={v => setFormValues(prev => ({ ...prev, [p.name]: v }))} />
                            {p.description && <p className="text-xs text-muted-foreground mt-1">{p.description}</p>}
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              )}
            </div>

            {/* Modal footer nav */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-border">
              <button onClick={() => setDeployOpen(false)} className="px-4 py-2 border border-border rounded-md text-sm hover:bg-accent">Cancel</button>
              <div className="flex gap-2">
                {deployStep > 0 && (
                  <button onClick={() => setDeployStep(s => s - 1)} className="flex items-center gap-1 px-4 py-2 border border-border rounded-md text-sm hover:bg-accent">
                    <ChevronLeft className="w-4 h-4" /> Previous
                  </button>
                )}
                {deployStep < 2 ? (
                  <button onClick={() => setDeployStep(s => s + 1)} disabled={deployStep === 0 && !selectedTemplate}
                    className="flex items-center gap-1 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50">
                    Next <ChevronRight className="w-4 h-4" />
                  </button>
                ) : (
                  <button onClick={handleDeploy} disabled={!jobName.trim() || deploying}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50">
                    {deploying && <Loader2 className="w-4 h-4 animate-spin" />} Deploy
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Logs Modal ── */}
      {logsJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setLogsJob(null)}>
          <div className="bg-card border border-border rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[90vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <div className="flex items-center gap-3">
                <h2 className="font-semibold">Job: {logsJob.name}</h2>
                {statusBadge(logsJob.status)}
              </div>
              <div className="flex items-center gap-2">
                {logsTab === 'logs' && (
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-muted-foreground">Lines:</label>
                    <input type="number" value={logTail} onChange={e => setLogTail(Number(e.target.value))}
                      className="w-20 px-2 py-1 border border-border rounded text-xs bg-background" />
                    <button onClick={refreshLogs} className="p-1.5 hover:bg-accent rounded" title="Refresh logs">
                      <RefreshCw className={`w-4 h-4 ${logsLoading ? 'animate-spin' : ''}`} />
                    </button>
                  </div>
                )}
                <button onClick={() => setLogsJob(null)} className="p-1 hover:bg-accent rounded"><X className="w-4 h-4" /></button>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-border px-6">
              {(['job', 'status', 'logs'] as const).map(tab => (
                <button key={tab} onClick={() => setLogsTab(tab)}
                  className={`px-4 py-2 text-sm font-medium capitalize border-b-2 -mb-px transition-colors ${logsTab === tab ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}>
                  {tab}
                </button>
              ))}
            </div>

            <div className="overflow-y-auto flex-1 p-6">
              {logsTab === 'job' && (
                <pre className="text-xs font-mono bg-muted p-4 rounded-lg whitespace-pre-wrap break-all">{jobMeta}</pre>
              )}
              {logsTab === 'status' && (
                <pre className="text-xs font-mono bg-muted p-4 rounded-lg whitespace-pre-wrap break-all">{jobStatus}</pre>
              )}
              {logsTab === 'logs' && (
                logsLoading ? (
                  <div className="flex justify-center py-10"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
                ) : Object.keys(jobLogs).length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">No logs available</p>
                ) : (
                  <div className="space-y-4">
                    {Object.entries(jobLogs).map(([pod, logs]) => (
                      <div key={pod}>
                        <p className="text-xs font-semibold text-muted-foreground mb-1">Pod: {pod}</p>
                        <pre className="text-xs font-mono bg-muted p-4 rounded-lg whitespace-pre-wrap break-all max-h-80 overflow-y-auto">{logs}</pre>
                      </div>
                    ))}
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Bulk Delete Confirmation ── */}
      {bulkDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setBulkDeleteConfirm(false)}>
          <div className="bg-card border border-border rounded-lg shadow-xl w-full max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
            <h2 className="font-semibold text-lg mb-2">Delete jobs</h2>
            <p className="text-sm text-muted-foreground mb-6">
              Are you sure you want to delete <span className="font-medium text-foreground">{selectedIds.size}</span> selected job(s)? This cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setBulkDeleteConfirm(false)} className="px-4 py-2 border border-border rounded-md text-sm hover:bg-accent">Cancel</button>
              <button onClick={handleBulkDelete} disabled={bulkDeleting}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700 disabled:opacity-50">
                {bulkDeleting && <Loader2 className="w-4 h-4 animate-spin" />} Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Service Logs Modal ── */}
      {serviceLogsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setServiceLogsOpen(false)}>
          <div className="bg-card border border-border rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[90vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <h2 className="font-semibold">Kalavai API service logs</h2>
              <div className="flex items-center gap-2">
                <label className="text-xs text-muted-foreground">Lines:</label>
                <input type="number" value={serviceLogTail}
                  onChange={e => setServiceLogTail(Number(e.target.value))}
                  className="w-20 px-2 py-1 border border-border rounded text-xs bg-background" />
                <button onClick={loadServiceLogs} className="p-1.5 hover:bg-accent rounded" title="Refresh">
                  <RefreshCw className={`w-4 h-4 ${serviceLogsLoading ? 'animate-spin' : ''}`} />
                </button>
                <button onClick={() => setServiceLogsOpen(false)} className="p-1 hover:bg-accent rounded">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="overflow-y-auto flex-1 p-6">
              {serviceLogsLoading ? (
                <div className="flex justify-center py-10"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
              ) : (
                <pre className="text-xs font-mono bg-muted p-4 rounded-lg whitespace-pre-wrap break-all">{serviceLogs || 'No logs available'}</pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function JobsPage() {
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
      <JobsContent />
    </AppLayout>
  );
}
