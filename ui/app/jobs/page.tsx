'use client';

import { useEffect, useState, useRef } from 'react';
import { useAuthStore, useConnectionStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { Pagination } from '@/components/Pagination';
import kalavaiApi from '@/utils/api';
import { getCachedTemplates, setCachedTemplates, updateCachedTemplateCategory } from '@/utils/templateCache';
import { Loader2, ExternalLink, Trash2, Plus, X, RefreshCw, ChevronLeft, ChevronRight, AlertTriangle, CheckCircle, Check, Copy, Info, Filter } from 'lucide-react';

interface Job {
  job_id: string;
  name: string;
  owner: string;
  status: string;
  workers: string;
  host_nodes: string;
  endpoint: Record<string, { port: number | null; address: string; link: string } | string>;
  spec?: Record<string, unknown>;
  conditions?: Record<string, unknown>;
}

interface Template { name: string; category?: string; }

interface TemplateParam {
  name: string; type: string | string[]; default: unknown;
  description: string; required: boolean; options?: string[];
  itemType?: string | string[]; // For arrays - the type of items in the array
  properties?: Record<string, TemplateParam>; // For objects - nested properties
}

interface TemplateData {
  values: Record<string, unknown>;
  schema: { 
    properties?: Record<string, { 
      type: string | string[]; 
      description?: string; 
      enum?: unknown[];
      properties?: Record<string, any>;
      items?: any;
      required?: string[];
    }>; 
    required?: string[] 
  };
  metadata: { name?: string; description?: string; icon?: string; sources?: string[]; version?: string; annotations?: Record<string, string>; category?: string };
}

// Helm charts expose grouping via the `category` Chart.yaml annotation
// (sometimes under annotations). Normalise all shapes to one string.
function getTemplateCategory(metadata: TemplateData['metadata'] | undefined): string {
  if (!metadata) return 'Other';
  if (metadata.category && String(metadata.category).trim() !== '') return String(metadata.category).trim();
  const annotations = metadata.annotations || {};
  for (const key of ['category', 'kalavai/category', 'kalavai-category']) {
    const v = annotations[key];
    if (v && String(v).trim() !== '') return String(v).trim();
  }
  return 'Other';
}

function parseEndpointUrl(ep: { port: number | null; address: string; link: string } | string): string {
  if (typeof ep === 'string') return ep;
  return ep.link;
}

// Helper function to get the primary type from a union type (e.g., ["integer", null] -> "integer")
function getPrimaryType(type: string | string[]): string {
  if (Array.isArray(type)) {
    // Return the first non-null type
    return type.find(t => t !== null) || type[0];
  }
  return type;
}

// Helper function to check if a type includes a specific type in a union
function hasType(type: string | string[], targetType: string): boolean {
  if (Array.isArray(type)) {
    return type.includes(targetType);
  }
  return type === targetType;
}

// Helper function to check if a type is nullable (includes null in union)
function isNullable(type: string | string[]): boolean {
  if (Array.isArray(type)) {
    return type.includes('null');
  }
  return false;
}

// Helper function to cast a value to the appropriate type based on schema type
function castValue(value: unknown, type: string | string[]): unknown {
  const primaryType = getPrimaryType(type);
  
  // Handle empty/null values - if type is nullable, return null, otherwise return undefined
  if (value === '' || value === null || value === undefined) {
    if (isNullable(type)) {
      return null;
    }
    return undefined;
  }
  
  // Cast based on primary type
  switch (primaryType) {
    case 'integer':
    case 'number':
      return Number(value);
    case 'boolean':
      return Boolean(value);
    case 'string':
    default:
      return String(value);
  }
}

// Returns true when a required field has no usable value.
// false is valid for booleans, 0 is valid for numbers — only undefined/null/''/[] count as empty.
function isEmptyValue(value: unknown, param: TemplateParam): boolean {
  if (hasType(param.type, 'boolean')) {
    return value === undefined || value === null;
  }
  if (hasType(param.type, 'array')) {
    return !Array.isArray(value) || value.length === 0;
  }
  if (hasType(param.type, 'object')) {
    if (value === undefined || value === null) return true;
    if (typeof value !== 'object' || Array.isArray(value)) return true;
    // Structured objects delegate emptiness to their nested required fields
    if (param.properties) return false;
    return Object.keys(value as Record<string, unknown>).length === 0;
  }
  if (hasType(param.type, 'integer') || hasType(param.type, 'number')) {
    return value === undefined || value === null || value === '' || Number.isNaN(Number(value));
  }
  // string, enum and anything else
  return value === undefined || value === null || String(value).trim() === '';
}

// Recursively collect dotted paths (e.g. "args.model") of required params with no value.
function getMissingRequired(
  params: Record<string, TemplateParam>,
  values: Record<string, unknown> | undefined | null,
  prefix = ''
): string[] {
  const missing: string[] = [];
  const safeValues = (values as Record<string, unknown>) || {};
  Object.values(params).forEach(p => {
    const v = safeValues[p.name];
    if (hasType(p.type, 'object') && p.properties) {
      const nested = getMissingRequired(p.properties, (v as Record<string, unknown>) || {}, `${prefix}${p.name}.`);
      missing.push(...nested);
      // Required free-form object (no nested required) with no value counts as missing itself
      if (p.required && nested.length === 0 && (v === undefined || v === null)) {
        missing.push(`${prefix}${p.name}`);
      }
      return;
    }
    if (p.required && isEmptyValue(v, p)) {
      missing.push(`${prefix}${p.name}`);
    }
  });
  return missing;
}

// Count missing required fields inside a (possibly nested) object param, for badges.
function countMissingInObject(param: TemplateParam, value: unknown): number {
  if (!param.properties) {
    return param.required && isEmptyValue(value, param) ? 1 : 0;
  }
  return getMissingRequired(param.properties, (value as Record<string, unknown>) || {}).length;
}

// Helper function to recursively cast all form values based on their schema types
function castFormValues(values: Record<string, unknown>, params: Record<string, TemplateParam>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  
  Object.entries(params).forEach(([name, param]) => {
    const value = values[name];
    
    if (hasType(param.type, 'object') && param.properties && typeof value === 'object' && value !== null && !Array.isArray(value)) {
      // Recursively cast nested object properties
      result[name] = castFormValues(value as Record<string, unknown>, param.properties);
    } else if (hasType(param.type, 'array') && Array.isArray(value)) {
      // Cast array items based on itemType
      if (param.itemType) {
        result[name] = value.map(item => castValue(item, param.itemType || ''));
      } else {
        result[name] = value;
      }
    } else {
      // Cast basic types
      result[name] = castValue(value, param.type);
    }
  });
  
  return result;
}

// Helper function to process object properties recursively
function processObjectProperties(
  properties: Record<string, any>, 
  values: Record<string, any> = {}, 
  requiredFields: string[] = [],
  depth: number = 0
): Record<string, TemplateParam> {
  const indent = '  '.repeat(depth);
  console.log(`${indent}[processObjectProperties] depth=${depth}, properties:`, Object.keys(properties));
  console.log(`${indent}[processObjectProperties] values:`, values);
  console.log(`${indent}[processObjectProperties] requiredFields:`, requiredFields);
  
  const result: Record<string, TemplateParam> = {};
  
  Object.entries(properties).forEach(([name, schema]) => {
    const value = values?.[name];
    const isRequired = requiredFields.includes(name);
    
    console.log(`${indent}[processObjectProperties] Processing field: ${name}, type: ${schema.type}, value:`, value);
    
    // Handle nested object types
    if (hasType(schema.type, 'object') && schema.properties) {
      console.log(`${indent}[processObjectProperties] Found nested object: ${name}`);
      const nestedRequired = (schema as any).required || [];
      const nestedParams = processObjectProperties(schema.properties, value as any, nestedRequired, depth + 1);
      
      result[name] = {
        name,
        default: value,
        type: 'object',
        description: schema.description || '',
        required: isRequired,
        properties: nestedParams,
      };
      console.log(`${indent}[processObjectProperties] Added nested object ${name} with ${Object.keys(nestedParams).length} properties`);
      return;
    }
    
    // Handle array types
    if (hasType(schema.type, 'array') && schema.items) {
      const itemSchema = schema.items as any;
      const itemType = itemSchema.enum ? 'enum' : getPrimaryType(itemSchema.type);
      
      result[name] = {
        name,
        default: value,
        type: 'array',
        description: schema.description || '',
        required: isRequired,
        itemType,
        options: itemSchema.enum as string[] | undefined,
      };
      console.log(`${indent}[processObjectProperties] Added array: ${name}`);
      return;
    }
    
    // Handle basic types
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      console.log(`${indent}[processObjectProperties] Skipping object without schema: ${name}`);
      return;
    }
    
    result[name] = {
      name,
      default: value,
      type: schema.enum ? 'enum' : getPrimaryType(schema.type),
      description: schema.description || '',
      required: isRequired,
      options: schema.enum as string[] | undefined,
    };
    console.log(`${indent}[processObjectProperties] Added basic type: ${name} (${result[name].type})`);
  });
  
  console.log(`${indent}[processObjectProperties] Returning result with ${Object.keys(result).length} properties:`, Object.keys(result));
  return result;
}

