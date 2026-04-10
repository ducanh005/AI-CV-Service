import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { interviewService } from "../services/interviewService";

export function useInterviews() {
  return useQuery({
    queryKey: ["interviews"],
    queryFn: interviewService.list,
  });
}

export function useCreateInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: interviewService.create,
    onSuccess: (data) => {
      queryClient.setQueryData(["interviews"], (oldData) => {
        if (!oldData) return [data];
        return [data, ...oldData];
      });
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
    },
  });
}
export function useSyncInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: interviewService.sync,
    onSuccess: (data) => {
      queryClient.setQueryData(["interviews"], (oldData) => {
        if (!oldData) return [data];
        return oldData.map((item) => (item.id === data.id ? data : item));
      });
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
    },
  });
}
export function useUpdateInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: interviewService.update,
    onSuccess: (data) => {
      queryClient.setQueryData(["interviews"], (oldData) => {
        if (!oldData) return [data];
        return oldData.map((item) => (item.id === data.id ? data : item));
      });
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
    },
  });
}

export function useDeleteInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: interviewService.remove,
    onSuccess: (_data, id) => {
      queryClient.setQueryData(["interviews"], (oldData) => {
        if (!oldData) return [];
        return oldData.filter((item) => item.id !== id);
      });
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
    },
  });
}