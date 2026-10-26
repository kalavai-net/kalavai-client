// Session-scoped cache for the job template list enriched with `category` annotations.
//
// Fetching the template list plus one metadata call per template is expensive,
// and templates rarely change, so the Jobs deploy modal reuses the last
// enriched result instead of refetching every time it opens.
// The cache lives for the current browser session (in-memory with a
// sessionStorage backup so it survives page reloads in the same tab) and is
// only voided by `invalidateTemplateCache()` (called from Settings after
// repositories are updated). There is intentionally no TTL: within a session
// templates must not refetch on their own.

export interface CachedTemplate {
  name: string;
  category?: string;
}

const STORAGE_KEY = 'kalavai-template-cache-v1';

let cachedTemplates: CachedTemplate[] | null = null;

function readStoredTemplates(): CachedTemplate[] | null {
  try {
    if (typeof window === 'undefined' || !window.sessionStorage) return null;
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return null;
    const list = parsed.filter(
      (t): t is CachedTemplate =>
        typeof t === 'object' &&
        t !== null &&
        typeof (t as CachedTemplate).name === 'string'
    );
    return list.map(t => ({ ...t }));
  } catch {
    return null;
  }
}

function writeStoredTemplates(templates: CachedTemplate[] | null): void {
  try {
    if (typeof window === 'undefined' || !window.sessionStorage) return;
    if (!templates) {
      window.sessionStorage.removeItem(STORAGE_KEY);
      return;
    }
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(templates));
  } catch {
    // Storage may be unavailable (private mode, quota) — in-memory cache still applies.
  }
}

export function getCachedTemplates(): CachedTemplate[] | null {
  if (cachedTemplates) {
    // Return copies so callers can't mutate the cached entries.
    return cachedTemplates.map(t => ({ ...t }));
  }
  const stored = readStoredTemplates();
  if (stored) {
    cachedTemplates = stored;
    return stored.map(t => ({ ...t }));
  }
  return null;
}

export function setCachedTemplates(templates: CachedTemplate[]): void {
  cachedTemplates = templates.map(t => ({ ...t }));
  writeStoredTemplates(cachedTemplates);
}

export function updateCachedTemplateCategory(name: string, category: string): void {
  // Ensure memory is hydrated from storage before patching so late category
  // enrichment isn't lost when the page was reloaded mid-session.
  if (!cachedTemplates) {
    cachedTemplates = readStoredTemplates();
    if (!cachedTemplates) return;
  }
  cachedTemplates = cachedTemplates.map(t =>
    t.name === name ? { ...t, category } : t
  );
  writeStoredTemplates(cachedTemplates);
}

export function invalidateTemplateCache(): void {
  cachedTemplates = null;
  writeStoredTemplates(null);
}
