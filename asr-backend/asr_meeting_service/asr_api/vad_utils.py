"""
VAD (Voice Activity Detection) 数据清洗模块
用于提升声纹质量：去除静音、降噪、提取纯净人声
"""
import os
import numpy as np
import wave
import struct
import subprocess
import tempfile


def vad_clean_audio(input_audio_path, output_audio_path=None, vad_mode='strict'):
    """
    VAD 数据清洗主函数
    
    :param input_audio_path: 输入音频路径
    :param output_audio_path: 输出音频路径（如果为 None，则覆盖原文件）
    :param vad_mode: VAD 模式 ('strict' 严格 / 'normal' 标准 / 'loose' 宽松)
    :return: 清洗后的音频路径，如果失败则返回原路径
    """
    try:
        print(f"[VAD] 开始清洗音频: {input_audio_path}")
        
        # 如果没有指定输出路径，生成临时输出路径
        if output_audio_path is None:
            temp_dir = os.path.dirname(input_audio_path)
            base_name = os.path.splitext(os.path.basename(input_audio_path))[0]
            output_audio_path = os.path.join(temp_dir, f"{base_name}_cleaned.wav")
        
        # 方案1：使用 ffmpeg 的 silenceremove 滤波器（推荐，无需额外依赖）
        success = _vad_clean_ffmpeg(input_audio_path, output_audio_path, vad_mode)
        
        if success:
            print(f"[VAD] ✅ 清洗完成: {output_audio_path}")
            return output_audio_path
        else:
            print(f"[VAD] ⚠️ ffmpeg VAD 清洗失败，使用原音频")
            return input_audio_path
            
    except Exception as e:
        print(f"[VAD] ❌ VAD 清洗异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return input_audio_path


def _vad_clean_ffmpeg(input_path, output_path, vad_mode='strict'):
    """
    使用 ffmpeg 的 silenceremove 滤波器进行 VAD 清洗
    
    原理：
    - 检测音频中的静音段
    - 去除静音段，保留人声段
    - 可选：添加静音前后填充，避免切得太碎
    
    :param vad_mode: 
        - 'strict': 严格模式，阈值低，去除更多静音
        - 'normal': 标准模式，平衡
        - 'loose': 宽松模式，阈值高，保留更多内容
    """
    try:
        # VAD 参数配置
        vad_params = {
            'strict': {
                'threshold': '-45dB',    # 静音检测阈值（越低越严格）
                'duration': '0.2',       # 静音持续时间（秒），超过此时长视为静音
                'pad': '0.1',            # 人声前后保留的静音填充（秒）
            },
            'normal': {
                'threshold': '-40dB',
                'duration': '0.3',
                'pad': '0.15',
            },
            'loose': {
                'threshold': '-35dB',
                'duration': '0.5',
                'pad': '0.2',
            }
        }
        
        params = vad_params.get(vad_mode, vad_params['normal'])
        
        # ffmpeg silenceremove 滤波器参数
        # start_periods=1: 去除开头的静音
        # start_duration/silence/start_threshold: 开头静音检测参数
        # stop_periods=-1: 处理整个音频
        # stop_duration/stop_threshold: 中间静音检测参数
        # stop_silence: 保留的静音填充
        cmd = [
            'ffmpeg',
            '-y',                          # 覆盖输出文件
            '-i', input_path,              # 输入文件
            '-af', f"""
                silenceremove=
                    start_periods=1:
                    start_duration=0.1:
                    start_threshold={params['threshold']}:
                    stop_periods=-1:
                    stop_duration={params['duration']}:
                    stop_threshold={params['threshold']}:
                    stop_silence={params['pad']}
            """.replace('\n', '').replace(' ', ''),
            '-ar', '16000',                # 采样率 16kHz（声纹模型要求）
            '-ac', '1',                    # 单声道
            '-c:a', 'pcm_s16le',           # 16-bit PCM 编码
            output_path
        ]
        
        print(f"[VAD] 执行 ffmpeg 命令: {' '.join(cmd[:10])}...")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            # 验证输出文件
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                original_size = os.path.getsize(input_path)
                cleaned_size = os.path.getsize(output_path)
                reduction = (1 - cleaned_size / original_size) * 100
                print(f"[VAD] 文件大小: {original_size/1024:.1f}KB → {cleaned_size/1024:.1f}KB (减少 {reduction:.1f}%)")
                return True
            else:
                print(f"[VAD] ⚠️ 输出文件为空或不存在")
                return False
        else:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            print(f"[VAD] ❌ ffmpeg 执行失败: {error_msg[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[VAD] ⚠️ VAD 清洗超时，使用原音频")
        return False
    except Exception as e:
        print(f"[VAD] ❌ ffmpeg VAD 清洗异常: {str(e)}")
        return False


def vad_clean_audio_bytes(audio_bytes, sample_rate=16000, vad_mode='strict'):
    """
    对音频字节数据进行 VAD 清洗（用于内存中处理）
    
    :param audio_bytes: 音频字节数据
    :param sample_rate: 采样率
    :param vad_mode: VAD 模式
    :return: 清洗后的音频字节数据
    """
    input_temp = None
    output_temp = None
    try:
        # 创建临时文件
        input_temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        input_temp.write(audio_bytes)
        input_temp.close()
        
        output_temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        output_temp.close()
        
        # 调用 VAD 清洗
        result_path = vad_clean_audio(input_temp.name, output_temp.name, vad_mode)
        
        # 读取结果
        with open(result_path, 'rb') as f:
            cleaned_bytes = f.read()
        
        return cleaned_bytes
        
    finally:
        # 清理临时文件
        for temp_file in [input_temp, output_temp]:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.remove(temp_file.name)
                except:
                    pass


def vad_filter_segments(segments, min_duration=0.5, vad_mode='strict'):
    """
    对分段结果进行 VAD 过滤
    
    :param segments: 分段列表 [{'start': ms, 'end': ms, 'text': str, ...}]
    :param min_duration: 最小有效时长（秒），短于此值的片段将被过滤或合并
    :param vad_mode: VAD 模式
    :return: 过滤后的分段列表
    """
    if not segments:
        return segments
    
    filtered = []
    for seg in segments:
        start_sec = seg.get('start', 0) / 1000.0
        end_sec = seg.get('end', 0) / 1000.0
        duration = end_sec - start_sec
        
        # 保留有效时长 >= min_duration 的片段
        if duration >= min_duration:
            filtered.append(seg)
        elif filtered:
            # 短片段合并到上一个片段
            filtered[-1]['end'] = seg.get('end', filtered[-1]['end'])
            filtered[-1]['text'] = filtered[-1].get('text', '') + ' ' + seg.get('text', '')
    
    print(f"[VAD] 分段过滤: {len(segments)} → {len(filtered)} (过滤 {len(segments) - len(filtered)} 个短片段)")
    return filtered


def get_audio_duration(audio_path):
    """获取音频时长（秒）"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if result.returncode == 0:
            duration = float(result.stdout.decode('utf-8').strip())
            return duration
    except:
        pass
    return 0


def get_audio_info(audio_path):
    """
    获取音频信息（用于调试）
    :return: {'duration': float, 'sample_rate': int, 'channels': int, 'size_bytes': int}
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration,size',
            '-show_entries', 'stream=sample_rate,channels',
            '-of', 'json',
            audio_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout.decode('utf-8'))
            return info
    except Exception as e:
        print(f"[VAD] 获取音频信息失败: {e}")
    return {}
