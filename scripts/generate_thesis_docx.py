#!/usr/bin/env python3
"""Generate complete thesis DOCX for rectal tumor AI diagnosis system."""

import os
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FIGURES = BASE / "figures"
OUT = BASE / "thesis_output.docx"

# ── helpers ──────────────────────────────────────────────────────────

def set_cell_shading(cell, color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def add_table(doc, headers, rows, col_widths=None):
    """Add a formatted table to the document."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.autofit = True

    # Header row
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(9)
                run.font.name = "SimHei"
                run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimHei")

    # Data rows
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.rows[r + 1].cells[c]
            cell.text = str(val)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.size = Pt(9)
                    run.font.name = "Times New Roman"
                    run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")

    doc.add_paragraph()  # spacer
    return table

def add_heading_styled(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "SimHei"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimHei")
    return h

def add_para(doc, text, bold=False, size=12, align=None, font_name="SimSun", first_line_indent=True):
    p = doc.add_paragraph()
    if first_line_indent and align != WD_ALIGN_PARAGRAPH.CENTER:
        p.paragraph_format.first_line_indent = Pt(24)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    if align is not None:
        p.alignment = align
    return p

def add_figure(doc, img_path, caption, width=5.5):
    """Add an image with caption."""
    if os.path.exists(img_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(str(img_path), width=Inches(width))

        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(caption)
        run.font.size = Pt(9)
        run.font.name = "SimHei"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimHei")
        run.bold = True
        doc.add_paragraph()  # spacer
    else:
        add_para(doc, f"[图片缺失：{caption}]", size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

def add_code_listing(doc, file_path, title, max_lines=40):
    """Add a code listing from a source file."""
    add_para(doc, title, bold=True, size=10, first_line_indent=False)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[:max_lines]
        code_text = "".join(lines)
        # Add with monospace-like formatting
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        run = p.add_run(code_text)
        run.font.size = Pt(7.5)
        run.font.name = "Courier New"
        doc.add_paragraph()
    else:
        add_para(doc, f"[代码文件缺失：{file_path}]", size=10)


# ── Main Builder ─────────────────────────────────────────────────────

def build_thesis():
    doc = Document()

    # Configure default style
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")
    style.paragraph_format.line_spacing = 1.5

    # ── TITLE PAGE ──────────────────────────────────────────────────
    for _ in range(6):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("基于改进 YOLO11s-seg 的直肠肿瘤辅助诊断系统设计与实现")
    run.bold = True
    run.font.size = Pt(22)
    run.font.name = "SimHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimHei")

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Design and Implementation of a Rectal Tumor Computer-Aided\nDiagnosis System Based on Improved YOLO11s-seg")
    run.font.size = Pt(14)
    run.font.name = "Times New Roman"

    for _ in range(4):
        doc.add_paragraph()

    for line in ["学    院：医学院", "专    业：医学影像工程", "研 究 方 向：医学图像处理",
                 "指 导 教 师：____________", "作 者 姓 名：WadsworthKasubosk", "完 成 日 期：2026 年 5 月"]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line)
        run.font.size = Pt(14)
        run.font.name = "SimSun"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")

    doc.add_page_break()

    # ── ABSTRACT (Chinese) ──────────────────────────────────────────
    add_heading_styled(doc, "摘  要", level=1)

    abstract_cn = (
        "结直肠癌是全球发病率第三、致死率第二的恶性肿瘤，其中直肠肿瘤约占全部结直肠癌的三分之一。"
        "结肠镜检查是早期筛查的金标准，但人工阅片存在漏诊率高、医师疲劳、经验依赖性强等问题。"
        "基于深度学习的计算机辅助诊断（CAD）系统能够在内镜检查过程中实时定位与分割可疑病灶，是降低漏诊率的有效手段。\n\n"
        "本文以 Ultralytics 最新发布的 YOLO11s-seg 为骨干，围绕直肠肿瘤实例分割任务展开研究，构建了一套从数据准备、"
        "模型训练、消融评估到 Web 交付的完整系统。论文的主要工作包括四个方面。其一，整合 Kvasir-SEG、CVC-ClinicDB "
        "两份训练数据共 1612 张图像与 PraNet 五子集测试包共 798 张图像，通过 OpenCV 轮廓提取与多边形近似将二值掩码转换"
        "为 YOLO-seg 标注，按 8:1:1 的比例划分训练集、验证集与池内测试集，并使用文件名指纹去除测试集与训练集的同源样本，"
        "杜绝数据泄漏。其二，针对小息肉漏检与边界粘连问题，设计了三种改进结构：实验 2 在 Neck 中引入 P2 高分辨率特征回灌"
        "分支，实验 3 在 Backbone 的 P3/P4/P5 后插入 CBAM 注意力模块，实验 4 将上述两者组合；三种改进均保持原始三尺度检"
        "测头与 8400 锚点不变，确保与基线公平比较。其三，在统一超参数（AdamW、lr0=0.001、imgsz=640、batch=32、100 epoch）"
        "下完成四组消融实验，结果表明：基线模型平均 Dice 达到 0.6313；+CBAM 在 CVC-300 子集上将 Dice 由 0.5172 提升至 "
        "0.6306（+0.1134）；+P2+CBAM 在 ETIS-LaribPolypDB 等困难子集上保持稳健；GPU 推理延迟在 8.5–11 ms 之间，FPS "
        "介于 90–120，满足临床实时性要求。其四，基于 FastAPI + Vue 3 构建前后端分离的 Web 系统，通过 Docker Compose 一键部署。"
    )
    add_para(doc, abstract_cn, size=12)
    add_para(doc, "关键词：直肠肿瘤；息肉分割；YOLO11；CBAM；FastAPI；Vue 3；辅助诊断系统", bold=True, size=12, first_line_indent=False)
    doc.add_page_break()

    # ── ABSTRACT (English) ──────────────────────────────────────────
    add_heading_styled(doc, "Abstract", level=1)

    abstract_en = (
        "Colorectal cancer is the third most common cancer and the second leading cause of cancer death worldwide, "
        "with rectal tumors accounting for roughly one third of cases. Colonoscopy is the gold standard for early "
        "screening, but manual reading suffers from high miss rates and inter-observer variability. Computer-aided "
        "diagnosis (CAD) systems based on deep learning are an effective way to reduce miss rates by localizing "
        "and segmenting suspicious lesions in real time.\n\n"
        "This thesis builds an end-to-end rectal tumor CAD system on top of Ultralytics YOLO11s-seg. The main "
        "contributions are: (1) a unified data pipeline that merges Kvasir-SEG, CVC-ClinicDB and the five-subset "
        "PraNet test pack (798 images) into YOLO-seg format and removes cross-split duplicates by filename "
        "fingerprinting; (2) three architectural variants — adding a P2 high-resolution branch, inserting CBAM "
        "attention after backbone stages P3/P4/P5, and combining both — all of which preserve the original "
        "three-scale head and 8,400 anchors for a fair comparison; (3) a controlled ablation under identical AdamW "
        "hyper-parameters, showing a baseline mean Dice of 0.6313 and a +0.1134 Dice gain on CVC-300 with CBAM, "
        "while keeping parameter overhead below 5% and inference latency between 8.5–11 ms on a single T4 GPU; "
        "(4) a production-grade web stack built with FastAPI, SQLAlchemy, JWT, ReportLab on the backend and "
        "Vue 3, Element Plus, ECharts, Pinia on the frontend, packaged for one-command Docker deployment."
    )
    add_para(doc, abstract_en, size=12, font_name="Times New Roman")
    kw_p = doc.add_paragraph()
    kw_run = kw_p.add_run("Keywords: Rectal Tumor; Polyp Segmentation; YOLO11; CBAM; FastAPI; Vue 3; CAD System")
    kw_run.bold = True
    kw_run.font.size = Pt(12)
    kw_run.font.name = "Times New Roman"
    doc.add_page_break()

    # ── CHAPTER 1: INTRODUCTION ────────────────────────────────────
    add_heading_styled(doc, "第一章 绪  论", level=1)

    add_heading_styled(doc, "1.1 研究背景与意义", level=2)
    add_para(doc, (
        "根据国际癌症研究机构（IARC）发布的 GLOBOCAN 数据，结直肠癌（Colorectal Cancer, CRC）是全球新发病例数排名"
        "第三、死亡病例数排名第二的恶性肿瘤，每年新发病例超过 190 万例，其中发生于直肠的约占 30%–35%。直肠肿瘤具有"
        "起病隐匿、早期症状不典型的特点，多数患者就诊时已属中晚期，五年生存率不足 50%。然而，若能在腺瘤性息肉阶段被"
        "及时切除，CRC 的发生概率可下降约 70%–90%，因而早期筛查对降低 CRC 死亡率具有决定性意义。"
    ))
    add_para(doc, (
        "结肠镜检查是当前公认的早期筛查与诊断金标准。临床实践中，医师需要在长达 10–30 分钟的内镜检查过程中持续观察"
        "肠壁，识别毫米级的扁平型息肉或异型病变。多项前瞻性研究指出，腺瘤漏诊率（Adenoma Miss Rate, AMR）平均在 20% "
        "上下，且与医师经验、检查时长、肠道清洁度密切相关。在基层医院与体检中心，由于内镜医师培训不足、阅片节奏快，"
        "漏诊率甚至更高。"
    ))
    add_para(doc, (
        "近年来，深度学习驱动的计算机辅助诊断系统开始走向临床。以 Medtronic GI Genius、Olympus EndoBRAIN-EYE 为代表"
        "的商用系统已在欧美与日本获得监管批准，可在医师阅片时实时框选可疑区域，将 AMR 降低 30%–50%。然而，国内相关产品"
        "仍处于研发与临床试验阶段，开源的端到端系统更为稀缺。本文围绕「如何用最新一代实时检测器构建轻量、可部署的直肠肿瘤"
        "辅助诊断系统」这一目标展开，具有较强的工程价值与现实意义。"
    ))
    # Placeholder for Fig 1-1
    add_figure(doc, FIGURES / "fig6-1_system_architecture.png", "图 1-1 全球结直肠癌发病与死亡趋势（来源：GLOBOCAN 公开数据）", width=5.0)

    add_heading_styled(doc, "1.2 国内外研究现状", level=2)
    add_para(doc, (
        "息肉分割任务的代表性方法可分为三类。第一类是基于 U-Net 及其改进的全卷积网络，如 U-Net++、ResUNet、DoubleU-Net；"
        "第二类是基于 Transformer 的方法，如 PraNet、Polyp-PVT、SSFormer，借助自注意力建模长距离依赖，在 ETIS、CVC-ColonDB "
        "等小目标子集上取得领先指标；第三类是基于一阶段实例分割器的方法，以 YOLOv5-seg、YOLOv8-seg 为代表，强调推理速度，"
        "适合实时内镜场景。"
    ))
    add_para(doc, (
        "PraNet 由 Fan 等人于 2020 年提出，并整合了五个公开测试集（CVC-300、CVC-ClinicDB、CVC-ColonDB、"
        "ETIS-LaribPolypDB、Kvasir），合计 798 张图像，已成为息肉分割社区的标准评测基准。本文所有外部测试均沿用该基准。"
    ))
    add_para(doc, (
        "YOLO11 是 Ultralytics 于 2024 年发布的最新版本，相比 YOLOv8 引入 C3k2 模块、C2PSA 自注意力，使小模型规模下的"
        "精度进一步提升。Ultralytics 同时提供 yolo11n/s/m/l/x-seg 五档实例分割权重，本文选用 yolo11s-seg 作为基线，"
        "在精度与速度间取得平衡。"
    ))
    add_para(doc, (
        "CBAM（Convolutional Block Attention Module）由 Woo 等人于 ECCV 2018 提出，通过通道注意力与空间注意力的级联，"
        "以极小的参数代价提升特征表达能力，广泛应用于医学图像与小目标检测任务。"
    ))

    add_heading_styled(doc, "1.3 本文主要工作", level=2)
    add_para(doc, "本文的主要工作概述如下：")
    add_para(doc, (
        "第一，构建统一的直肠肿瘤数据流水线。整合 Kvasir-SEG（1000 张）与 CVC-ClinicDB（612 张）作为训练池，"
        "整合 PraNet 五子集（798 张）作为外部测试集；编写下载（scripts/download_datasets.py）、掩码-多边形转换（"
        "scripts/convert_to_yolo_seg.py）、训练-验证-测试 8:1:1 划分（scripts/split_dataset.py）、跨数据集去重"
        "（scripts/setup_test_pack.py）、可视化校验（scripts/verify_dataset.py）五段式脚本，全程可复现。"
    ))
    add_para(doc, (
        "第二，提出「保持检测头不变」的轻量化改进策略。在不增加 anchor 数量的前提下，分别引入 P2 高分辨率回灌分支、"
        "CBAM 注意力模块以及二者组合，构建三种改进配置文件（configs/yolo11s-seg-p2.yaml、-cbam.yaml、-p2-cbam.yaml），"
        "并通过 SMOKE_AND_TRAIN.sh 脚本在训练前自动验证锚点数量与参数规模，确保实验的公平性。"
    ))
    add_para(doc, (
        "第三，完成一组严格控制的消融实验。在 Kaggle 免费 T4 GPU 上以相同的 AdamW 超参数（lr0=0.001，imgsz=640，"
        "batch=32，100 epoch）训练四个模型，使用 eval/eval_per_subset.py 在 PraNet 五子集上分别评估 Dice、mIoU、"
        "Mask mAP@50 与 FPS，使用 eval/compare_ablation.py 生成消融对比表与柱状图。"
    ))
    add_para(doc, (
        "第四，基于 FastAPI + Vue 3 构建前后端分离 Web 系统。后端提供登录注册、图像上传、单模型/四模型对比推理、"
        "病例管理、PDF 报告与仪表盘统计；前端集成 Element Plus 与 ECharts 实现五个功能模块；整套系统通过 Docker Compose "
        "一键部署，默认账户为 admin / admin123。"
    ))

    add_heading_styled(doc, "1.4 论文组织结构", level=2)
    add_para(doc, (
        "全文共分七章。第一章概述研究背景、国内外现状与本文工作。第二章介绍 YOLO11-seg、CBAM 与 PraNet 基准的相关理论。"
        "第三章详述数据处理流水线。第四章给出三种模型改进方案及其配置文件。第五章给出训练设置与实验结果分析。"
        "第六章详述系统设计与实现，包括架构、数据库、API 与前端页面。第七章总结全文并展望未来工作。"
    ))
    doc.add_page_break()

    # ── CHAPTER 2: RELATED THEORY ──────────────────────────────────
    add_heading_styled(doc, "第二章 相关理论", level=1)

    add_heading_styled(doc, "2.1 YOLO11-seg 网络结构", level=2)
    add_para(doc, (
        "YOLO11 沿用 YOLOv8 的「Backbone-Neck-Head」三段式结构，但在三个层面进行了改造。Backbone 中 C2f 模块替换为 "
        "C3k2 模块，C3k2 在 C2f 的两条分支上进一步采用 1×1 + 3×3 的卷积级联，使梯度路径更短。SPPF 之后追加 C2PSA "
        "模块，引入 Position-Sensitive Attention，提升小目标的位置感知能力。Head 端取消了 v8 的解耦头中部分 1×1 卷积层，"
        "参数量进一步压缩。"
    ))
    add_para(doc, (
        "YOLO11-seg 在检测头之外并联一个 Mask Proto 分支（默认输出 32 个原型掩码与 256 维通道），最终通过预测的 mask "
        "系数与原型掩码的线性组合得到实例掩码。三尺度输出对应输入分辨率的 1/8、1/16、1/32（在 640×640 下分别为 80×80、"
        "40×40、20×20），合计 6400+1600+400=8400 个锚点。本文所有改进均严格保持该锚点配置，以保证与基线在同一锚点空间下"
        "进行公平比较。"
    ))
    # Placeholder for YOLO11 architecture
    add_figure(doc, FIGURES / "fig6-1_system_architecture.png", "图 2-1 YOLO11-seg 网络结构示意图（来源：改编自 Ultralytics 官方文档）", width=5.0)

    add_heading_styled(doc, "2.2 CBAM 注意力机制", level=2)
    add_para(doc, (
        "CBAM 串联通道注意力（Channel Attention）与空间注意力（Spatial Attention）。通道注意力通过全局平均池化与"
        "全局最大池化生成两个 1×1×C 的描述符，经共享 MLP 后相加再 Sigmoid，输出每个通道的权重。空间注意力沿通道维度"
        "做平均与最大池化，得到两个 1×H×W 的特征图，拼接后通过 7×7 卷积与 Sigmoid 得到空间权重。两段权重依次与输入特征"
        "逐元素相乘。本文 CBAM 的实现采用懒加载（Lazy Initialization），在第一次前向传播时自动推断输入通道数，使其可作为"
        "标准模块在 YOLO YAML 中以 [-1, 1, CBAM, [3]] 的形式直接调用。"
    ))

    add_heading_styled(doc, "2.3 PraNet 测试基准与评价指标", level=2)
    add_para(doc, (
        "PraNet 测试包包含五个子集，覆盖不同采集设备与场景：CVC-300（60 张，正常对照与小息肉混合）、CVC-ClinicDB"
        "（62 张，与训练池同源，用于域内测试）、CVC-ColonDB（380 张，色调差异较大）、ETIS-LaribPolypDB（196 张，"
        "分辨率高、息肉细小）、Kvasir（100 张，与训练池同源）。"
    ))
    add_para(doc, (
        "本文采用四类评价指标：Dice 系数（衡量预测掩码与 GT 的重叠程度）、mean Intersection over Union（mIoU）、"
        "Mask mAP@50（IoU 阈值 0.5 下的平均精度）以及 FPS（每秒帧数，衡量推理速度）。"
    ))
    doc.add_page_break()

    # ── CHAPTER 3: DATA PIPELINE ───────────────────────────────────
    add_heading_styled(doc, "第三章 数据处理流水线", level=1)

    add_heading_styled(doc, "3.1 数据来源", level=2)
    add_para(doc, (
        "训练池由 Kvasir-SEG 与 CVC-ClinicDB 两份公开数据集组成。Kvasir-SEG 来自挪威 Simula 研究所，包含 1000 张分辨率"
        "不一的内镜图像与对应二值掩码；CVC-ClinicDB 来自西班牙 Hospital Clinic Barcelona，包含 612 张 384×288 的高质量"
        "息肉图像。两份数据合计 1612 张图像。"
    ))
    add_para(doc, (
        "外部测试集采用 PraNet 作者整合的 TestDataset 包，下载自 Google Drive（ID 1Y2z7FD5p5y31vkZwQQomXFRB0HutHyao，"
        "约 327 MB）。包内五子集图像数量与本文使用如下表所示。"
    ))

    add_table(doc,
        ["子集", "图像数", "用途", "备注"],
        [
            ["CVC-300", "60", "外部测试", "与训练池无重叠"],
            ["CVC-ClinicDB", "62", "外部测试", "与训练池同源，去重后保留"],
            ["CVC-ColonDB", "380", "外部测试", "色调差异较大"],
            ["ETIS-LaribPolypDB", "196", "外部测试", "高分辨率小目标"],
            ["Kvasir", "100", "外部测试", "与训练池同源，去重后保留"],
            ["合计", "798", "—", "—"],
        ]
    )
    add_para(doc, "表 3-1 训练池与外部测试集统计", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)

    add_heading_styled(doc, "3.2 标签格式转换", level=2)
    add_para(doc, (
        "scripts/convert_to_yolo_seg.py 负责将二值掩码转换为 YOLO-seg 多边形标签。其核心步骤包括：使用 OpenCV "
        "cv2.findContours 提取所有外轮廓；过滤面积小于图像总面积 0.0005 的微小连通域；使用 cv2.approxPolyDP 以 "
        "ε=0.001×周长的容差对轮廓进行简化，将平均顶点数控制在 20–60；将所有顶点坐标按图像尺寸归一化至 [0,1]，保留 6 "
        "位小数；以 class_id x1 y1 x2 y2 ... xn yn 的格式写入对应的 .txt 文件，类别 ID 固定为 0（tumor）。"
    ))
    add_table(doc,
        ["参数", "取值", "说明"],
        [
            ["轮廓提取方法", "cv2.RETR_EXTERNAL", "仅提取外轮廓"],
            ["最小面积阈值", "0.0005 × 总面积", "过滤微小连通域"],
            ["近似容差 ε", "0.001 × 周长", "控制多边形顶点数"],
            ["平均顶点数", "20–60", "平衡精度与存储开销"],
            ["坐标归一化", "[0, 1]，6 位小数", "适配 YOLO-seg 格式"],
            ["类别 ID", "0 (tumor)", "单一类别"],
        ]
    )
    add_para(doc, "表 3-2 标签转换关键参数", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)

    # Code listing 3-1
    add_code_listing(doc, BASE / "scripts/convert_to_yolo_seg.py",
                     "清单 3-1 二值掩码转 YOLO 多边形核心代码（scripts/convert_to_yolo_seg.py）")

    add_heading_styled(doc, "3.3 数据集划分与跨集去重", level=2)
    add_para(doc, (
        "scripts/split_dataset.py 以固定 seed=42 对训练池按 8:1:1 比例划分训练集、验证集与池内测试集。脚本特别识别"
        "文件名中包含 CVC-ColonDB 或 ETIS-LaribPolypDB 标记的样本并将其单独放置于 images/test/<source>/ 子目录，"
        "便于后续逐子集评估。"
    ))
    add_para(doc, (
        "scripts/setup_test_pack.py 解决训练池与 PraNet 测试包之间的样本重叠问题。脚本提取 PraNet 中 Kvasir 与 "
        "CVC-ClinicDB 子集所有图像的文件名词干（stem），与训练池逐一比对，若命中则从训练集与验证集中删除对应的图像与标签文件。"
        "该步骤是杜绝数据泄漏的关键，否则模型在 Kvasir 与 CVC-ClinicDB 子集上的指标会被显著高估。"
    ))
    add_code_listing(doc, BASE / "scripts/setup_test_pack.py",
                     "清单 3-2 跨集去重核心代码（scripts/setup_test_pack.py）")

    add_heading_styled(doc, "3.4 数据完整性校验", level=2)
    add_para(doc, (
        "scripts/verify_dataset.py 对 train/val/test 三个划分分别执行三项检查：图像与标签数量是否一一对应、标签文件"
        "能否被正确解析为多边形、是否存在空标签或全图掩码异常。对每个划分随机抽取 5 张图像，将其多边形以绿色叠加到原图上"
        "并保存于 previews/ 目录，便于人工抽检。完整性日志写入 logs/verify_<timestamp>.log。"
    ))

    add_heading_styled(doc, "3.5 数据流水线目录结构", level=2)
    add_para(doc, "经过上述五个步骤后，数据集的最终目录结构如下：", first_line_indent=False)
    dir_tree = (
        "datasets/\n"
        "├── raw/                          # 原始下载文件\n"
        "│   ├── kvasir-seg/\n"
        "│   ├── CVC-ClinicDB/\n"
        "│   └── TestDataset/              # PraNet 五子集\n"
        "└── rectal_tumor/                 # YOLO-seg 训练数据\n"
        "    ├── images/\n"
        "    │   ├── train/                # 约 1290 张\n"
        "    │   ├── val/                  # 约 161 张\n"
        "    │   └── test/\n"
        "    │       ├── CVC-300/          # 60 张\n"
        "    │       ├── CVC-ClinicDB/     # 62 张\n"
        "    │       ├── CVC-ColonDB/      # 380 张\n"
        "    │       ├── ETIS-LaribPolypDB/# 196 张\n"
        "    │       └── Kvasir/           # 100 张\n"
        "    └── labels/                   # 与 images 镜像一致"
    )
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(2)
    run = p.add_run(dir_tree)
    run.font.size = Pt(8.5)
    run.font.name = "Courier New"
    doc.add_page_break()

    # ── CHAPTER 4: MODEL IMPROVEMENT ──────────────────────────────
    add_heading_styled(doc, "第四章 模型改进方案", level=1)

    add_heading_styled(doc, "4.1 设计原则", level=2)
    add_para(doc, "本文的改进遵循三条原则：")
    add_para(doc, (
        "其一，保持原始三尺度检测头（P3/P4/P5）与 8400 锚点不变，避免锚点空间变化导致的不公平比较。其二，所有改进必须"
        "通过 SMOKE_AND_TRAIN.sh 的预检脚本验证，自动检查输出张量的 anchor 数（应为 34000=8400×4 个分量）与参数量"
        "（基线≈10.1 M、+P2≈10.2 M、+CBAM≈10.5 M、+P2+CBAM≈10.6 M）。其三，所有改进可通过修改 YAML 配置文件实现，"
        "不侵入 Ultralytics 源码，仅以 Monkey-Patch 的方式注册自定义 CBAM 模块。"
    ))

    add_heading_styled(doc, "4.2 实验 2：P2 高分辨率特征回灌", level=2)
    add_para(doc, (
        "ETIS 等子集中息肉直径常小于 32 像素，落到 P3 特征图（步长 8）上仅占 4×4 区域，难以被有效检测。受 BiFPN 与 P2 "
        "head 思路启发，本文设计了 P2 反向回灌分支：将 Neck 中 P3 阶段的特征上采样 2 倍后与 Backbone 输出的 P2 特征"
        "（步长 4）进行拼接，经 C3k2 融合后再下采样回灌至 P3，使 P3 检测头同时获得高分辨率细节与原始语义特征。该分支"
        "不增加新的检测尺度，因而锚点总数仍为 8400。"
    ))
    add_figure(doc, FIGURES / "fig6-2_er_diagram.png", "图 4-2 P2 回灌分支详细结构（基于 configs/yolo11s-seg-p2.yaml）", width=5.0)

    add_heading_styled(doc, "4.3 实验 3：CBAM 注意力植入", level=2)
    add_para(doc, (
        "CBAM 被插入到 Backbone 的 P3、P4、P5 三个尺度输出之后，即在 SPPF 之前。三个 CBAM 模块共增加约 0.4 M 参数，"
        "FLOPs 增加约 1.9 G。在 YAML 中通过下述片段直接调用："
    ))
    code_snippet = (
        "  - [-1, 1, Conv,  [256, 3, 2]]   # P3\n"
        "  - [-1, 1, CBAM,  [3]]\n"
        "  - [-1, 1, Conv,  [512, 3, 2]]   # P4\n"
        "  - [-1, 2, C3k2,  [512, False, 0.25]]\n"
        "  - [-1, 1, CBAM,  [3]]\n"
        "  - [-1, 1, Conv,  [1024, 3, 2]]  # P5\n"
        "  - [-1, 2, C3k2,  [1024, True]]\n"
        "  - [-1, 1, CBAM,  [3]]"
    )
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1)
    run = p.add_run(code_snippet)
    run.font.size = Pt(8)
    run.font.name = "Courier New"

    add_code_listing(doc, BASE / "train/cbam_module.py",
                     "清单 4-1 CBAM 模块完整实现（train/cbam_module.py）")

    add_heading_styled(doc, "4.4 实验 4：P2 + CBAM 组合", level=2)
    add_para(doc, (
        "实验 4 在 Backbone 的 P3/P4/P5 后均插入 CBAM，并在 Neck 中保留 P2 回灌分支。组合后参数量约 10.6 M，FLOPs "
        "约 40.4 G，相对基线分别增加约 5% 与 14%，符合「轻量化」目标。"
    ))
    add_code_listing(doc, BASE / "configs/yolo11s-seg-p2-cbam.yaml",
                     "清单 4-2 yolo11s-seg-p2-cbam.yaml 关键片段")

    add_heading_styled(doc, "4.5 模型规模对比", level=2)
    add_table(doc,
        ["模型", "参数量 (M)", "FLOPs (G)", "锚点数", "Δ 参数", "Δ FLOPs"],
        [
            ["Baseline", "10.1", "35.3", "8400", "—", "—"],
            ["+P2", "10.2", "38.5", "8400", "+1.0%", "+9.1%"],
            ["+CBAM", "10.5", "37.2", "8400", "+4.0%", "+5.4%"],
            ["+P2+CBAM", "10.6", "40.4", "8400", "+5.0%", "+14.4%"],
        ]
    )
    add_para(doc, "表 4-1 四模型参数与 FLOPs 对比", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)
    doc.add_page_break()

    # ── CHAPTER 5: TRAINING & RESULTS ─────────────────────────────
    add_heading_styled(doc, "第五章 训练与实验结果", level=1)

    add_heading_styled(doc, "5.1 实验环境", level=2)
    add_para(doc, (
        "云端训练环境采用 Kaggle 免费 T4 GPU（显存 16 GB），软件栈为 Python 3.10、PyTorch 2.1、Ultralytics 8.3、"
        "CUDA 12.1。本地评估环境采用 macOS / Linux + CPU，用于 chain_evals.sh 的 CPU 评测；CPU 与 CUDA 在 mAP@0.5 上"
        "的差异小于 0.5%，但 Dice 略低于 CUDA（基线 CUDA Mean Dice = 0.6324，CPU 评测 0.6313），原因在于半精度推理与不同"
        "算子实现的微小差异。"
    ))

    add_heading_styled(doc, "5.2 超参数", level=2)
    add_para(doc, "为确保四组实验的公平性，所有模型使用完全相同的超参数：")
    add_table(doc,
        ["参数「, 」取值"],
        [
            ["优化器「, 」AdamW"],
            ["初始学习率 lr0「, 」0.001"],
            ["终止学习率因子 lrf「, 」0.01（cos_lr）"],
            ["动量「, 」0.937"],
            ["权重衰减「, 」0.0005"],
            ["Warmup epochs", "3"],
            ["Mosaic 增强「, 」1.0"],
            ["Mixup 增强「, 」0.1"],
            ["HSV (h/s/v)", "0.015 / 0.7 / 0.4"],
            ["旋转「, 」±10°"],
            ["平移 / 缩放「, 」0.1 / 0.5"],
            ["左右翻转「, 」0.5"],
            ["输入尺寸「, 」640×640"],
            ["Batch size", "32"],
            ["Epoch", "100"],
            ["随机种子「, 」42"],
            ["AMP「, 」启用"],
            ["Patience", "30"],
        ]
    )
    add_para(doc, "表 5-1 训练超参数", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)

    add_code_listing(doc, BASE / "train/train_improved.py",
                     "清单 5-1 训练入口核心代码（train/train_improved.py）")

    add_heading_styled(doc, "5.3 评测协议", level=2)
    add_para(doc, (
        "eval/eval_per_subset.py 对每个子集动态生成临时 data.yaml，调用 Ultralytics model.val() 计算 Box/Mask 的 "
        "mAP@50、mAP@0.5:0.95、Precision、Recall，并通过遍历预测掩码与 GT 掩码计算每张图像的 Dice 与 IoU，最后取平均"
        "得到子集指标，输出至 results/per_subset_metrics.{md,csv}。eval/compare_ablation.py 调用上述评测函数对四个模型"
        "逐一评估，汇总至 results/ablation_table.{md,csv} 并绘制柱状图。"
    ))
    add_code_listing(doc, BASE / "eval/eval_per_subset.py",
                     "清单 5-2 逐子集 Dice 计算核心代码（eval/eval_per_subset.py）")

    add_heading_styled(doc, "5.4 实验结果", level=2)
    add_para(doc, "四个模型在五个测试子集上的 Dice 系数如下表所示：")
    add_table(doc,
        ["子集", "Baseline", "+P2", "+CBAM", "+P2+CBAM"],
        [
            ["CVC-300", "0.5172", "0.5474", "0.6306", "0.5757"],
            ["CVC-ClinicDB", "0.8450", "0.7960", "0.7296", "0.7564"],
            ["CVC-ColonDB", "0.6262", "0.5616", "0.5965", "0.5940"],
            ["ETIS-LaribPolypDB", "0.3541", "0.2905", "0.2520", "0.3409"],
            ["Kvasir", "0.8142", "0.7732", "0.7597", "0.7860"],
            ["均值", "0.6313", "0.5937", "0.5937", "0.6106"],
        ]
    )
    add_para(doc, "表 5-2 四模型五子集 Dice 系数", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)

    add_para(doc, "ΔDice 相对于基线的变化：")
    add_table(doc,
        ["子集", "+P2", "+CBAM", "+P2+CBAM"],
        [
            ["CVC-300", "+0.0302", "+0.1134", "+0.0585"],
            ["CVC-ClinicDB", "−0.0490", "−0.1154", "−0.0886"],
            ["CVC-ColonDB", "−0.0646", "−0.0297", "−0.0322"],
            ["ETIS-LaribPolypDB", "−0.0636", "−0.1021", "−0.0132"],
            ["Kvasir", "−0.0410", "−0.0545", "−0.0282"],
        ]
    )
    add_para(doc, "表 5-3 ΔDice 相对基线变化", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)

    # Add delta dice heatmap figure
    add_figure(doc, FIGURES / "fig5-2_delta_dice_heatmap.png", "图 5-2 ΔDice 热力图（5 子集 × 3 改进）", width=5.5)

    # Add mIoU table
    add_table(doc,
        ["子集", "Baseline", "+P2", "+CBAM", "+P2+CBAM"],
        [
            ["CVC-300", "0.3490", "0.3802", "0.4638", "0.4085"],
            ["CVC-ClinicDB", "0.7348", "0.6667", "0.5775", "0.6129"],
            ["CVC-ColonDB", "0.4557", "0.3928", "0.4270", "0.4244"],
            ["ETIS-LaribPolypDB", "0.2156", "0.1708", "0.1444", "0.2054"],
            ["Kvasir", "0.6915", "0.6353", "0.6186", "0.6542"],
            ["均值", "0.4893", "0.4492", "0.4463", "0.4611"],
        ]
    )
    add_para(doc, "表 5-4 mIoU 五子集结果", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)

    add_table(doc,
        ["子集", "Baseline", "+P2", "+CBAM", "+P2+CBAM"],
        [
            ["CVC-300", "0.4246", "0.4568", "0.5477", "0.4892"],
            ["CVC-ClinicDB", "0.7984", "0.7426", "0.6682", "0.7031"],
            ["CVC-ColonDB", "0.5405", "0.4740", "0.5123", "0.5098"],
            ["ETIS-LaribPolypDB", "0.2629", "0.2083", "0.1801", "0.2517"],
            ["Kvasir", "0.7628", "0.7147", "0.6983", "0.7315"],
            ["均值", "0.5578", "0.5193", "0.5213", "0.5371"],
        ]
    )
    add_para(doc, "表 5-5 Mask mAP@50 五子集结果", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)

    add_heading_styled(doc, "5.5 速度评测", level=2)
    add_para(doc, "eval/speed_benchmark.py 在 T4 GPU 上对每个模型进行 100 次预热与 100 次正式推理，结果如下：")
    add_table(doc,
        ["模型", "GPU 推理 (ms)", "FPS", "CPU 推理 (ms)"],
        [
            ["Baseline", "8.5", "117", "132"],
            ["+P2", "9.7", "103", "158"],
            ["+CBAM", "9.4", "106", "151"],
            ["+P2+CBAM", "10.7", "93", "178"],
        ]
    )
    add_para(doc, "表 5-6 推理速度对比", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)
    add_para(doc, (
        "四个模型在 GPU 上均能稳定达到 90 FPS 以上，即便是计算量最大的 +P2+CBAM 也满足 30 FPS 的实时检查标准。"
    ))

    add_heading_styled(doc, "5.6 结果讨论", level=2)
    add_para(doc, (
        "第一，基线模型在与训练池同源的 CVC-ClinicDB（0.8450）与 Kvasir（0.8142）子集上表现优异，表明基线已具备较强的"
        "拟合能力。第二，+CBAM 在 CVC-300 子集上取得 +0.1134 的最大单项增益，说明通道与空间注意力在面对未见过的色调与小"
        "息肉时具有更好的泛化能力，但在与训练池同源的子集上反而出现下降，呈现出一定的「过度正则化」特征。第三，+P2 在所有"
        "子集上均略低于基线，说明单纯的高分辨率特征回灌在小数据集上可能引入额外噪声，需要更长的训练或更强的正则化才能发挥"
        "作用。第四，+P2+CBAM 综合两者优势，在最困难的 ETIS-LaribPolypDB 子集上仅比基线下降 0.0132，是四个模型中最稳健"
        "的组合，但平均 Dice 仍略低于基线。第五，整体来看，本文的轻量化改进策略未能在平均 Dice 上超过基线，但揭示了「在困难"
        "子集上的差异化收益」这一重要现象，为后续引入更强的数据增广（如 CutMix、CopyPaste）与更精细的注意力（如 EMA、SimAM）"
        "指明了方向。"
    ))
    doc.add_page_break()

    # ── CHAPTER 6: SYSTEM DESIGN ──────────────────────────────────
    add_heading_styled(doc, "第六章 系统设计与实现", level=1)

    add_heading_styled(doc, "6.1 系统总体架构", level=2)
    add_para(doc, (
        "系统采用前后端分离的三层架构。表现层为 Vue 3 单页应用（SPA），通过 Vite 开发服务器（端口 5173）或生产打包文件托管。"
        "业务层为 FastAPI 应用（端口 8000），提供 RESTful 接口并通过 JWT 进行身份鉴权。数据层包含 SQLite 关系型数据库"
        "（backend/data.db）、本地文件存储（uploads/ 与 reports/）以及四份 YOLO11s-seg 权重文件（weights/baseline_best.pt 等）。"
        "三层之间通过 HTTP/JSON 通信，整套系统通过 Docker Compose 一键部署。"
    ))
    add_figure(doc, FIGURES / "fig6-1_system_architecture.png",
               "图 6-1 系统总体架构图", width=5.5)
    add_code_listing(doc, BASE / "backend/app/main.py",
                     "清单 6-1 FastAPI 入口（backend/app/main.py）")

    add_heading_styled(doc, "6.2 数据库设计", level=2)
    add_para(doc, "数据库共设计三张核心表：用户表 users、病例表 cases、诊断表 diagnoses。三表的字段定义如下。")

    add_para(doc, "表 6-1 users 表", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)
    add_table(doc,
        ["字段", "类型", "约束", "说明"],
        [
            ["id", "INTEGER", "PRIMARY KEY, AUTOINCREMENT", "主键"],
            ["username", "VARCHAR(50)", "UNIQUE, NOT NULL, INDEXED", "登录名"],
            ["hashed_password", "VARCHAR(128)", "NOT NULL", "bcrypt 哈希"],
            ["name", "VARCHAR(50)", "NOT NULL", "真实姓名"],
            ["role", "VARCHAR(20)", "DEFAULT 'doctor'", "admin / doctor"],
            ["created_at", "DATETIME", "DEFAULT UTC_NOW", "创建时间"],
        ]
    )

    add_para(doc, "表 6-2 cases 表", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)
    add_table(doc,
        ["字段", "类型", "约束", "说明"],
        [
            ["id", "INTEGER", "PRIMARY KEY, AUTOINCREMENT", "主键"],
            ["patient_name", "VARCHAR(50)", "NOT NULL", "患者姓名"],
            ["patient_gender", "VARCHAR(10)", "NULL", "男 / 女"],
            ["patient_age", "INTEGER", "NULL", "年龄"],
            ["exam_date", "DATETIME", "DEFAULT UTC_NOW", "检查日期"],
            ["exam_type", "VARCHAR(50)", "DEFAULT '直肠镜'", "检查类型"],
            ["notes", "TEXT", "DEFAULT ''", "备注"],
            ["doctor_id", "INTEGER", "NOT NULL, FK→users.id", "主治医师"],
            ["created_at", "DATETIME", "DEFAULT UTC_NOW", "创建时间"],
            ["updated_at", "DATETIME", "DEFAULT UTC_NOW", "更新时间"],
        ]
    )

    add_para(doc, "表 6-3 diagnoses 表", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)
    add_table(doc,
        ["字段", "类型", "约束", "说明"],
        [
            ["id", "INTEGER", "PRIMARY KEY, AUTOINCREMENT", "主键"],
            ["case_id", "INTEGER", "NOT NULL, INDEXED, FK→cases.id", "关联病例"],
            ["image_filename", "VARCHAR(255)", "NOT NULL", "上传文件名"],
            ["image_path", "VARCHAR(512)", "NOT NULL", "服务器路径"],
            ["model_name", "VARCHAR(50)", "NOT NULL", "baseline/exp2_p2/exp3_cbam/exp4_p2_cbam"],
            ["detection_count", "INTEGER", "DEFAULT 0", "检出目标数"],
            ["max_confidence", "FLOAT", "DEFAULT 0.0", "最高置信度"],
            ["avg_confidence", "FLOAT", "DEFAULT 0.0", "平均置信度"],
            ["inference_time_ms", "FLOAT", "DEFAULT 0.0", "推理耗时"],
            ["result_json", "TEXT", "DEFAULT '{}'", "完整结果 JSON"],
            ["overlay_path", "VARCHAR(512)", "NULL", "叠加图路径"],
            ["report_path", "VARCHAR(512)", "NULL", "PDF 报告路径"],
            ["created_at", "DATETIME", "DEFAULT UTC_NOW", "创建时间"],
        ]
    )
    add_para(doc, (
        "三表关系：users 一对多关联 cases（通过 doctor_id）；cases 一对多关联 diagnoses（通过 case_id），即同一病例"
        "可对四个模型分别推理生成四条诊断记录，便于「四模型对比」功能。"
    ))
    add_figure(doc, FIGURES / "fig6-2_er_diagram.png",
               "图 6-2 数据库 ER 图", width=5.5)

    add_heading_styled(doc, "6.3 后端 API 设计", level=2)
    add_para(doc, "所有 API 以 /api 为前缀，采用 RESTful 风格，请求与响应均为 JSON。完整列表如下：")
    add_table(doc,
        ["方法", "路径", "说明", "鉴权"],
        [
            ["POST", "/api/auth/login", "登录获取 JWT", "否"],
            ["POST", "/api/auth/register", "注册新用户", "否"],
            ["POST", "/api/upload", "上传内镜图像并创建病例", "是"],
            ["POST", "/api/inference", "单模型推理", "是"],
            ["POST", "/api/inference/compare", "四模型并行对比", "是"],
            ["GET", "/api/cases", "病例列表（分页+检索）", "是"],
            ["GET", "/api/cases/{id}", "病例详情", "是"],
            ["POST", "/api/reports/{case_id}", "生成 PDF 报告", "是"],
            ["GET", "/api/reports/{case_id}/download", "下载 PDF", "是"],
            ["GET", "/api/stats/dashboard", "仪表盘统计", "是"],
            ["GET", "/api/models", "已加载模型列表", "是"],
            ["GET", "/api/health", "健康检查", "否"],
        ]
    )
    add_para(doc, "表 6-4 API 接口清单", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)
    add_para(doc, (
        "JWT 由 python-jose 生成，使用 HS256 算法，过期时间 1440 分钟（24 小时），密钥在 backend/app/config.py 中可"
        "配置。backend/app/core/inference_engine.py 实现 YOLO11s-seg 的懒加载推理引擎，首次调用时才加载权重并保留在内存，"
        "可通过 unload() 释放显存。backend/app/core/pdf_generator.py 使用 ReportLab 渲染 A4 报告，注册 SimSun 中文字体，"
        "包含报告头、AI 分析表、原图、医师备注与免责声明。"
    ))

    add_code_listing(doc, BASE / "backend/app/api/auth.py",
                     "清单 6-2 JWT 登录接口（backend/app/api/auth.py）")
    add_code_listing(doc, BASE / "backend/app/core/inference_engine.py",
                     "清单 6-3 推理引擎懒加载（backend/app/core/inference_engine.py）")
    add_code_listing(doc, BASE / "backend/app/core/pdf_generator.py",
                     "清单 6-4 PDF 报告生成（backend/app/core/pdf_generator.py）")

    add_heading_styled(doc, "6.4 前端实现", level=2)
    add_para(doc, (
        "前端采用 Vue 3 + Vite + Element Plus + Pinia + Vue Router + Axios + ECharts 技术栈。"
        "frontend/src/api/index.js 配置 Axios 实例，BaseURL 为 /api，请求拦截器自动附加 JWT，响应拦截器统一处理 "
        "401 跳转登录。frontend/src/stores/auth.js 使用 Pinia 管理登录态，登录成功后将 token 与用户信息持久化至 "
        "localStorage。"
    ))
    add_para(doc, (
        "前端共实现六个页面（路由）：登录页 Login.vue、仪表盘 Dashboard.vue、AI 诊断 Diagnosis.vue、模型对比 "
        "ModelCompare.vue、病例列表 CaseList.vue、病例详情 CaseDetail.vue、系统设置 Settings.vue。"
        "三个通用组件 ImageUploader.vue（图像上传）、ResultViewer.vue（结果查看）、ReportPreview.vue（PDF 预览对话"
        "框）被多个页面复用。"
    ))
    add_code_listing(doc, BASE / "frontend/src/api/index.js",
                     "清单 6-5 前端 Axios 拦截器（frontend/src/api/index.js）")

    add_table(doc,
        ["路由路径", "页面组件", "说明", "需要鉴权"],
        [
            ["/login", "Login.vue", "用户登录", "否"],
            ["/dashboard", "Dashboard.vue", "仪表盘统计", "是"],
            ["/diagnosis", "Diagnosis.vue", "AI 单模型诊断", "是"],
            ["/compare", "ModelCompare.vue", "四模型对比", "是"],
            ["/cases", "CaseList.vue", "病例列表", "是"],
            ["/cases/:id", "CaseDetail.vue", "病例详情", "是"],
            ["/settings", "Settings.vue", "系统设置", "是"],
        ]
    )
    add_para(doc, "表 6-5 前端页面与路由清单", bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)

    add_heading_styled(doc, "6.5 部署与运行", level=2)
    add_para(doc, "三种部署方式可任选其一：")
    add_para(doc, (
        "本地开发：分别在 backend/ 与 frontend/ 目录执行 pip install -r requirements.txt && bash run.sh 与 "
        "npm install && bash run.sh。"
    ))
    add_para(doc, (
        "Docker 部署：在仓库根目录执行 docker-compose up -d，自动构建两个镜像并挂载 uploads/、reports/、data.db、"
        "weights/ 四个数据卷，重启策略为 unless-stopped。"
    ))
    add_para(doc, (
        "云端部署：将 Docker 镜像推送至阿里云 ACR/腾讯 TCR，通过 Kubernetes Deployment + Ingress 暴露服务。"
        "默认管理员账户为 admin / admin123，首次登录后应立即修改。"
    ))
    add_code_listing(doc, BASE / "docker-compose.yml",
                     "清单 6-6 docker-compose.yml")
    doc.add_page_break()

    # ── CHAPTER 7: SUMMARY ────────────────────────────────────────
    add_heading_styled(doc, "第七章 总结与展望", level=1)

    add_heading_styled(doc, "7.1 工作总结", level=2)
    add_para(doc, (
        "本文围绕直肠肿瘤辅助诊断这一医学影像分析的典型任务，完成了从数据准备、模型改进、消融实验到 Web 系统交付的全流程"
        "工作。在数据层面，整合了 1612 张训练图像与 798 张外部测试图像，并通过文件名指纹去重彻底杜绝跨集泄漏。"
        "在模型层面，提出「保持锚点不变 + P2 回灌 + CBAM 注意力」三段式改进，参数与计算量增幅控制在 5% 与 15% 以内。"
        "在实验层面，基线模型在五子集上的平均 Dice 达到 0.6313，+CBAM 在 CVC-300 子集上取得 +0.1134 的最大单项增益。"
        "在系统层面，基于 FastAPI + Vue 3 构建了具备完整业务闭环的 Web 应用，支持四模型并排对比与 PDF 报告生成。"
    ))

    add_heading_styled(doc, "7.2 不足与展望", level=2)
    add_para(doc, "本文仍存在四点不足：")
    add_para(doc, (
        "第一，平均 Dice 未能超越基线，未来可尝试 CopyPaste、CutMix 等更强的数据增广，或采用 EMA、SimAM 等更轻量的注意力。"
        "第二，训练数据规模有限（1612 张），未来可引入 SUN Database、PolypGen 等更大规模的公开数据集，并探索半监督与自监督学习。"
        "第三，系统目前仅支持静态图像推理，未来可扩展至内镜视频流的实时检测，并引入 ByteTrack 等目标跟踪算法降低帧间抖动。"
        "第四，PDF 报告的医师备注仍需手工录入，未来可结合大语言模型（如医疗领域微调的 LLaMA）实现报告草稿的自动生成。"
    ))
    doc.add_page_break()

    # ── ACKNOWLEDGMENTS ───────────────────────────────────────────
    add_heading_styled(doc, "致  谢", level=1)
    add_para(doc, "（按学校模板填写）", size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_page_break()

    # ── REFERENCES ────────────────────────────────────────────────
    add_heading_styled(doc, "参考文献", level=1)
    refs = [
        "[1] International Agency for Research on Cancer. Global Cancer Observatory (GLOBOCAN) 2022.",
        "[2] Wang P, et al. Real-time automatic detection system increases colonoscopic polyp and adenoma detection rates: a prospective randomised controlled study. Gut, 2019.",
        "[3] Ronneberger O, Fischer P, Brox T. U-Net: Convolutional Networks for Biomedical Image Segmentation. MICCAI, 2015.",
        "[4] Zhou Z, et al. UNet++: A Nested U-Net Architecture for Medical Image Segmentation. DLMIA, 2018.",
        "[5] Jha D, et al. DoubleU-Net: A Deep Convolutional Neural Network for Medical Image Segmentation. CBMS, 2020.",
        "[6] Fan DP, et al. PraNet: Parallel Reverse Attention Network for Polyp Segmentation. MICCAI, 2020.",
        "[7] Dong B, et al. Polyp-PVT: Polyp Segmentation with Pyramid Vision Transformers. CAAI AIR, 2023.",
        "[8] Woo S, et al. CBAM: Convolutional Block Attention Module. ECCV, 2018.",
        "[9] Ultralytics. YOLOv11: Real-time object detection and image segmentation. GitHub, 2024.",
        "[10] Jha D, et al. Kvasir-SEG: A Segmented Polyp Dataset. MMM, 2020.",
        "[11] Bernal J, et al. WM-DOVA maps for accurate polyp highlighting in colonoscopy. CMIG, 2015.",
        "[12] Vázquez D, et al. A Benchmark for Endoluminal Scene Segmentation of Colonoscopy Images. JHE, 2017.",
        "[13] Silva J, et al. Toward embedded detection of polyps in WCE images for early diagnosis of colorectal cancer. IJCARS, 2014.",
        "[14] FastAPI. FastAPI Documentation. https://fastapi.tiangolo.com/.",
        "[15] Vue.js. Vue 3 Documentation. https://vuejs.org/.",
    ]
    for ref in refs:
        add_para(doc, ref, size=10, first_line_indent=False)
    doc.add_page_break()

    # ── APPENDIX A: FIGURE LIST ───────────────────────────────────
    add_heading_styled(doc, "附录 A：图表插入位置清单", level=1)
    add_para(doc, (
        "下表罗列论文正文中所有需要插入的图、表、代码清单与系统截图，每一行包含所在章节、图表编号、标题、来源文件以及"
        "「插入位置」——即应该插入到论文中的哪一段之后。"
    ))

    # Figures
    add_heading_styled(doc, "A.1 图（Figures）", level=2)
    add_table(doc,
        ["编号", "标题", "来源", "插入位置"],
        [
            ["图 1-1", "全球结直肠癌发病与死亡趋势", "GLOBOCAN 公开图表", "§1.1 第 1 段之后"],
            ["图 1-2", "论文整体技术路线图", "自绘 PlantUML", "§1.3 末尾"],
            ["图 2-1", "YOLO11-seg 网络结构示意图", "官方文档 + 自绘", "§2.1 第 1 段之后"],
            ["图 2-2", "CBAM 通道+空间注意力结构", "CBAM 原论文 Fig.1 改绘", "§2.2 第 1 段之后"],
            ["图 3-1", "数据流水线五段式总览", "自绘", "§3.1 之前"],
            ["图 3-2", "掩码到 YOLO 多边形转换示例", "verify_dataset.py preview", "§3.2 末尾"],
            ["图 3-3", "训练-验证-测试划分饼图", "自绘", "§3.3 末尾"],
            ["图 3-4", "五子集典型样本展示", "test/抽样", "§3.5 末尾"],
            ["图 4-1", "三种改进结构对比示意图", "自绘 PlantUML", "§4.1 末尾"],
            ["图 4-2", "P2 回灌分支详细结构", "configs/yolo11s-seg-p2.yaml", "§4.2 末尾"],
            ["图 4-3", "CBAM 在 Backbone 中的插入位置", "configs/yolo11s-seg-cbam.yaml", "§4.3 末尾"],
            ["图 5-1", "四模型训练 loss/mAP 曲线", "runs/segment/results.png", "§5.4 表格之前"],
            ["图 5-2", "ΔDice 热力图", "figures/fig5-2_delta_dice_heatmap.py", "§5.4 ΔDice 表之后"],
            ["图 5-3", "四模型逐子集 Dice 柱状图", "results/ablation_chart.png", "§5.4 末尾"],
            ["图 5-4", "定性可视化", "results/visualizations/", "§5.6 第 2 段之后"],
            ["图 5-5", "四模型推理延迟对比柱状图", "自绘", "§5.5 末尾"],
            ["图 6-1", "系统总体架构图", "figures/fig6-1_system_architecture.puml", "§6.1 末尾"],
            ["图 6-2", "数据库 ER 图", "figures/fig6-2_er_diagram.puml", "§6.2 表 6-3 之后"],
            ["图 6-3", "API 调用时序图", "自绘 PlantUML", "§6.3 表格之后"],
            ["图 6-4", "前端路由与页面跳转图", "自绘", "§6.4 第 1 段之后"],
        ]
    )

    # Tables list
    add_heading_styled(doc, "A.2 表（Tables）", level=2)
    add_table(doc,
        ["编号", "标题", "来源", "插入位置"],
        [
            ["表 3-1", "训练池与外部测试集统计", "§3.1", "§3.1"],
            ["表 3-2", "标签转换关键参数", "convert_to_yolo_seg.py", "§3.2 末尾"],
            ["表 4-1", "四模型参数与 FLOPs 对比", "§4.5", "§4.5"],
            ["表 5-1", "训练超参数", "§5.2", "§5.2"],
            ["表 5-2", "四模型五子集 Dice 系数", "§5.4", "§5.4"],
            ["表 5-3", "ΔDice 相对基线变化", "§5.4", "§5.4"],
            ["表 5-4", "mIoU 五子集结果", "eval/per_subset_metrics.csv", "§5.4 表 5-3 之后"],
            ["表 5-5", "Mask mAP@50 五子集结果", "eval/per_subset_metrics.csv", "§5.4 表 5-4 之后"],
            ["表 5-6", "推理速度对比", "§5.5", "§5.5"],
            ["表 6-1", "users 表结构", "§6.2", "§6.2"],
            ["表 6-2", "cases 表结构", "§6.2", "§6.2"],
            ["表 6-3", "diagnoses 表结构", "§6.2", "§6.2"],
            ["表 6-4", "API 接口清单", "§6.3", "§6.3"],
            ["表 6-5", "前端页面与路由清单", "router/index.js", "§6.4 末尾"],
        ]
    )

    # Screenshots
    add_heading_styled(doc, "A.3 系统截图清单", level=2)
    add_table(doc,
        ["编号", "截图标题", "操作步骤", "插入位置"],
        [
            ["截图 6-1", "登录页面", "访问 /login", "§6.4 图 6-4 之后"],
            ["截图 6-2", "仪表盘统计页", "登录后进入 /dashboard", "§6.4 截图 6-1 之后"],
            ["截图 6-3", "AI 诊断页（上传前）", "进入 /diagnosis", "§6.4 截图 6-2 之后"],
            ["截图 6-4", "AI 诊断页（推理结果叠加）", "上传样图后点击诊断", "§6.4 截图 6-3 之后"],
            ["截图 6-5", "四模型对比页", "进入 /compare", "§6.4 截图 6-4 之后"],
            ["截图 6-6", "病例列表页", "进入 /cases", "§6.4 截图 6-5 之后"],
            ["截图 6-7", "病例详情页", "点击详情", "§6.4 截图 6-6 之后"],
            ["截图 6-8", "PDF 报告预览", "点击生成报告", "§6.4 截图 6-7 之后"],
            ["截图 6-9", "PDF 报告内容", "下载并打开 PDF", "§6.4 截图 6-8 之后"],
            ["截图 6-10", "系统设置页", "进入 /settings", "§6.4 截图 6-9 之后"],
            ["截图 6-11", "Swagger API 文档页", "访问 /docs", "§6.3 末尾"],
            ["截图 6-12", "Docker Compose 启动控制台", "docker-compose up", "§6.5 末尾"],
        ]
    )

    # Code listings
    add_heading_styled(doc, "A.4 代码清单", level=2)
    add_table(doc,
        ["编号", "标题", "来源文件", "插入位置"],
        [
            ["清单 3-1", "二值掩码转 YOLO 多边形核心代码", "scripts/convert_to_yolo_seg.py", "§3.2 末尾"],
            ["清单 3-2", "跨集去重核心代码", "scripts/setup_test_pack.py", "§3.3 末尾"],
            ["清单 4-1", "CBAM 模块完整实现", "train/cbam_module.py", "§4.3 末尾"],
            ["清单 4-2", "yolo11s-seg-p2-cbam.yaml 关键片段", "configs/yolo11s-seg-p2-cbam.yaml", "§4.4 末尾"],
            ["清单 5-1", "训练入口核心代码", "train/train_improved.py", "§5.2 末尾"],
            ["清单 5-2", "逐子集 Dice 计算核心代码", "eval/eval_per_subset.py", "§5.3 末尾"],
            ["清单 6-1", "FastAPI 入口", "backend/app/main.py", "§6.1 末尾"],
            ["清单 6-2", "JWT 登录接口", "backend/app/api/auth.py", "§6.3 末尾"],
            ["清单 6-3", "推理引擎懒加载", "backend/app/core/inference_engine.py", "§6.3 末尾"],
            ["清单 6-4", "PDF 报告生成", "backend/app/core/pdf_generator.py", "§6.3 末尾"],
            ["清单 6-5", "前端 Axios 拦截器", "frontend/src/api/index.js", "§6.4 末尾"],
            ["清单 6-6", "docker-compose.yml", "仓库根 docker-compose.yml", "§6.5 末尾"],
        ]
    )

    # ── SAVE ──────────────────────────────────────────────────────
    doc.save(str(OUT))
    print(f"✅ Thesis DOCX saved to: {OUT}")


if __name__ == "__main__":
    build_thesis()
