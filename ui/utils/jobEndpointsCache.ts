// Cache of pool service endpoints exposed by deployed jobs.
//
// The jobs table already fetches full job details (including endpoints) via
// `fetchJobDetails`. The Deploy modal's Parameters step reuses that data so it
// doesn't have to call the API again. The snapshot is renewed every time the
// job table loads (see `loadJobs` in `app/jobs/page.tsx`).

export interface CachedJobEndpoint {
  jobName: string;
  owner: string;
  service: string;
  url: string;
  status?: string;
}

export interface CachedEndpointsSnapshot {
  /** Epoch ms when the snapshot was taken (i.e. when the job table loaded). */
  updatedAt: number;
  /** Namespace filter that was active for the job table load (`null` = all). */
  namespace: string | null;
  endpoints: CachedJobEndpoint[];
}

let cachedSnapshot: CachedEndpointsSnapshot | null = null;

export function setCachedJobEndpoints(snapshot: CachedEndpointsSnapshot): void {
  cachedSnapshot = {
    updatedAt: snapshot.updatedAt,
    namespace: snapshot.namespace,
    endpoints: snapshot.endpoints.map(e => ({ ...e })),
  };
}

export function getCachedJobEndpoints(): CachedEndpointsSnapshot | null {
  if (!cachedSnapshot) return null;
  return {
    ...cachedSnapshot,
    endpoints: cachedSnapshot.endpoints.map(e => ({ ...e })),
  };
}

export function invalidateJobEndpointsCache(): void {
  cachedSnapshot = null;
}
