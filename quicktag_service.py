"""QuickTagCloud (https://novelai.quicktagcloud.com/?c=artist_nai5_personal&update=2026.10.7)
服饰与造型详细 Tag 检索引擎：
- 内置 4,559 条精选服饰/内衣/鞋袜/发型/配饰词条（含《更衣人偶》《叫我千藤就好了の衣柜》与所长法典服饰卷），
  即使不安装生图插件、单独使用衣柜插件也能 100% 离线毫秒级检索；
- 若本地存在完整 grimoire.db 则自动联合检索 1.9 万条全量词库；
- 支持从 novelai.quicktagcloud.com (assets.quicktagcloud.com) 在线拉取最新服饰词库更新；
- 支持在用户/AI添加新衣服时，自动根据中文名称与描述匹配并补全高细节 Danbooru 英文标准 Tag。
"""

from __future__ import annotations

import json
import re
import sqlite3
import urllib.request
from pathlib import Path
from typing import Any

QUICKTAG_WEB_URL = "https://novelai.quicktagcloud.com/?c=artist_nai5_personal&update=2026.10.7"
QUICKTAG_DATA_SOURCE_URL = "https://novelai.quicktagcloud.com/data-source.json"

PLUGIN_DIR = Path(__file__).resolve().parent
CODEX_JSON_PATH = PLUGIN_DIR / "data" / "quicktag_clothing_codex.json"

GRIMOIRE_DB_CANDIDATES = [
    PLUGIN_DIR.parent.parent / "plugin_data" / "astrbot_plugin_nai_image" / "grimoire.db",
    PLUGIN_DIR.parent / "astrbot_plugin_nai_image" / "data" / "grimoire.db",
]

