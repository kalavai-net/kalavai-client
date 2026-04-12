# Feature Flags

This document describes how to use the feature flags implemented in the Kalavai UI to control the visibility of certain pages based on environment variables.

## Available Feature Flags

The following feature flags are available:

- `SHOW_RESOURCES` - Controls the visibility of the Resources page
- `SHOW_MONITORING` - Controls the visibility of the Monitoring page  
- `SHOW_USER_SPACES` - Controls the visibility of the User Spaces page

## How to Use

### Environment Variables

Set the following environment variables to control feature availability:

```bash
# Enable/disable Resources page
SHOW_RESOURCES=true

# Enable/disable Monitoring page
SHOW_MONITORING=true

# Enable/disable User Spaces page
SHOW_USER_SPACES=true
```

### Values

- `"true"` (case-insensitive) - Feature is enabled
- `"false"` (case-insensitive) - Feature is disabled
- Any other value or unset - Uses default value (enabled)

### Default Values

All features are enabled by default if the environment variable is not set.

## Implementation Details

### Feature Flag Utility

The feature flags are implemented using:

- `ui/utils/featureFlags.ts` - Core feature flag logic
- `ui/components/FeatureGate.tsx` - React component for conditional rendering
- `ui/components/FeatureNotAvailable.tsx` - Component shown when feature is disabled

### Navigation Integration

The sidebar navigation (`ui/components/Sidebar.tsx`) automatically hides navigation items for disabled features.

### Page Protection

Each protected page is wrapped with the `FeatureGate` component:

```tsx
<FeatureGate feature="SHOW_RESOURCES" featureName="Resources">
  <AppLayout>
    <ResourcesContent />
  </AppLayout>
</FeatureGate>
```

### Environment Variable Injection

Environment variables are injected into the client-side code through the Next.js layout (`ui/app/layout.tsx`) to make them available in the browser.

## Examples

### Disable All Features Except Dashboard

```bash
SHOW_RESOURCES=false
SHOW_MONITORING=false
SHOW_USER_SPACES=false
```

### Enable Only Monitoring

```bash
SHOW_RESOURCES=false
SHOW_MONITORING=true
SHOW_USER_SPACES=false
```

### Using Docker

When running with Docker, set the environment variables:

```bash
docker run -e SHOW_RESOURCES=false -e SHOW_MONITORING=true kalavai-ui
```

### Using Docker Compose

```yaml
services:
  ui:
    environment:
      - SHOW_RESOURCES=false
      - SHOW_MONITORING=true
      - SHOW_USER_SPACES=false
```

## User Experience

When a feature is disabled:

1. The navigation item is hidden from the sidebar
2. Direct URL access to the feature page shows a "Feature Not Available" message
3. Users can navigate back to the previous page

## Development

During development, you can check feature flag status by:

1. Navigating to the Settings page and viewing the "Feature Flags" section
2. Setting environment variables in your `.env.local` file
3. Using browser developer tools to modify `window.env`

## Troubleshooting

### Feature Still Visible After Disabling

1. Check that the environment variable is properly set
2. Restart the application after changing environment variables
3. Clear browser cache and reload
4. Check browser console for any JavaScript errors

### Feature Not Working in Production

1. Ensure the environment variables are properly passed to the container
2. Verify the Next.js build process includes the environment variables
3. Check that the variables are not being overridden by other configuration
