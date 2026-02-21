'use client';

import { useEffect, useState, useRef } from 'react';
import { useAuthStore, useConnectionStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { Pagination } from '@/components/Pagination';
import kalavaiApi from '@/utils/api';
import { Loader2, ExternalLink, Copy, Check, RefreshCw, AlertTriangle, Filter } from 'lucide-react';

interface Service {
  namespace: string;
  name: string;
  internal: Record<string, string>;
  external: Record<string, string>;
}

function CopyButton({ url }: { url: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      title={copied ? 'Copied!' : `Copy: ${url}`}
      className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-colors ${
        copied
          ? 'bg-green-100 text-green-700 border border-green-200'
          : 'bg-muted hover:bg-accent text-foreground border border-border'
      }`}
    >
      {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
      {copied ? 'Copied!' : url.split(':').slice(0, -1).join(':').replace('http://', '').split('.')[0] || url}
    </button>
  );
}

function ServicesContent() {
  const { userSpaces, selectedUserSpace, loadConnectionState } = useConnectionStore();

  const [namespaceFilter, setNamespaceFilter] = useState<string | null>(null);
  const initialised = useRef(false);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 10;

  useEffect(() => {
    loadConnectionState();
    loadServices();
  }, []);

  useEffect(() => {
    if (initialised.current) return;
    if (selectedUserSpace) {
      initialised.current = true;
      setNamespaceFilter(selectedUserSpace);
    }
  }, [selectedUserSpace]);

  // Reset to page 1 when filter changes
  useEffect(() => { setPage(1); }, [namespaceFilter]);

  const loadServices = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await kalavaiApi.fetchPoolServices();
      if (data?.error) { setError(data.error); return; }
      const formattedServices: Service[] = [];
      
      Object.entries(data).forEach(([namespace, namespaceServices]) => {
        (namespaceServices as { name: string; endpoints: Record<string, { internal: string; external?: string }> }[]).forEach((service) => {
          formattedServices.push({
            namespace,
            name: service.name,
            internal: Object.fromEntries(
              Object.entries(service.endpoints).map(([name, ep]) => [name, ep.internal])
            ),
            external: Object.fromEntries(
              Object.entries(service.endpoints)
                .filter(([_, ep]) => ep.external)
                .map(([name, ep]) => [name, `http://${ep.external}`])
            ),
          });
        });
      });
      
      setServices(formattedServices);
    } catch (err) {
      setError(`Failed to load services: ${err}`);
    } finally {
      setIsLoading(false);
    }
  };

  const visibleServices = namespaceFilter
    ? services.filter((s) => s.namespace === namespaceFilter)
    : services;
  const pagedServices = visibleServices.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

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
          <h1 className="text-3xl font-bold">Core Services</h1>
          <p className="text-muted-foreground">Core services available in the pool</p>
        </div>
        <button onClick={loadServices} className="flex items-center gap-2 px-3 py-2 border border-border rounded-md text-sm hover:bg-accent">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
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

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {visibleServices.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No services found{namespaceFilter ? ` in namespace "${namespaceFilter}"` : ''}.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Namespace</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Name</th>
                <th className="px-4 py-3 text-left text-sm font-medium">External Endpoints</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Internal Endpoints</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {pagedServices.map((service) => (
                <tr key={`${service.namespace}-${service.name}`} className="hover:bg-muted/50">
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-muted rounded text-sm">{service.namespace}</span>
                  </td>
                  <td className="px-4 py-3 font-medium">{service.name}</td>
                  <td className="px-4 py-3">
                    <div className="space-y-1">
                      {Object.entries(service.external).map(([name, url]) => (
                        <a
                          key={name}
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-sm text-primary hover:underline"
                        >
                          {name}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="space-y-1.5">
                      {Object.entries(service.internal).map(([name, url]) => (
                        <div key={name} className="flex items-center gap-2">
                          <span className="text-sm font-medium min-w-0 shrink-0">{name}</span>
                          <CopyButton url={url} />
                        </div>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <Pagination page={page} pageSize={PAGE_SIZE} total={visibleServices.length} onPageChange={setPage} />
      </div>
    </div>
  );
}

export default function ServicesPage() {
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
      <ServicesContent />
    </AppLayout>
  );
}
