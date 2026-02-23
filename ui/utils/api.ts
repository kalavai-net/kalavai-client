import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores';

const ACCESS_KEY = process.env.NEXT_PUBLIC_ACCESS_KEY || null;

// Use the Next.js proxy to avoid CORS — requests go to /api/kalavai/* which
// next.config.js rewrites to the actual Kalavai API server.
const API_BASE = '/api/kalavai';

class KalavaiApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add API key
    this.client.interceptors.request.use((config) => {
      if (ACCESS_KEY) {
        config.headers['X-API-Key'] = ACCESS_KEY;
      }
      return config;
    });
  }

  // Pool Management
  async createPool(data: {
    cluster_name: string;
    ip_address: string;
    num_gpus: number;
    node_name: string;
    location: string;
  }) {
    return this.post('create_pool', data);
  }

  async joinPool(data: {
    token: string;
    ip_address?: string;
    node_name?: string;
    num_gpus?: number;
  }) {
    return this.post('join_pool', data);
  }

  async attachToPool(data: {
    token: string;
    node_name?: string;
    frontend?: boolean;
  }) {
    return this.post('attach_to_pool', data);
  }

  async stopPool(data: { skip_node_deletion?: boolean } = {}) {
    return this.post('stop_pool', data);
  }

  async deleteNodes(nodes: string[]) {
    return this.post('delete_nodes', { nodes });
  }

  async cordonNodes(nodes: string[]) {
    return this.post('cordon_nodes', { nodes });
  }

  async uncordonNodes(nodes: string[]) {
    return this.post('uncordon_nodes', { nodes });
  }

  // Auth & Status
  async getPoolToken(mode: number) {
    return this.get('get_pool_token', { params: { mode } });
  }

  async getPoolCredentials() {
    return this.get('get_pool_credentials');
  }

  async isConnected() {
    return this.get('is_connected');
  }

  async isAgentRunning() {
    return this.get('is_agent_running');
  }

  async isServer() {
    return this.get('is_server');
  }

  // Info
  async fetchDevices() {
    return this.get('fetch_devices');
  }

  async fetchResources(nodes?: string[]) {
    const response = await this.client.get('/fetch_resources', {
      data: nodes ? { nodes } : undefined,
    });
    return response.data;
  }

  async fetchJobNames() {
    return this.get('fetch_job_names');
  }

  async fetchGpus(available?: boolean) {
    return this.get('fetch_gpus', { params: { available } });
  }

  async fetchJobDetails(force_namespace?: string) {
    return this.get('fetch_job_details', { params: { force_namespace } });
  }

  async fetchJobLogs(
    job_name: string,
    force_namespace?: string,
    pod_name?: string,
    tail: number = 100
  ) {
    return this.get('fetch_job_logs', {
      params: { job_name, force_namespace, pod_name, tail },
    });
  }

  async fetchServiceLogs(tail: number = 100) {
    return this.get('fetch_service_logs', { params: { tail } });
  }

  async fetchJobTemplates() {
    return this.get('fetch_job_templates');
  }

  async fetchPoolServices() {
    return this.get('fetch_pool_services');
  }

  async fetchTemplateAll(name: string) {
    return this.get('fetch_template_all', { params: { name } });
  }

  async fetchTemplateValues(name: string) {
    return this.get('fetch_template_values', { params: { name } });
  }

  async fetchTemplateMetadata(name: string) {
    return this.get('fetch_template_metadata', { params: { name } });
  }

  async fetchTemplateSchema(name: string) {
    return this.get('fetch_template_schema', { params: { name } });
  }

  // Job Management
  async deployJob(data: {
    name: string;
    template_name: string;
    values: Record<string, unknown>;
    force_namespace?: string;
    target_labels?: Record<string, string[]>;
    target_labels_ops?: string;
  }) {
    return this.post('deploy_job', data);
  }

  async deployCustomJob(data: {
    template_str: string;
    values: Record<string, unknown>;
    force_namespace?: string;
    default_values?: Record<string, unknown>;
    target_labels?: Record<string, string[]>;
  }) {
    return this.post('deploy_custom_job', data);
  }

  async deleteJob(name: string, force_namespace?: string) {
    return this.post('delete_job', { name, force_namespace });
  }

  // User Spaces
  async getAvailableUserSpaces() {
    return this.get('get_available_user_spaces');
  }

  async getUserSpaceQuota(space_name?: string) {
    return this.get('get_user_space_quota', { params: { space_name } });
  }

  async setUserSpaceQuota(user_id: string, quota: Record<string, string>) {
    return this.post('set_user_space_quota', { user_id, quota });
  }

  // Node Labels
  async addNodeLabels(node_name: string, labels: Record<string, string>) {
    return this.post('add_node_labels', { node_name, labels });
  }

  async getNodeLabels(nodes?: string[]) {
    const params = new URLSearchParams();
    if (nodes) {
      nodes.forEach((n) => params.append('nodes', n));
    }
    const response = await this.client.get('/get_node_labels', { params });
    return response.data;
  }

  // Agent Management
  async pauseAgent() {
    return this.post('pause_agent');
  }

  async resumeAgent() {
    return this.post('resume_agent');
  }

  // Repository Management
  async updateRepositories() {
    return this.post('update_repositories');
  }

  // IP Addresses
  async getIpAddresses(subnet?: string) {
    return this.get('get_ip_addresses', { params: { subnet } });
  }

  // Worker Config
  async generateWorkerConfig(data: {
    node_name: string;
    mode: number;
    target_platform: string;
    num_gpus: number;
    ip_address?: string;
    storage_compatible?: boolean;
  }) {
    return this.post('generate_worker_config', data);
  }

  // Health Check
  async health() {
    return this.get('health');
  }

  // Generic methods
  private async get(endpoint: string, config?: AxiosRequestConfig) {
    const response = await this.client.get(`/${endpoint}`, config);
    return response.data;
  }

  private async post(endpoint: string, data?: unknown) {
    const response = await this.client.post(`/${endpoint}`, data);
    return response.data;
  }
}

export const kalavaiApi = new KalavaiApiClient();
export default kalavaiApi;
