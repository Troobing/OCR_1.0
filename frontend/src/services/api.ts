/**
 * API 通信层 — 所有前后端交互的 HTTP 请求封装
 * Config: baseURL、超时时间、请求/响应格式
 */

import axios from 'axios';

const http = axios.create({
  baseURL: '/api',
  timeout: 120000,
});

// ─── 类型定义 ───

export interface ImageInfo {
  id: string;
  filename: string;
  size: number;
  width: number;
  height: number;
}

interface UploadResponse {
  images: ImageInfo[];
}

export interface ExtractResult {
  image_id: string;
  filename: string;
  content: string;
  status: 'success' | 'error';
  error: string | null;
}

interface ExtractResponse {
  results: ExtractResult[];
}

export interface ApiConfig {
  base_url: string;
  api_key: string;
  model: string;
}

// ─── API 方法 ───

export async function uploadImages(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const res = await http.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function extractContent(
  imageIds: string[],
  config: ApiConfig
): Promise<ExtractResponse> {
  const res = await http.post<ExtractResponse>('/extract', {
    image_ids: imageIds,
    api_key: config.api_key,
    base_url: config.base_url || undefined,
    model: config.model || undefined,
  });
  return res.data;
}

export async function syncConfig(config: ApiConfig): Promise<void> {
  await http.post('/config', config);
}

export async function downloadWord(
  imageIds: string[],
  contents: string[],
  merge: boolean
): Promise<Blob> {
  const res = await http.post(
    '/download',
    { image_ids: imageIds, contents, merge },
    { responseType: 'blob' }
  );
  return res.data;
}