function buildParams(data: TemplateData): Record<string, TemplateParam> {
  console.log('[buildParams] Input data:', JSON.stringify(data, null, 2));
  console.log('[buildParams] data.values keys:', Object.keys(data.values || {}));
  console.log('[buildParams] data.schema:', data.schema);
  console.log('[buildParams] data.schema.properties keys:', Object.keys(data.schema?.properties || {}));
  console.log('[buildParams] data.schema.required:', data.schema?.required);
  
  // Check what fields have schemas vs values
  const valueKeys = Object.keys(data.values || {});
  const schemaKeys = Object.keys(data.schema?.properties || {});
  console.log('[buildParams] Fields with values but no schema:', valueKeys.filter(k => !schemaKeys.includes(k)));
  console.log('[buildParams] Fields with schema but no values:', schemaKeys.filter(k => !valueKeys.includes(k)));
  
  const params: Record<string, TemplateParam> = {};
  const required = data.schema?.required || [];
  const schemaProps = data.schema?.properties || {};
  const valuesRecord = (data.values || {}) as Record<string, unknown>;

  Object.entries(schemaProps).forEach(([name, schema]) => {
    const value = valuesRecord?.[name];
    
    console.log(`[buildParams] Processing top-level field: ${name}, type: ${schema.type}, value:`, value);
    
    // Handle object types
    if (hasType(schema.type, 'object') && schema.properties) {
      console.log(`[buildParams] Found top-level object: ${name}`);
      const nestedRequired = (schema as any).required || [];
      const nestedParams = processObjectProperties(schema.properties, value as any, nestedRequired, 1);
      
      params[name] = {
        name,
        default: value,
        type: 'object',
        description: schema.description || '',
        required: required.includes(name),
        properties: nestedParams,
      };
      console.log(`[buildParams] Added top-level object ${name} with ${Object.keys(nestedParams).length} properties`);
      return;
    }
    
    // Handle array types
    if (hasType(schema.type, 'array') && schema.items) {
      const itemSchema = schema.items as any;
      const itemType = itemSchema.enum ? 'enum' : getPrimaryType(itemSchema.type);
      
      params[name] = {
        name,
        default: value,
        type: 'array',
        description: schema.description || '',
        required: required.includes(name),
        itemType,
        options: itemSchema.enum as string[] | undefined,
      };
      console.log(`[buildParams] Added top-level array: ${name}`);
      return;
    }
    
    // Handle basic types (existing logic)
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      console.log(`[buildParams] Skipping object without schema: ${name}`);
      return;
    }
    
    params[name] = {
      name,
      default: value,
      type: schema.enum ? 'enum' : getPrimaryType(schema.type),
      description: schema.description || '',
      required: required.includes(name),
      options: schema.enum as string[] | undefined,
    };
    console.log(`[buildParams] Added basic type: ${name} (${params[name].type})`);
  });
  
  console.log(`[buildParams] Final result:`, params);
  console.log(`[buildParams] Final result keys:`, Object.keys(params));
  console.log(`[buildParams] Object fields:`, Object.entries(params).filter(([_, p]) => p.type === 'object').map(([name, p]) => `${name} (${Object.keys(p.properties || {}).length} properties)`));
  
  return params;
}

