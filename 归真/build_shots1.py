#!/usr/bin/env python3
"""Build 1/shots.json from 1/tts.txt (exact text) with scene mapping.

Scene images are generated per-scene (one image reused across shots in that
scene). Prompts embed character appearance from characters.json for consistency.
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
CHARS = json.loads((BASE / "characters.json").read_text(encoding="utf-8"))

VOICE = {
    "旁白": "zh-CN-YunyangNeural",
    "石头": "zh-CN-XiaoyiNeural",
    "王婶": "zh-CN-YunxiaNeural",
    "母亲": "zh-CN-XiaoxiaoNeural",
    "刘医生": "zh-CN-YunxiNeural",
}

# scene -> (prompt, gen_video)
SCENES = {
    "片头": ("1960s Chinese mountain village in early spring, rolling green hills, a distant dirt road, soft morning light, no text", False),
    "场景一": (f"{CHARS['石头(童年)']['appearance']}, lying on his stomach on a flat green rock on a hillside, watching a long line of ants marching on the stone, early spring afternoon", True),
    "场景二": ("a rocky hilltop at dusk, a boy crouching beside a large grey rock, a tiny glowing silver insect trapped in a shadowed rock crevice, faint silver light", True),
    "场景三": ("interior of a 1960s Chinese commune clinic, a young barefoot doctor examining a feverish boy lying on a wooden bed, dim oil lamp light", True),
    "场景四": ("surreal dreamlike vision of a body dissolving into warm flowing light like melting sugar, fever hallucination, heat and cool currents, dreamlike", True),
    "场景五": ("a boy lying with eyes closed on a clinic bed, a warm golden glow traveling along his arms and body like meridians, gentle light", True),
    "场景六": (f"{CHARS['石头(童年)']['appearance']}, sitting under a jujube tree in a rural courtyard at dusk, one hand on his waist, deep quiet feeling", True),
    "场景七": ("a hillside green rock at sunset, cooking smoke rising from a village below, a boy standing on the slope, distant rocky ridge, warm golden light", True),
    "片尾": ("a distant small figure walking down a mountain path at sunset toward a village with smoke rising, cinematic wide shot", False),
}

# (scene, speaker, text)
UNITS = [
    ("片头", "旁白", "一九六八年，春。"),
    ("场景一", "旁白", "山坡上的草已经绿了。六岁的石头趴在青石上，下巴枕着交叠的手臂，眼睛一眨不眨地盯着前方。一窝蚂蚁正在搬家。蚂蚁的队伍从石缝里蜿蜒而出，每一只都衔着一粒白色的卵。迎面碰上了，触角碰一碰，便各自错开，像村口那条土路上两个熟人打招呼。"),
    ("场景一", "旁白", "他不知道自己为什么能看这么久。看蚂蚁的时候，他觉得自己的身体也跟着安静下来。像一盆水，放着放着，水面不动了，泥沙沉下去，水变得透亮。"),
    ("场景一", "王婶", "这孩子怕是天生就静。"),
    ("场景一", "旁白", "母亲摸着石头的脑袋，笑了笑。"),
    ("场景一", "母亲", "我们石头就是性子静。"),
    ("场景一", "旁白", "石头不知道什么叫性子静。他只知道，看蚂蚁看得久了，整个人像被清水洗了一遍。"),
    ("场景二", "旁白", "太阳往西歪的时候，石头的鼻子里闻到了一股焦糊味。不是烧秸秆的味道。那股味道更淡，像有什么东西被烤过了头，正在变焦、变脆。"),
    ("场景二", "旁白", "石头从青石上爬起来，往山坡上走。往左走，味道变淡。往右走，味道变淡。只有往上，那味道越来越浓。"),
    ("场景二", "旁白", "六岁的孩子不知道什么叫直觉。他只知道，有什么东西在上面。"),
    ("场景二", "旁白", "山坡顶上是一片乱石岗。石头绕过那块最大的山岩，蹲了下来。山岩背阴的石缝里，夹着一团银色的光。不是太阳的反光。那光是从石头缝里自己发出来的，银色的，像月光落在水面上。"),
    ("场景二", "旁白", "那不是一团光，是一只虫子。比苍蝇大不了多少。翅膀是透明的，身体是深灰色，和石头的颜色几乎一样。"),
    ("场景二", "旁白", "虫子的半边身体浸在石缝里积下的水里，翅膀贴着湿漉漉的石面，挣不开。银光随着它的挣扎一明一灭。"),
    ("场景二", "旁白", "石头慢慢伸出手，捏住那只虫子的翅膀，轻轻往外拉。虫子的身体从石缝里脱出来的一瞬间，虎口一麻，像被火烧过的针扎了一下。"),
    ("场景二", "旁白", "石头低头看，虎口上多了两个极细小的红点，已经开始渗血。银色的光剧烈地闪了一下，熄灭了。虫子从他指间滑落，掉在碎石上，迅速变暗，从深灰变成枯黄，和周围的碎石再无分别。"),
    ("场景二", "旁白", "石头上沾着一点银色的粉末，在暮色里闪着微弱的光。石头用另一只手去擦，粉末却渗进了皮肤，消失了。"),
    ("场景二", "旁白", "然后他开始发烧。"),
    ("场景三", "旁白", "石头被母亲背到公社卫生院，已经烧得迷糊了。四里山路，母亲是一路小跑着下来的。父亲在生产队上工，赶不回来。母亲用一条旧被单把他捆在背上，深一脚浅一脚地往山下跑。"),
    ("场景三", "旁白", "卫生院的赤脚医生刘医生，三十来岁，给石头量了体温，看了舌苔，翻了眼皮。"),
    ("场景三", "刘医生", "可能是急性脑膜炎。"),
    ("场景三", "旁白", "母亲的脸色一下子变白了。"),
    ("场景三", "刘医生", "也可能是被什么毒虫咬了。你们那山上，开春了蛇虫多。先观察。"),
    ("场景三", "旁白", "石头躺在硬板床上，身上盖着母亲的外衣。他听见母亲在外面跟刘医生说话，声音压得很低。"),
    ("场景三", "母亲", "家里还有几斤粮票。"),
    ("场景三", "刘医生", "先不说这个。"),
    ("场景三", "旁白", "石头嘴唇干裂，喉咙像塞了一团棉花。他想说话，却张不开嘴。他在心里说："),
    ("场景三", "石头", "妈，我没事。"),
    ("场景三", "旁白", "后来他就什么都不知道了。"),
    ("场景四", "旁白", "那三天里，他觉得自己像一棵被连根拔起的树，又重新被栽进土里。"),
    ("场景四", "旁白", "先是全身发烫，热从皮肤往里走，走过肌肉，走过骨头，一直走到最里面。他觉得自己整个人都化掉了。不是消失，是化开，像糖化在水里。"),
    ("场景四", "旁白", "然后是冷。冷从最里面往外走，走过骨头，走过肌肉，走过皮肤。冷走过的地方，原来的东西被冲掉了，新的东西长出来。"),
    ("场景四", "旁白", "很多年后，他找到一句话来形容那个感觉——脱胎换骨。"),
    ("场景五", "旁白", "不是睁开眼睛的醒。他闭着眼睛，但能感觉到自己躺在那里。身体是热的，不是发烧的那种热，像灶膛里的火，不急不躁地燃着。"),
    ("场景五", "旁白", "他感觉到那股热有自己的路。从虎口开始，被虫子扎过的地方，有一个很小的点，比周围都热。热从那里出发，沿着一条线往上走，走过手腕，走过小臂，走到肩膀，然后分两路。一路往上，走脖子，走头顶，再降下来。另一路往下，走胸口，走肚子，走腰。"),
    ("场景五", "旁白", "热走到哪里，哪里就舒服。像水管被堵住了，忽然通了。"),
    ("场景五", "旁白", "三天的烧退下去以后，石头的身体变轻了。走路的时候，脚抬起来不那么费劲了。他能看清对面山坡上那棵歪脖子松树的松针，能听见村口狗叫、风过山梁、枣树枝条轻轻相碰的声音。"),
    ("场景六", "旁白", "石头坐在枣树下。傍晚太阳落下去，热也跟着走了。凉从脚底往上走，走到腰的时候，他忽然觉得腰那个地方有什么东西在动。很轻很轻的跳，像另一颗心脏。比自己的心跳慢得多，但很深。"),
    ("场景六", "旁白", "他把手放在腰上，感觉那个跳动。手放上去，跳动就从手心传上来，沿着手臂，一直传到胸口，传到喉咙，传到头顶。整个人像一口钟，被轻轻敲了一下，嗡嗡地响。"),
    ("场景七", "旁白", "石头又来到山坡上那块青石前。蚂蚁的巢穴已经搬完了，原来的洞口空荡荡的，只有几粒沙子。"),
    ("场景七", "旁白", "他想起那只虫子。银色的光，虎口上的一麻，两个针尖大小的红点。"),
    ("场景七", "旁白", "他把右手翻过来，看虎口。红点已经看不见了，皮肤光滑，和其他地方没什么两样。"),
    ("场景七", "旁白", "石头把手心贴在腰上。那个跳动还在，慢，但很深。像一口井，井底有水，水面平平静静的，但水是活的。"),
    ("场景七", "旁白", "山坡下面的村子里，炊烟又开始升起来了。石头深吸一口气。"),
    ("场景七", "旁白", "春天的空气里，有泥土的腥气，有青草的涩味，有桃花若有若无的甜，有牛棚里传来的粪味，有灶膛里烧松枝的焦香。"),
    ("场景七", "旁白", "他把这些味道一层一层分开，闻得很清楚。气吸进去，从鼻子往下走，走到肚子。在肚子里停了一下，然后往外走。"),
    ("场景七", "旁白", "一吸一呼之间，腰上那个跳动，刚好跳了一下。"),
    ("场景七", "旁白", "太阳正从山梁上落下去。乱石岗的方向，有风吹过石缝，发出细细的声响，像有什么东西在叹息。"),
    ("场景七", "旁白", "石头没有回头，往山下走去。他一步一步走着，腰里的跳动，也慢慢和脚步合上了。"),
    ("片尾", "旁白", "第一章 完。"),
]


def main():
    shots = []
    for scene, speaker, text in UNITS:
        prompt, gen_video = SCENES[scene]
        shots.append({
            "scene": scene,
            "speaker": speaker,
            "voice": VOICE[speaker],
            "text": text,
            "image": None,
            "prompt": prompt,
            "gen_video": gen_video,
        })

    for i, s in enumerate(shots, start=1):
        s["id"] = i

    out = BASE / "1" / "shots.json"
    out.write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")

    audio = "".join(s["text"] for s in shots)
    tts = (BASE / "1" / "tts.txt").read_text(encoding="utf-8")
    stripped = "".join(l.strip() for l in tts.splitlines() if l.strip()).replace('"', '').replace('“', '').replace('”', '').replace('‘', '').replace('’', '')
    full = stripped + "第一章 完。"
    (BASE / "1" / "tts_full.txt").write_text(full, encoding="utf-8")

    def n(t): return re.sub(r"\s", "", t)
    print("shots:", len(shots))
    print("text equal:", n(audio) == n(full), "chars:", len(n(audio)))
    if n(audio) != n(full):
        import difflib
        sm = difflib.SequenceMatcher(None, n(audio), n(full))
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "equal":
                print(tag, repr(n(audio)[i1:i2]), repr(n(full)[j1:j2]))


if __name__ == "__main__":
    main()
