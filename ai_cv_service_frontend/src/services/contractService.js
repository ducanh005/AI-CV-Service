import api from './api';

export const contractService = {
  listTargets: async ({ companyId } = {}) => {
    const { data } = await api.get('/contracts/targets', {
      params: companyId ? { company_id: companyId } : undefined,
    });
    return data;
  },
  list: async (params) => {
    const { data } = await api.get('/contracts', { params });
    return data;
  },
  create: async ({ payload, companyId }) => {
    const { data } = await api.post('/contracts', payload, {
      params: companyId ? { company_id: companyId } : undefined,
    });
    return data;
  },
  update: async ({ id, payload, companyId }) => {
    const { data } = await api.patch(`/contracts/${id}`, payload, {
      params: companyId ? { company_id: companyId } : undefined,
    });
    return data;
  },
  updateStatus: async ({ id, payload, companyId }) => {
    const { data } = await api.patch(`/contracts/${id}/status`, payload, {
      params: companyId ? { company_id: companyId } : undefined,
    });
    return data;
  },
  renew: async ({ id, payload, companyId }) => {
    const { data } = await api.post(`/contracts/${id}/renew`, payload, {
      params: companyId ? { company_id: companyId } : undefined,
    });
    return data;
  },
  terminate: async ({ id, payload, companyId }) => {
    const { data } = await api.post(`/contracts/${id}/terminate`, payload, {
      params: companyId ? { company_id: companyId } : undefined,
    });
    return data;
  },
  listHistory: async ({ id, companyId }) => {
    const { data } = await api.get(`/contracts/${id}/history`, {
      params: companyId ? { company_id: companyId } : undefined,
    });
    return data;
  },
  uploadDocument: async ({ id, formData, companyId }) => {
    const { data } = await api.post(`/contracts/${id}/documents`, formData, {
      params: companyId ? { company_id: companyId } : undefined,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },
};
