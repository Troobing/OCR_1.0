/**
 * 纯文本转换 — 将 LLM 提取的混合文字+LaTeX 公式文本转为纯文本（公式转 Unicode）
 * 负责：把 $...$ / $$...$$ 公式渲染后取 textContent，方便复制粘贴到不支持 LaTeX 的环境
 * Config: 无
 * （复制全文按钮背后的文本处理逻辑）
 * Skill：KaTeX、DOMParser
 */


import katex from 'katex';
import { extractFormulas } from './formula';

/**
 * 把单个公式转成纯文本。用 MathML 输出取 textContent，避免 htmlAndMathml 模式下文本重复。
 */
function formulaToPlainText(formula: string, displayMode: boolean): string {
  // throwOnError:false 保证不抛异常；output:'mathml' 让 DOMParser 能稳定取到 textContent
  const html = katex.renderToString(formula, {
    displayMode,
    throwOnError: false,
    output: 'mathml',
  });
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return doc.body.textContent?.trim() || formula;
}

/**
 * 把完整内容（文字 + LaTeX 公式 + Markdown 表格）转成纯文本。
 * 公式转 Unicode 近似文本，表格保留 | 分隔形式，换行保留。
 */
export function contentToPlainText(content: string): string {
  if (!content) return '';

  const { text, blocks, inlines } = extractFormulas(content);

  // 占位符还原为公式纯文本
  let processed = text.replace(/\u0000KBLOCK_(\d+)\u0000/g, (_, i: string) =>
    formulaToPlainText(blocks[Number(i)] || '', true),
  );
  processed = processed.replace(/\u0000KINLINE_(\d+)\u0000/g, (_, i: string) =>
    formulaToPlainText(inlines[Number(i)] || '', false),
  );

  return processed;
}
