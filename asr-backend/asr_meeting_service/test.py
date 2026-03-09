import ffmpeg

# 测试基础功能（获取ffmpeg版本，需系统已安装ffmpeg可执行文件）
try:
    # 执行ffmpeg -version命令（需先在系统安装ffmpeg）
    result = ffmpeg.probe("")  # 空参数仅测试导入和基础调用，非实际解析
except ffmpeg.Error as e:
    # 即使报错（因无输入文件），也说明包已正常加载
    print("ffmpeg-python 导入成功，核心模块可用")
    print("错误原因（预期）：", e.stderr.decode('utf-8')[:100])  # 仅打印前100字符
except Exception as e:
    print("ffmpeg-python 加载异常：", str(e))
else:
    print("ffmpeg-python 完全正常")