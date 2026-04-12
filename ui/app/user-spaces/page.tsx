'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores';
import { AppLayout } from '@/components/AppLayout';
import { LoginForm } from '@/components/LoginForm';
import { FeatureGate } from '@/components/FeatureGate';
import { 
  Layers, 
  Plus, 
  Edit2, 
  Trash2, 
  Cpu, 
  Monitor, 
  MemoryStick, 
  Loader2, 
  Check, 
  X,
  Users,
  Shield,
  RefreshCw
} from 'lucide-react';
import kalavaiApi from '@/utils/api';

interface UserSpace {
  name: string;
  quota?: {
    cpu?: string;
    memory?: string;
    'nvidia.com/gpu'?: string;
    'amd.com/gpu'?: string;
  };
  used?: {
    cpu?: string;
    memory?: string;
    'nvidia.com/gpu'?: string;
    'amd.com/gpu'?: string;
  };
  labels?: Record<string, string>;
}

interface QuotaFormData {
  cpu: string;
  memory: string;
  nvidiaGpu: string;
  amdGpu: string;
  labels: Record<string, string>;
}

export default function UserSpacesPage() {
  const { isLoggedIn } = useAuthStore();
  const [userSpaces, setUserSpaces] = useState<UserSpace[]>([]);
  const [selectedSpace, setSelectedSpace] = useState<UserSpace | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [formData, setFormData] = useState<QuotaFormData>({
    cpu: '',
    memory: '',
    nvidiaGpu: '',
    amdGpu: '',
    labels: {}
  });
  const [newSpaceName, setNewSpaceName] = useState('');
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [quotaLoading, setQuotaLoading] = useState(false);

  const loadUserSpaces = async () => {
    try {
      setLoading(true);
      const spaces = await kalavaiApi.getAvailableUserSpaces();
      console.log('Available spaces:', spaces);
      
      // Check for API error response
      if (spaces && typeof spaces === 'object' && 'error' in spaces) {
        console.error('API returned error:', spaces.error);
        setFormErrors({ general: spaces.error || 'Failed to load user spaces. Please try again.' });
        setUserSpaces([]);
        return;
      }
      
      // Only load space names initially, without quota data
      const spacesWithoutQuota = spaces.map((name: string) => ({ 
        name, 
        quota: undefined, 
        used: undefined, 
        labels: undefined 
      }));
      
      console.log('Spaces without quota data:', spacesWithoutQuota);
      setUserSpaces(spacesWithoutQuota);
    } catch (error) {
      console.error('Failed to load user spaces:', error);
      setFormErrors({ general: 'Failed to load user spaces. Please try again.' });
      setUserSpaces([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isLoggedIn) {
      loadUserSpaces();
    }
  }, [isLoggedIn]);

  const handleSpaceSelect = async (spaceName: string) => {
    console.log('[UI DEBUG] handleSpaceSelect called with spaceName:', spaceName);
    const space = userSpaces.find(s => s.name === spaceName);
    console.log('[UI DEBUG] Found space in userSpaces:', space);
    if (!space) return;
    
    setSelectedSpace(space);
    setQuotaLoading(true);
    
    // Always fetch fresh quota data when selecting a space
    try {
      console.log('[UI DEBUG] Fetching quota for space:', spaceName);
      const response = await kalavaiApi.getUserSpaceQuota(spaceName);
      console.log('[UI DEBUG] Raw API response in handleSpaceSelect:', response);
      
      // Check for API error response
      if (response && typeof response === 'object' && 'error' in response) {
        console.error('API returned error:', response.error);
        setFormErrors({ general: response.error || 'Failed to load quota. Please try again.' });
        setSelectedSpace({ name: spaceName, quota: undefined, used: undefined, labels: undefined });
        setFormData({
          cpu: '',
          memory: '',
          nvidiaGpu: '',
          amdGpu: '',
          labels: {}
        });
        return;
      }
      
      // Handle the new structured response from API client
      let quotaData = null;
      let usedData = null;
      let labelsData = {};
      
      if (response && typeof response === 'object') {
        console.log('[UI DEBUG] Processing response object');
        
        // Check if response has the new structure with quota, used, labels
        if (response.quota) {
          console.log('[UI DEBUG] Using response.quota:', response.quota);
          quotaData = response.quota;
          usedData = response.used || {};
          labelsData = response.labels || {};
        }
        // Fallback to original logic for backward compatibility
        else if (response.quota) {
          console.log('[UI DEBUG] Using response.quota (old format):', response.quota);
          quotaData = response.quota;
          labelsData = response.labels || {};
        } 
        // Check if response itself is the quota (direct response)
        else if (response.cpu || response.memory || response['nvidia.com/gpu'] || response['amd.com/gpu']) {
          console.log('[UI DEBUG] Using response as direct quota:', response);
          quotaData = response;
          labelsData = response.labels || {};
        }
        // Check if response is an array with quota data
        else if (Array.isArray(response) && response.length > 0) {
          console.log('[UI DEBUG] Processing array response:', response);
          const firstItem = response[0];
          if (firstItem.quota) {
            quotaData = firstItem.quota;
            usedData = firstItem.used || {};
            labelsData = firstItem.labels || {};
          } else if (firstItem.cpu || firstItem.memory || firstItem['nvidia.com/gpu'] || firstItem['amd.com/gpu']) {
            quotaData = firstItem;
            labelsData = firstItem.labels || {};
          }
        } else {
          console.log('[UI DEBUG] No quota data found in response structure');
        }
      } else {
        console.log('[UI DEBUG] Response is not an object or is null:', response);
      }
      
      console.log('[UI DEBUG] Final processed quota data:', quotaData);
      console.log('[UI DEBUG] Final processed used data:', usedData);
      console.log('[UI DEBUG] Final processed labels data:', labelsData);
      
      const updatedSpace = { 
        name: spaceName, 
        quota: quotaData, 
        used: usedData,
        labels: labelsData 
      };
      
      console.log('[UI DEBUG] Updated space object:', updatedSpace);
      setSelectedSpace(updatedSpace);
      
      // Update the space in the list
      setUserSpaces(prev => 
        prev.map(s => s.name === spaceName ? updatedSpace : s)
      );
      
      if (quotaData && Object.keys(quotaData).length > 0) {
        console.log('[UI DEBUG] Setting form data with quota:', quotaData);
        setFormData({
          cpu: quotaData.cpu ? 
          (quotaData.cpu.includes('m') ? (parseFloat(quotaData.cpu.replace('m', '')) / 1000).toString() : quotaData.cpu) 
          : '',
          memory: quotaData.memory ? quotaData.memory.replace('Gi', '') : '',
          nvidiaGpu: quotaData['nvidia.com/gpu'] || '',
          amdGpu: quotaData['amd.com/gpu'] || '',
          labels: labelsData || {}
        });
      } else {
        console.log('[UI DEBUG] No quota data found, clearing form');
        setFormData({
          cpu: '',
          memory: '',
          nvidiaGpu: '',
          amdGpu: '',
          labels: {}
        });
      }
    } catch (error) {
      console.error('[UI DEBUG] Failed to load quota:', error);
      setFormErrors({ general: 'Failed to load quota. Please try again.' });
      // Still set the space even if quota fails
      setSelectedSpace(space);
      setFormData({
        cpu: '',
        memory: '',
        nvidiaGpu: '',
        amdGpu: '',
        labels: {}
      });
    } finally {
      setQuotaLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (showCreateForm && !newSpaceName) {
      errors.general = 'Space name is required';
    }
    
    // Kubernetes naming convention validation for space names
    if (showCreateForm && newSpaceName) {
      const k8sNameRegex = /^[a-z0-9]([-a-z0-9]*[a-z0-9])?$/;
      if (!k8sNameRegex.test(newSpaceName)) {
        errors.newSpaceName = 'Invalid name. Use lowercase letters, numbers, and hyphens only. Must start and end with alphanumeric character.';
      }
      if (newSpaceName.length > 100) {
        errors.newSpaceName = errors.newSpaceName || 'Space name must be 100 characters or less.';
      }
    }
    
    if (!formData.cpu && !formData.memory && !formData.nvidiaGpu && !formData.amdGpu) {
      errors.general = errors.general || 'At least one resource quota must be specified';
    }
    
    if (formData.cpu && isNaN(parseFloat(formData.cpu))) {
      errors.cpu = 'CPU quota must be a number';
    }
    
    if (formData.memory && isNaN(parseFloat(formData.memory))) {
      errors.memory = 'Memory quota must be a number';
    }
    
    if (formData.nvidiaGpu && isNaN(parseInt(formData.nvidiaGpu))) {
      errors.nvidiaGpu = 'NVIDIA GPU quota must be an integer';
    }
    
    if (formData.amdGpu && isNaN(parseInt(formData.amdGpu))) {
      errors.amdGpu = 'AMD GPU quota must be an integer';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (spaceName?: string) => {
    if (!validateForm()) return;
    
    try {
      setSubmitting(true);
      const quota: Record<string, string> = {};
      
      if (formData.cpu) quota.cpu = formData.cpu;
      if (formData.memory) quota.memory = `${formData.memory}Gi`;
      if (formData.nvidiaGpu) quota['nvidia.com/gpu'] = formData.nvidiaGpu;
      if (formData.amdGpu) quota['amd.com/gpu'] = formData.amdGpu;
      
      console.log('[DEBUG] Form data:', formData);
      console.log('[DEBUG] Sending quota to API:', quota);
      console.log('[DEBUG] CPU value:', formData.cpu, '-> quota.cpu:', quota.cpu);
      
      const name = spaceName || newSpaceName || selectedSpace?.name || '';
      if (!name) {
        setFormErrors({ general: 'Space name is required' });
        return;
      }
      
      const response = await kalavaiApi.setUserSpaceQuota(name, quota);
      
      // Check for API error response
      if (response && typeof response === 'object' && 'error' in response) {
        console.error('API returned error:', response.error);
        setFormErrors({ general: response.error || 'Failed to save quota. Please try again.' });
        return;
      }
      
      setShowCreateForm(false);
      setShowEditForm(false);
      setFormErrors({});
      loadUserSpaces();
      
      if (spaceName || newSpaceName) {
        setSelectedSpace({ name: name, quota, labels: formData.labels });
        setNewSpaceName(''); // Reset new space name
      }
    } catch (error) {
      console.error('Failed to set quota:', error);
      setFormErrors({ general: 'Failed to save quota. Please try again.' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedSpace) return;
    
    try {
      setSubmitting(true);
      const response = await kalavaiApi.deleteUserSpace(selectedSpace.name);
      
      // Check for API error response
      if (response && typeof response === 'object' && 'error' in response) {
        console.error('API returned error:', response.error);
        setFormErrors({ general: response.error || 'Failed to delete user space. Please try again.' });
        return;
      }
      
      // Remove from list and clear selection
      setUserSpaces(prev => prev.filter(s => s.name !== selectedSpace.name));
      setSelectedSpace(null);
      setShowDeleteConfirm(false);
      resetForm();
    } catch (error) {
      console.error('Failed to delete user space:', error);
      setFormErrors({ general: 'Failed to delete user space. Please try again.' });
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      cpu: '',
      memory: '',
      nvidiaGpu: '',
      amdGpu: '',
      labels: {}
    });
    setNewSpaceName('');
    setFormErrors({});
  };

  const handleCreateNew = () => {
    resetForm();
    setShowCreateForm(true);
    setShowEditForm(false);
    setSelectedSpace(null);
  };

  const handleEdit = () => {
    if (!selectedSpace) return;
    setShowEditForm(true);
    setShowCreateForm(false);
  };

  const addLabel = () => {
    const key = prompt('Enter label key:');
    if (!key) return;
    
    const value = prompt('Enter label value:');
    if (!value) return;
    
    setFormData(prev => ({
      ...prev,
      labels: { ...prev.labels, [key]: value }
    }));
  };

  const removeLabel = (key: string) => {
    setFormData(prev => ({
      ...prev,
      labels: Object.fromEntries(
        Object.entries(prev.labels).filter(([k]) => k !== key)
      )
    }));
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-background">
        <LoginForm />
      </div>
    );
  }

  return (
    <FeatureGate feature="SHOW_USER_SPACES" featureName="User Spaces">
      <AppLayout>
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Users className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">User Spaces</h1>
              <p className="text-muted-foreground">Manage user spaces and resource quotas</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* User Spaces List */}
          <div className="lg:col-span-1">
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Layers className="w-5 h-5" />
                  Available Spaces
                </h2>
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => {
                      loadUserSpaces();
                      if (selectedSpace) {
                        handleSpaceSelect(selectedSpace.name);
                      }
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 bg-muted border border-border rounded-lg hover:bg-muted/80 transition-colors text-sm whitespace-nowrap"
                    title="Refresh spaces and quota data"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                  </button>
                  <button
                    onClick={handleCreateNew}
                    className="flex items-center gap-2 px-3 py-1.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm whitespace-nowrap"
                  >
                    <Plus className="w-4 h-4" />
                    Add
                  </button>
                </div>
              </div>
              
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin" />
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Select User Space</label>
                    <select
                      value={selectedSpace?.name || ''}
                      onChange={(e) => e.target.value && handleSpaceSelect(e.target.value)}
                      className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary bg-background"
                    >
                      <option value="">Choose a space...</option>
                      {userSpaces.map((space) => (
                        <option key={space.name} value={space.name}>
                          {space.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {userSpaces.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      No user spaces found
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Space Details and Forms */}
          <div className="lg:col-span-2">
            {selectedSpace && !showCreateForm && !showEditForm && (
              <div className="bg-card border border-border rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold">{selectedSpace.name}</h2>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleEdit}
                      className="flex items-center gap-2 px-3 py-1.5 bg-muted border border-border rounded-lg hover:bg-muted/80 transition-colors"
                    >
                      <Edit2 className="w-4 h-4" />
                      Edit
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(true)}
                      className="flex items-center gap-2 px-3 py-1.5 bg-red-50 border border-red-200 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                </div>

                {quotaLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    <span className="ml-3 text-muted-foreground">Loading resource quotas...</span>
                  </div>
                ) : selectedSpace.quota ? (
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium flex items-center gap-2">
                      <Shield className="w-5 h-5" />
                      Resource Quotas
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {selectedSpace.quota.cpu && (
                        <div className="flex items-center gap-3 p-3 bg-muted/40 rounded-lg">
                          <Cpu className="w-5 h-5 text-blue-500" />
                          <div className="flex-1">
                            <div className="text-sm font-medium">CPU</div>
                            <div className="text-lg font-bold">
                              {selectedSpace.used?.cpu ? 
                                (selectedSpace.used.cpu.includes('m') ? (parseFloat(selectedSpace.used.cpu.replace('m', '')) / 1000).toFixed(3) : selectedSpace.used.cpu) 
                                : '0'} / {selectedSpace.quota.cpu || '0'} cores
                            </div>
                            {selectedSpace.used?.cpu && selectedSpace.quota.cpu && (
                              <div className="text-xs text-muted-foreground">
                                {((parseFloat(selectedSpace.used.cpu.includes('m') ? selectedSpace.used.cpu.replace('m', '') : selectedSpace.used.cpu) / 
                                   parseFloat(selectedSpace.quota.cpu.includes('m') ? (parseFloat(selectedSpace.quota.cpu.replace('m', '')) / 1000).toString() : selectedSpace.quota.cpu)) * 100).toFixed(1)}% used
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {selectedSpace.quota.memory && (
                        <div className="flex items-center gap-3 p-3 bg-muted/40 rounded-lg">
                          <MemoryStick className="w-5 h-5 text-green-500" />
                          <div className="flex-1">
                            <div className="text-sm font-medium">Memory</div>
                            <div className="text-lg font-bold">
                              {selectedSpace.used?.memory || '0'} / {selectedSpace.quota.memory} GB
                            </div>
                            {selectedSpace.used?.memory && (
                              <div className="text-xs text-muted-foreground">
                                {((parseFloat(selectedSpace.used.memory) / parseFloat(selectedSpace.quota.memory)) * 100).toFixed(1)}% used
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {selectedSpace.quota['nvidia.com/gpu'] && (
                        <div className="flex items-center gap-3 p-3 bg-muted/40 rounded-lg">
                          <Monitor className="w-5 h-5 text-purple-500" />
                          <div className="flex-1">
                            <div className="text-sm font-medium">NVIDIA GPUs</div>
                            <div className="text-lg font-bold">
                              {selectedSpace.used?.['nvidia.com/gpu'] || '0'} / {selectedSpace.quota['nvidia.com/gpu']}
                            </div>
                            {selectedSpace.used?.['nvidia.com/gpu'] && (
                              <div className="text-xs text-muted-foreground">
                                {((parseInt(selectedSpace.used['nvidia.com/gpu']) / parseInt(selectedSpace.quota['nvidia.com/gpu'])) * 100).toFixed(1)}% used
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {selectedSpace.quota['amd.com/gpu'] && (
                        <div className="flex items-center gap-3 p-3 bg-muted/40 rounded-lg">
                          <Monitor className="w-5 h-5 text-red-500" />
                          <div className="flex-1">
                            <div className="text-sm font-medium">AMD GPUs</div>
                            <div className="text-lg font-bold">
                              {selectedSpace.used?.['amd.com/gpu'] || '0'} / {selectedSpace.quota['amd.com/gpu']}
                            </div>
                            {selectedSpace.used?.['amd.com/gpu'] && (
                              <div className="text-xs text-muted-foreground">
                                {((parseInt(selectedSpace.used['amd.com/gpu']) / parseInt(selectedSpace.quota['amd.com/gpu'])) * 100).toFixed(1)}% used
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Shield className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">No resource quotas set</p>
                    <p className="text-sm text-muted-foreground mt-2">
                      This space has unlimited resource access
                    </p>
                  </div>
                )}

                {selectedSpace.labels && Object.keys(selectedSpace.labels).length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-lg font-medium mb-3">Labels</h3>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(selectedSpace.labels).map(([key, value]) => (
                        <span
                          key={key}
                          className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm"
                        >
                          {key}: {value}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Create/Edit Form */}
            {(showCreateForm || showEditForm) && (
              <div className="bg-card border border-border rounded-xl p-6">
                <h2 className="text-xl font-semibold mb-6">
                  {showCreateForm ? 'Create New User Space' : `Edit ${selectedSpace?.name}`}
                </h2>

                {formErrors.general && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    {formErrors.general}
                  </div>
                )}

                {showCreateForm && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-2 text-foreground">Space Name</label>
                    <input
                      type="text"
                      value={newSpaceName}
                      onChange={(e) => setNewSpaceName(e.target.value)}
                      className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary bg-background text-foreground placeholder:text-foreground/60 ${
                        formErrors.newSpaceName ? 'border-red-500' : 'border-border'
                      }`}
                      placeholder="e.g., my-user-space"
                    />
                    {formErrors.newSpaceName && (
                      <p className="text-red-500 text-xs mt-1">{formErrors.newSpaceName}</p>
                    )}
                  </div>
                )}

                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">CPU (cores)</label>
                      <input
                        type="text"
                        value={formData.cpu}
                        onChange={(e) => setFormData({ ...formData, cpu: e.target.value })}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary bg-background text-foreground placeholder:text-foreground/60 ${
                          formErrors.cpu ? 'border-red-500' : 'border-border'
                        }`}
                        placeholder="e.g., 0.5"
                      />
                      {formErrors.cpu && (
                        <p className="text-red-500 text-xs mt-1">{formErrors.cpu}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">Memory (GB)</label>
                      <input
                        type="text"
                        value={formData.memory}
                        onChange={(e) => setFormData({ ...formData, memory: e.target.value })}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary bg-background text-foreground placeholder:text-foreground/60 ${
                          formErrors.memory ? 'border-red-500' : 'border-border'
                        }`}
                        placeholder="e.g., 8"
                      />
                      {formErrors.memory && (
                        <p className="text-red-500 text-xs mt-1">{formErrors.memory}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">NVIDIA GPUs</label>
                      <input
                        type="text"
                        value={formData.nvidiaGpu}
                        onChange={(e) => setFormData({ ...formData, nvidiaGpu: e.target.value })}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary bg-background text-foreground placeholder:text-foreground/60 ${
                          formErrors.nvidiaGpu ? 'border-red-500' : 'border-border'
                        }`}
                        placeholder="e.g., 1"
                      />
                      {formErrors.nvidiaGpu && (
                        <p className="text-red-500 text-xs mt-1">{formErrors.nvidiaGpu}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">AMD GPUs</label>
                      <input
                        type="text"
                        value={formData.amdGpu}
                        onChange={(e) => setFormData({ ...formData, amdGpu: e.target.value })}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary bg-background text-foreground placeholder:text-foreground/60 ${
                          formErrors.amdGpu ? 'border-red-500' : 'border-border'
                        }`}
                        placeholder="e.g., 1"
                      />
                      {formErrors.amdGpu && (
                        <p className="text-red-500 text-xs mt-1">{formErrors.amdGpu}</p>
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium">Labels</label>
                      <button
                        onClick={addLabel}
                        className="text-xs px-2 py-1 bg-muted border border-border rounded hover:bg-muted/80 transition-colors"
                      >
                        Add Label
                      </button>
                    </div>
                    <div className="space-y-2">
                      {Object.entries(formData.labels).map(([key, value]) => (
                        <div key={key} className="flex items-center gap-2">
                          <span className="text-sm flex-1">
                            <span className="font-medium">{key}:</span> {value}
                          </span>
                          <button
                            onClick={() => removeLabel(key)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                      {Object.keys(formData.labels).length === 0 && (
                        <p className="text-sm text-muted-foreground">No labels defined</p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 mt-6">
                  <button
                    onClick={() => handleSubmit(showCreateForm ? newSpaceName : undefined)}
                    disabled={submitting}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                  >
                    {submitting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Check className="w-4 h-4" />
                    )}
                    {showCreateForm ? 'Create Space' : 'Save Changes'}
                  </button>
                  <button
                    onClick={() => {
                      setShowCreateForm(false);
                      setShowEditForm(false);
                      resetForm();
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-muted border border-border rounded-lg hover:bg-muted/80 transition-colors"
                  >
                    <X className="w-4 h-4" />
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {!selectedSpace && !showCreateForm && (
              <div className="bg-card border border-border rounded-xl p-12 text-center">
                <Layers className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Space Selected</h3>
                <p className="text-muted-foreground mb-6">
                  Select a user space from the list to view details or create a new one
                </p>
                <button
                  onClick={handleCreateNew}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Create New Space
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* Delete Confirmation Dialog */}
        {showDeleteConfirm && selectedSpace && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card border border-border rounded-xl p-6 max-w-md w-full mx-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-red-100">
                  <Trash2 className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">Delete User Space</h3>
                  <p className="text-sm text-muted-foreground">
                    This action cannot be undone
                  </p>
                </div>
              </div>
              
              <div className="mb-6">
                <p className="text-muted-foreground mb-2">
                  Are you sure you want to delete the user space:
                </p>
                <div className="p-3 bg-muted/40 rounded-lg border border-border/50">
                  <span className="font-medium">{selectedSpace.name}</span>
                </div>
                {selectedSpace.quota && (
                  <p className="text-xs text-muted-foreground mt-2">
                    All resource quotas and configurations will be permanently removed.
                  </p>
                )}
              </div>
              
              {formErrors.general && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  {formErrors.general}
                </div>
              )}
              
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDelete}
                  disabled={submitting}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {submitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  Delete Space
                </button>
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setFormErrors({});
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-muted border border-border rounded-lg hover:bg-muted/80 transition-colors"
                >
                  <X className="w-4 h-4" />
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
    </FeatureGate>
  );
}
