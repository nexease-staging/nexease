import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateMigrationInput,
  MigrationBatch,
  MigrationData,
  MigrationJobData,
  MigrationListData,
  MigrationUploadData,
} from "@/features/migration/types";


export async function listMigrationBatches(
  limit = 100,
): Promise<MigrationListData> {
  const parameters =
    new URLSearchParams();

  parameters.set(
    "limit",
    String(limit),
  );

  const response =
    await apiRequest<MigrationListData>(
      `/migrations/?${parameters.toString()}`,
    );

  return response.data;
}


export async function getMigrationBatch(
  batchId: string,
): Promise<MigrationBatch> {
  const response =
    await apiRequest<MigrationData>(
      `/migrations/${batchId}/`,
    );

  return response.data.migration;
}


export async function createMigrationBatch(
  input: CreateMigrationInput,
): Promise<MigrationBatch> {
  const response =
    await apiRequest<MigrationData>(
      "/migrations/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.migration;
}


export async function uploadMigrationFile(
  batchId: string,
  file: File,
): Promise<MigrationUploadData> {
  const formData =
    new FormData();

  formData.append(
    "file",
    file,
  );

  const response =
    await apiRequest<MigrationUploadData>(
      `/migrations/${batchId}/upload/`,
      {
        method: "POST",
        body: formData,
      },
    );

  return response.data;
}


export async function validateMigration(
  batchId: string,
): Promise<MigrationJobData> {
  const response =
    await apiRequest<MigrationJobData>(
      `/migrations/${batchId}/validate/`,
      {
        method: "POST",
      },
    );

  return response.data;
}


export async function importMigration(
  batchId: string,
): Promise<MigrationJobData> {
  const response =
    await apiRequest<MigrationJobData>(
      `/migrations/${batchId}/import/`,
      {
        method: "POST",
      },
    );

  return response.data;
}