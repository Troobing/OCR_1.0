"""
Word 文档生成 — 将 AI 提取内容（文字 + $...$/$$...$$ 公式）渲染为 .docx
Config: 字体/字号/页边距、公式转换 XSLT、合并/分开下载逻辑

处理流水线：
  解析内容(分离文字/公式) → LaTeX → MathML → XSLT → OMML → python-docx 拼装 .docx
"""

import re
import io
import zipfile
from typing import Optional
from lxml import etree
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

# ─── MathML → OMML XSLT 转换表 ───

_MATHML_TO_OMML_XSLT = r'''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:math="http://www.w3.org/1998/Math/MathML"
  xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
  exclude-result-prefixes="math">

  <xsl:template match="text()"><xsl:value-of select="."/></xsl:template>
  <xsl:template match="math:math"><m:oMath><xsl:apply-templates/></m:oMath></xsl:template>

  <xsl:template match="math:mi">
    <m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t><xsl:apply-templates/></m:t></m:r>
  </xsl:template>
  <xsl:template match="math:mn">
    <m:r><m:t><xsl:apply-templates/></m:t></m:r>
  </xsl:template>
  <xsl:template match="math:mo">
    <m:r><m:t><xsl:apply-templates/></m:t></m:r>
  </xsl:template>
  <xsl:template match="math:mtext">
    <m:r><m:t><xsl:apply-templates/></m:t></m:r>
  </xsl:template>
  <xsl:template match="math:mrow"><xsl:apply-templates/></xsl:template>

  <xsl:template match="math:msup">
    <m:sSup>
      <m:e><xsl:apply-templates select="*[1]"/></m:e>
      <m:sup><xsl:apply-templates select="*[2]"/></m:sup>
    </m:sSup>
  </xsl:template>
  <xsl:template match="math:msub">
    <m:sSub>
      <m:e><xsl:apply-templates select="*[1]"/></m:e>
      <m:sub><xsl:apply-templates select="*[2]"/></m:sub>
    </m:sSub>
  </xsl:template>
  <xsl:template match="math:msubsup">
    <m:sSubSup>
      <m:e><xsl:apply-templates select="*[1]"/></m:e>
      <m:sub><xsl:apply-templates select="*[2]"/></m:sub>
      <m:sup><xsl:apply-templates select="*[3]"/></m:sup>
    </m:sSubSup>
  </xsl:template>

  <xsl:template match="math:mfrac">
    <m:f>
      <m:fPr/>
      <m:num><xsl:apply-templates select="*[1]"/></m:num>
      <m:den><xsl:apply-templates select="*[2]"/></m:den>
    </m:f>
  </xsl:template>

  <xsl:template match="math:msqrt">
    <m:rad><m:radPr/><m:e><xsl:apply-templates/></m:e></m:rad>
  </xsl:template>
  <xsl:template match="math:mroot">
    <m:rad>
      <m:radPr><m:degHide m:val="0"/></m:radPr>
      <m:deg><xsl:apply-templates select="*[2]"/></m:deg>
      <m:e><xsl:apply-templates select="*[1]"/></m:e>
    </m:rad>
  </xsl:template>

  <xsl:template match="math:mfenced">
    <m:d>
      <m:dPr>
        <m:begChr m:val="{@open}"/>
        <m:endChr m:val="{@close}"/>
      </m:dPr>
      <m:e><xsl:apply-templates/></m:e>
    </m:d>
  </xsl:template>

  <xsl:template match="math:mover">
    <m:acc>
      <m:accPr><m:chr m:val="{*[2]/text()}"/></m:accPr>
      <m:e><xsl:apply-templates select="*[1]"/></m:e>
    </m:acc>
  </xsl:template>

  <xsl:template match="math:*">
    <m:r><m:t><xsl:value-of select="."/></m:t></m:r>
  </xsl:template>

</xsl:stylesheet>
'''

# ─── XSLT 懒加载编译 ───

_xslt_transform: Optional[etree.XSLT] = None

def _get_xslt() -> etree.XSLT:
    global _xslt_transform
    if _xslt_transform is None:
        _xslt_transform = etree.XSLT(
            etree.fromstring(_MATHML_TO_OMML_XSLT.encode("utf-8"))
        )
    return _xslt_transform

# ─── 主入口 ───

def generate_word(
    contents: list[str],
    image_ids: list[str],
    merge: bool = True,
) -> tuple[bytes, str, str]:
    """生成 Word 文档。merge=True → 单个 .docx，merge=False → .zip 内含多个 .docx"""
    if merge:
        doc = Document()
        _setup_document_style(doc)
        for i, content in enumerate(contents):
            if i > 0:
                doc.add_page_break()
            _build_document_from_content(doc, content)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue(), "提取结果.docx", \
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for content, image_id in zip(contents, image_ids):
                doc = Document()
                _setup_document_style(doc)
                _build_document_from_content(doc, content)
                file_buffer = io.BytesIO()
                doc.save(file_buffer)
                file_buffer.seek(0)
                zf.writestr(f"{image_id}.docx", file_buffer.getvalue())
        zip_buffer.seek(0)
        return zip_buffer.getvalue(), "提取结果.zip", "application/zip"

