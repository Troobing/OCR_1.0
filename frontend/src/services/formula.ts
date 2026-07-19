/**
 * 公式两段式抽取 — ResultViewer 与 plainText 共用
 * 负责：把 $$...$$ 块级公式与 $...$ 行内公式抽出为占位符，避免 HTML 转义破坏 LaTeX
 * Config: 无
 * （提取结果渲染和纯文本转换的共用模块）
 * Skill：正则、占位符模式
 */


export interface FormulaExtraction {
  text: string;
  blocks: string[];   // $$...$$ 公式原文（已 trim）
  inlines: string[];  // $...$ 公式原文（已 trim）
}

// 占位符使用 \u0000 控制字符前缀，LLM 输出几乎不会出现，避免与内容冲突
const BLOCK_PH = (i: number) => `\u0000KBLOCK_${i}\u0000`;
const INLINE_PH = (i: number) => `\u0000KINLINE_${i}\u0000`;

const BLOCK_REGEX = /\$\$([\s\S]*?)\$\$/g;
const INLINE_REGEX = /\$([^$\n]+?)\$/g;

/**
 * 抽出 $$...$$ 与 $...$ 公式，用占位符替换，返回 { text, blocks, inlines }。
 * 顺序：先块级后行内（与原 ResultViewer/plainText 实现一致）。
 */
export function extractFormulas(content: string): FormulaExtraction {
  const blocks: string[] = [];
  const inlines: string[] = [];

  let text = content.replace(BLOCK_REGEX, (_, f: string) => {
    blocks.push(f.trim());
    return BLOCK_PH(blocks.length - 1);
  });

  text = text.replace(INLINE_REGEX, (_, f: string) => {
    inlines.push(f.trim());
    return INLINE_PH(inlines.length - 1);
  });

  return { text, blocks, inlines };
}

/** 第 i 个块级公式的占位符 */
export function blockPlaceholder(i: number): string {
  return BLOCK_PH(i);
}

/** 第 i 个行内公式的占位符 */
export function inlinePlaceholder(i: number): string {
  return INLINE_PH(i);
}
