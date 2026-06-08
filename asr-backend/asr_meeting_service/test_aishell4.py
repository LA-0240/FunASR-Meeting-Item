#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AISHELL-4 测试集评估脚本
使用 FunASR 对 AISHELL-4 测试集进行语音识别和说话人分离
"""

import os
import sys
import json
import argparse
import textgrid
import soundfile as sf
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

# 添加当前目录添加到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asr_meeting_service.settings")
import django
django.setup()

from asr_api.models import asr_model, voiceprint_model


class AISHELL4Evaluator:
    def __init__(self, test_dir: str, output_dir: str = "./aishell4_results"):
        """
        初始化评估器
        
        Args:
            test_dir: AISHELL-4 测试集目录
            output_dir: 输出结果目录
        """
        self.test_dir = Path(test_dir)
        self.output_dir = Path(output_dir)
        self.wav_dir = self.test_dir / "test" / "wav"
        self.textgrid_dir = self.test_dir / "test" / "TextGrid"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rttm_output_dir = self.output_dir / "rttm"
        self.rttm_output_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_output_dir = self.output_dir / "transcripts"
        self.transcript_output_dir.mkdir(parents=True, exist_ok=True)

    def parse_textgrid(self, textgrid_path: str):
        """
        解析 TextGrid 文件获取标注信息
        
        Args:
            textgrid_path: TextGrid 文件路径
        
        Returns:
            dict: 包含说话人、开始时间、结束时间和文本的列表
        """
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
        
        # 按开始时间排序
        annotations.sort(key=lambda x: x['start_time'])
        return annotations

    def parse_rttm(self, rttm_path: str):
        """
        解析 RTTM 文件
        
        Args:
            rttm_path: RTTM 文件路径
        
        Returns:
            list: 说话人信息列表
        """
        speakers = []
        with open(rttm_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if parts[0] == 'SPEAKER':
                    speakers.append({
                        'file_id': parts[1],
                        'start_time': float(parts[3]),
                        'duration': float(parts[4]),
                        'speaker': parts[7]
                    })
        return speakers

    def transcribe_audio(self, audio_path: str):
        """
        使用 FunASR 转录音频
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            dict: 转录结果
        """
        try:
            # 读取音频
            audio_path = str(audio_path)
            print(f"正在处理: {os.path.basename(audio_path)}")
            
            # 调用 FunASR 模型
            result = asr_model(audio_path)
            
            # 解析结果
            segments = []
            if 'sentence_info' in result:
                sent_info = result['sentence_info']
                sent_info_list = sent_info if isinstance(sent_info, list) else [sent_info]
                for seg in sent_info_list:
                    segments.append({
                        'start_time': seg.get('start', 0),
                        'end_time': seg.get('end', 0),
                        'text': seg.get('text', ''),
                        'speaker': seg.get('spk', 'UNKNOWN')
                    })
            elif 'text' in result:
                segments.append({
                    'start_time': 0,
                    'end_time': 0,
                    'text': result.get('text', ''),
                    'speaker': 'UNKNOWN'
                })
            
            return {
                'segments': segments,
                'raw_result': result
            }
        except Exception as e:
            print(f"转录 {audio_path} 错误: {e}")
            return {'segments': [], 'raw_result': {'error': str(e)}}

    def save_rttm(self, file_id: str, segments: list, rttm_path: str):
        """
        保存结果为 RTTM 格式
        
        Args:
            file_id: 文件 ID
            segments: 分段列表
            rttm_path: RTTM 文件路径
        """
        with open(rttm_path, 'w', encoding='utf-8') as f:
            # 收集所有说话人
            speakers = set()
            for seg in segments:
                speakers.add(seg['speaker'])
            
            # 写入 SPKR-INFO
            for speaker in speakers:
                f.write(f"SPKR-INFO {file_id} 1 <NA> <NA> <NA> UNKNOWN {speaker}\n")
            
            # 写入 SPEAKER
            for seg in segments:
                duration = seg['end_time'] - seg['start_time']
                if duration > 0:
                    f.write(f"SPEAKER {file_id} 1 {seg['start_time']:.2f} {duration:.2f} <NA> <NA> {seg['speaker']}\n")
            
            # 写入 LEXEME (文本)
            for seg in segments:
                duration = seg['end_time'] - seg['start_time']
                if duration > 0 and seg['text']:
                    f.write(f"LEXEME {file_id} 1 {seg['start_time']:.2f} {duration:.2f} {seg['text']} LEX {seg['speaker']}\n")

    def save_transcript(self, file_id: str, segments: list, transcript_path: str):
        """
        保存转录文本
        
        Args:
            file_id: 文件 ID
            segments: 分段列表
            transcript_path: 输出路径
        """
        with open(transcript_path, 'w', encoding='utf-8') as f:
            for seg in segments:
                f.write(f"[{seg['start_time']:.2f} - {seg['end_time']:.2f}\n")
                f.write(f"说话人 {seg['speaker']}: {seg['text']}\n\n")

    def evaluate_single_file(self, audio_file: Path):
        """
        评估单个音频文件
        
        Args:
            audio_file: 音频文件路径
        
        Returns:
            dict: 评估结果
        """
        file_id = audio_file.stem
        print(f"\n{'='*60}")
        print(f"处理文件: {file_id}")
        
        # 获取对应的标注文件
        textgrid_file = self.textgrid_dir / f"{file_id}.TextGrid"
        rttm_file = self.textgrid_dir / f"{file_id}.rttm"
        
        # 读取标注
        annotations = []
        if textgrid_file.exists():
            annotations = self.parse_textgrid(str(textgrid_file))
            print(f"标注段落数: {len(annotations)}")
        
        # 进行转录
        result = self.transcribe_audio(audio_file)
        segments = result['segments']
        print(f"识别段落数: {len(segments)}")
        
        # 保存结果
        rttm_output = self.rttm_output_dir / f"{file_id}.rttm"
        self.save_rttm(file_id, segments, str(rttm_output))
        
        transcript_output = self.transcript_output_dir / f"{file_id}.txt"
        self.save_transcript(file_id, segments, str(transcript_output))
        
        # 保存原始结果
        raw_result_path = self.transcript_output_dir / f"{file_id}.json"
        with open(raw_result_path, 'w', encoding='utf-8') as f:
            json.dump({
                'file_id': file_id,
                'annotations': annotations,
                'transcription': segments,
                'raw_result': result['raw_result']
            }, f, ensure_ascii=False, indent=2)
        
        return {
            'file_id': file_id,
            'annotation_count': len(annotations),
            'transcription_count': len(segments),
            'rttm_path': str(rttm_output),
            'transcript_path': str(transcript_output)
        }

    def evaluate_all(self):
        """
        评估整个测试集
        """
        print("="*60)
        print("开始评估 AISHELL-4 测试集")
        print("="*60)
        
        # 获取所有音频文件
        audio_files = sorted(list(self.wav_dir.glob("*.flac"))) + sorted(list(self.wav_dir.glob("*.wav")))
        print(f"找到 {len(audio_files)} 个音频文件")
        
        results = []
        for audio_file in tqdm(audio_files, desc="处理进度"):
            result = self.evaluate_single_file(audio_file)
            results.append(result)
        
        # 保存汇总结果
        summary_path = self.output_dir / "summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_files': len(results),
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*60)
        print(f"评估完成！结果保存在: {self.output_dir}")
        print(f"  - RTTM 文件: {self.rttm_output_dir}")
        print(f"  - 转录文本: {self.transcript_output_dir}")
        print(f"  - 汇总结果: {summary_path}")
        print("="*60)
        
        return results


def main():
    parser = argparse.ArgumentParser(description="AISHELL-4 测试集评估")
    parser.add_argument(
        "--test-dir", 
        type=str,
        default="../AISHELL-4-test",
        help="AISHELL-4 测试集目录"
    )
    parser.add_argument(
        "--output-dir", 
        type=str,
        default="./aishell4_results",
        help="输出结果目录"
    )
    parser.add_argument(
        "--single-file",
        type=str,
        default=None,
        help="只处理单个文件（文件名，不含扩展名）"
    )
    
    args = parser.parse_args()
    
    evaluator = AISHELL4Evaluator(
        test_dir=args.test_dir,
        output_dir=args.output_dir
    )
    
    if args.single_file:
        # 处理单个文件
        audio_path = evaluator.wav_dir / f"{args.single_file}.flac"
        if not audio_path.exists():
            audio_path = evaluator.wav_dir / f"{args.single_file}.wav"
        if audio_path.exists():
            evaluator.evaluate_single_file(audio_path)
        else:
            print(f"文件不存在: {args.single_file}")
    else:
        # 处理整个测试集
        evaluator.evaluate_all()


if __name__ == "__main__":
    main()
