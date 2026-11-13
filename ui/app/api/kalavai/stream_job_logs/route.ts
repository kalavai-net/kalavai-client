// Streaming proxy for endpoints that must stay live (SSE log streams).
// Unlike next.config.js rewrites (which buffer the upstream response),
// this route handler pipes the backend body chunk-by-chunk with
// `response.body.pipeTo`, so the browser receives frames as they arrive.
const BACKEND_URL =
  process.env.KALAVAI_API_URL ||
  process.env.NEXT_PUBLIC_KALAVAI_API_URL ||
  'http://0.0.0.0:49152';

export async function GET(request: Request) {
  const incoming = new URL(request.url);
  const target = new URL('/fetch_job_logs', BACKEND_URL);
  for (const [key, value] of incoming.searchParams.entries()) {
    target.searchParams.set(key, value);
  }

  const headers: Record<string, string> = {};
  const accessKey =
    request.headers.get('x-api-key') || process.env.NEXT_PUBLIC_ACCESS_KEY || '';
  if (accessKey) headers['X-API-Key'] = accessKey;

  let upstream: Response;
  try {
    upstream = await fetch(target.toString(), {
      headers,
      // Do not impose a client timeout; abort propagates from the browser.
      signal: request.signal,
    });
  } catch (err) {
    return new Response(`Stream proxy error: ${err}`, { status: 502 });
  }

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => '');
    return new Response(text || `Backend error: ${upstream.status}`, {
      status: upstream.status || 502,
    });
  }

  const { readable, writable } = new TransformStream();
  upstream.body.pipeTo(writable, { signal: request.signal }).catch(() => {
    try {
      writable.abort();
    } catch {
      /* client went away */
    }
  });

  return new Response(readable, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  });
}
