import requests
import time
from datetime import datetime

def test_asr_service(audio_file_path, hotword=None):
    # API端点
    url = "http://localhost:8000/asr"

    # 准备文件
    with open(audio_file_path, "rb") as audio_file:
        files = {"file": (audio_file_path.split("/")[-1], audio_file)}
        data = {"hotword": hotword} if hotword else {}

        # 发送请求
        start_time = time.time()
        print(f"{datetime.now()} - 开始发送请求...")
        response = requests.post(url, files=files, data=data)

        # 处理响应
        if response.status_code == 200:
            result = response.json()
            print(f"{datetime.now()} - 识别成功!")
            print(f"文件名: {result['filename']}")
            print("识别结果（带标点+说话人）：")
            # 解析结构化的说话人+文本
            for idx, segment in enumerate(result['transcription']):
                print(f"\n片段{idx+1}：")
                print(f"说话人：{segment['spk']}")
                print(f"文本：{segment['text']}")
            print(f"\n总处理时间: {time.time() - start_time:.2f}秒")
            return result
        else:
            print(f"{datetime.now()} - 识别失败!")
            print(f"状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None

if __name__ == "__main__":
    # 测试调用
    audio_file = r"F:\Text_FunASR\FunASR-main\TTT.mp3"  # 替换为你的音频文件路径
    hotword = "创业项目,宠物项圈,VR非遗保护"  # 可选热词

    result = test_asr_service(audio_file, hotword)