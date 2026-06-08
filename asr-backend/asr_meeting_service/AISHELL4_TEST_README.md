# AISHELL-4 测试集使用说明

## 测试集结构

```
AISHELL-4-test/
└── test/
    ├── wav/              # 音频文件 (FLAC格式)
    │   ├── S_R003S01C01.flac
    │   ├── S_R003S01C02.flac
    │   └── ...
    └── TextGrid/         # 标注文件
        ├── S_R003S01C01.TextGrid   # Praat格式的完整标注（包含文本和说话人）
        ├── S_R003S01C01.rttm       # RTTM格式的说话人标注
        └── ...
```

## 快速开始

### 1. 安装依赖

```bash
pip install textgrid tqdm requests
```

---

## 方法一：使用后端 API 测试（推荐）

使用真实的后端 API 接口，包含登录获取 Token 并调用 ASR 接口：

### 步骤

1. **启动后端服务**（在另一个终端）：
```bash
cd asr-backend/asr_meeting_service
python manage.py runserver
```

2. **运行 API 测试脚本**：
```bash
cd asr-backend/asr_meeting_service

# 测试单个文件（使用默认账号 1/lch123456）
python api_test.py --single-file S_R003S01C01

# 测试整个数据集
python api_test.py --output-dir ./api_test_results

# 使用自定义参数
python api_test.py \
  --api-url http://localhost:8000 \
  --username 1 \
  --password lch123456 \
  --single-file S_R003S01C01
```

### API 测试脚本特点

- 自动登录获取 Bearer Token
- 通过 `/api/user/login` 接口登录
- 调用 `/api/asr` 接口进行语音识别
- 支持声纹匹配功能
- 结果包含标注与 API 返回对比

---

## 方法二：使用简化版测试

不依赖 Django，直接使用 FunASR：

```bash
cd asr_meeting_service

# 测试单个文件
python simple_test.py --single-file S_R003S01C01

# 测试整个数据集
python simple_test.py --output-dir ./test_results
```

---

## 方法三：使用 Django 集成版测试

需要先配置好 Django 环境：

```bash
cd asr_meeting_service

# 测试单个文件
python test_aishell4.py --single-file S_R003S01C01

# 测试整个数据集
python test_aishell4.py --output-dir ./aishell4_results
```

---

## 输出说明

测试结果会保存在指定的输出目录：

```
api_test_results/       # API 测试输出
├── S_R003S01C01.json   # 单个文件的完整结果
├── S_R003S01C02.json
└── ...

test_results/           # 简化版测试输出
├── S_R003S01C01.json
└── ...
```

每个 JSON 文件包含：
- `annotations`: AISHELL-4 的标准标注
- `api_result` / `transcription`: 识别结果
- `raw_result`: 原始输出（如适用）

---

## 文件命名规则

- `S_`: 小型会议室 (Small)
- `M_`: 中型会议室 (Medium)
- `L_`: 大型会议室 (Large)
- `R003`: 房间编号
- `S01`: 场景编号
- `C01`: 通道编号

---

## 使用官方评估工具（可选）

如果需要使用 AISHELL-4 官方的评估脚本计算 CER：

1. 在 `AISHELL-4-master/eval/` 目录下操作
2. 将生成的 RTTM 文件复制到相应目录
3. 运行官方评估脚本

参考 `AISHELL-4-master/eval/README.md` 了解更多细节。
