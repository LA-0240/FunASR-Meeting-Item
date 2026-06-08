#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用后端 API 测试 AISHELL-4 数据集
包含登录获取 Token 并调用 ASR 接口
输出详细的评估指标和统计结果
"""

import os
import sys
import json
import time
import requests
import argparse
import textgrid
import re
from pathlib import Path
from tqdm import tqdm


def calculate_cer(hypothesis, reference):
    """
    计算字符错误率 (Character Error Rate)
    
    Args:
        hypothesis: 识别结果文本
        reference: 标注文本
    
    Returns:
        CER 值 (0.0 - 1.0)
    """
    # 预处理文本：去除空格和标点
    def clean_text(text):
        if not text:
            return ""
        # 去除空格、换行等空白字符
        text = re.sub(r"\s+", "", text)
        # 去除常见标点符号（逐个替换避免转义问题）
        punctuations = "，。！？、；：\"'（）【】《》.,!?;:()[]<>"
        for p in punctuations:
            text = text.replace(p, "")
        return text

    hyp = clean_text(hypothesis)
    ref = clean_text(reference)

    if not ref:
        return 0.0

    # 计算编辑距离 (Levenshtein distance)
    m, n = len(hyp), len(ref)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if hyp[i - 1] == ref[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # 删除
                dp[i][j - 1] + 1,      # 插入
                dp[i - 1][j - 1] + cost  # 替换
            )

    return dp[m][n] / len(ref)


def merge_segments_text(segments):
    """将多个分段的文本合并成一个完整文本"""
    texts = []
    for seg in segments:
        if seg.get("text"):
            texts.append(seg["text"])
    return "".join(texts)


class AISHELL4APITester:
    def __init__(self, test_dir: str, output_dir: str = "./api_test_results",
                 api_base_url: str = "http://localhost:8000",
                 username: str = "1", password: str = "lch123456"):
        """
        初始化 API 测试器
        
        Args:
            test_dir: AISHELL-4 测试集目录
            output_dir: 输出结果目录
            api_base_url: API 基础 URL
            username: 登录用户名
            password: 登录密码
        """
        self.test_dir = Path(test_dir)
        self.output_dir = Path(output_dir)
        self.wav_dir = self.test_dir / "test" / "wav"
        self.textgrid_dir = self.test_dir / "test" / "TextGrid"
        self.api_base_url = api_base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token = None
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计数据
        self.stats = {
            "total_files": 0,
            "success_files": 0,
            "failed_files": 0,
            "total_duration": 0.0,
            "total_process_time": 0.0,
            "total_ref_segments": 0,
            "total_hyp_segments": 0,
            "total_ref_characters": 0,
            "total_hyp_characters": 0,
            "cer_list": [],
            "file_results": []
        }

    def login(self):
        """登录获取 Token"""
        print("正在登录...")
        print(f"API 地址: {self.api_base_url}")
        print(f"用户名: {self.username}")
        
        url = f"{self.api_base_url}/user/login"
        data = {
            "username": self.username,
            "password": self.password
        }
        try:
            response = requests.post(url, json=data, timeout=30)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    self.token = result.get("token")
                    print(f"登录成功！用户名: {result.get('username')}")
                    print(f"Token: {self.token[:50]}...")
                    return True
                else:
                    print(f"登录失败: {result.get('detail')}")
                    return False
            else:
                print(f"HTTP 错误: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print("\n" + "="*60)
            print("连接失败！请检查：")
            print("1. 后端服务是否已启动？")
            print("2. API 地址是否正确？")
            print("3. 端口是否正确？")
            print("="*60)
            print("\n启动后端服务的命令：")
            print("  cd asr-backend/asr_meeting_service")
            print("  python manage.py runserver")
            return False
        except Exception as e:
            print(f"登录出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def parse_textgrid(self, textgrid_path: str):
        """解析 TextGrid 文件"""
        tg = textgrid.TextGrid.fromFile(textgrid_path)
        annotations = []
        speakers = set()
        total_duration = 0.0
        
        for tier in tg:
            speaker_name = tier.name
            speakers.add(speaker_name)
            for interval in tier:
                # 获取文本内容 - 不同版本的textgrid库可能有不同的属性
                if hasattr(interval, 'mark'):
                    text = interval.mark
                elif hasattr(interval, 'text'):
                    text = interval.text
                else:
                    text = ""
                
                if text.strip():
                    duration = interval.maxTime - interval.minTime
                    total_duration += duration
                    annotations.append({
                        "speaker": speaker_name,
                        "start_time": interval.minTime,
                        "end_time": interval.maxTime,
                        "duration": duration,
                        "text": text.strip()
                    })
        annotations.sort(key=lambda x: x["start_time"])
        
        return {
            "annotations": annotations,
            "speakers": sorted(list(speakers)),
            "num_speakers": len(speakers),
            "total_duration": total_duration
        }

    def transcribe_audio(self, audio_file: Path):
        """调用 ASR API 转录音频，计时"""
        if not self.token:
            print("未登录，无法调用 API")
            return None, 0.0

        url = f"{self.api_base_url}/asr"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        start_time = time.time()
        try:
            with open(audio_file, "rb") as f:
                files = {"file": f}
                response = requests.post(url, headers=headers, files=files, timeout=1200)
                result = response.json()
                process_time = time.time() - start_time
                return result, process_time
        except Exception as e:
            process_time = time.time() - start_time
            print(f"API 调用出错: {e}")
            return None, process_time

    def test_single_file(self, audio_file: Path):
        """测试单个文件，返回详细结果"""
        file_id = audio_file.stem
        self.stats["total_files"] += 1
        
        print(f"\n{'=' * 80}")
        print(f"处理文件: {file_id}")
        print(f"{'=' * 80}")

        # 获取标注
        textgrid_file = self.textgrid_dir / f"{file_id}.TextGrid"
        ref_data = None
        if textgrid_file.exists():
            ref_data = self.parse_textgrid(str(textgrid_file))
            print(f"标注信息:")
            print(f"  - 说话人数量: {ref_data['num_speakers']}")
            print(f"  - 说话人列表: {', '.join(ref_data['speakers'])}")
            print(f"  - 标注段落数: {len(ref_data['annotations'])}")
            print(f"  - 音频总时长: {ref_data['total_duration']:.2f} 秒")
            self.stats["total_ref_segments"] += len(ref_data['annotations'])
            self.stats["total_duration"] += ref_data['total_duration']

        # 调用 ASR
        result, process_time = self.transcribe_audio(audio_file)
        self.stats["total_process_time"] += process_time

        # 计算评估指标
        cer = None
        ref_text = ""
        hyp_text = ""
        num_hyp_segments = 0
        num_hyp_speakers = 0
        hyp_speakers = []
        
        if result and result.get("status") == "success":
            self.stats["success_files"] += 1
            segments = result.get("segments", [])
            num_hyp_segments = len(segments)
            self.stats["total_hyp_segments"] += num_hyp_segments
            
            # 获取说话人
            hyp_speaker_set = set()
            for seg in segments:
                spk = seg.get('speaker', 'unknown')
                hyp_speaker_set.add(spk)
            hyp_speakers = sorted(list(hyp_speaker_set))
            num_hyp_speakers = len(hyp_speakers)
            
            # 合并文本计算 CER
            if ref_data:
                ref_text = merge_segments_text(ref_data['annotations'])
                hyp_text = merge_segments_text(segments)
                cer = calculate_cer(hyp_text, ref_text)
                self.stats["cer_list"].append(cer)
                self.stats["total_ref_characters"] += len(ref_text.replace(' ', ''))
                self.stats["total_hyp_characters"] += len(hyp_text.replace(' ', ''))
            
            print(f"\n识别结果:")
            print(f"  - 状态: 成功")
            print(f"  - 识别段落数: {num_hyp_segments}")
            print(f"  - 识别说话人数: {num_hyp_speakers}")
            print(f"  - 识别说话人: {', '.join(hyp_speakers)}")
            print(f"  - 处理时间: {process_time:.2f} 秒")
            if cer is not None:
                print(f"  - 字符错误率 (CER): {cer:.2%}")
            
            if segments:
                print(f"\n前 3 段识别结果:")
                for i, seg in enumerate(segments[:3]):
                    display_text = seg['text'][:60] + "..." if len(seg['text']) > 60 else seg['text']
                    print(f"  [{i+1}] [{seg['start_time']:.2f}-{seg['end_time']:.2f}] {seg['speaker']}: {display_text}")
        else:
            self.stats["failed_files"] += 1
            print(f"\n识别结果:")
            print(f"  - 状态: 失败")
            print(f"  - 处理时间: {process_time:.2f} 秒")
            print(f"  - 错误信息: {result}")

        # 保存详细结果
        file_result = {
            "file_id": file_id,
            "success": result.get("status") == "success" if result else False,
            "process_time": process_time,
            "reference": ref_data,
            "hypothesis": {
                "segments": result.get("segments", []) if result else [],
                "speakers": hyp_speakers,
                "num_speakers": num_hyp_speakers,
                "num_segments": num_hyp_segments
            },
            "metrics": {
                "cer": cer,
                "ref_characters": len(ref_text.replace(' ', '')),
                "hyp_characters": len(hyp_text.replace(' ', ''))
            },
            "raw_result": result
        }
        self.stats["file_results"].append(file_result)

        output_file = self.output_dir / f"{file_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(file_result, f, ensure_ascii=False, indent=2)

        print(f"\n结果已保存到: {output_file}")
        return file_result

    def print_summary(self, total_start_time):
        """打印完整的测试总结"""
        total_elapsed = time.time() - total_start_time
        
        print(f"\n{'=' * 80}")
        print(f"                          测试结果统计报告")
        print(f"{'=' * 80}")
        
        # 基本统计
        print(f"\n【基本统计】")
        print(f"  总文件数: {self.stats['total_files']}")
        print(f"  成功: {self.stats['success_files']}")
        print(f"  失败: {self.stats['failed_files']}")
        if self.stats['total_files'] > 0:
            print(f"  成功率: {self.stats['success_files']/self.stats['total_files']*100:.2f}%")
        
        # 时间统计
        print(f"\n【时间统计】")
        print(f"  音频总时长: {self.stats['total_duration']:.2f} 秒")
        print(f"  总处理时间: {self.stats['total_process_time']:.2f} 秒")
        print(f"  总耗时: {total_elapsed:.2f} 秒")
        if self.stats['total_duration'] > 0:
            rtf = self.stats['total_process_time'] / self.stats['total_duration']
            print(f"  实时率 (RTF): {rtf:.3f}x")
        
        # 分段统计
        print(f"\n【分段统计】")
        print(f"  标注总段数: {self.stats['total_ref_segments']}")
        print(f"  识别总段数: {self.stats['total_hyp_segments']}")
        
        # 字符统计
        print(f"\n【字符统计】")
        print(f"  标注总字符数: {self.stats['total_ref_characters']}")
        print(f"  识别总字符数: {self.stats['total_hyp_characters']}")
        
        # CER 统计
        if self.stats['cer_list']:
            avg_cer = sum(self.stats['cer_list']) / len(self.stats['cer_list'])
            min_cer = min(self.stats['cer_list'])
            max_cer = max(self.stats['cer_list'])
            print(f"\n【字符错误率 (CER)】")
            print(f"  平均 CER: {avg_cer:.2%}")
            print(f"  最低 CER: {min_cer:.2%}")
            print(f"  最高 CER: {max_cer:.2%}")
            print(f"  准确率: {(1 - avg_cer) * 100:.2f}%")
        
        # 每个文件的结果
        print(f"\n【各文件详情】")
        print(f"  {'文件名':<20} {'状态':<8} {'处理时间':<10} {'CER':<10} {'标注说话人':<15} {'识别说话人':<15}")
        print(f"  {'-' * 80}")
        for fr in self.stats['file_results']:
            status = "✓成功" if fr['success'] else "✗失败"
            cer_str = f"{fr['metrics']['cer']:.2%}" if fr['metrics']['cer'] is not None else "-"
            ref_spk = str(fr['reference']['num_speakers']) if fr['reference'] else "-"
            hyp_spk = str(fr['hypothesis']['num_speakers']) if fr['hypothesis'] else "-"
            print(f"  {fr['file_id']:<20} {status:<8} {fr['process_time']:<10.2f} {cer_str:<10} {ref_spk:<15} {hyp_spk:<15}")
        
        print(f"\n{'=' * 80}")
        print(f"                          测试结束")
        print(f"{'=' * 80}")

    def test_all(self):
        """测试所有文件"""
        audio_files = sorted(list(self.wav_dir.glob("*.flac"))) + sorted(list(self.wav_dir.glob("*.wav")))
        print(f"找到 {len(audio_files)} 个音频文件")
        
        total_start_time = time.time()
        
        for audio_file in tqdm(audio_files, desc="处理进度"):
            self.test_single_file(audio_file)
        
        # 保存统计结果
        summary_file = self.output_dir / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        print(f"\n统计结果已保存到: {summary_file}")
        
        # 打印总结
        self.print_summary(total_start_time)


def main():
    parser = argparse.ArgumentParser(description="使用 API 测试 AISHELL-4")
    parser.add_argument("--test-dir", default="../AISHELL-4-test", help="测试集目录")
    parser.add_argument("--output-dir", default="./api_test_results", help="输出目录")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API 基础 URL")
    parser.add_argument("--username", default="1", help="登录用户名")
    parser.add_argument("--password", default="lch123456", help="登录密码")
    parser.add_argument("--single-file", help="只测试单个文件")

    args = parser.parse_args()

    tester = AISHELL4APITester(
        test_dir=args.test_dir,
        output_dir=args.output_dir,
        api_base_url=args.api_url,
        username=args.username,
        password=args.password
    )

    # 登录
    if not tester.login():
        print("无法继续，退出")
        return

    total_start_time = time.time()

    if args.single_file:
        audio_path = Path(args.test_dir) / "test" / "wav" / f"{args.single_file}.flac"
        if not audio_path.exists():
            audio_path = audio_path.with_suffix(".wav")
        if audio_path.exists():
            tester.test_single_file(audio_path)
        else:
            print(f"文件不存在: {args.single_file}")
    else:
        tester.test_all()
    
    # 打印总结
    if not args.single_file:
        tester.print_summary(total_start_time)


if __name__ == "__main__":
    main()
