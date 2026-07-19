/**
 * Markdown 表格抽取 — ResultViewer 专用
 * 负责：把 |...| 形式的 Markdown 表格抽出为占位符，避免 HTML 转义破坏结构
 * Config: 无
 * （提取结果中表格渲染的前置处理）
 * Skill：正则、占位符模式
 */


export interface TableExtraction {
  text: string;
  tables: string[];  // Markdown 表格原文（多行 |...| 文本）
}

// 占位符使用 \u0000 控制字符前缀，与 formula.ts 的占位符不冲突（KBLOCK/KINLINE/TBL 互不重叠）
const TABLE_PH = (i: number) => `\u0000TBL_${i}\u0000`;

// 一行形如 |...|（首尾 | 必须都有，与 word_generator._TABLE_LINE 一致）
const TABLE_LINE = /^\s*\|.*\|\s*$/;
// 分隔行：|---|---| 或 |:---:|:---|（含 : 对齐标记）
const SEPARATOR = /^\s*\|?[\s:|-]+\|?\s*$/;

/**
 * 抽出连续的 Markdown 表格行，用占位符替换。
 * 判定：连续 ≥2 行匹配 TABLE_LINE，且第 2 行是分隔行（含 ---）。
 * 不满足条件的 |...| 文本原样保留，不被误判为表格。
 */
export function extractTables(content: string): TableExtraction {
  const tables: string[] = [];
  const lines = content.split('\n');
  const out: string[] = [];
  let i = 0;

  while (i < lines.length) {
    if (TABLE_LINE.test(lines[i])) {
      const start = i;
      while (i < lines.length && TABLE_LINE.test(lines[i])) {
        i++;
      }
      const block = lines.slice(start, i);
      // 第 2 行必须是分隔行才算表格（与 Markdown 标准一致）
      if (block.length >= 2 && SEPARATOR.test(block[1]) && block[1].includes('---')) {
        tables.push(block.join('\n'));
        out.push(TABLE_PH(tables.length - 1));
        continue;
      }
      // 不是表格，原样输出
      out.push(...block);
    } else {
      out.push(lines[i]);
      i++;
    }
  }

  return { text: out.join('\n'), tables };
}

/** 第 i 个表格的占位符 */
export function tablePlaceholder(i: number): string {
  return TABLE_PH(i);
}

function escapeCell(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function splitRow(line: string): string[] {
  // 去掉首尾 |，按 | 切分（与 word_generator._split_table_row 一致）
  let s = line.trim();
  if (s.startsWith('|')) s = s.slice(1);
  if (s.endsWith('|')) s = s.slice(0, -1);
  return s.split('|').map((c) => c.trim());
}

/**
 * Markdown 表格 → HTML <table>。
 * - 表头加粗（<th>）
 * - 列数按表头对齐：数据行不足补空 <td>，多余截断
 */
export function markdownTableToHtml(tableText: string): string {
  const lines = tableText.trim().split('\n');
  if (lines.length < 2) {
    // 退化保护：单行不构成表格，原样返回转义后的文本
    return escapeCell(tableText);
  }

  const header = splitRow(lines[0]);
  const cols = header.length;
  // 跳过第 2 行（分隔行），从第 3 行开始是数据
  const bodyRows = lines.slice(2).map(splitRow);

  const thHtml = header.map((c) => `<th>${escapeCell(c)}</th>`).join('');
  const trHtml = bodyRows
    .map((r) => {
      // 补齐列数到 cols，多余截断
      const cells = [...r, ...Array(Math.max(0, cols - r.length)).fill('')].slice(0, cols);
      return `<tr>${cells.map((c) => `<td>${escapeCell(c)}</td>`).join('')}</tr>`;
    })
    .join('');

  return `<table><thead><tr>${thHtml}</tr></thead><tbody>${trHtml}</tbody></table>`;
}
