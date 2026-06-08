#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的 AISHELL-4 测试脚本
不依赖 Django，直接使用 FunASR
"""

import os
import sys
import json
import argparse
import textgrid
from pathlib import Path
from tqdm import tqdm

# 尝试导入 FunASR
try:
    from funasr import AutoModel
except ImportError:
    print("请先安装 FunASR: pip install funasr")
    sys.exit(1)


class SimpleAISHELL4Tester:
    def __init__(self, test_dir: str, output_dir: str = "./test_results"):
        """
        初始化测试器
        
        Args:
            test_dir: AISHELL-4 测试集目录
            output_dir: 输出结果目录
        """
        self.test_dir = Path(test_dir)
        self.output_dir = Path(output_dir)
        self.wav_dir = self.test_dir / "test" / "wav"
        self.textgrid_dir = self.test_dir / "test" / "TextGrid"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载 FunASR 模型
        print("正在加载 FunASR 模型...")
        self.model = AutoModel(
            model="paraformer-zh",
            vad_model="fsmn-vad",
            punc_model="ct-punc",
            spk_model="cam++",
            device="cpu"  # 使用 cpu，有 GPU 可改为 "cuda"
        )
        print("模型加载完成！")

    def parse_textgrid(self, textgrid_path: str):
        """解析 TextGrid 文件"""
        tg = textgrid.TextGrid.fromFile(textgrid_path)
        annotations = []
        for tier in tg:
            speaker_name = tier.name
            for interval in tier:
                if interval.text.strip():
                    annotations.append({
                        'speaker': speaker_name,
                        'start_time': interval.minTime,
                        'end_time': interval.maxTime,
                        'text': interval.text.strip()
                    })
        annotations.sort(key=lambda x: x['start_time'])
        return annotations

    def transcribe(self, audio_path: str):
        """转录音频"""
        try:
            result = self.model.generate(input=audio_path)
            
            # 解析结果
            segments = []
            if result and len(result) > 0:
                if 'sentence_info' in result[0]:
                    for seg in result[0]['sentence_info']:
                        segments.append({
                            'start_time': seg.get('start', 0),
                            'end_time': seg.get('end', 0),
                            'text': seg.get('text', ''),
                            'speaker': seg.get('spk', 'UNKNOWN')
                        })
            
            return {
                'segments': segments,
                'raw_result': result
            }
        except Exception as e:
            print(f"转录错误: {e}")
            return {'segments': [], 'raw_result': {'error': str(e)}}

    def test_single_file(self, audio_file: Path):
        """测试单个文件"""
        file_id = audio_file.stem
        print(f"\n{'='*60}")
        print(f"处理: {file_id}")
        
        # 读取标注
        textgrid_file = self.textgrid_dir / f"{file_id}.TextGrid"
        annotations = []
        if textgrid_file.exists():
            annotations = self.parse_textgrid(str(textgrid_file))
            print(f"标注段落数: {len(annotations)}")
        
        # 转录
        result = self.transcribe(str(audio_file))
        segments = result['segments']
        print(f"识别段落数: {len(segments)}")
        
        # 保存结果
        output_file = self.output_dir / f"{file_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'file_id': file_id,
                'annotations': annotations,
                'transcription': segments,
                'raw_result': result['raw_result']
            }, f, ensure_ascii=False, indent=2)
        
        print(f"结果保存到: {output_file}")
        return result

    def test_all(self):
        """测试所有文件"""
        audio_files = sorted(list(self.wav_dir.glob("*.flac"))) + sorted(list(self.wav_dir.glob("*.wav")))
        print(f"找到 {len(audio_files)} 个音频文件")
        
        for audio_file in tqdm(audio_files, desc="处理进度"):
            self.test_single_file(audio_file)
        
        print("\n测试完成！")


def main():
    parser = argparse.ArgumentParser(description="AISHELL-4 简化测试")
    parser.add_argument("--test-dir", default="../AISHELL-4-test", help="测试集目录")
    parser.add_argument("--output-dir", default="./test_results", help="输出目录")
    parser.add_argument("--single-file", help="只测试单个文件")
    
    args = parser.parse_args()
    
    tester = SimpleAISHELL4Tester(
        test_dir=args.test_dir,
        output_dir=args.output_dir
    )
    
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


if __name__ == "__main__":
    main()
