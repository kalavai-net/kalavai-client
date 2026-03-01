# Kalavai Platform UI

A modern, JavaScript-based web interface for the Kalavai client - a distributed GPU pool management platform. This UI provides an intuitive dashboard for managing compute resources, deploying AI workloads, and monitoring pool health.

## Overview

This project is a complete reimplementation of the original Python Reflex-based GUI, ported to a modern JavaScript stack using Next.js, TypeScript, Tailwind CSS, and React.

### Key Features

- **Home Page**: Landing page with quick actions and pool overview
- **Dashboard**: Resource monitoring with real-time gauges and statistics
- **Resources**: Node management with GPU tracking, labeling, and cordoning
- **Jobs**: Job deployment with template-based workflows and log viewing
- **Services**: Core service monitoring and endpoint management
- **Settings**: Theme customization (colors, radius, scaling)

## Technology Stack

- **Framework**: [Next.js 14](https://nextjs.org/) (React 18)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **State Management**: [Zustand](https://github.com/pmndrs/zustand) with persistence
- **Icons**: [Lucide React](https://lucide.dev/)
- **Charts**: [Recharts](https://recharts.org/)
- **HTTP Client**: [Axios](https://axios-http.com/)

## Prerequisites

- Node.js 18+ 
- npm or yarn
- Running Kalavai API server (default: http://0.0.0.0:49152)

## Setup

1. **Install dependencies**:
   ```bash
   cd ui
   npm install
   ```

2. **Configure environment** (optional):
   Create a `.env.local` file:
   ```
   NEXT_PUBLIC_KALAVAI_API_URL=http://0.0.0.0:49152
   NEXT_PUBLIC_ACCESS_KEY=your_access_key_here
   ```

3. **Run development server**:
   ```bash
   npm run dev
   ```

4. **Open in browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
ui/
├── app/                    # Next.js App Router pages
│   ├── dashboard/         # Dashboard page
│   ├── jobs/              # Jobs management page
│   ├── resources/         # Resources page
│   ├── services/          # Services page
│   ├── settings/          # Settings page
│   ├── globals.css        # Global styles with Tailwind
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── AppLayout.tsx      # Application layout wrapper
│   ├── LoginForm.tsx      # Authentication form
│   └── Sidebar.tsx        # Navigation sidebar
├── stores/                # Zustand state management
│   └── index.ts           # Auth, connection, and theme stores
├── utils/                 # Utility functions
│   ├── api.ts             # Kalavai API client
│   └── cn.ts              # Tailwind class merging
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── postcss.config.js
```

## API Integration

The UI communicates with the Kalavai core API via REST endpoints. The API client (`utils/api.ts`) provides typed methods for all available operations:

### Pool Management
- `createPool()` - Create a new compute pool
- `joinPool()` - Join an existing pool
- `stopPool()` - Stop and clean up pool
- `deleteNodes()` - Remove nodes from pool
- `cordonNodes()` / `uncordonNodes()` - Control node scheduling

### Resource Monitoring
- `fetchDevices(nodeLabels?)` - List all compute devices (optionally filtered by node labels)
- `fetchResources()` - Get resource utilization
- `fetchGpus()` - Get GPU information
- `getComputeUsage(data)` - Get compute usage metrics for time range
- `fetchNodesMetrics(data)` - Get node metrics time series data

### Job Management
- `fetchJobDetails()` - List deployed jobs
- `deployJob()` - Deploy from template
- `deleteJob()` - Remove a job
- `fetchJobLogs()` - View job logs

### Templates
- `fetchJobTemplates()` - List available templates
- `fetchTemplateAll()` - Get template details

## Authentication

The UI supports optional access key authentication via the `NEXT_PUBLIC_ACCESS_KEY` environment variable. When set, users must provide the matching key on first access.

## Theming

The UI includes a customizable theme system with:

- **Primary Colors**: 14 accent colors (grass, blue, indigo, violet, etc.)
- **Secondary Colors**: 6 gray variants
- **Border Radius**: 5 options from none to full
- **Scaling**: 5 scale levels from 90% to 110%

Settings are persisted in browser local storage.

## Usage Guide

### Connecting to a Pool

1. Navigate to the Home page
2. If not connected, available user spaces will be displayed
3. Use the CLI or join interface to connect to a pool

### Deploying a Job

1. Go to the **Jobs** page
2. Click **Deploy Job**
3. Enter a name and select a template
4. Configure template parameters
5. Click **Deploy**

### Managing Resources

1. Navigate to **Resources** page
2. View all connected nodes and their GPU status
3. Click on a node to view labels and resources
4. Use action buttons to cordon, uncordon, or delete nodes

### Viewing Dashboard

1. Go to **Dashboard** for pool overview
2. Monitor CPU, GPU, and memory utilization
3. View device and job counts

### Customizing Appearance

1. Visit **Settings** page
2. Select primary and secondary colors
3. Adjust border radius preference
4. Change interface scaling

## Development

### Adding New Pages

1. Create a new folder under `app/`
2. Add `page.tsx` with your component
3. Update `Sidebar.tsx` navigation if needed

### Adding API Endpoints

1. Add method to `KalavaiApiClient` class in `utils/api.ts`
2. Use existing methods as reference

### State Management

- Use `useAuthStore` for authentication state
- Use `useConnectionStore` for pool connection state
- Use `useThemeStore` for theme preferences

## Troubleshooting

### Connection Issues

- Verify Kalavai API is running at the configured URL
- Check `NEXT_PUBLIC_KALAVAI_API_URL` environment variable
- Ensure no firewall blocking the connection

### Build Errors

- Ensure all dependencies installed: `npm install`
- Clear `.next` folder: `rm -rf .next`
- Check Node.js version (18+ required)

### API Errors

- Check browser console for detailed error messages
- Verify API key if `NEXT_PUBLIC_ACCESS_KEY` is set
- Ensure Kalavai core API is accessible

## Deployment

### Docker

The image installs dependencies at build time but runs `next build` at container startup, so environment variables injected at runtime are picked up correctly.

**Build the image:**
```bash
docker build -t ghcr.io/kalavai-net/kalavai-ui:latest .
```

**Run the container**, passing env vars directly:
```bash
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_KALAVAI_API_URL=http://your-api-server:49152 \
  -e NEXT_PUBLIC_ACCESS_KEY=your-access-key \
  ghcr.io/kalavai-net/kalavai-ui:latest
```

The UI will be available at [http://localhost:3000](http://localhost:3000).

> **Note:** The first startup takes ~30 seconds while `next build` runs inside the container.

### Kubernetes

An example manifest is provided in `k8s-deployment.yaml`. Update the env var values and apply:

```bash
kubectl apply -f k8s-deployment.yaml
```

The manifest creates a `Deployment` and a `ClusterIP` `Service` on port 80. To expose the UI externally, change the `Service` type to `LoadBalancer` or add an `Ingress`.

For sensitive values, use a Kubernetes `Secret` instead of a plain env var:

```yaml
env:
  - name: NEXT_PUBLIC_ACCESS_KEY
    valueFrom:
      secretKeyRef:
        name: kalavai-ui-secret
        key: access-key
```

## License

This project is part of the Kalavai client distribution. See the main project repository for licensing details.

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing TypeScript patterns
- Components use Tailwind CSS for styling
- State changes use Zustand stores
- New features include proper TypeScript types

## Support

For issues and feature requests, please refer to the main Kalavai client repository or documentation at https://kalavai-net.github.io/kalavai-client/
