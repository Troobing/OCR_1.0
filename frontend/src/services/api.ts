/**
 * API 通信层 — HTTP（开发模式）或 pywebview 桥接（exe 模式）
 * 负责：封装上传/提取/下载/删除的所有后台通信
 * Config: baseURL、超时时间
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

// ─── 模式检测 ───

function getBridge() { return (window as any).pywebview?.api; }
function isBridge() { return !!getBridge(); }

const http = axios.create({ baseURL: '/api', timeout: 120000 });

// ─── 工具 ───

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve((reader.result as string).split(',')[1]);
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

export async function deleteImage(imageId: string): Promise<void> {
  if (isBridge()) { await getBridge().delete_image(imageId); return; }
  await http.delete(`/images/${imageId}`);
}

export async function extractContent(imageIds: string[]): Promise<ExtractResponse> {
  if (isBridge()) return { results: await getBridge().extract_content(imageIds) };
  const res = await http.post<ExtractResponse>('/extract', { image_ids: imageIds });
  return res.data;
}

export async function downloadWord(
  imageIds: string[], contents: string[], merge: boolean
): Promise<{ path: string; filename: string }> {
  if (isBridge()) return await getBridge().download_word(imageIds, contents, merge);
  const res = await http.post('/download', { image_ids: imageIds, contents, merge });
  return res.data;
}
