# NodePort for thanos query component
THANOS_QUERY_ENDPOINT="http://localhost:32298"

# Test basic connectivity
echo "\nBasic connectivity test\n"
curl -G "${THANOS_QUERY_ENDPOINT}/api/v1/query" \
  --data-urlencode 'query=up'

# Query with time range (last hour) - FIXED TIME FORMAT
echo "\nQuery with time range test\n"
curl -G "${THANOS_QUERY_ENDPOINT}/api/v1/query_range" \
  --data-urlencode 'query=rate(prometheus_http_requests_total[5m])' \
  --data-urlencode 'start=2026-02-15T19:00:00Z' \
  --data-urlencode 'end=2026-02-15T20:00:00Z'

echo "\nQuery range test\n"
# Check store endpoints (shows data sources)
curl -G "${THANOS_QUERY_ENDPOINT}/api/v1/stores"

# Test data availability (should show recent metrics) - FIXED AGGREGATE
echo "\nData availability test\n"
curl -G "${THANOS_QUERY_ENDPOINT}/api/v1/query" \
  --data-urlencode 'query=count by (__name__)({job=~".+"})'

# Test with absolute time (RFC3339 format)
echo "\nAbsolute time test\n"
curl -G "${THANOS_QUERY_ENDPOINT}/api/v1/query" \
  --data-urlencode 'query=prometheus_build_info' \
  --data-urlencode 'time=2026-02-15T13:00:00Z'

echo "\nFinal test completed\n"
