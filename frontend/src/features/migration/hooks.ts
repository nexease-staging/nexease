import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createMigrationBatch,
  getMigrationBatch,
  importMigration,
  listMigrationBatches,
  uploadMigrationFile,
  validateMigration,
} from "@/features/migration/api";

import {
  migrationQueryKeys,
} from "@/features/migration/query-keys";

import type {
  CreateMigrationInput,
} from "@/features/migration/types";


export function useMigrationList(
  limit = 100,
  enabled = true,
) {
  return useQuery({
    queryKey:
      migrationQueryKeys.list(
        limit,
      ),

    queryFn: () =>
      listMigrationBatches(
        limit,
      ),

    enabled,

    staleTime: 15_000,
  });
}


export function useMigration(
  batchId: string | null | undefined,
  enabled = true,
) {
  return useQuery({
    queryKey:
      migrationQueryKeys.detail(
        batchId ?? "",
      ),

    queryFn: () =>
      getMigrationBatch(
        batchId!,
      ),

    enabled:
      enabled
      &&
      Boolean(batchId),

    staleTime: 5_000,
  });
}


export function useCreateMigration() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateMigrationInput,
    ) =>
      createMigrationBatch(
        input,
      ),

    onSuccess: async (
      migration,
    ) => {
      queryClient.setQueryData(
        migrationQueryKeys.detail(
          migration.id,
        ),
        migration,
      );

      await queryClient.invalidateQueries({
        queryKey:
          migrationQueryKeys.lists(),
      });
    },
  });
}


export function useUploadMigrationFile() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      batchId,
      file,
    }: {
      batchId: string;
      file: File;
    }) =>
      uploadMigrationFile(
        batchId,
        file,
      ),

    onSuccess: async (
      data,
    ) => {
      queryClient.setQueryData(
        migrationQueryKeys.detail(
          data.migration.id,
        ),
        data.migration,
      );

      await queryClient.invalidateQueries({
        queryKey:
          migrationQueryKeys.lists(),
      });
    },
  });
}


export function useValidateMigration() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      batchId: string,
    ) =>
      validateMigration(
        batchId,
      ),

    onSuccess: async (
      data,
    ) => {
      queryClient.setQueryData(
        migrationQueryKeys.detail(
          data.migration.id,
        ),
        data.migration,
      );

      await queryClient.invalidateQueries({
        queryKey:
          migrationQueryKeys.lists(),
      });
    },
  });
}


export function useImportMigration() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      batchId: string,
    ) =>
      importMigration(
        batchId,
      ),

    onSuccess: async (
      data,
    ) => {
      queryClient.setQueryData(
        migrationQueryKeys.detail(
          data.migration.id,
        ),
        data.migration,
      );

      await queryClient.invalidateQueries({
        queryKey:
          migrationQueryKeys.lists(),
      });
    },
  });
}