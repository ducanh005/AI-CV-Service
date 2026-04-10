import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { contractService } from '../services/contractService';

export function useContractTargets(params, enabled = true) {
  return useQuery({
    queryKey: ['contracts', 'targets', params],
    queryFn: () => contractService.listTargets(params),
    enabled,
  });
}

export function useContracts(params, enabled = true) {
  return useQuery({
    queryKey: ['contracts', params],
    queryFn: () => contractService.list(params),
    enabled,
  });
}

export function useContractHistory(id, params, enabled = true) {
  return useQuery({
    queryKey: ['contracts', 'history', id, params],
    queryFn: () => contractService.listHistory({ id, companyId: params?.companyId }),
    enabled: enabled && Boolean(id),
  });
}

export function useCreateContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: contractService.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contracts'] }),
  });
}

export function useUpdateContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: contractService.update,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contracts'] }),
  });
}

export function useUpdateContractStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: contractService.updateStatus,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contracts'] }),
  });
}

export function useRenewContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: contractService.renew,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contracts'] }),
  });
}

export function useTerminateContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: contractService.terminate,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contracts'] }),
  });
}

export function useUploadContractDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: contractService.uploadDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contracts'] }),
  });
}
