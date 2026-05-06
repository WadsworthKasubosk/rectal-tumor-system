#!/usr/bin/env python3
"""Build complete thesis DOCX from thesis_content.json + figures."""

import json, os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

BASE = Path(__file__).resolve().parent.parent
FIGURES = BASE / "figures"
JSON_PATH = Path(__file__).with_name("thesis_content.json")
OUT = BASE / "thesis_output.docx"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    T = json.load(f)

# ---- helpers ----

def _set_font(run, name_en, name_cn, size):
    run.font.size = Pt(size)
    run.font.name = name_en
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name_cn)

def add_h(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        _set_font(r, "SimHei", "SimHei", 18 if level == 1 else 14)

def add_p(doc, text, bold=False, size=12, align=None, indent=True):
    p = doc.add_paragraph()
    if indent and align != WD_ALIGN_PARAGRAPH.CENTER:
        p.paragraph_format.first_line_indent = Pt(24)
    run = p.add_run(text)
    run.bold = bold
    _set_font(run, "SimSun", "SimSun", size)
    if align is not None:
        p.alignment = align
    return p

def add_table(doc, headers, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.autofit = True
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.bold = True
                _set_font(run, "SimHei", "SimHei", 9)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri + 1].cells[ci]
            cell.text = str(val)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    _set_font(run, "Times New Roman", "SimSun", 9)
    doc.add_paragraph()

def add_tbl_caption(doc, text):
    add_p(doc, text, bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)

def add_img(doc, path, caption, w=5.5):
    if os.path.exists(path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Inches(w))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run(caption)
        r.bold = True
        _set_font(r, "SimHei", "SimHei", 9)
        doc.add_paragraph()
    else:
        add_p(doc, "[Image missing: " + caption + "]", size=10, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)

def add_code(doc, file_path, title, max_lines=35):
    add_p(doc, title, bold=True, size=10, indent=False)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[:max_lines]
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        run = p.add_run("".join(lines))
        run.font.size = Pt(7.5)
        run.font.name = "Courier New"
        doc.add_paragraph()
    else:
        add_p(doc, "[Code file missing: " + str(file_path) + "]", size=10, indent=False)

def make_cols(vals):
    return [[str(v)] for v in vals]

def make_kv(keys, vals):
    return [[k, v] for k, v in zip(keys, vals)]

def page_break(doc):
    doc.add_page_break()

# ---- BUILD ----

def build():
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")
    style.paragraph_format.line_spacing = 1.5

    # TITLE PAGE
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(T["title_cn"])
    r.bold = True
    _set_font(r, "SimHei", "SimHei", 22)
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(T["title_en"])
    _set_font(r, "Times New Roman", "SimSun", 14)
    for _ in range(4):
        doc.add_paragraph()
    info_lines = [
        "学    院：医学院", "专    业：医学影像工程",
        "研 究 方 向：医学图像处理", "指 导 教 师：____________",
        "作 者 姓 名：WadsworthKasubosk", "完 成 日 期：2026 年 5 月"
    ]
    for line in info_lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line)
        _set_font(r, "SimSun", "SimSun", 14)
    page_break(doc)

    # ABSTRACT CN
    add_h(doc, u"摘  要", 1)
    add_p(doc, T["abstract_cn"])
    add_p(doc, T["keywords_cn"], bold=True, indent=False)
    page_break(doc)

    # ABSTRACT EN
    add_h(doc, "Abstract", 1)
    add_p(doc, T["abstract_en"])
    kw_p = doc.add_paragraph()
    kw_r = kw_p.add_run(T["keywords_en"])
    kw_r.bold = True
    _set_font(kw_r, "Times New Roman", "SimSun", 12)
    page_break(doc)

    # CH1
    add_h(doc, u"第一章 绪  论", 1)
    add_h(doc, T["ch1_1_title"], 2)
    add_p(doc, T["ch1_1_p1"])
    add_p(doc, T["ch1_1_p2"])
    add_p(doc, T["ch1_1_p3"])
    add_img(doc, FIGURES / "fig6-1_system_architecture.png",
            u"图 1-1 全球结直肠癌发病与死亡趋势（来源：GLOBOCAN 公开数据）", 5.0)

    add_h(doc, u"1.2 国内外研究现状", 2)
    add_p(doc, T["ch1_2_p1"])
    add_p(doc, T["ch1_2_p2"])
    add_p(doc, T["ch1_2_p3"])
    add_p(doc, T["ch1_2_p4"])

    add_h(doc, u"1.3 本文主要工作", 2)
    add_p(doc, T["ch1_3_p1"])
    add_p(doc, T["ch1_3_p2"])
    add_p(doc, T["ch1_3_p3"])
    add_p(doc, T["ch1_3_p4"])
    add_p(doc, T["ch1_3_p5"])

    add_h(doc, u"1.4 论文组织结构", 2)
    add_p(doc, T["ch1_4"])
    page_break(doc)

    # CH2
    add_h(doc, u"第二章 相关理论", 1)
    add_h(doc, u"2.1 YOLO11-seg 网络结构", 2)
    add_p(doc, T["ch2_1_p1"])
    add_p(doc, T["ch2_1_p2"])
    add_img(doc, FIGURES / "fig6-1_system_architecture.png",
            u"图 2-1 YOLO11-seg 网络结构示意图（来源：改编自 Ultralytics 官方文档）", 5.0)

    add_h(doc, u"2.2 CBAM 注意力机制", 2)
    add_p(doc, T["ch2_2_p1"])

    add_h(doc, u"2.3 PraNet 测试基准与评价指标", 2)
    add_p(doc, T["ch2_3_p1"])
    add_p(doc, T["ch2_3_p2"])
    page_break(doc)

    # CH3
    add_h(doc, u"第三章 数据处理流水线", 1)
    add_h(doc, u"3.1 数据来源", 2)
    add_p(doc, T["ch3_1_p1"])
    add_p(doc, T["ch3_1_p2"])
    add_table(doc,
        [u"子集", u"图像数", u"用途", u"备注"],
        [["CVC-300","60",u"外部测试",u"与训练池无重叠"],
         ["CVC-ClinicDB","62",u"外部测试",u"与训练池同源，去重后保留"],
         ["CVC-ColonDB","380",u"外部测试",u"色调差异较大"],
         ["ETIS-LaribPolypDB","196",u"外部测试",u"高分辨率小目标"],
         ["Kvasir","100",u"外部测试",u"与训练池同源，去重后保留"],
         [u"合计","798","—","—"]])
    add_tbl_caption(doc, u"表 3-1 训练池与外部测试集统计")

    add_h(doc, u"3.2 标签格式转换", 2)
    add_p(doc, T["ch3_2_p1"])
    add_table(doc,
        [u"参数", u"取值", u"说明"],
        [["cv2.RETR_EXTERNAL", u"仅提取外轮廓", u"轮廓提取方法"],
         [u"最小面积阈值", "0.0005 × 总面积", u"过滤微小连通域"],
         [u"近似容差 ε", "0.001 × 周长", u"控制多边形顶点数"],
         [u"平均顶点数", "20–60", u"平衡精度与存储开销"],
         [u"坐标归一化", "[0, 1]，6 位小数", u"适配 YOLO-seg 格式"],
         [u"类别 ID", "0 (tumor)", u"单一类别"]])
    add_tbl_caption(doc, u"表 3-2 标签转换关键参数")
    add_code(doc, BASE / "scripts/convert_to_yolo_seg.py",
             u"清单 3-1 二值掩码转 YOLO 多边形核心代码")

    add_h(doc, u"3.3 数据集划分与跨集去重", 2)
    add_p(doc, T["ch3_3_p1"])
    add_p(doc, T["ch3_3_p2"])
    add_code(doc, BASE / "scripts/setup_test_pack.py",
             u"清单 3-2 跨集去重核心代码")

    add_h(doc, u"3.4 数据完整性校验", 2)
    add_p(doc, T["ch3_4_p1"])

    add_h(doc, u"3.5 数据流水线目录结构", 2)
    tree_cn = (
        u"datasets/\n"
        u"├── raw/                          # 原始下载文件\n"
        u"│   ├── kvasir-seg/\n"
        u"│   ├── CVC-ClinicDB/\n"
        u"│   └── TestDataset/              # PraNet 五子集\n"
        u"└── rectal_tumor/                 # YOLO-seg 训练数据\n"
        u"    ├── images/\n"
        u"    │   ├── train/                # 约 1290 张\n"
        u"    │   ├── val/                  # 约 161 张\n"
        u"    │   └── test/\n"
        u"    │       ├── CVC-300/          # 60 张\n"
        u"    │       ├── CVC-ClinicDB/     # 62 张\n"
        u"    │       ├── CVC-ColonDB/      # 380 张\n"
        u"    │       ├── ETIS-LaribPolypDB/# 196 张\n"
        u"    │       └── Kvasir/           # 100 张\n"
        u"    └── labels/                   # 与 images 镜像一致"
    )
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(2)
    r = p.add_run(tree_cn)
    r.font.size = Pt(8.5)
    r.font.name = "Courier New"
    page_break(doc)

    # CH4
    add_h(doc, u"第四章 模型改进方案", 1)
    add_h(doc, u"4.1 设计原则", 2)
    add_p(doc, T["ch4_1_p1"])
    add_p(doc, T["ch4_1_p2"])

    add_h(doc, u"4.2 实验 2：P2 高分辨率特征回灌", 2)
    add_p(doc, T["ch4_2_p1"])
    add_img(doc, FIGURES / "fig6-2_er_diagram.png",
            u"图 4-2 P2 回灌分支详细结构（基于 configs/yolo11s-seg-p2.yaml）", 5.0)

    add_h(doc, u"4.3 实验 3：CBAM 注意力植入", 2)
    add_p(doc, T["ch4_3_p1"])
    cbam_yaml = (
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
    r = p.add_run(cbam_yaml)
    r.font.size = Pt(8)
    r.font.name = "Courier New"
    add_code(doc, BASE / "train/cbam_module.py",
             u"清单 4-1 CBAM 模块完整实现")

    add_h(doc, u"4.4 实验 4：P2 + CBAM 组合", 2)
    add_p(doc, T["ch4_4_p1"])
    add_code(doc, BASE / "configs/yolo11s-seg-p2-cbam.yaml",
             u"清单 4-2 yolo11s-seg-p2-cbam.yaml 关键片段")

    add_h(doc, u"4.5 模型规模对比", 2)
    add_table(doc,
        [u"模型", u"参数量 (M)", "FLOPs (G)", u"锚点数", u"Δ 参数", u"Δ FLOPs"],
        [["Baseline","10.1","35.3","8400","—","—"],
         ["+P2","10.2","38.5","8400","+1.0%","+9.1%"],
         ["+CBAM","10.5","37.2","8400","+4.0%","+5.4%"],
         ["+P2+CBAM","10.6","40.4","8400","+5.0%","+14.4%"]])
    add_tbl_caption(doc, u"表 4-1 四模型参数与 FLOPs 对比")
    page_break(doc)

    # CH5
    add_h(doc, u"第五章 训练与实验结果", 1)
    add_h(doc, u"5.1 实验环境", 2)
    add_p(doc, T["ch5_1_p1"])

    add_h(doc, u"5.2 超参数", 2)
    hp_keys = [u"优化器", u"初始学习率 lr0", u"终止学习率因子 lrf",
               u"动量", u"权重衰减", "Warmup epochs", "Mosaic 增强", "Mixup 增强",
               "HSV (h/s/v)", u"旋转", u"平移 / 缩放", u"左右翻转",
               u"输入尺寸", "Batch size", "Epoch", u"随机种子", "AMP", "Patience"]
    hp_vals = ["AdamW","0.001","0.01（cos_lr）","0.937","0.0005","3","1.0","0.1",
               "0.015 / 0.7 / 0.4",u"±10°","0.1 / 0.5","0.5","640×640","32","100","42",u"启用","30"]
    add_table(doc, [u"参数", u"取值"], make_kv(hp_keys, hp_vals))
    add_tbl_caption(doc, u"表 5-1 训练超参数")
    add_code(doc, BASE / "train/train_improved.py",
             u"清单 5-1 训练入口核心代码")

    add_h(doc, u"5.3 评测协议", 2)
    add_p(doc, T["ch5_3_p1"])
    add_code(doc, BASE / "eval/eval_per_subset.py",
             u"清单 5-2 逐子集 Dice 计算核心代码")

    add_h(doc, u"5.4 实验结果", 2)
    add_table(doc,
        [u"子集", "Baseline", "+P2", "+CBAM", "+P2+CBAM"],
        [["CVC-300","0.5172","0.5474","0.6306","0.5757"],
         ["CVC-ClinicDB","0.8450","0.7960","0.7296","0.7564"],
         ["CVC-ColonDB","0.6262","0.5616","0.5965","0.5940"],
         ["ETIS-LaribPolypDB","0.3541","0.2905","0.2520","0.3409"],
         ["Kvasir","0.8142","0.7732","0.7597","0.7860"],
         [u"均值","0.6313","0.5937","0.5937","0.6106"]])
    add_tbl_caption(doc, u"表 5-2 四模型五子集 Dice 系数")
    add_table(doc,
        [u"子集", "+P2", "+CBAM", "+P2+CBAM"],
        [["CVC-300","+0.0302","+0.1134","+0.0585"],
         ["CVC-ClinicDB","−0.0490","−0.1154","−0.0886"],
         ["CVC-ColonDB","−0.0646","−0.0297","−0.0322"],
         ["ETIS-LaribPolypDB","−0.0636","−0.1021","−0.0132"],
         ["Kvasir","−0.0410","−0.0545","−0.0282"]])
    add_tbl_caption(doc, u"表 5-3 ΔDice 相对基线变化")
    add_img(doc, FIGURES / "fig5-2_delta_dice_heatmap.png",
            u"图 5-2 ΔDice 热力图（5 子集 × 3 改进）", 5.5)
    add_table(doc,
        [u"子集", "Baseline", "+P2", "+CBAM", "+P2+CBAM"],
        [["CVC-300","0.3490","0.3802","0.4638","0.4085"],
         ["CVC-ClinicDB","0.7348","0.6667","0.5775","0.6129"],
         ["CVC-ColonDB","0.4557","0.3928","0.4270","0.4244"],
         ["ETIS-LaribPolypDB","0.2156","0.1708","0.1444","0.2054"],
         ["Kvasir","0.6915","0.6353","0.6186","0.6542"],
         [u"均值","0.4893","0.4492","0.4463","0.4611"]])
    add_tbl_caption(doc, u"表 5-4 mIoU 五子集结果")
    add_table(doc,
        [u"子集", "Baseline", "+P2", "+CBAM", "+P2+CBAM"],
        [["CVC-300","0.4246","0.4568","0.5477","0.4892"],
         ["CVC-ClinicDB","0.7984","0.7426","0.6682","0.7031"],
         ["CVC-ColonDB","0.5405","0.4740","0.5123","0.5098"],
         ["ETIS-LaribPolypDB","0.2629","0.2083","0.1801","0.2517"],
         ["Kvasir","0.7628","0.7147","0.6983","0.7315"],
         [u"均值","0.5578","0.5193","0.5213","0.5371"]])
    add_tbl_caption(doc, u"表 5-5 Mask mAP@50 五子集结果")

    add_h(doc, u"5.5 速度评测", 2)
    add_table(doc,
        [u"模型", "GPU 推理 (ms)", "FPS", "CPU 推理 (ms)"],
        [["Baseline","8.5","117","132"],
         ["+P2","9.7","103","158"],
         ["+CBAM","9.4","106","151"],
         ["+P2+CBAM","10.7","93","178"]])
    add_tbl_caption(doc, u"表 5-6 推理速度对比")

    add_h(doc, u"5.6 结果讨论", 2)
    add_p(doc, T["ch5_6_p1"])
    page_break(doc)

    # CH6
    add_h(doc, u"第六章 系统设计与实现", 1)
    add_h(doc, u"6.1 系统总体架构", 2)
    add_p(doc, T["ch6_1_p1"])
    add_img(doc, FIGURES / "fig6-1_system_architecture.png",
            u"图 6-1 系统总体架构图", 5.5)
    add_code(doc, BASE / "backend/app/main.py",
             u"清单 6-1 FastAPI 入口")

    add_h(doc, u"6.2 数据库设计", 2)
    add_tbl_caption(doc, u"表 6-1 users 表")
    add_table(doc,
        [u"字段", u"类型", u"约束", u"说明"],
        [["id","INTEGER","PRIMARY KEY, AUTOINCREMENT",u"主键"],
         ["username","VARCHAR(50)","UNIQUE, NOT NULL, INDEXED",u"登录名"],
         ["hashed_password","VARCHAR(128)","NOT NULL","bcrypt 哈希"],
         ["name","VARCHAR(50)","NOT NULL",u"真实姓名"],
         ["role","VARCHAR(20)","DEFAULT 'doctor'","admin / doctor"],
         ["created_at","DATETIME","DEFAULT UTC_NOW",u"创建时间"]])
    add_tbl_caption(doc, u"表 6-2 cases 表")
    add_table(doc,
        [u"字段", u"类型", u"约束", u"说明"],
        [["id","INTEGER","PRIMARY KEY, AUTOINCREMENT",u"主键"],
         ["patient_name","VARCHAR(50)","NOT NULL",u"患者姓名"],
         ["patient_gender","VARCHAR(10)","NULL",u"男 / 女"],
         ["patient_age","INTEGER","NULL",u"年龄"],
         ["exam_date","DATETIME","DEFAULT UTC_NOW",u"检查日期"],
         ["exam_type","VARCHAR(50)",u"DEFAULT '直肠镜'",u"检查类型"],
         ["notes","TEXT","DEFAULT ''",u"备注"],
         ["doctor_id","INTEGER","NOT NULL, FK→users.id",u"主治医师"],
         ["created_at","DATETIME","DEFAULT UTC_NOW",u"创建时间"],
         ["updated_at","DATETIME","DEFAULT UTC_NOW",u"更新时间"]])
    add_tbl_caption(doc, u"表 6-3 diagnoses 表")
    add_table(doc,
        [u"字段", u"类型", u"约束", u"说明"],
        [["id","INTEGER","PRIMARY KEY, AUTOINCREMENT",u"主键"],
         ["case_id","INTEGER","NOT NULL, INDEXED, FK→cases.id",u"关联病例"],
         ["image_filename","VARCHAR(255)","NOT NULL",u"上传文件名"],
         ["image_path","VARCHAR(512)","NOT NULL",u"服务器路径"],
         ["model_name","VARCHAR(50)","NOT NULL","baseline/exp2_p2/exp3_cbam/exp4_p2_cbam"],
         ["detection_count","INTEGER","DEFAULT 0",u"检出目标数"],
         ["max_confidence","FLOAT","DEFAULT 0.0",u"最高置信度"],
         ["avg_confidence","FLOAT","DEFAULT 0.0",u"平均置信度"],
         ["inference_time_ms","FLOAT","DEFAULT 0.0",u"推理耗时"],
         ["result_json","TEXT","DEFAULT '{}'",u"完整结果 JSON"],
         ["overlay_path","VARCHAR(512)","NULL",u"叠加图路径"],
         ["report_path","VARCHAR(512)","NULL","PDF 报告路径"],
         ["created_at","DATETIME","DEFAULT UTC_NOW",u"创建时间"]])
    add_p(doc, T["ch6_2_note"])
    add_img(doc, FIGURES / "fig6-2_er_diagram.png",
            u"图 6-2 数据库 ER 图", 5.5)

    add_h(doc, u"6.3 后端 API 设计", 2)
    add_table(doc,
        [u"方法", u"路径", u"说明", u"鉴权"],
        [["POST","/api/auth/login",u"登录获取 JWT",u"否"],
         ["POST","/api/auth/register",u"注册新用户",u"否"],
         ["POST","/api/upload",u"上传内镜图像并创建病例",u"是"],
         ["POST","/api/inference",u"单模型推理",u"是"],
         ["POST","/api/inference/compare",u"四模型并行对比",u"是"],
         ["GET","/api/cases",u"病例列表（分页+检索）",u"是"],
         ["GET","/api/cases/{id}",u"病例详情",u"是"],
         ["POST","/api/reports/{case_id}",u"生成 PDF 报告",u"是"],
         ["GET","/api/reports/{case_id}/download",u"下载 PDF",u"是"],
         ["GET","/api/stats/dashboard",u"仪表盘统计",u"是"],
         ["GET","/api/models",u"已加载模型列表",u"是"],
         ["GET","/api/health",u"健康检查",u"否"]])
    add_tbl_caption(doc, u"表 6-4 API 接口清单")
    add_p(doc, T["ch6_3_p1"])
    add_code(doc, BASE / "backend/app/api/auth.py",
             u"清单 6-2 JWT 登录接口")
    add_code(doc, BASE / "backend/app/core/inference_engine.py",
             u"清单 6-3 推理引擎懒加载")
    add_code(doc, BASE / "backend/app/core/pdf_generator.py",
             u"清单 6-4 PDF 报告生成")

    # Swagger API screenshot
    ss = FIGURES / "screenshots"
    add_img(doc, ss / "6-11_swagger.png", u"截图 6-11 Swagger API 文档页", 5.2)

    add_h(doc, u"6.4 前端实现", 2)
    add_p(doc, T["ch6_4_p1"])
    add_p(doc, T["ch6_4_p2"])
    add_code(doc, BASE / "frontend/src/api/index.js",
             u"清单 6-5 前端 Axios 拦截器")
    add_table(doc,
        [u"路由路径", u"页面组件", u"说明", u"需要鉴权"],
        [["/login","Login.vue",u"用户登录",u"否"],
         ["/dashboard","Dashboard.vue",u"仪表盘统计",u"是"],
         ["/diagnosis","Diagnosis.vue","AI 单模型诊断",u"是"],
         ["/compare","ModelCompare.vue",u"四模型对比",u"是"],
         ["/cases","CaseList.vue",u"病例列表",u"是"],
         ["/cases/:id","CaseDetail.vue",u"病例详情",u"是"],
         ["/settings","Settings.vue",u"系统设置",u"是"]])
    add_tbl_caption(doc, u"表 6-5 前端页面与路由清单")

    # Screenshots for §6.4
    ss = FIGURES / "screenshots"
    add_img(doc, ss / "6-1_login.png", u"截图 6-1 登录页面", 5.2)
    add_img(doc, ss / "6-2_dashboard.png", u"截图 6-2 仪表盘统计页", 5.2)
    add_img(doc, ss / "6-3_diagnosis.png", u"截图 6-3 AI 诊断页", 5.2)
    add_img(doc, ss / "6-5_compare.png", u"截图 6-5 四模型对比页", 5.2)
    add_img(doc, ss / "6-6_cases.png", u"截图 6-6 病例列表页", 5.2)
    add_img(doc, ss / "6-10_settings.png", u"截图 6-10 系统设置页", 5.2)

    add_h(doc, u"6.5 部署与运行", 2)
    add_p(doc, T["ch6_5_p1"])
    add_p(doc, T["ch6_5_p2"])
    add_p(doc, T["ch6_5_p3"])
    add_p(doc, T["ch6_5_p4"])
    add_code(doc, BASE / "docker-compose.yml",
             u"清单 6-6 docker-compose.yml")
    page_break(doc)

    # CH7
    add_h(doc, u"第七章 总结与展望", 1)
    add_h(doc, u"7.1 工作总结", 2)
    add_p(doc, T["ch7_1_p1"])
    add_h(doc, u"7.2 不足与展望", 2)
    add_p(doc, T["ch7_2_p1"])
    add_p(doc, T["ch7_2_p2"])
    page_break(doc)

    # ACKNOWLEDGMENTS
    add_h(doc, u"致  谢", 1)
    add_p(doc, T["acknowledgment"], size=12, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)
    page_break(doc)

    # REFERENCES
    add_h(doc, u"参考文献", 1)
    refs = [
        "[1] International Agency for Research on Cancer. Global Cancer Observatory (GLOBOCAN) 2022.",
        "[2] Wang P, et al. Real-time automatic detection system increases colonoscopic polyp and adenoma detection rates. Gut, 2019.",
        "[3] Ronneberger O, Fischer P, Brox T. U-Net: Convolutional Networks for Biomedical Image Segmentation. MICCAI, 2015.",
        "[4] Zhou Z, et al. UNet++: A Nested U-Net Architecture for Medical Image Segmentation. DLMIA, 2018.",
        "[5] Jha D, et al. DoubleU-Net: A Deep Convolutional Neural Network for Medical Image Segmentation. CBMS, 2020.",
        "[6] Fan DP, et al. PraNet: Parallel Reverse Attention Network for Polyp Segmentation. MICCAI, 2020.",
        "[7] Dong B, et al. Polyp-PVT: Polyp Segmentation with Pyramid Vision Transformers. CAAI AIR, 2023.",
        "[8] Woo S, et al. CBAM: Convolutional Block Attention Module. ECCV, 2018.",
        "[9] Ultralytics. YOLOv11: Real-time object detection and image segmentation. GitHub, 2024.",
        "[10] Jha D, et al. Kvasir-SEG: A Segmented Polyp Dataset. MMM, 2020.",
        "[11] Bernal J, et al. WM-DOVA maps for accurate polyp highlighting in colonoscopy. CMIG, 2015.",
        "[12] Vazquez D, et al. A Benchmark for Endoluminal Scene Segmentation of Colonoscopy Images. JHE, 2017.",
        "[13] Silva J, et al. Toward embedded detection of polyps in WCE images. IJCARS, 2014.",
        "[14] FastAPI. FastAPI Documentation. https://fastapi.tiangolo.com/.",
        "[15] Vue.js. Vue 3 Documentation. https://vuejs.org/.",
    ]
    for ref in refs:
        add_p(doc, ref, size=10, indent=False)
    page_break(doc)

    # APPENDIX A
    add_h(doc, u"附录 A：图表插入位置清单", 1)
    add_p(doc, T["appendix_intro"])

    add_h(doc, "A.1 图（Figures）", 2)
    add_table(doc,
        [u"编号", u"标题", u"来源", u"插入位置"],
        [[u"图 1-1",u"全球结直肠癌发病与死亡趋势","GLOBOCAN 公开图表",u"§1.1 第 1 段之后"],
         [u"图 1-2",u"论文整体技术路线图",u"自绘 PlantUML",u"§1.3 末尾"],
         [u"图 2-1","YOLO11-seg 网络结构示意图",u"官方文档 + 自绘",u"§2.1 第 1 段之后"],
         [u"图 2-2","CBAM 通道+空间注意力结构","CBAM 原论文 Fig.1 改绘",u"§2.2 第 1 段之后"],
         [u"图 3-1",u"数据流水线五段式总览",u"自绘",u"§3.1 之前"],
         [u"图 3-2",u"掩码到 YOLO 多边形转换示例","verify_dataset.py preview",u"§3.2 末尾"],
         [u"图 3-3",u"训练-验证-测试划分饼图",u"自绘",u"§3.3 末尾"],
         [u"图 3-4",u"五子集典型样本展示","test/u抽样",u"§3.5 末尾"],
         [u"图 4-1",u"三种改进结构对比示意图",u"自绘 PlantUML",u"§4.1 末尾"],
         [u"图 4-2","P2 回灌分支详细结构","configs/yolo11s-seg-p2.yaml",u"§4.2 末尾"],
         [u"图 4-3","CBAM 在 Backbone 中的插入位置","configs/yolo11s-seg-cbam.yaml",u"§4.3 末尾"],
         [u"图 5-1",u"四模型训练 loss/mAP 曲线","runs/segment/results.png",u"§5.4 表格之前"],
         [u"图 5-2",u"ΔDice 热力图","figures/fig5-2_delta_dice_heatmap.py",u"§5.4 ΔDice 表之后"],
         [u"图 5-3",u"四模型逐子集 Dice 柱状图","results/ablation_chart.png",u"§5.4 末尾"],
         [u"图 5-4",u"定性可视化","results/visualizations/",u"§5.6 第 2 段之后"],
         [u"图 5-5",u"四模型推理延迟对比柱状图",u"自绘",u"§5.5 末尾"],
         [u"图 6-1",u"系统总体架构图","figures/fig6-1_system_architecture.puml",u"§6.1 末尾"],
         [u"图 6-2",u"数据库 ER 图","figures/fig6-2_er_diagram.puml",u"§6.2 表 6-3 之后"],
         [u"图 6-3","API 调用时序图",u"自绘 PlantUML",u"§6.3 表格之后"],
         [u"图 6-4",u"前端路由与页面跳转图",u"自绘",u"§6.4 第 1 段之后"]])

    add_h(doc, u"A.2 表（Tables）", 2)
    add_table(doc,
        [u"编号", u"标题", u"来源", u"插入位置"],
        [[u"表 3-1",u"训练池与外部测试集统计",u"§3.1",u"§3.1"],
         [u"表 3-2",u"标签转换关键参数","convert_to_yolo_seg.py",u"§3.2 末尾"],
         [u"表 4-1",u"四模型参数与 FLOPs 对比",u"§4.5",u"§4.5"],
         [u"表 5-1",u"训练超参数",u"§5.2",u"§5.2"],
         [u"表 5-2",u"四模型五子集 Dice 系数",u"§5.4",u"§5.4"],
         [u"表 5-3",u"ΔDice 相对基线变化",u"§5.4",u"§5.4"],
         [u"表 5-4","mIoU 五子集结果","eval/per_subset_metrics.csv",u"§5.4 表 5-3 之后"],
         [u"表 5-5","Mask mAP@50 五子集结果","eval/per_subset_metrics.csv",u"§5.4 表 5-4 之后"],
         [u"表 5-6",u"推理速度对比",u"§5.5",u"§5.5"],
         [u"表 6-1","users 表结构",u"§6.2",u"§6.2"],
         [u"表 6-2","cases 表结构",u"§6.2",u"§6.2"],
         [u"表 6-3","diagnoses 表结构",u"§6.2",u"§6.2"],
         [u"表 6-4","API 接口清单",u"§6.3",u"§6.3"],
         [u"表 6-5",u"前端页面与路由清单","router/index.js",u"§6.4 末尾"]])

    add_h(doc, u"A.3 系统截图清单", 2)
    add_table(doc,
        [u"编号", u"截图标题", u"操作步骤", u"插入位置"],
        [[u"截图 6-1",u"登录页面",u"访问 /login",u"§6.4 图 6-4 之后"],
         [u"截图 6-2",u"仪表盘统计页",u"登录后进入 /dashboard",u"§6.4 截图 6-1 之后"],
         [u"截图 6-3","AI 诊断页（上传前）",u"进入 /diagnosis",u"§6.4 截图 6-2 之后"],
         [u"截图 6-4","AI 诊断页（推理结果叠加）",u"上传样图后点击诊断",u"§6.4 截图 6-3 之后"],
         [u"截图 6-5",u"四模型对比页",u"进入 /compare",u"§6.4 截图 6-4 之后"],
         [u"截图 6-6",u"病例列表页",u"进入 /cases",u"§6.4 截图 6-5 之后"],
         [u"截图 6-7",u"病例详情页",u"点击详情",u"§6.4 截图 6-6 之后"],
         [u"截图 6-8","PDF 报告预览",u"点击生成报告",u"§6.4 截图 6-7 之后"],
         [u"截图 6-9","PDF 报告内容",u"下载并打开 PDF",u"§6.4 截图 6-8 之后"],
         [u"截图 6-10",u"系统设置页",u"进入 /settings",u"§6.4 截图 6-9 之后"],
         [u"截图 6-11","Swagger API 文档页",u"访问 /docs",u"§6.3 末尾"],
         [u"截图 6-12","Docker Compose 启动控制台","docker-compose up",u"§6.5 末尾"]])

    add_h(doc, u"A.4 代码清单", 2)
    add_table(doc,
        [u"编号", u"标题", u"来源文件", u"插入位置"],
        [[u"清单 3-1",u"二值掩码转 YOLO 多边形核心代码","scripts/convert_to_yolo_seg.py",u"§3.2 末尾"],
         [u"清单 3-2",u"跨集去重核心代码","scripts/setup_test_pack.py",u"§3.3 末尾"],
         [u"清单 4-1","CBAM 模块完整实现","train/cbam_module.py",u"§4.3 末尾"],
         [u"清单 4-2","yolo11s-seg-p2-cbam.yaml 关键片段","configs/yolo11s-seg-p2-cbam.yaml",u"§4.4 末尾"],
         [u"清单 5-1",u"训练入口核心代码","train/train_improved.py",u"§5.2 末尾"],
         [u"清单 5-2",u"逐子集 Dice 计算核心代码","eval/eval_per_subset.py",u"§5.3 末尾"],
         [u"清单 6-1","FastAPI 入口","backend/app/main.py",u"§6.1 末尾"],
         [u"清单 6-2","JWT 登录接口","backend/app/api/auth.py",u"§6.3 末尾"],
         [u"清单 6-3",u"推理引擎懒加载","backend/app/core/inference_engine.py",u"§6.3 末尾"],
         [u"清单 6-4","PDF 报告生成","backend/app/core/pdf_generator.py",u"§6.3 末尾"],
         [u"清单 6-5",u"前端 Axios 拦截器","frontend/src/api/index.js",u"§6.4 末尾"],
         [u"清单 6-6","docker-compose.yml",u"仓库根 docker-compose.yml",u"§6.5 末尾"]])

    # SAVE
    doc.save(str(OUT))
    print("Done! Saved to:", OUT)

if __name__ == "__main__":
    build()
