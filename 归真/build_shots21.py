#!/usr/bin/env python3
"""Build 21/shots.json from 21/tts.txt (exact text) with realistic-bright scenes."""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent

VOICE = {
    "旁白": "zh-CN-YunyangNeural",
    "陈静远": "zh-CN-YunxiNeural",
    "周小梅": "zh-CN-XiaoxiaoNeural",
    "曹副县长": "zh-CN-YunjianNeural",
    "老赵": "zh-CN-YunxiNeural",
    "父亲": "zh-CN-YunjianNeural",
    "母亲": "zh-CN-YunxiaNeural",
    "建国": "zh-CN-YunxiNeural",
    "建军": "zh-CN-YunxiNeural",
}

# scene -> (prompt, gen_video)
SCENES = {
    "片头": ("a 1994 Chinese county town street in autumn, bright sunlight, a middle-aged man in a plain suit walking toward a grey government office building, vivid colors", True),
    "场景一": ("a 1994 Chinese government canteen farewell lunch, colleagues raising enamel cups, steam rising from dishes, bright warm indoor light", True),
    "场景二": ("a 1994 Chinese county government office, a fifty-year-old deputy county chief in a dark suit talking to a middle-aged assistant, bright daylight through window", True),
    "场景三": ("a middle-aged man standing by an office window looking out at a grey government courtyard with old locust trees, bright autumn light", True),
    "场景四": ("a busy 1994 Chinese government office desk piled with red-stamped documents, a middle-aged man reviewing papers, bright morning light", False),
    "场景五": ("a 1994 Chinese home at night, a woman sewing a child's pants under a warm lamp, her husband sitting across the table, cozy bright interior", True),
    "场景六": ("a middle-aged man reading a project report at a government office desk, frowning at numbers, bright desk lamp, winter light", True),
    "场景七": ("a deputy county chief and a middle-aged assistant discussing a report across a desk in a government office, bright natural light", True),
    "场景八": ("a government office corridor, a deputy county chief talking to a middle-aged man after a meeting, bright fluorescent light", False),
    "场景九": ("a middle-aged man sitting in a meeting room chair with eyes closed, breathing calmly, documents on a long table, bright window light", True),
    "场景十": ("a 1994 Chinese county hospital emergency room, an old father with a plastered leg on a bed, family around, bright clinical light", True),
    "场景十一": ("an elderly mother carrying a thermos in a hospital corridor, bent back, rough hands, bright daylight", True),
    "场景十二": ("a middle-aged man massaging his old father's leg in a rural brick-bed room, warm afternoon light through a paper window", True),
    "场景十三": ("a Chinese New Year's Eve family dinner in a rural courtyard house, snowy jujube tree outside, warm bright indoor light", True),
    "场景十四": ("a middle-aged man standing before a moss-covered rocky ridge at night, moonlight on grey stone, bright moon", True),
    "场景十五": ("a 1994 Chinese home interior, a wife bathing a small child in a wooden tub, steam rising, husband kneeling beside, warm bright light", True),
    "片尾": ("a snowy jujube tree in a rural courtyard at night, warm light from a window, falling snow, bright moon", False),
}

