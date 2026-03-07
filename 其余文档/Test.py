import sys
import torch

# 强制CPU运行（适配核显，关键！）
torch.set_num_threads(4)
torch.set_default_device("cpu")

print("当前Python解释器路径：", sys.executable)

from funasr import AutoModel

# 1. 初始化模型（核心：添加device="cpu"+完整CAM++配置）
model = AutoModel(
    model="paraformer-zh",          # 核心语音识别模型
    model_revision="v2.0.4",
    vad_model="fsmn-vad",           # 语音活动检测（分割语音片段）
    vad_model_revision="v2.0.4",
    punc_model="ct-punc",           # 标点符号恢复
    punc_model_revision="v2.0.4",
    spk_model="cam++",              # CAM++说话人识别模型
    spk_model_revision="v2.0.2",
    device="cpu"                    # 强制CPU，适配核显
)

# 2. 调用模型（核心：开启说话人识别参数）
audio_path = r"F:\Text_FunASR\FunASR-main\Test.wav"  # 确保是16kHz单声道WAV
result = model.generate(
    input=audio_path,
    batch_size_s=100,  # 核显适配：减小批量
    hotword="",
    return_timestamp=True,          # 返回时间戳
    spk_recog=True,                 # 开启说话人识别（关键！）
    spk_num=2                       # 预设说话人数量（可根据实际调整，如3/4）
)

# 3. 处理结果（提取并打印带说话人标签的日志）
print("\n========== 带说话人标签的识别日志 ==========")
for idx, item in enumerate(result):
    print(f"\n【第{idx+1}段语音】")
    # 打印识别文本
    print(f"识别文本: {item['text']}")
    # 打印时间戳+说话人标签（核心：解析CAM++输出的spk信息）
    if "timestamp" in item and "spk" in item:
        for i, (start, end) in enumerate(item["timestamp"]):
            # 匹配每个时间片段的说话人
            spk_label = item["spk"][i] if i < len(item["spk"]) else "UNKNOWN"
            text_segment = item["text"].split("，")[i] if i < len(item["text"].split("，")) else ""
            print(f"  [{round(start,2)}s - {round(end,2)}s] [说话人{spk_label}]：{text_segment}")
    else:
        print("  无说话人标签（音频过短/无有效语音）")
    print("-" * 60)