# 常见中文服饰特征词 -> 标准高细节 Danbooru Tag 兜底映射字典（用于组合增强）
CN_TO_DETAILED_NAI_TAGS: list[tuple[tuple[str, ...], str]] = [
    (("百褶裙", "百褶短裙", "微裙"), "pleated skirt, miniskirt, microskirt, high-waist skirt"),
    (("包臀裙", "一步裙", "铅笔裙"), "pencil skirt, tight skirt, high-waist skirt, side slit, hip focus"),
    (("连衣裙", "吊带裙", "真丝裙"), "camisole dress, spaghetti straps, sleeveless dress, minidress, cleavage"),
    (("睡裙", "睡衣", "吊带睡裙"), "nightgown, negligee, see-through, lace-trimmed dress, spaghetti straps"),
    (("旗袍", "中式"), "cheongsam, chinese clothes, mandarin collar, side slit, pelvic curtain, chinese knot"),
    (("死库水", "连体泳衣"), "school swimsuit, competition swimsuit, one-piece swimsuit, highleg swimsuit, skindentation"),
    (("比基尼", "泳装"), "bikini, micro bikini, side-tie bikini bottom, string bikini, cleavage"),
    (("女仆", "女仆装"), "maid, maid headdress, maid apron, frilled apron, frilled dress, puffy short sleeves"),
    (("兔女郎",), "playboy bunny, fake rabbit ears, bunny tail, strapless leotard, highleg leotard, wrist cuffs, bowighs"),
    (("水手服", "JK", "校服"), "serafuku, sailor collar, neckerchief, pleated skirt, miniskirt"),
    (("地雷系",), "jirai kei, frilled shirt, black bowtie, ribbon, suspender skirt, pleated skirt"),
    (("天使界限", "亚文化"), "tenshi kaiwai, oversized hoodie, loose sleeves, leg warmers, hairband"),
    (("白衬衫", "男友衬衫", "衬衫"), "white shirt, dress shirt, collared shirt, oversized shirt, partially unbuttoned, see-through shirt"),
    (("毛衣", "针织衫", "露肩毛衣"), "sweater, ribbed sweater, off-shoulder sweater, loose sleeves, collarbone"),
    (("开衫", "针织开衫"), "cardigan, knitted cardigan, open cardigan, off shoulder, loose sleeves"),
    (("连帽衫", "卫衣", "外套"), "hoodie, black jacket, open jacket, hood down, loose sleeves"),
    (("吊带", "背心", "抹胸"), "camisole, spaghetti straps, sleeveless, tight top, bare shoulders, cleavage"),
    (("渔网袜", "网袜"), "fishnet thighhighs, fishnet legwear, black fishnet, skindentation"),
    (("不对称", "单边袜", "单侧"), "asymmetrical legwear, single thighhigh, one bare leg, double thigh garter, black thigh strap, skindentation"),
    (("黑丝", "连裤袜", "丝袜"), "black pantyhose, see-through pantyhose, sheer legwear, shiny pantyhose"),
    (("白丝",), "white pantyhose, see-through pantyhose, sheer legwear"),
    (("肉丝", "肤色丝袜", "咖丝"), "brown pantyhose, see-through pantyhose, sheer legwear"),
    (("过膝袜", "长筒袜", "绝对领域"), "thighhighs, black thighhighs, see-through thighhighs, lace-trimmed legwear, zettai ryouiki, skindentation"),
    (("吊袜带", "吊带袜"), "garter straps, garter belt, thighhighs, skindentation"),
    (("大腿环", "腿环", "绑带"), "thigh strap, double thigh garter, black thigh strap, skindentation"),
    (("丁字裤", "T字裤", "细绳内裤"), "thong, g-string, micro panties, side-tie panties, see-through panties"),
    (("蕾丝内裤", "三角裤", "内裤"), "lace-trimmed panties, see-through panties, lowleg panties, bow panties"),
    (("蕾丝文胸", "胸罩", "半杯", "内衣"), "lace-trimmed bra, see-through bra, sheer bra, cleavage"),
    (("无肩带", "抹胸内衣"), "strapless bra, lace-trimmed bra, half-cup bra, cleavage"),
    (("前扣",), "front-hook bra, lace-trimmed bra, deep cleavage"),
    (("真空", "不穿内衣", "未穿"), "no bra, nipples visible through clothes, covered nipples"),
    (("胸贴",), "pasties, nipple pasties, no bra"),
    (("高跟鞋", "细跟"), "high heels, stiletto heels, black footwear"),
    (("凉鞋", "凉拖"), "sandals, high-heel sandals, strappy heels, toenails, pink nails"),
    (("拖鞋",), "slippers, indoor"),
    (("赤足", "光脚", "不穿鞋"), "barefoot, no shoes, toes, pink nails"),
    (("狐狸尾巴", "狐尾", "大尾巴"), "fluffy fox tail, animal tail, large tail, bushy tail, tail from under skirt"),
    (("猫耳", "猫尾", "猫娘"), "cat ears, animal ears, cat tail, fluffy tail"),
    (("项圈", "颈带", "choker"), "black choker, lace choker, neck ribbon, collarbone"),
    (("铃铛",), "bell, neck bell, gold bell, bell collar"),
    (("脚链",), "anklet, ankle ornament, jewelry"),
    (("丸子头", "盘发"), "hair bun, single hair bun, messy hair, updo, nape"),
    (("双马尾",), "twintails, long hair, hair ribbon"),
    (("麻花辫", "辫子"), "side braid, single braid, low braid, hair over one shoulder"),
    (("半扎发", "发簪"), "half updo, hairpin, sidelocks, very long hair"),
    (("披肩发", "散落", "长发"), "very long hair, hair down, floating hair, shiny hair"),
    (("半透", "透明", "薄纱"), "see-through, sheer clothes, translucent fabric"),
    (("勒肉", "紧身"), "skindentation, tight clothes"),
]

_CACHED_CODEX_ITEMS: list[dict[str, Any]] | None = None


def clean_codex_tags(raw_tags: str) -> str:
    """将法典词条净化为适合衣柜拼接的标准 Tag 字符串（剥离 1girl/solo/背景/设置行与多层括号权重）。"""
    lines = []
    for line in (raw_tags or "").splitlines():
        s = line.strip()
        if not s or s.startswith(("负面", "negative", "Steps:", "Sampler:", "Prompt Guidance", "设置")):
            continue
        s = re.sub(r"^char\d+[:：]\s*", "", s, flags=re.IGNORECASE)
        lines.append(s.rstrip(",， "))
    joined = ", ".join(lines)
    # 剥离 {{{tag}}} 或 [[tag]] 外壳，保留纯正 Danbooru 原子词
    joined = re.sub(r"[\{\}\[\]]+", "", joined)
    skip_global = {"1girl", "solo", "1boy", "2girls", "hetero", "simple background", "white background"}
    parts = []
    seen = set()
    for p in joined.split(","):
        t = p.strip()
        if not t:
            continue
        low = t.lower()
        if low in skip_global or low in seen:
            continue
        seen.add(low)
        parts.append(t)
    return ", ".join(parts)


