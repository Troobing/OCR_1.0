/**
 * 结果渲染 — 将 LLM 提取的混合文字+LaTeX公式文本渲染为可视化内容
 * Config: KaTeX 渲染参数、公式/文字样式、正则匹配规则
（提取结果显示区，含公式渲染）
 */

import { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface Props {
  content: string;
}

function renderFormula(formula: string, displayMode: boolean): string {
  try {
    return katex.renderToString(formula, { displayMode, throwOnError: false });
  } catch {
    return `<code>${formula}</code>`;
  }
}

export default function ResultViewer({ content }: Props) {
  const html = useMemo(() => {
    if (!content) return '';

    const blockFormulas: string[] = [];
    let processed = content.replace(/\$\$([\s\S]*?)\$\$/g, (_, f: string) => {
      blockFormulas.push(f.trim());
      return `%%BLOCK_${blockFormulas.length - 1}%%`;
    });

    const inlineFormulas: string[] = [];
    processed = processed.replace(/\$([^$]+?)\$/g, (_, f: string) => {
      inlineFormulas.push(f.trim());
      return `%%INLINE_${inlineFormulas.length - 1}%%`;
    });

    let escaped = processed
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br/>');

    blockFormulas.forEach((f, i) => {
      escaped = escaped.replace(`%%BLOCK_${i}%%`, renderFormula(f, true));
    });
    inlineFormulas.forEach((f, i) => {
      escaped = escaped.replace(`%%INLINE_${i}%%`, renderFormula(f, false));
    });

    return escaped;
  }, [content]);

  return (
    <div
      className="result-viewer"
      dangerouslySetInnerHTML={{ __html: html }}
      style={{ fontSize: 15, lineHeight: 1.8, wordBreak: 'break-word', padding: '12px 0' }}
    />
  );
}
