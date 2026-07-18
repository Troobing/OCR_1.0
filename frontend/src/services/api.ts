/**
 * API 通信层 — HTTP（开发模式）或 pywebview 桥接（exe 模式）
 * Config: baseURL、超时时间、请求/响应格式
 * （前端与后端网络请求）
 * Skill：Axios、FormData、pywebview JS Bridge
 */

import axios from 'axios';

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

// ─── 模式检测（运行时检查，pywebview 注入有延迟）───

function getBridge() { return (window as any).pywebview?.api; }
function isBridge() { return !!getBridge(); }

const http = axios.create({ baseURL: '/api', timeout: 120000 });

// ─── 工具 ───

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      // reader.result 是 "data:image/png;base64,xxxx"，只取 xxxx 部分
      const dataUrl = reader.result as string;
      resolve(dataUrl.split(',')[1]);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

// ─── API 方法 ───

export async function uploadImages(files: File[]): Promise<UploadResponse> {
  if (isBridge()) {
    const fileData = await Promise.all(
      Array.from(files).map(async (f) => ({
        name: f.name, size: f.size, type: f.type, data: await fileToBase64(f),
      }))
    );
    return { images: await getBridge().upload_images(fileData) };
  }

  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const res = await http.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function extractContent(
  imageIds: string[], config: ApiConfig
): Promise<ExtractResponse> {
  if (isBridge()) {
    return {
      results: await getBridge().extract_content(
        imageIds, config.api_key, config.base_url, config.model,
      ),
    };
  }

  const res = await http.post<ExtractResponse>('/extract', {
    image_ids: imageIds,
    api_key: config.api_key,
    base_url: config.base_url || undefined,
    model: config.model || undefined,
  });
  return res.data;
}

export async function saveConfigToDisk(config: ApiConfig): Promise<void> {
  if (isBridge()) {
    await getBridge().save_config(config.base_url, config.api_key, config.model);
    return;
  }
  await http.post('/config', config);
}

export async function loadConfigFromDisk(): Promise<ApiConfig> {
  if (isBridge()) return await getBridge().load_config();
  const res = await http.get('/config');
  return res.data;
}

export async function downloadWord(
  imageIds: string[], contents: string[], merge: boolean
): Promise<{ path: string; filename: string }> {
  if (isBridge()) return await getBridge().download_word(imageIds, contents, merge);
  const res = await http.post('/download', { image_ids: imageIds, contents, merge });
  return res.data;
}