def _load_local_codex() -> list[dict[str, Any]]:
    global _CACHED_CODEX_ITEMS
    if _CACHED_CODEX_ITEMS is not None:
        return _CACHED_CODEX_ITEMS
    if CODEX_JSON_PATH.is_file():
        try:
            data = json.loads(CODEX_JSON_PATH.read_text(encoding="utf-8"))
            items = data.get("items") or []
            if isinstance(items, list):
                _CACHED_CODEX_ITEMS = items
                return items
        except Exception:
            pass
    _CACHED_CODEX_ITEMS = []
    return _CACHED_CODEX_ITEMS


def _get_grimoire_db() -> Path | None:
    for p in GRIMOIRE_DB_CANDIDATES:
        if p.is_file():
            return p
    return None


def search_quicktag_clothing(query: str, limit: int = 12) -> list[dict[str, Any]]:
    """从 QuickTagCloud 词库（本地独立服饰词库 + grimoire.db）检索详细服饰 Tag。"""
    q = (query or "").strip()
    if not q:
        return []
    tokens = [t.strip() for t in re.split(r"[\s,，/、+()（）·]+", q) if len(t.strip()) >= 1]
    if not tokens:
        tokens = [q]

    results: list[dict[str, Any]] = []
    seen_titles: set[str] = set()

    # 1. 优先查内置的 quicktag_clothing_codex.json（保证衣柜插件单独分发也能 100% 检索）
    codex_items = _load_local_codex()
    scored: list[tuple[int, dict[str, Any]]] = []
    for it in codex_items:
        title = str(it.get("title") or "")
        cat = str(it.get("category") or "")
        tags = str(it.get("tags") or "")
        vol = str(it.get("volume") or "")
        score = 0
        for tok in tokens[:6]:
            tl = tok.lower()
            if tl == title.lower():
                score += 120
            elif tl in title.lower():
                score += 60
            if tl in cat.lower():
                score += 25
            if tl in tags.lower():
                score += 20
        if score > 0:
            if vol in ("叫我千藤就好了の衣柜", "更衣人偶") or "服饰" in cat or "服装" in cat:
                score += 15
            scored.append((score, it))

    scored.sort(key=lambda x: (-x[0], len(str(x[1].get("title") or ""))))
    for sc, it in scored[:limit]:
        key = f"{it.get('volume')}:{it.get('title')}"
        if key not in seen_titles:
            seen_titles.add(key)
            raw_t = str(it.get("tags") or "")
            results.append({
                "volume": it.get("volume", "QuickTagCloud"),
                "category": it.get("category", "服饰"),
                "title": it.get("title", ""),
                "raw_tags": raw_t,
                "clean_tags": clean_codex_tags(raw_t),
                "score": sc,
            })

    # 2. 若结果不足且存在全量 grimoire.db，补充检索
    if len(results) < limit:
        db_path = _get_grimoire_db()
        if db_path:
            try:
                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()
                tok0 = f"%{tokens[0]}%"
                rows = cur.execute(
                    """
                    SELECT volume, category, title, tags
                    FROM grimoire_entries
                    WHERE title LIKE ? OR category LIKE ? OR tags LIKE ?
                    LIMIT ?
                    """,
                    (tok0, tok0, tok0, limit * 2),
                ).fetchall()
                conn.close()
                for vol, cat, title, raw_t in rows:
                    key = f"{vol}:{title}"
                    if key not in seen_titles:
                        seen_titles.add(key)
                        results.append({
                            "volume": vol,
                            "category": cat,
                            "title": title,
                            "raw_tags": raw_t,
                            "clean_tags": clean_codex_tags(raw_t),
                            "score": 30,
                        })
                        if len(results) >= limit:
                            break
            except Exception:
                pass

    return results[:limit]


