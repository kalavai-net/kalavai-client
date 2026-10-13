// Short-term cache for the job template list enriched with `category` annotations.
//
// Fetching the template list plus one metadata call per template is expensive,
// and templates rarely change, so the Jobs deploy modal reuses the last
// enriched result instead of refetching every time it opens.
// The cache is voided by `invalidateTemplateCache()` (called from Settings
// after repositories are updated) and expires on its own after a short TTL.

export interface CachedTemplate {
  name: string;
  category?: string;
}

const TEMPLATE_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

let cachedTemplates: CachedTemplate[] | null = null;
let cachedAt = 0;

export function getCachedTemplates(): CachedTemplate[] | null {
  if (!cachedTemplates) return null;
  if (Date.now() - cachedAt > TEMPLATE_CACHE_TTL_MS) {
    cachedTemplates = null;
    return null;
  }
  // Return copies so callers can't mutate the cached entries.
  return cachedTemplates.map(t => ({ ...t }));
}

export function setCachedTemplates(templates: CachedTemplate[]): void {
  cachedTemplates = templates.map(t => ({ ...t }));
  cachedAt = Date.now();
}

export function updateCachedTemplateCategory(name: string, category: string): void {
  if (!cachedTemplates) return;
  cachedTemplates = cachedTemplates.map(t =>
    t.name === name ? { ...t, category } : t
  );
}

export function invalidateTemplateCache(): void {
  cachedTemplates = null;
  cachedAt = 0;
}
