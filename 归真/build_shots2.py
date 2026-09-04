#!/usr/bin/env python3
"""Rebuild 2/shots.json: finer-grained scenes, character-rich prompts,
more characters on screen. Text/speaker/voice unchanged from tts.txt."""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
CHARS = json.loads((BASE / "characters.json").read_text(encoding="utf-8"))

SHI = CHARS["石头(童年)"]["appearance"]
MU = CHARS["母亲"]["appearance"]
WS = CHARS["王婶"]["appearance"]
JG = CHARS["建国"]["appearance"]
JJ = CHARS["建军"]["appearance"]
ZLS = CHARS["周老师"]["appearance"]
YY = CHARS["爷爷"]["appearance"]
FQ = CHARS["父亲"]["appearance"]

# granular scene -> (prompt, gen_video)
SCENES = {
    "片头": ("a 1960s Chinese mountain village in early summer, green hills, dirt road, bright daylight", False),
    "村口王婶": (f"{WS} meeting {SHI} at the village entrance, patting his head, {MU} beside them, earthen wall and wooden gate", True),
    "陈家小院吃饭": (f"{SHI} eating porridge at a wooden table in a rural courtyard, {MU} ladling thick porridge into his bowl, jujube tree, summer morning", True),
    "打猪草": (f"a six-year-old boy in an old but clean cotton shirt and his older teenage brother with fair light skin cutting pig grass on a summer hillside, a thin pig in the distance, wicker baskets, bright afternoon light", True),
    "虎口发热": (f"close-up of {SHI}'s right hand, the thumb-index web glowing faintly warm, tiny red dots on the skin, dusk hillside", True),
    "兄弟对话": (f"a six-year-old boy and his older teenage brother with fair light skin standing on a grassy hillside, the brother holding a sickle, boy looking at his own hand", True),
    "热如河": (f"{SHI} standing on a hillside at dusk, a faint warm line of light tracing down his arm like a river, distant village below", True),
    "祠堂入学": (f"inside a 1960s Chinese ancestral hall used as a one-room school, {ZLS} writing the three characters 人口手 in black brush strokes on a black wooden board, {SHI} sitting at a plank desk", True),
    "师生问答": (f"{ZLS} and {SHI} outside the ancestral hall, teacher handing a twig, boy writing the character 人 on the ground with his finger", True),
    "放学路上": (f"{ZLS} talking to {MU} on a village road at dusk, {SHI} standing nearby, earthen houses", False),
    "山坡摔倒": (f"{SHI} lying on a grassy hillside after falling with a basket of pig grass, looking up at the first stars, deep blue dusk sky", True),
    "爷爷临终": (f"{YY} lying on a heated brick bed in a dim rural room, holding {SHI}'s hand, {MU} standing at the door, winter afternoon light", True),
    "灶房": (f"{MU} cooking at a clay stove in a rural kitchen, firelight, {SHI} standing at the door, bare jujube tree outside", False),
    "上山挖坟": (f"an old thin man with white hair and a teenage boy with black hair and light skin digging a grave with hoes on a winter mountain slope beside an old tomb, bare trees, cold morning light", False),
    "下山对话": (f"{JJ} and {SHI} walking down a mountain path at dusk, older brother glancing at the boy, quiet", False),
    "年夜饭": (f"a Chinese New Year's Eve family dinner around a table, an old father with white hair, a gentle mother, a six-year-old boy, a teenage brother with light tan skin and black hair, a strong young brother, a bowl of stew with a few slices of meat, warm bright lamp light, snowy jujube tree outside", True),
    "乱石岗": (f"{SHI} standing on a snow-covered rocky hillside at early spring, gazing toward a distant rock ridge, right hand raised to look at his palm", True),
    "片尾": ("a snowy jujube tree in a rural courtyard at night, warm light from a window, falling snow", False),
}

# shot id -> granular scene name
ID_SCENE = {}
for i in range(1, 107):
    if i == 1: ID_SCENE[i] = "片头"
    elif i <= 4: ID_SCENE[i] = "村口王婶"
    elif i <= 9: ID_SCENE[i] = "陈家小院吃饭"
    elif i <= 13: ID_SCENE[i] = "打猪草"
    elif i <= 17: ID_SCENE[i] = "虎口发热"
    elif i <= 24: ID_SCENE[i] = "兄弟对话"
    elif i == 25: ID_SCENE[i] = "热如河"
    elif i <= 32: ID_SCENE[i] = "祠堂入学"
    elif i <= 51: ID_SCENE[i] = "师生问答"
    elif i <= 59: ID_SCENE[i] = "放学路上"
    elif i <= 64: ID_SCENE[i] = "山坡摔倒"
    elif i <= 76: ID_SCENE[i] = "爷爷临终"
    elif i <= 81: ID_SCENE[i] = "灶房"
    elif i <= 84: ID_SCENE[i] = "上山挖坟"
    elif i <= 92: ID_SCENE[i] = "下山对话"
    elif i <= 101: ID_SCENE[i] = "年夜饭"
    elif i <= 105: ID_SCENE[i] = "乱石岗"
    else: ID_SCENE[i] = "片尾"

KEY_VIDEO = {14, 15, 25, 31, 49, 62, 71, 73, 102, 105}


def main():
    p = BASE / "2" / "shots.json"
    shots = json.loads(p.read_text(encoding="utf-8"))
    for s in shots:
        scene = ID_SCENE[s["id"]]
        prompt, gen = SCENES[scene]
        s["scene"] = scene
        s["prompt"] = prompt
        s["gen_video"] = s["id"] in KEY_VIDEO
        s.pop("image", None)
        s.pop("image_url", None)
        s.pop("video", None)
    p.write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")

    # verify text equality
    audio = "".join(s["text"] for s in shots)
    tts = (BASE / "2" / "tts.txt").read_text(encoding="utf-8")
    stripped = "".join(l.strip() for l in tts.splitlines() if l.strip()).replace('"', '').replace('“', '').replace('”', '').replace('‘', '').replace('’', '')
    full = stripped + "第二章 完。"
    (BASE / "2" / "tts_full.txt").write_text(full, encoding="utf-8")

    def n(t): return re.sub(r"\s", "", t)
    print("shots:", len(shots), "scenes:", len(set(s["scene"] for s in shots)))
    print("text equal:", n(audio) == n(full), "chars:", len(n(audio)))
    print("gen_video ids:", [s["id"] for s in shots if s["gen_video"]])


if __name__ == "__main__":
    main()
