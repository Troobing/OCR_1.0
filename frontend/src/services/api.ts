/**
 * API 通信层 — HTTP（开发模式）或 pywebview 桥接（exe 模式）
 * 负责：封装上传/提取/下载/配置/删除的所有后台通信
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

/**
 * API 配置。api_key 字段在前端可能为掩码或空（后端不向前端下发完整 key）。
 * has_key 用于 UI 提示"已配置/未配置"。
 */
export interface ApiConfig {
  base_url: string;
  api_key: string;
  model: string;
  has_key?: boolean;
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

/**
 * 等待 pywebview 桥接对象注入完成。轮询直到超时。
 */
export function waitForBridge(timeoutMs = 3000): Promise<boolean> {
  return new Promise((resolve) => {
    if (getBridge()) return resolve(true);
    const start = Date.now();
    const timer = setInterval(() => {
      if (getBridge()) {
        clearInterval(timer);
        resolve(true);
      } else if (Date.now() - start > timeoutMs) {
        clearInterval(timer);
        resolve(false);
      }
    }, 50);
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

export async function deleteImage(imageId: string): Promise<void> {
  if (isBridge()) {
    await getBridge().delete_image(imageId);
    return;
  }
  await http.delete(`/images/${imageId}`);
}

export async function extractContent(imageIds: string[]): Promise<ExtractResponse> {
  // API Key 由后端自管，前端不再传 config
  if (isBridge()) {
    return { results: await getBridge().extract_content(imageIds) };
  }

  const res = await http.post<ExtractResponse>('/extract', { image_ids: imageIds });
  return res.data;
}

export async function saveConfigToDisk(config: ApiConfig): Promise<void> {
  // 仅当 api_key 非空且不是掩码时才发送该字段；为空则让后端保留原值
  const apiKeyTrimmed = (config.api_key || '').trim();
  const isMask = /^\*{4}.+/.test(apiKeyTrimmed);  // 形如 ****1234
  const payload: Record<string, string> = {
    base_url: config.base_url,
    model: config.model,
  };
  if (apiKeyTrimmed && !isMask) {
    payload.api_key = apiKeyTrimmed;
  }

  if (isBridge()) {
    await getBridge().save_config(
      payload.base_url, payload.api_key ?? null, payload.model,
    );
    return;
  }
  await http.post('/config', payload);
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