# ─── 文档样式 ───

def _setup_document_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    font = style.font
    font.name = "宋体"
    font.size = Pt(12)

    # 设置中文字体槽
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        from lxml import etree
        rfonts = etree.SubElement(rpr, qn('w:rFonts'))
    rfonts.set(qn('w:eastAsia'), '宋体')

    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.18)
    section.right_margin = Cm(3.18)

# ─── 内容构建 ───

def _build_document_from_content(doc: Document, content: str) -> None:
    """解析 content，将文字+公式混合内容渲染到 doc 中"""
    segments = _parse_content(content)
    groups = _group_segments(segments)
    for group in groups:
        if len(group) == 1 and group[0]["type"] == "block_formula":
            omml = _latex_to_omml(group[0]["content"])
            if omml is not None:
                _add_omml_paragraph(doc, omml, alignment=WD_ALIGN_PARAGRAPH.CENTER)
            else:
                _add_fallback_formula(doc, group[0]["content"], block=True)
        else:
            _add_mixed_paragraph(doc, group)

def _group_segments(segments: list[dict]) -> list[list[dict]]:
    """将 text + inline_formula 归为一组，block_formula 单独成组"""
    groups: list[list[dict]] = []
    current: list[dict] = []
    for seg in segments:
        if seg["type"] == "block_formula":
            if current:
                groups.append(current)
                current = []
            groups.append([seg])
        else:
            current.append(seg)
    if current:
        groups.append(current)
    return groups

def _add_mixed_paragraph(doc: Document, group: list[dict]) -> None:
    """一行内的文字+行内公式放在同一个 Word 段落中，避免公式强制换行"""
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.line_spacing = 1.15
    for seg in group:
        if seg["type"] == "text":
            lines = seg["content"].split("\n")
            for i, line in enumerate(lines):
                if i > 0:
                    from docx.oxml import OxmlElement
                    br_run = OxmlElement("w:r")
                    br_run.append(OxmlElement("w:br"))
                    para._element.append(br_run)
                if line.strip():
                    para.add_run(line.strip())
        elif seg["type"] == "inline_formula":
            omml = _latex_to_omml(seg["content"])
            if omml is not None:
                try:
                    omml_elem = etree.fromstring(omml.encode("utf-8"))
                    from docx.oxml import OxmlElement
                    run_elem = OxmlElement("w:r")
                    run_elem.append(omml_elem)
                    para._element.append(run_elem)
                except Exception:
                    para.add_run(f"${seg['content']}$")
            else:
                fallback_run = para.add_run(f"${seg['content']}$")
                fallback_run.font.name = "Consolas"
                fallback_run.font.size = Pt(10.5)

# ─── 正则解析：拆分文字 & 公式 ───

def _parse_content(content: str) -> list[dict]:
    """用正则将混合文字和 $...$/$$...$$ 的内容拆成结构化片段"""
    segments: list[dict] = []
    pos = 0
    pattern = re.compile(r"(\$\$(.+?)\$\$|\$(.+?)\$)", re.DOTALL)
    for match in pattern.finditer(content):
        if match.start() > pos:
            text_before = content[pos:match.start()]
            if text_before.strip():
                segments.append({"type": "text", "content": text_before})
        if match.group(2) is not None:
            segments.append({"type": "block_formula", "content": match.group(2).strip()})
        else:
            segments.append({"type": "inline_formula", "content": match.group(3).strip()})
        pos = match.end()
    if pos < len(content):
        remaining = content[pos:]
        if remaining.strip():
            segments.append({"type": "text", "content": remaining})
    return segments

# ─── LaTeX → OMML 转换 ───

def _latex_to_omml(latex: str) -> Optional[str]:
    """LaTeX → MathML → OMML。失败返回 None，调用方降级为纯文本"""
    try:
        from latex2mathml import converter
        mathml_str = converter.convert(latex)
        mathml_elem = etree.fromstring(mathml_str.encode("utf-8"))
        transform = _get_xslt()
        return str(transform(mathml_elem))
    except Exception:
        return None

# ─── 辅助：向 Document 添加内容块 ───

def _add_text_paragraph(doc: Document, text: str) -> None:
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        para = doc.add_paragraph(line)
        para.paragraph_format.space_after = Pt(6)
        para.paragraph_format.line_spacing = 1.15

def _add_omml_paragraph(doc: Document, omml_xml: str, alignment: Optional[int] = None) -> None:
    para = doc.add_paragraph()
    if alignment is not None:
        para.alignment = alignment
    try:
        omml_elem = etree.fromstring(omml_xml.encode("utf-8"))
        from docx.oxml import OxmlElement
        run_elem = OxmlElement("w:r")
        run_elem.append(omml_elem)
        para._element.append(run_elem)
    except etree.XMLSyntaxError as e:
        para.add_run(f"[公式解析错误: {e}]")

def _add_fallback_formula(doc: Document, latex: str, block: bool = False) -> None:
    para = doc.add_paragraph()
    if block:
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(latex)
    run.font.name = "Consolas"
    run.font.size = Pt(10.5)