def auto_generate_detailed_nai_tags(name: str, desc: str, existing_tags: str = "") -> str:
    """当用户新增衣物但未填写详细 Tag（或填写过于简略）时，
    自动结合 QuickTagCloud 词库检索 + 部位特征映射，生成高精度 Danbooru 英文标准 Tag 组合。
    """
    combined_cn = f"{name} {desc}".strip()
    parts: list[str] = []

    if existing_tags and existing_tags.strip():
        parts.append(existing_tags.strip())

    # 1. 匹配中文精细结构与服饰特征词典
    for kw_tuple, tag_str in CN_TO_DETAILED_NAI_TAGS:
        if any(k.lower() in combined_cn.lower() for k in kw_tuple):
            parts.append(tag_str)

    # 2. 检索 QuickTagCloud 服饰词库取最匹配词条的精细服装 Tag
    hits = search_quicktag_clothing(name, limit=2)
    if not hits and desc:
        hits = search_quicktag_clothing(desc[:25], limit=2)
    for h in hits[:1]:
        ct = h.get("clean_tags", "")
        if ct:
            # 取前 15 个核心服饰原子词，避免混入过多动作词
            sub_tags = [x.strip() for x in ct.split(",") if x.strip()][:15]
            parts.append(", ".join(sub_tags))

    # 保序去重
    seen: set[str] = set()
    final_tags: list[str] = []
    for chunk in parts:
        for t in chunk.split(","):
            s = t.strip()
            if not s:
                continue
            low = s.lower()
            if low not in seen:
                seen.add(low)
                final_tags.append(s)

    return ", ".join(final_tags)


def discover_new_outfit_candidate(
    temp_c: float = 20.0,
    style_hint: str = "",
    exclude_titles: set[str] | None = None,
) -> dict[str, Any] | None:
    """从 QuickTagCloud 4,559 条服饰词库中自动淘出一套高细节新衣服候选（供每日自动找衣服或试穿审批）。"""
    import random
    import time as _time

    codex_items = _load_local_codex()
    if not codex_items:
        return None

    excl = exclude_titles or set()
    hint = (style_hint or "").strip().lower()

    # 优先从《叫我千藤就好了の衣柜》《更衣人偶》和明确服饰分类中挑选
    candidates: list[dict[str, Any]] = []
    for it in codex_items:
        title = str(it.get("title") or "").strip()
        cat = str(it.get("category") or "").strip()
        vol = str(it.get("volume") or "").strip()
        if not title or title in excl:
            continue
        if hint and (hint in title.lower() or hint in cat.lower()):
            candidates.append(it)
            continue
        if not hint:
            if vol in ("叫我千藤就好了の衣柜", "更衣人偶") or any(k in cat for k in ("日常服", "制服", "礼服", "内衣", "泳装", "旗袍", "兔女郎", "女仆", "睡衣", "丝袜", "穿搭")):
                candidates.append(it)

    if not candidates:
        candidates = codex_items

    chosen = random.choice(candidates)
    title = str(chosen.get("title") or "新潮穿搭").strip()
    vol = str(chosen.get("volume") or "QuickTagCloud").strip()
    cat = str(chosen.get("category") or "精选服饰").strip()
    clean_t = clean_codex_tags(str(chosen.get("tags") or ""))
    detailed_t = auto_generate_detailed_nai_tags(title, cat, clean_t)

    cand_id = f"pending_{int(_time.time() * 1000) % 100000000}"
    return {
        "id": cand_id,
        "kind": "item",
        "slot": "top",
        "source_volume": vol,
        "source_category": cat,
        "name": f"{title}",
        "desc": f"从【{vol} · {cat}】淘来的新衣服：{title}（可根据喜好微调细节）",
        "nai_tags": detailed_t,
        "temp_min": 10.0,
        "temp_max": 38.0,
        "categories": ["weekend_home", "weekday", "mild", "hot", "night"],
        "created_at": _time.strftime("%Y-%m-%d %H:%M:%S"),
    }