function buildResourcesParams(data: TemplateData): Record<string, TemplateParam> {
  const params: Record<string, TemplateParam> = {};
  
  // Check if resources property exists in schema
  const resourcesSchema = data.schema?.properties?.['resources'];
  
  if (!resourcesSchema) {
    return params;
  }
  
  // If resources is an object with properties, parse those properties
  if (resourcesSchema.type === 'object' && resourcesSchema.properties) {
    const required = resourcesSchema.required || [];
    const resourcesValues = data.values?.['resources'] as Record<string, unknown> || {};
    
    const processedParams = processObjectProperties(resourcesSchema.properties, resourcesValues, required, 1);
    Object.assign(params, processedParams);
  }
  
  return params;
}

function statusBadge(status: string) {
  const cls = status === 'Running' ? 'bg-green-100 text-green-800' :
    status === 'Pending' ? 'bg-yellow-100 text-yellow-800' :
    status === 'Error' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800';
  return <span className={`px-2 py-0.5 rounded text-xs font-medium ${cls}`}>{status || '—'}</span>;
}

function ParamField({ param, value, onChange, invalid }: { param: TemplateParam; value: unknown; onChange: (v: unknown) => void; invalid?: boolean }) {
  const base = `w-full px-3 py-2 border rounded-md text-sm bg-background ${invalid ? 'border-red-500 ring-1 ring-red-500' : 'border-border'}`;
  
  // Handle array types
  if (hasType(param.type, 'array')) {
    const arrayValue = Array.isArray(value) ? value : [];
    const stringValue = arrayValue.length > 0 ? String(arrayValue[0]) : '';
    
    if (hasType(param.itemType || '', 'enum') && param.options) {
      return (
        <div className="space-y-2">
          <select 
            className={base} 
            value={stringValue} 
            onChange={e => {
              const newValue = e.target.value ? [castValue(e.target.value, param.itemType || '')] : [];
              onChange(newValue);
            }}
          >
            <option value="">Select value...</option>
            {param.options.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
          <p className="text-xs text-muted-foreground">Array type - first item shown, empty array = null</p>
        </div>
      );
    }
    
    if (hasType(param.itemType || '', 'integer') || hasType(param.itemType || '', 'number')) {
      return (
        <div className="space-y-2">
          <input 
            type="number" 
            className={base} 
            value={stringValue}
            onChange={e => {
              const numValue = castValue(e.target.value, param.itemType || '');
              onChange(numValue === '' ? [] : [numValue]);
            }} 
          />
          <p className="text-xs text-muted-foreground">Array type - first item shown, empty array = null</p>
        </div>
      );
    }
    
    if (hasType(param.itemType || '', 'boolean')) {
      return (
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input 
              type="checkbox" 
              checked={arrayValue.length > 0 ? Boolean(arrayValue[0]) : false} 
              onChange={e => onChange([castValue(e.target.checked, param.itemType || '')])} 
              className="w-4 h-4" 
            />
            <span className="text-sm">{arrayValue.length > 0 ? String(arrayValue[0]) : 'false'}</span>
          </label>
          <p className="text-xs text-muted-foreground">Array type - first item shown, empty array = null</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-2">
        <input 
          type="text" 
          className={base} 
          value={stringValue} 
          onChange={e => onChange(e.target.value ? [castValue(e.target.value, param.itemType || '')] : [])} 
        />
        <p className="text-xs text-muted-foreground">Array type - first item shown, empty array = null</p>
      </div>
    );
  }
  
  // Existing logic for basic types
  if (hasType(param.type, 'enum') && param.options) {
    return <select className={base} value={String(value ?? param.default ?? '')} onChange={e => onChange(castValue(e.target.value, param.type))}>
      {param.options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>;
  }
  if (hasType(param.type, 'integer') || hasType(param.type, 'number')) {
    return <input type="number" className={base} value={String(value ?? param.default ?? '')}
      onChange={e => onChange(castValue(e.target.value, param.type))} />;
  }
  if (hasType(param.type, 'boolean')) {
    return <label className="flex items-center gap-2 cursor-pointer">
      <input type="checkbox" checked={Boolean(value ?? param.default)} onChange={e => onChange(castValue(e.target.checked, param.type))} className="w-4 h-4" />
      <span className="text-sm">{String(value ?? param.default)}</span>
    </label>;
  }
  return <input type="text" className={base} value={String(value ?? param.default ?? '')} onChange={e => onChange(castValue(e.target.value, param.type))} />;
}

function ObjectParamField({ param, value, onChange }: { param: TemplateParam; value: unknown; onChange: (v: unknown) => void }) {
  const objectValue = (value as Record<string, unknown>) || {};
  const missing: string[] = param.properties ? getMissingRequired(param.properties, objectValue) : [];
  const [expanded, setExpanded] = useState(missing.length > 0);
  // Auto-expand when required fields inside are still empty so users can see what's left.
  useEffect(() => {
    if (missing.length > 0) setExpanded(true);
  }, [param.name]);

  if (!param.properties) return null;

  const hasMissing = missing.length > 0;

  return (
    <div className={`border rounded-md ${hasMissing ? 'border-red-500' : 'border-border'}`}>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-2 text-sm font-medium text-left hover:bg-muted flex items-center justify-between"
      >
        <span>{param.name} {param.required && <span className="text-red-500">*</span>}
          {hasMissing && (
            <span className="ml-2 text-xs font-normal px-1.5 py-0.5 rounded bg-red-100 text-red-700">
              {missing.length} required missing
            </span>
          )}
        </span>
        <ChevronRight className={`w-4 h-4 transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3 border-t border-border">
          {param.description && (
            <p className="text-xs text-muted-foreground pt-2">{param.description}</p>
          )}
          {Object.values(param.properties).map(nestedParam => {
            const nestedValue = objectValue[nestedParam.name];
            if (hasType(nestedParam.type, 'object')) {
              return (
                <ObjectParamField
                  key={nestedParam.name}
                  param={nestedParam}
                  value={nestedValue}
                  onChange={v => onChange({ ...objectValue, [nestedParam.name]: v })}
                />
              );
            }
            const nestedInvalid = nestedParam.required && isEmptyValue(nestedValue, nestedParam);
            return (
              <div key={nestedParam.name}>
                <label className="block text-sm font-medium mb-1">
                  {nestedParam.name} {nestedParam.required && <span className="text-red-500">*</span>}
                </label>
                <ParamField
                  param={nestedParam}
                  value={nestedValue}
                  onChange={v => onChange({ ...objectValue, [nestedParam.name]: v })}
                  invalid={nestedInvalid}
                />
                {nestedParam.description && (
                  <p className="text-xs text-muted-foreground mt-1">{nestedParam.description}</p>
                )}
                {nestedInvalid && (
                  <p className="text-xs text-red-600 mt-1">This field is required</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
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
  const [copiedEndpoint, setCopiedEndpoint] = useState<string | null>(null);

  // Deploy modal
  const [deployOpen, setDeployOpen] = useState(false);
  const [deployStep, setDeployStep] = useState(0);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  const [categoriesLoaded, setCategoriesLoaded] = useState(0);
  const [categoriesTotal, setCategoriesTotal] = useState(0);
  const categoriesRunRef = useRef(0);
  const [selectedCategory, setSelectedCategory] = useState('');
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
  const [randomSuffix, setRandomSuffix] = useState(true);
  const [resourcesParams, setResourcesParams] = useState<Record<string, TemplateParam>>({});
  const [resourcesValues, setResourcesValues] = useState<Record<string, unknown>>({});
  const [maxResources, setMaxResources] = useState<Record<string, number>>({});
  const [maxResourcesLoading, setMaxResourcesLoading] = useState(false);

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

  const copyEndpoint = async (jobId: string, name: string, url: string) => {
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
      } else {
        // Fallback for non-secure contexts where navigator.clipboard is unavailable
        const ta = document.createElement('textarea');
        ta.value = url;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      setCopiedEndpoint(`${jobId}:${name}`);
      setTimeout(() => setCopiedEndpoint(null), 2000);
      showMsg('success', `Copied ${name} endpoint to clipboard`);
    } catch {
      showMsg('error', 'Failed to copy endpoint to clipboard');
    }
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

  // Load max resources when deploy modal is open on step 1 (targets) and labels change
  useEffect(() => {
    if (deployOpen && deployStep === 1) {
      loadMaxResources();
    }
  }, [deployOpen, deployStep, selectedLabels]);

  const loadJobs = async (ns: string | null) => {
    setIsLoading(true); setError(null);
    try {
      const details = await kalavaiApi.fetchJobDetails(ns ?? undefined);
      if (details?.error) { setError(details.error); return; }
      const formatted: Job[] = (Array.isArray(details) ? details : []).map((job: Job) => ({
        ...job,
        endpoint: Object.fromEntries(
          Object.entries(job.endpoint || {}).map(([n, ep]) => [n, parseEndpointUrl(ep as { port: number | null; address: string; link: string } | string)])
        ),
      }));
      setJobs(formatted);
    } catch (err) { setError(`Failed to load jobs: ${err}`); }
    finally { setIsLoading(false); }
  };

  const loadMaxResources = async () => {
    setMaxResourcesLoading(true);
    try {
      // Convert selectedLabels from Record<string, string[]> to Record<string, string>
      // by taking the first value from each array
      const nodeLabels: Record<string, string> = {};
      Object.entries(selectedLabels).forEach(([key, values]) => {
        if (values && values.length > 0) {
          nodeLabels[key] = values[0];
        }
      });
      console.log('[loadMaxResources] Calling API with nodeLabels:', nodeLabels);
      const data = await kalavaiApi.getMaxResources(nodeLabels);
      console.log('[loadMaxResources] Received data:', data);
      setMaxResources(data || {});
    } catch (err) {
      console.error('[loadMaxResources] error:', err);
      setMaxResources({});
    } finally {
      setMaxResourcesLoading(false);
    }
  };

  const openDeployModal = async () => {
    setDeployOpen(true); setDeployStep(0); setSelectedCategory(''); setSelectedTemplate('');
    setTemplateData(null); setParams({}); setFormValues({});
    setJobName(''); setSelectedLabels({}); setRandomSuffix(true);
    setMaxResources({});
    // Reuse the short-term cache so reopening the modal doesn't refetch
    // the template list + per-template metadata.
    const cached = getCachedTemplates();
    if (cached) {
      setTemplates(cached);
      setTemplatesLoading(false);
      setCategoriesLoading(false); setCategoriesLoaded(cached.length); setCategoriesTotal(cached.length);
    } else {
      setTemplatesLoading(true);
      setCategoriesLoading(false); setCategoriesLoaded(0); setCategoriesTotal(0);
      try {
        const data = await kalavaiApi.fetchJobTemplates();
        console.log('[fetchJobTemplates] raw response:', data);
        if (data?.error) {
          showMsg('error', `Failed to load templates: ${data.error}`);
          setTemplates([]);
        } else {
          const list: Template[] = Array.isArray(data) ? data : [];
          setTemplates(list.map(t => ({ ...t })));
          setCachedTemplates(list.map(t => ({ name: t.name })));
          // Enrich with `category` annotation from chart metadata so templates can be grouped.
          // Bounded concurrency (avoids N parallel requests) with progress tracking.
          // Fire-and-forget: picker shows a loading indicator until all resolve.
          const runId = ++categoriesRunRef.current;
          setCategoriesLoading(list.length > 0);
          setCategoriesLoaded(0);
          setCategoriesTotal(list.length);
          void (async () => {
            const CONCURRENCY = 5;
            let next = 0;
            const worker = async () => {
              while (categoriesRunRef.current === runId) {
                const i = next++;
                if (i >= list.length) return;
                const t = list[i];
                let category = 'Other';
                try {
                  const meta = await kalavaiApi.fetchTemplateMetadata(t.name);
                  if (categoriesRunRef.current !== runId) return;
                  category = getTemplateCategory(meta);
                } catch {
                  if (categoriesRunRef.current !== runId) return;
                }
                setTemplates(prev => prev.map(p => p.name === t.name ? { ...p, category } : p));
                updateCachedTemplateCategory(t.name, category);
                if (categoriesRunRef.current === runId) {
                  setCategoriesLoaded(prev => prev + 1);
                }
              }
            };
            await Promise.all(Array.from({ length: Math.min(CONCURRENCY, list.length) }, () => worker()));
            if (categoriesRunRef.current === runId) {
              setCategoriesLoading(false);
            }
          })();
        }
      } catch (err) {
        console.error('[fetchJobTemplates] error:', err);
        showMsg('error', `Failed to load templates: ${err}`);
        setTemplates([]);
      }
      finally { setTemplatesLoading(false); }
    }
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
      // Sync resolved category back into the list entry (covers race where
      // metadata enrichment hadn't finished before selection).
      const category = getTemplateCategory(data?.metadata);
      setTemplates(prev => prev.map(p => p.name === name ? { ...p, category } : p));
      updateCachedTemplateCategory(name, category);
      if (!selectedCategory) setSelectedCategory(category);
      const p = buildParams(data);
      setParams(p);
      const defaults: Record<string, unknown> = {};
      Object.entries(p).forEach(([k, v]) => { defaults[k] = v.default; });
      setFormValues(defaults);
      
      // Build resources params
      const rp = buildResourcesParams(data);
      setResourcesParams(rp);
      const resourceDefaults: Record<string, unknown> = {};
      Object.entries(rp).forEach(([k, v]) => { resourceDefaults[k] = v.default; });
      setResourcesValues(resourceDefaults);
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
      // Debug: Log the formValues structure to verify nested object handling
      console.log('[handleDeploy] formValues structure:', JSON.stringify(formValues, null, 2));
      console.log('[handleDeploy] Object parameters in formValues:', 
        Object.entries(formValues)
          .filter(([_, value]) => typeof value === 'object' && value !== null && !Array.isArray(value))
          .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
      );
      
      // Cast all form values based on their schema types
      const castedValues = castFormValues(formValues, params);
      console.log('[handleDeploy] Casted values:', JSON.stringify(castedValues, null, 2));
      
      const payload: Parameters<typeof kalavaiApi.deployJob>[0] = {
        name: jobName.toLowerCase().trim(),
        template_name: selectedTemplate,
        values: castedValues,
        force_namespace: namespaceFilter ?? undefined,
        random_suffix: randomSuffix,
      };
      if (Object.keys(selectedLabels).length > 0) {
        payload.target_labels = selectedLabels;
        payload.target_labels_ops = labelMode;
      }
      if (Object.keys(resourcesValues).length > 0) {
        payload.resources = castFormValues(resourcesValues, resourcesParams);
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

  // True when this param or any nested descendant is marked required in the schema.
  // Used so objects containing required children stay in the visible Parameters
  // section instead of being hidden under Advanced parameters.
  const containsRequired = (p: TemplateParam): boolean => {
    if (p.required) return true;
    if (p.properties) return Object.values(p.properties).some(containsRequired);
    return false;
  };

  const requiredParams = Object.values(params).filter(containsRequired);
  const optionalParams = Object.values(params).filter(p => !containsRequired(p));
  const missingRequired = getMissingRequired(params, formValues);
  const missingResourcesRequired = getMissingRequired(resourcesParams, resourcesValues);
  const canDeploy = jobName.trim() !== '' && missingRequired.length === 0 && missingResourcesRequired.length === 0;

  // Group templates by their Helm `category` annotation for the category-first picker.
  const templateCategories = Array.from(new Set(templates.map(t => t.category || 'Other'))).sort((a, b) => {
    if (a === 'Other') return 1;
    if (b === 'Other') return -1;
    return a.localeCompare(b);
  });
  const categoryTemplates = selectedCategory
    ? templates.filter(t => (t.category || 'Other') === selectedCategory)
    : [];

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
                        {Object.entries(job.endpoint).map(([name, url]) => {
                          const href = String(url);
                          const copied = copiedEndpoint === `${job.job_id}:${name}`;
                          return (
                            <div key={name} className="flex items-center gap-1">
                              <a href={href} target="_blank" rel="noopener noreferrer"
                                className="flex items-center gap-1 text-sm text-primary hover:underline min-w-0">
                                <span className="truncate">{name}</span> <ExternalLink className="w-3 h-3 shrink-0" />
                              </a>
                              <button onClick={() => copyEndpoint(job.job_id, name, href)}
                                className="p-1 hover:bg-accent rounded shrink-0" title={`Copy ${name} endpoint URL`}>
                                {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5 text-muted-foreground" />}
                              </button>
                            </div>
                          );
                        })}
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
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
                    <>
                      <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1">Category</label>
                        <select className="w-full px-3 py-2 border border-border rounded-md text-sm bg-background disabled:opacity-50"
                          value={selectedCategory} disabled={categoriesLoading}
                          onChange={e => {
                            setSelectedCategory(e.target.value);
                            setSelectedTemplate('');
                            setTemplateData(null); setParams({}); setFormValues({});
                          }}>
                          <option value="">{categoriesLoading ? 'Loading categories…' : 'Select category…'}</option>
                          {templateCategories.map(c => {
                            const count = templates.filter(t => (t.category || 'Other') === c).length;
                            return <option key={c} value={c}>{c} ({count})</option>;
                          })}
                        </select>
                        {categoriesLoading && (
                          <p className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1.5" role="status" aria-live="polite">
                            <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
                            Loading categories… {categoriesLoaded}/{categoriesTotal}
                          </p>
                        )}
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1">Template</label>
                        <select className="w-full px-3 py-2 border border-border rounded-md text-sm bg-background disabled:opacity-50"
                          value={selectedTemplate} disabled={!selectedCategory || categoriesLoading}
                          onChange={e => { if (e.target.value) loadTemplateDetails(e.target.value); }}>
                          <option value="">{selectedCategory ? 'Select template…' : 'Select a category first…'}</option>
                          {categoryTemplates.map(t => <option key={t.name} value={t.name}>{t.name}</option>)}
                        </select>
                      </div>
                    </>
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
                  
                  {/* Resources section */}
                  {Object.keys(resourcesParams).length > 0 && (
                    <details className="border border-border rounded-md">
                      <summary className="px-3 py-2 text-sm font-medium cursor-pointer hover:bg-muted">Resources</summary>
                      <div className="px-3 pb-3 space-y-3 pt-2">
                        {/* Max resources info panel */}
                        {Object.keys(maxResources).length > 0 && (
                          <div className="bg-muted/50 border border-border rounded-md p-3">
                            <div className="flex items-center gap-2 mb-2">
                              <Info className="w-4 h-4 text-muted-foreground" />
                              <p className="text-sm font-medium">Max worker resources (available)</p>
                              {maxResourcesLoading && <Loader2 className="w-3 h-3 animate-spin text-muted-foreground" />}
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              {maxResources.cpu !== undefined && maxResources.cpu > 0 && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">CPU cores:</span>
                                  <span className="font-medium">{maxResources.cpu}</span>
                                </div>
                              )}
                              {maxResources.memory !== undefined && maxResources.memory > 0 && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Memory:</span>
                                  <span className="font-medium">{(maxResources.memory / (1024 ** 3)).toFixed(2)} GB</span>
                                </div>
                              )}
                              {maxResources['ephemeral-storage'] !== undefined && maxResources['ephemeral-storage'] > 0 && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Storage:</span>
                                  <span className="font-medium">{(maxResources['ephemeral-storage'] / (1024 ** 3)).toFixed(2)} GB</span>
                                </div>
                              )}
                              {maxResources.vram !== undefined && maxResources.vram > 0 && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">GPU memory:</span>
                                  <span className="font-medium">{(maxResources.vram / (1024 ** 3)).toFixed(2)} GB</span>
                                </div>
                              )}
                              {Object.keys(maxResources).length > 0 && Object.values(maxResources).every(v => v === 0) && (
                                <div className="col-span-2 text-muted-foreground text-center">
                                  No resource data available
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                        {Object.entries(resourcesParams).map(([name, param]) => (
                          <div key={name}>
                            {param.type === 'object' ? (
                              <ObjectParamField 
                                param={param} 
                                value={resourcesValues[name]} 
                                onChange={v => setResourcesValues(prev => ({ ...prev, [name]: v }))} 
                              />
                            ) : (
                              <>
                                <label className="block text-sm font-medium mb-1">
                                  {name} {param.required && <span className="text-red-500">*</span>}
                                </label>
                                <ParamField
                                  param={param}
                                  value={resourcesValues[name]}
                                  onChange={v => setResourcesValues(prev => ({ ...prev, [name]: v }))}
                                  invalid={param.required && isEmptyValue(resourcesValues[name], param)}
                                />
                                {param.description && <p className="text-xs text-muted-foreground mt-1">{param.description}</p>}
                                {param.required && isEmptyValue(resourcesValues[name], param) && (
                                  <p className="text-xs text-red-600 mt-1">This field is required</p>
                                )}
                              </>
                            )}
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              )}

              {/* Step 2: Parameters */}
              {deployStep === 2 && (
                <div className="space-y-4">
                  <p className="text-sm font-medium">Populate template values</p>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">Job name <span className="text-red-500">*</span></label>
                    <input type="text" className={`w-full px-3 py-2 border rounded-md text-sm bg-background ${!jobName.trim() ? 'border-red-500 ring-1 ring-red-500' : 'border-border'}`}
                      placeholder="my-job" value={jobName} onChange={e => setJobName(e.target.value)} />
                    {!jobName.trim() && (
                      <p className="text-xs text-red-600 mt-1">Job name is required</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <input 
                      type="checkbox" 
                      id="random-suffix" 
                      checked={randomSuffix} 
                      onChange={e => setRandomSuffix(e.target.checked)} 
                      className="w-4 h-4 rounded accent-primary cursor-pointer" 
                    />
                    <label htmlFor="random-suffix" className="text-sm cursor-pointer">
                      Add random suffix to job name
                    </label>
                  </div>
                  {(missingRequired.length > 0 || missingResourcesRequired.length > 0) && (
                    <div className="flex items-start gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <div>
                        <p className="font-medium">Required fields missing: {missingRequired.length + missingResourcesRequired.length}</p>
                        <p className="text-xs mt-0.5 break-all">{[...missingRequired, ...missingResourcesRequired.map(m => `resources.${m}`)].join(', ')}</p>
                      </div>
                    </div>
                  )}
                  {requiredParams.length > 0 && (
                    <div className="space-y-3">
                      <p className="text-xs font-semibold uppercase text-muted-foreground">Parameters <span className="normal-case font-normal">— fields marked <span className="text-red-500">*</span> are required</span></p>
                      {requiredParams.map(p => {
                        const invalid = hasType(p.type, 'object')
                          ? countMissingInObject(p, formValues[p.name]) > 0
                          : p.required && isEmptyValue(formValues[p.name], p);
                        return (
                          <div key={p.name}>
                            {hasType(p.type, 'object') ? (
                              <ObjectParamField
                                param={p}
                                value={formValues[p.name]}
                                onChange={v => setFormValues(prev => ({ ...prev, [p.name]: v }))}
                              />
                            ) : (
                              <>
                                <label className="block text-sm font-medium mb-1">
                                  {p.name} <span className="text-red-500">*</span>
                                </label>
                                <ParamField
                                  param={p}
                                  value={formValues[p.name]}
                                  onChange={v => setFormValues(prev => ({ ...prev, [p.name]: v }))}
                                  invalid={invalid}
                                />
                                {p.description && <p className="text-xs text-muted-foreground mt-1">{p.description}</p>}
                                {invalid && (
                                  <p className="text-xs text-red-600 mt-1">This field is required</p>
                                )}
                              </>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                  {optionalParams.length > 0 && (
                    <details className="border border-border rounded-md">
                      <summary className="px-3 py-2 text-sm font-medium cursor-pointer hover:bg-muted">Advanced parameters</summary>
                      <div className="px-3 pb-3 space-y-3 pt-2">
                        {optionalParams.map(p => (
                          <div key={p.name}>
                            {p.type === 'object' ? (
                              <ObjectParamField 
                                param={p} 
                                value={formValues[p.name]} 
                                onChange={v => setFormValues(prev => ({ ...prev, [p.name]: v }))} 
                              />
                            ) : (
                              <>
                                <label className="block text-sm font-medium mb-1">{p.name}</label>
                                <ParamField 
                                  param={p} 
                                  value={formValues[p.name]} 
                                  onChange={v => setFormValues(prev => ({ ...prev, [p.name]: v }))} 
                                />
                                {p.description && <p className="text-xs text-muted-foreground mt-1">{p.description}</p>}
                              </>
                            )}
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
                  <button onClick={handleDeploy} disabled={!canDeploy || deploying}
                    title={!canDeploy ? `Fill all required fields: ${[...missingRequired, ...missingResourcesRequired.map(m => `resources.${m}`)].join(', ') || 'job name'}` : 'Deploy job'}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed">
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
