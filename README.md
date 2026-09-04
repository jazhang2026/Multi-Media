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

seq 13 15 | xargs -P 3 -I {} bash -c 'echo "Start $1" && python3 make_video.py "$1/video_config.json" > /dev/null 2>&1 && echo "$1 OK" || echo "$1 FAILED"' _ {}

seq 1 12 | xargs -P 3 -I {} bash -c 'echo "Start $1" && python3 make_video_with_subtitles.py "$1/video_config.json" --keep-srt > /dev/null 2>&1 && echo "$1 OK" || echo "$1 FAILED"' _ {}

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
source .venv/bin/activate
whisper 1/chpt.mp3 --model small --language Chinese --output_format srt --output_dir 1
```
这会生成 1/chpt.srt。

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
  --video 1/chpt1.mp4 \
  --audio 1/chpt.mp3 \
  --text 1/tts.txt \
  --model medium \
  --output 1/chpt1_subtitled.mp4

python3 add_subtitles.py \
  --video 1/story_video.mp4 \
  --audio 1/chpt.mp3 \
  --output 1/story_video_subtitled.mp4
```


A. 一次性准备（全局一致性）
人物档案 归真/characters.json：常驻人物固定外貌描述 + Edge-TTS 音色（石头童年 XiaoyiNeural、陈静远成年 YunxiNeural、母亲 XiaoxiaoNeural、王婶 YunxiaNeural、建国/建军 YunxiNeural、周老师/父亲/曹副县长 YunjianNeural、周小梅 XiaoxiaoNeural 等）。
场景档案：固定风格后缀＝水墨水彩（ink-wash watercolor illustration, muted earthy tones, 1960s Chinese countryside, consistent character design），常用场景关键词统一。
音色表写入 gen_audio.py 的 VOICE，全书统一。
B. 每章流程（第 N 章）
文本准备（已有）：N/chpt.txt → N/script.txt → N/tts.txt。
分镜头：生成 N/shots.json（scene / speaker / text / voice / image / prompt / gen_video）；文本逐字来自 N/tts.txt，末尾加「第N章 完。」，并生成 N/tts_full.txt。
生成图片：Agnes 按场景生成水墨水彩图 → N/images_gen/scene_XX.png（每场景 1 张，镜头复用）。生成后你自己看文件确认整体效果（不做联系表）。
生成动态视频片段：仅对关键/玄幻镜头（银光虫、幻象、热流走经络、静坐、乱石岗等，每章约 5–10 段）用 Agnes agnes-video 做 image-to-video → N/output/scene_XX.mp4。
分角色配音：gen_audio.py --chapter N → N/audio/shot_XX.mp3（旁白 -8%~-12%，配合镜头间停顿，目标 10–15 分钟）。
合成：assemble.py --chapter N → N/chptN_ai.mp4。静态图不加变焦（保持静态），动态只来自 Agnes 视频片段。
同步字幕：make_srt_from_shots.py --chapter N → N/chptN_ai_synced.srt（按每段配音时长精确对时，字幕与语音同步）。
烧录字幕：→ N/chptN_ai_full_sub.mp4。
背景音乐：统一混入 output000.mp3（音量 18%，循环）→ 最终版 N/chptN_ai_full_sub_bgm.mp4。
时长检查：若 < 10 分钟，加大旁白停顿或放慢语速，落在 10–15 分钟。
C. 执行顺序
先重做第 1 章（现有 9:23 不够 10 分钟，且要统一到水墨水彩 + 人物/音色档案 + 动态片段 + 音乐）。
每章流程：出图 → 你自己看 → 确认 → 做视频。
全部章节用 output000.mp3 作背景音乐。
确认无误的话，我就从第 1 章开始执行（先建 characters.json，再出图给你看）。