# (scene, speaker, text)
UNITS = [
    ("片头", "旁白", "一九九四年，秋。"),
    ("场景一", "旁白", "一九九四年秋，陈静远调回县政府办公室，任副主任。调令是县委组织部下的。离开卫生局那天，局里的同事在食堂给他送行。"),
    ("场景一", "老赵", "你是从政研室出去的，现在回来当副主任，算是回家了。"),
    ("场景二", "旁白", "县政府办公室副主任的工作和卫生局完全不同。卫生局管的是一个行业，县政府办公室管的是全县。农业、工业、文教、卫生、民政——每一个副县长的分管领域，办公室都要配合。陈静远主要联系分管文教卫生的曹副县长。"),
    ("场景二", "曹副县长", "你在卫生局干过，又跟省中医院的刘主任学过医，文教卫生这一块你熟。但你现在的岗位不只是医疗卫生，教育、文化、体育，都要管。办公室副主任是协调岗位，不是业务岗位。你要做的是让各部门之间不打架，让文件流转不卡壳，让领导交办的事情有着落。"),
    ("场景三", "旁白", "他在这栋楼里进进出出快十年了。从文教科到县办，从县办到政研室，从政研室到柳河，从柳河到卫生局，现在又回到县办。十年转了一圈，回到原点。但原点不一样了。十年前他是一个刚出校门的大学生，连公文格式都要现学；现在他管着好几个人的办公室，能替副县长分责，多少懂一些医，多少懂一些农，多少懂一些人事。热在身体里走了二十六年，他转了一圈，热也转了一圈。"),
    ("场景四", "旁白", "办公室的工作很忙。每天早晨七点半到办公室，先把当天的文件过一遍，重要的标红，紧急的标三角，涉密的单独放。然后看曹副县长的日程。八点钟曹副县长到办公室，他过去汇报当天的工作安排。"),
    ("场景四", "旁白", "但陈静远发现，忙和忙不一样。以前在卫生局，忙的是业务——这个病人的脉，那个村的卫生室，每一件事都是具体的，看得见的。现在在县政府办公室，忙的是协调——这个部门和那个部门意见不统一，要协调；这个文件几个部门会签，要催办。每一件事都是无形的，看不见的。业务忙是身体累，协调忙是心累。"),
    ("场景五", "周小梅", "你在柳河修路，是看得见的；在卫生局建针灸科，也是看得见的。现在当办公室副主任，做的事都看不见。你觉得不踏实。"),
    ("场景五", "旁白", "陈静远没说话。她说得对。看不见，就不踏实。"),
    ("场景五", "周小梅", "但你想过没有——你写的文件，下面执行了，就变成了看得见的东西。你协调好一个矛盾，两个部门不扯皮了，事情就办成了。这些也是真的。只是不归你一个人。"),
    ("场景六", "旁白", "那年冬天，县里出了一件事。柳河乡的药材种植这几年发展得快，县里决定在柳河建一个药材加工厂，县供销社和乡政府联合投资。项目报到县政府办公室，需要曹副县长签字。"),
    ("场景六", "旁白", "他把报告放下。五百吨。柳河乡去年药材总产量是三百吨。今年最多三百五十吨。五百吨，就是把周边几个乡的药材全拉来也不够。"),
    ("场景七", "曹副县长", "原料供应的数据，你是怎么看出问题的？"),
    ("场景七", "陈静远", "在卫生局的时候下乡调研过柳河的药材种植，对产量有一个大致印象。报告里写的加工能力超过了实际产量，差距太大。"),
    ("场景七", "曹副县长", "这个项目是供销社牵头的，他们很积极。你把意见写下来，我批给他们。"),
    ("场景七", "旁白", "陈静远写了意见。没有说项目不行，只说建议进一步核实原料供应能力，附上了柳河乡近三年药材产量的详细数据。报告转到供销社，供销社主任亲自带队去柳河重新核实，发现实际产量确实只有三百五十吨。项目规模从八十万调整为五十五万，加工能力调整为四百吨，预留了扩产空间。"),
    ("场景七", "旁白", "后来事实证明这个调整是及时的——第二年药材行情波动，产量没增加，如果当初上了八十万的项目，产能闲置一半。"),
    ("场景八", "曹副县长", "小陈，你对数字有一种直觉。这种直觉不是天生的，是你这十几年在各个岗位上跑出来的。"),
    ("场景八", "旁白", "陈静远没接话。他知道那不全是跑出来的，还有一部分是热在身体里走了半辈子走出来的。"),
    ("场景九", "旁白", "办公室的工作不只是看文件。更多的精力花在了协调上。协调是机关里最磨人的活——一件事几个部门都沾边，谁也不愿意牵头；一个文件几个部门都要会签，谁都想改几个字。"),
    ("场景九", "旁白", "他睁开眼睛。办公室还是原来的办公室，文件还是堆在桌上。但他心里不堵了。他想起《道德经》里的话——静胜躁，寒胜热，清静为天下正。机关里的事，急躁没用。该等的等，该催的催。能把心静下来，就是功夫。"),
    ("场景九", "旁白", "他开始在办公室练静坐。不是盘腿打坐，是坐在椅子上，闭目调息片刻。别人以为他在闭目养神，只有他自己知道他在让热走一遍全身。走一圈，心里的烦闷就少一分。走三圈，那些在会上听来的争执就像远处的声音，听得见，但不扰心了。以前是被动走，后来是主动走，现在是在嘈杂中走。事上练出来的静，比打坐练出来的静更稳。"),
    ("场景十", "旁白", "那年冬天，父亲摔了。建国托人把电话打到县政府办公室——爹上枣树捡枣子，脚踩空了，摔了髋骨，刚送到县医院。"),
    ("场景十", "父亲", "你咋来了。建国给你打的电话？说了让他别打。"),
    ("场景十", "周小梅", "髋骨骨折，已经做了外固定，没有生命危险。但伤筋动骨一百天，这么大年纪了，至少要躺三个月，以后能不能站起来走路还不好说。"),
    ("场景十", "父亲", "院子里那棵枣树，今年结的枣子落了一地。我想去捡，脚踩空了。"),
    ("场景十", "旁白", "陈静远看着父亲的背影。父亲老了。肩胛骨从衣服下面高高地凸出来，脖子上的皮肤松了，头发全白了。他想起十七岁那年去县城一中报到，父亲拉板车送他，四十里山路，拉了一路。板车轱辘嘎吱嘎吱响，父亲的背影越来越小，最后拐过街角看不见了。现在父亲躺在病床上，左腿不能动了。"),
    ("场景十", "陈静远", "以后别捡枣子了。"),
    ("场景十", "父亲", "暖。"),
    ("场景十", "陈静远", "暖就好。"),
    ("场景十一", "旁白", "她生了他，奶了他，把他从六岁的发烧里背到公社卫生院，背了四里山路，现在拎个暖壶都要扶着墙走。"),
    ("场景十一", "母亲", "你爹去年还能扶着墙走。今年枣子多，他舍不得糟蹋。人老了不服老，不服老就摔。"),
    ("场景十二", "旁白", "父亲出院后，陈静远每隔几天就去帮他推拿一次。腿上的肌肉因为长时间固定开始萎缩，膝盖僵得打不了弯。他用掌根按在肾俞和命门，用热气帮他稳住气血，再慢慢把腿上的经络松开——从环跳按到委中，从委中推到承山。每次推完，那条僵硬的腿能微微弯一点。"),
    ("场景十二", "父亲", "你这个手，是不是当年周老师说的那个——身子不一样？"),
    ("场景十二", "陈静远", "是。"),
    ("场景十三", "旁白", "那年过年，一家人又聚在了一起。枣树光秃秃的，枝条上落着雪。"),
    ("场景十三", "建国", "你上次推过以后，天阴不疼了。"),
    ("场景十三", "建军", "哥，你推拿的手艺能治病，我打家具的手艺能养家。咱俩都是手艺人了。"),
    ("场景十三", "旁白", "这双手不能号脉，但它们和他的一样，都找到了自己的路。"),
    ("场景十四", "旁白", "二十七年了。虎口的虎口，腰上的关元——热在身体里走了二十七年。从一只银色的虫子开始，走到现在。小时候热是被动的——发烧走，摔跤走，看蚂蚁搬家走。后来是主动的——看书走，练球走，号脉走，推拿走，扎针走。现在热在机关里走——看文件走，协调矛盾走，静坐走。以前他以为修行是打坐，是站桩，是远离人群。现在他知道，修行也在事里。事上磨出来的静，比打坐磨出来的静更稳。事上练出来的热，比独处练出来的热更经得起消耗。"),
    ("场景十五", "周小梅", "你回来了。"),
    ("场景十五", "陈静远", "嗯。"),
    ("片尾", "旁白", "第二十一章 完。"),
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

    out = BASE / "21" / "shots.json"
    out.write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")

    # verify concatenated text == tts_full
    audio = "".join(s["text"] for s in shots)
    tts = (BASE / "21" / "tts.txt").read_text(encoding="utf-8")
    stripped = "".join(l.strip() for l in tts.splitlines() if l.strip()).replace('"', '').replace('“', '').replace('”', '').replace('‘', '').replace('’', '')
    full = stripped + "第二十一章 完。"
    (BASE / "21" / "tts_full.txt").write_text(full, encoding="utf-8")
    def n(t): return re.sub(r"\s", "", t)
    print("shots:", len(shots))
    print("audio chars:", len(n(audio)), "tts_full chars:", len(n(full)))
    print("text equal:", n(audio) == n(full))
    if n(audio) != n(full):
        import difflib
        sm = difflib.SequenceMatcher(None, n(audio), n(full))
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "equal":
                print(tag, repr(n(audio)[i1:i2]), repr(n(full)[j1:j2]))


if __name__ == "__main__":
    main()
