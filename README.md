# 基于 YOLOv11 的直肠肿瘤辅助诊断系统

本科毕业设计，使用 YOLOv11-seg 对肠镜图像中的直肠肿瘤（息肉）进行实例分割。

---

## Phase 5: 系统集成 — 快速启动

### 1. 后端

```bash
cd backend
pip install -r requirements.txt
bash run.sh
# API 文档: http://localhost:8000/docs
```

### 2. 前端

```bash
cd frontend
npm install
bash run.sh
# 界面: http://localhost:5173
```

### 3. Docker

```bash
docker-compose up -d
```

### 默认账号

- 用户名: `admin`
- 密码: `admin123`

### 系统技术栈

| 层 | 技术 |
|---|------|
| 后端 | FastAPI + Uvicorn + SQLAlchemy + SQLite |
| 认证 | JWT (python-jose + passlib) |
| AI 推理 | ultralytics YOLO11-seg |
| PDF 报告 | reportlab |
| 前端 | Vue 3 + Vite + Element Plus + ECharts + Pinia |

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 登录 |
| POST | /api/auth/register | 注册 |
| POST | /api/upload | 上传图像 |
| POST | /api/inference | AI 诊断 |
| GET | /api/cases | 病例列表 |
| GET | /api/cases/{id} | 病例详情 |
| POST | /api/reports/{case_id} | 生成报告 |
| GET | /api/reports/{case_id}/download | 下载报告 |
| GET | /api/stats/dashboard | 仪表盘统计 |
| GET | /api/models | 可用模型列表 |

---

## Phase 1-4: 训练与评估

### 数据集

| 数据集 | 用途 |
|--------|------|
| Kvasir-SEG | 训练池 |
| CVC-ClinicDB | 训练池 |
| CVC-ColonDB | 外部测试集 |
| ETIS-LaribPolypDB | 外部测试集 |

### 快速开始

```bash
pip install -r requirements.txt
python scripts/download_datasets.py
python scripts/convert_to_yolo_seg.py
python scripts/split_dataset.py
python scripts/verify_dataset.py
```

### 训练

```bash
# Baseline
python train/train_baseline.py

# Phase 3 改进实验
bash run_phase3.sh
```

### 项目结构

```
rectal-tumor-system/
├── backend/           # FastAPI 后端 (Phase 5)
│   ├── app/
│   │   ├── main.py
│   │   ├── models/    # ORM
│   │   ├── api/       # 路由
│   │   └── core/      # 推理引擎/可视化/PDF
│   ├── weights/       # YOLO 权重
│   └── data.db
├── frontend/          # Vue 3 前端 (Phase 5)
├── train/             # 训练脚本
├── eval/              # 评估 & 可视化
├── configs/           # YOLO 训练/模型配置
├── scripts/           # 数据处理
└── run_phase3.sh      # 一键消融实验
```

### Kaggle 训练指南（免费 T4 GPU）

详见 `notebooks/kaggle_train.ipynb`。
