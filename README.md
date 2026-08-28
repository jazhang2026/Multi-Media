# Multi-Media
 All multi media projects

 **归真** 是我与 Deepseek AI 一起创作的小说. 使用 Edge TTS 生成音频， ChatGPT Images 和 Gemini 2.5 Image 生成 图像, MoviePy 合成视频.
 
 视频链接：
 https://www.youtube.com/@jazhang-b7x


## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install edge-tts moviepy

edge-tts --list-voices

edge-tts --list-voices | grep "zh-CN"


edge-tts --file story.txt --voice zh-CN-XiaoxiaoNeural --write-media story.mp3
edge-tts --file "chpt.txt" --voice zh-CN-YunyangNeural --write-media chpt.mp3
```

Run this from Multi-Media/归真: 
Parallel processing, run TTS for all chapters at once
```bash
source ../.venv/bin/activate
 
seq 4 40 | xargs -P 10 -I {} bash -c 'cd "{}" && echo "Processing {}" && edge-tts --file chpt.txt --voice zh-CN-YunyangNeural --write-media chpt.mp3 && echo "{} OK" || echo "{} FAILED"'
```

ChatGPT Images 生成 图像。

## Usage

```bash
source .venv/bin/activate
python3 make_video.py 1/video_config.json
```

Parallel processing, run TTS for all chapters at once
```bash
source .venv/bin/activate

seq 4 6 | xargs -P 3 -I {} 
bash -c 'echo "Start {}" && python3 make_video.py {}/video_config.json > /dev/null 2>&1 && echo "{
} OK" || echo "{} FAILED"'
```

# 视频里面加字幕

## 最简单的方法是：

用 OpenAI Whisper 给音频生成带时间轴的字幕文件（.srt）。
用 FFmpeg 把字幕烧录进视频。
1. 安装 Whisper
```bash
source .venv/bin/activate
pip install openai-whisper
```
### 2. 生成字幕文件
```bash
whisper chpt1.mp3 --model small --language Chinese --output_format srt
```
这会生成 chpt1.srt。

模型大小：tiny 最快但准确度低，base 够用，small 中文效果更好。你的机器跑 small 应该没问题，就是慢一点。

### 3. 把字幕烧录到视频
```bash
ffmpeg -i story_video.mp4 \
  -vf "subtitles=chpt1.srt:force_style='FontName=Noto Sans CJK SC,FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=50'" \
  -c:a copy \
  story_video_subtitled.mp4
```
### 4. 中文字体显示问题
如果字幕显示为方框或乱码，说明 FFmpeg 找不到合适的中文字体。可以：

安装系统字体：
```bash
sudo apt install fonts-noto-cjk
```
或者在 FFmpeg 命令里指定字体文件路径：
```bash
ffmpeg -i story_video.mp4 \
  -vf "subtitles=chpt1.srt:force_style='FontName=/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc,FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=50'" \
  -c:a copy \
  story_video_subtitled.mp4
```

### 提醒
edge-tts 只生成音频，不带时间信息，所以必须用 Whisper 这类工具给字幕打时间戳。
如果你想上传到 YouTube 并让 YouTube 自动生成/识别字幕，也可以只上传不带字幕的视频，YouTube 会自动生成。但自己烧录进去更可控。
需要我帮你写一个 add_subtitles.py 脚本，把这三步合并成一条命令吗？

## Created add_subtitles.py.

### Usage
Run from the 归真 directory:

```bash
source ../.venv/bin/activate
python3 add_subtitles.py \
  --video 1/story_video.mp4 \
  --audio 1/chpt.mp3 \
  --output 1/story_video_subtitled.mp4
```
