"""9 部位模块化精细拆分衣柜库与自由拼装引擎（发型、外搭、上衣/连衣裙、下装、胸罩、内裤、丝袜与鞋饰）。"""

from __future__ import annotations

import random
from typing import Any

SLOTS = ("hair", "outer", "top", "bottom", "bra", "panties", "legwear", "shoes", "accessory")

# 默认身体外貌原子词条包示例（纯正 Danbooru 标准 Tag 组合）
STARRY_APPEARANCE_BLOCKS: dict[str, str] = {
    "hair_color": "1.4::dark blue hair::, two-tone hair, gradient hair, 0.7::silver hair::, starry hair",
    "eyes": "gradient eyes, light blue eyes, pale purple eyes",
    "body": "tall female, delicate face, soft cheeks, pale skin, medium breasts, slender waist, wide hips, long legs",
}
STARRY_BASE_APPEARANCE_TAGS = ", ".join(STARRY_APPEARANCE_BLOCKS.values())


WARDROBE_ITEMS: dict[str, list[dict[str, Any]]] = {
    "hair": [
        {
            "id": "hair_starry_neko_floral",
            "slot": "hair",
            "name": "星空散落长发配毛绒猫耳与红金花簪",
            "desc": "深蓝渐变银灰的星空长发柔顺散落肩头，头顶戴着一对敏感轻颤的毛绒猫耳，发间别着华丽的红金山茶花发饰与蕾丝流苏",
            "nai_tags": "very long hair, hair down, cat ears, animal ears, hair flower, red camellia, hair ornament, gold hair ornament, hair ribbon, tassels, cat tail",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
        },
        {
            "id": "hair_starry_loose",
            "slot": "hair",
            "name": "星空长发·自然披肩",
            "desc": "深蓝渐变银灰的星空长发自然散落在肩头与后背，发尾带着细碎星光感",
            "nai_tags": "very long hair, hair down, floating hair, shiny hair",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "weekday", "mild", "cold", "rainy", "night"],
        },
        {
            "id": "hair_silver_pin_halfup",
            "slot": "hair",
            "name": "星月银簪·慵懒半挽发",
            "desc": "用一根银色星月发簪将星空长发松松挽起一半，几缕碎发垂在白皙耳畔与颈侧",
            "nai_tags": "very long hair, long hair, half updo, hairpin, crescent hair ornament, sidelocks",
            "temp_min": 12,
            "temp_max": 42,
            "categories": ["weekday", "weekend_home", "mild", "hot"],
        },
        {
            "id": "hair_side_braid",
            "slot": "hair",
            "name": "单侧低麻花辫",
            "desc": "深蓝渐变银灰单侧低麻花辫",
            "nai_tags": "1.4::single braid, side braid::, low braid, braided hair, hair over one shoulder, stray hair",
            "temp_min": -10,
            "temp_max": 38,
            "categories": ["weekend_home", "weekday", "mild", "rainy"],
        },
        {
            "id": "hair_high_bun_neck",
            "slot": "hair",
            "name": "居家随性高挽丸子头",
            "desc": "把星空长发随手高高挽成一个蓬松丸子头，大方露出修长白皙的后颈与精致锁骨",
            "nai_tags": "long hair, hair bun, single hair bun, messy hair, updo, nape, collarbone",
            "temp_min": 18,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
        },
    ],
    "outer": [
        {
            "id": "outer_black_hoodie_jacket",
            "slot": "outer",
            "name": "黑色宽松半敞连帽薄开衫",
            "desc": "外搭一件随性半敞的黑色宽松连帽薄衫，自然垂落在手肘与大腿两侧",
            "nai_tags": "black jacket, open jacket, hoodie, hood down, loose sleeves, off shoulder",
            "temp_min": 12,
            "temp_max": 36,
            "categories": ["weekend_home", "weekday", "mild", "night"],
        },
        {
            "id": "outer_crimson_sheer_sleeves",
            "slot": "outer",
            "name": "绯红半透薄纱分离袖（缀金铃铛）",
            "desc": "双臂套着轻薄如雾的绯红色半透明薄纱分离袖，上臂系着红绳与清脆的小金铃铛",
            "nai_tags": "detached sleeves, red sleeves, sheer sleeves, see-through sleeves, arm garter, bell, red ribbon",
            "temp_min": 12,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
        },
        {
            "id": "outer_white_cardigan",
            "slot": "outer",
            "name": "米白露肩软糯针织开衫",
            "desc": "米白色宽松软糯露肩针织开衫",
            "nai_tags": "white cardigan, knitted cardigan, off shoulder, open cardigan, unbuttoned, loose sleeves, sleeves past wrists, bare shoulders",
            "temp_min": 12,
            "temp_max": 30,
            "categories": ["weekend_home", "mild", "rainy"],
        },
        {
            "id": "outer_none",
            "slot": "outer",
            "name": "无外搭（清爽单穿）",
            "desc": "无外搭",
            "nai_tags": "bare shoulders, collarbone, exposed shoulders",
            "temp_min": 20,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
        },
        {
            "id": "outer_starry_long_cardigan",
            "slot": "outer",
            "name": "夜空蓝长款针织开衫",
            "desc": "深邃夜空蓝长款宽松针织开衫",
            "nai_tags": "dark blue cardigan, long cardigan, knitted cardigan, open cardigan, loose sleeves",
            "temp_min": 8,
            "temp_max": 24,
            "categories": ["rainy", "mild", "cold", "weekday"],
        },
        {
            "id": "outer_grey_blazer",
            "slot": "outer",
            "name": "浅灰修身薄款西装外套",
            "desc": "剪裁利落的浅灰薄款西装外套",
            "nai_tags": "grey jacket, blazer, open jacket, jacket on shoulders, formal",
            "temp_min": 14,
            "temp_max": 28,
            "categories": ["weekday", "mild"],
        },
        {
            "id": "outer_sheer_shawl",
            "slot": "outer",
            "name": "蝉翼白半透薄纱开衫",
            "desc": "超薄蝉翼白半透明纱质开衫",
            "nai_tags": "white cardigan, see-through, sheer clothes, shawl, open cardigan, bare shoulders",
            "temp_min": 24,
            "temp_max": 42,
            "categories": ["hot", "weekday", "weekend_home"],
        },
        {
            "id": "outer_black_silk_robe",
            "slot": "outer",
            "name": "暗夜黑真丝带腰带睡袍",
            "desc": "暗夜黑垂感真丝睡袍",
            "nai_tags": "black robe, open robe, silk robe, long sleeves",
            "temp_min": 10,
            "temp_max": 35,
            "categories": ["night", "weekend_home"],
        },
    ],
    "top": [
        {
            "id": "top_black_tight_camisole",
            "slot": "top",
            "name": "黑色轻薄修身低胸吊带衫",
            "desc": "黑色轻薄修身打底吊带，勾勒出饱满挺拔的D罩杯胸型与纤细腰肢",
            "nai_tags": "black camisole, sleeveless, spaghetti straps, tight top, cleavage, bare shoulders",
            "temp_min": 14,
            "temp_max": 40,
            "categories": ["weekend_home", "hot", "night", "weekday"],
        },
        {
            "id": "top_crimson_sheer_cheongsam_leotard",
            "slot": "top",
            "name": "绯红蝉翼薄纱挂脖高叉旗袍连体衣（半透露乳尖）",
            "desc": "极具视觉冲击的绯红色中式立领挂脖高叉连体薄纱衣，上半截胸口大片雪腻D罩杯浑圆完全敞露，仅在乳晕与粉嫩乳尖处横兜着一层薄如蝉翼的半透明水润红纱，两颗饱满乳尖与腰腹肚脐隔着贴肤薄纱清晰凸起；下摆呈深V高叉直达大腿根，腰侧缀着金属盘扣中国结与红蓝宝石流苏",
            "nai_tags": "chinese clothes, mandarin collar, red leotard, halterneck, see-through, sheer clothes, cleavage cutout, covered nipples, nipples, navel, highleg leotard, pelvic curtain, hip vent, tassels",
            "temp_min": 16,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
            "is_dress": True,
        },
        {
            "id": "top_naked",
            "slot": "top",
            "name": "脱光上衣（赤裸上身）",
            "desc": "上衣已完全脱光，毫无遮挡地展露白皙细腻的香肩、纤细腰肢与胸前饱满软弹的D罩杯雪白双乳",
            "nai_tags": "topless, bare breasts, nipples, areolae, collarbone",
            "temp_min": 18,
            "temp_max": 42,
            "categories": ["naked"],
        },
        {
            "id": "top_champagne_camisole_dress",
            "slot": "top",
            "name": "浅香槟色真丝吊带短裙（连身）",
            "desc": "浅香槟色真丝吊带短裙",
            "nai_tags": "champagne dress, camisole, dress, minidress, sleeveless dress, spaghetti straps, silk, satin, cleavage, collarbone",
            "temp_min": 15,
            "temp_max": 35,
            "categories": ["weekend_home", "mild", "hot"],
        },
        {
            "id": "top_black_offshoulder_sweater",
            "slot": "top",
            "name": "黑色宽松露肩针织毛衣",
            "desc": "黑色宽松露肩针织毛衣",
            "nai_tags": "black sweater, ribbed sweater, off-shoulder sweater, single off shoulder, loose clothes, sleeves past wrists, collarbone, cleavage",
            "temp_min": 8,
            "temp_max": 25,
            "categories": ["weekday", "weekend_home", "mild", "rainy", "cold"],
        },
        {
            "id": "top_boyfriend_white_shirt",
            "slot": "top",
            "name": "男友风微透丝质长白衬衫",
            "desc": "宽松微透的丝质长款白衬衫",
            "nai_tags": "white shirt, oversized shirt, dress shirt, collared shirt, buttoned shirt, see-through shirt",
            "temp_min": 18,
            "temp_max": 38,
            "categories": ["weekend_home", "hot", "night"],
        },
        {
            "id": "top_purple_silk_blouse",
            "slot": "top",
            "name": "浅紫罗兰垂感真丝V领衬衫",
            "desc": "浅紫罗兰色垂感真丝V领衬衫",
            "nai_tags": "light purple shirt, blouse, satin, deep v-neck, tight shirt, button gap, cleavage",
            "temp_min": 14,
            "temp_max": 32,
            "categories": ["weekday", "mild", "hot"],
        },
        {
            "id": "top_white_scoop_modal",
            "slot": "top",
            "name": "纯白贴身U领莫代尔打底衫",
            "desc": "纯白贴身U领莫代尔长袖上衣",
            "nai_tags": "white shirt, tight shirt, long sleeves, scoop neck, taut shirt, collarbone, cleavage",
            "temp_min": 10,
            "temp_max": 25,
            "categories": ["weekday", "weekend_home", "mild", "rainy"],
        },
        {
            "id": "top_pink_angora_sweater",
            "slot": "top",
            "name": "雾粉色大V领马海毛软毛衣",
            "desc": "雾粉色宽松大V领马海毛软毛衣",
            "nai_tags": "pink sweater, v-neck sweater, off-shoulder sweater, loose sweater, collarbone, cleavage",
            "temp_min": -10,
            "temp_max": 18,
            "categories": ["cold", "weekend_home", "weekday"],
        },
        {
            "id": "top_black_lace_negligee",
            "slot": "top",
            "name": "暗夜黑蕾丝拼接真丝睡裙（连身）",
            "desc": "暗夜黑胸前蕾丝拼接真丝吊带睡裙",
            "nai_tags": "black dress, nightgown, negligee, see-through, lace-trimmed dress, spaghetti straps, side slit, cleavage",
            "temp_min": 12,
            "temp_max": 38,
            "categories": ["night", "weekend_home"],
        },
    ],
    "bottom": [
        {
            "id": "bot_naked",
            "slot": "bottom",
            "name": "脱光下装（未穿裙裤）",
            "desc": "下装已完全脱去，毫无遮掩地露出圆润挺翘的雪白臀部与修长匀称的大腿根",
            "nai_tags": "bottomless, bare thighs, wide hips",
            "temp_min": 18,
            "temp_max": 42,
            "categories": ["naked"],
        },
        {
            "id": "bot_dress_none",
            "slot": "bottom",
            "name": "连身裙摆（免穿独立下装）",
            "desc": "连身裙或旗袍下摆自然垂落（无需额外穿独立下装）",
            "nai_tags": "",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "weekday", "mild", "hot", "cold", "rainy", "night"],
        },
        {
            "id": "bot_black_pleated_microskirt",
            "slot": "bottom",
            "name": "黑色极短高腰百褶微裙",
            "desc": "黑色极短高腰百褶超短裙，裙摆堪堪遮住臀弯，露出大片雪白大腿根",
            "nai_tags": "solid black pleated skirt, miniskirt, high-waist skirt",
            "temp_min": 12,
            "temp_max": 40,
            "categories": ["weekend_home", "hot", "night", "weekday"],
        },
        {
            "id": "bot_grey_pleated_skirt",
            "slot": "bottom",
            "name": "深灰色高腰百褶短裙",
            "desc": "深灰色高腰百褶短裙",
            "nai_tags": "grey skirt, pleated skirt, miniskirt, microskirt, high-waist skirt",
            "temp_min": 10,
            "temp_max": 34,
            "categories": ["weekday", "weekend_home", "mild", "rainy"],
        },
        {
            "id": "bot_black_slit_pencil_skirt",
            "slot": "bottom",
            "name": "黑色高腰侧开叉包臀一步裙",
            "desc": "黑色高腰侧开叉包臀一步裙",
            "nai_tags": "black skirt, pencil skirt, high-waist skirt, tight skirt, side slit",
            "temp_min": 14,
            "temp_max": 34,
            "categories": ["weekday", "mild", "hot"],
        },
        {
            "id": "bot_black_wool_shorts",
            "slot": "bottom",
            "name": "黑色高腰修身毛呢短裤",
            "desc": "黑色高腰修身毛呢短裤",
            "nai_tags": "black shorts, short shorts, high-waist shorts, tight shorts",
            "temp_min": -10,
            "temp_max": 24,
            "categories": ["cold", "weekday", "weekend_home", "mild"],
        },
        {
            "id": "bot_no_pants_shirt",
            "slot": "bottom",
            "name": "下身失踪（仅靠长上衣遮掩）",
            "desc": "未穿外裤与短裙，长款下摆堪堪盖住大腿根与臀弯，一弯腰就会春光乍泄",
            "nai_tags": "bottomless, oversized shirt, bare thighs",
            "temp_min": 18,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
        },
    ],
    "bra": [
        {
            "id": "bra_champagne_strapless",
            "slot": "bra",
            "name": "浅香槟无肩带蕾丝半杯软托胸罩",
            "desc": "浅香槟色无肩带蕾丝半杯软托文胸",
            "nai_tags": "beige bra, strapless bra, lace-trimmed bra",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "mild", "hot", "weekday"],
        },
        {
            "id": "bra_purple_blue_front_clasp",
            "slot": "bra",
            "name": "深紫蓝前扣式蕾丝半杯胸罩",
            "desc": "深紫蓝色无肩带蕾丝半杯前扣内衣",
            "nai_tags": "dark blue bra, purple bra, lace-trimmed bra, front-hook bra",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "weekday", "mild", "rainy"],
        },
        {
            "id": "bra_black_sheer_halfcup",
            "slot": "bra",
            "name": "黑色半透明蕾丝1/2杯托胸文胸",
            "desc": "黑色半透明薄纱蕾丝1/2杯文胸",
            "nai_tags": "black bra, lace-trimmed bra, see-through bra, sheer bra, areola slip",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night", "weekday"],
        },
        {
            "id": "bra_wine_red_pushup",
            "slot": "bra",
            "name": "酒红色深V聚拢蕾丝胸罩",
            "desc": "酒红色深V聚拢蕾丝文胸",
            "nai_tags": "dark red bra, lace-trimmed bra, bra visible through clothes",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekday", "mild", "night"],
        },
        {
            "id": "bra_milk_white_french",
            "slot": "bra",
            "name": "奶白法式刺绣薄纱三角杯",
            "desc": "奶白色无钢圈法式刺绣薄纱三角杯",
            "nai_tags": "white bra, lace-trimmed bra, see-through bra",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "mild", "cold", "rainy"],
        },
        {
            "id": "bra_pasties_only",
            "slot": "bra",
            "name": "肤色隐形硅胶花瓣胸贴",
            "desc": "仅贴着一对薄薄的肤色硅胶胸贴，整团饱满胸乳毫无束缚地随着动作轻轻颤动",
            "nai_tags": "pasties, nipple pasties, no bra",
            "temp_min": 18,
            "temp_max": 42,
            "categories": ["hot", "weekend_home", "night"],
        },
        {
            "id": "bra_none_commando",
            "slot": "bra",
            "name": "真空未穿胸罩（完全解放）",
            "desc": "上身真空未穿胸罩，软弹饱满的D罩杯直接贴合外衣布料，前端两颗娇嫩樱桃隔着薄布料微微顶起",
            "nai_tags": "no bra, nipples visible through clothes, covered nipples",
            "temp_min": 16,
            "temp_max": 42,
            "categories": ["night", "weekend_home"],
        },
    ],
    "panties": [
        {
            "id": "pan_naked",
            "slot": "panties",
            "name": "脱光内裤（下身真空）",
            "desc": "小内裤已被彻底褪下，双腿间白皙粉嫩的私密一线天毫无防备地裸露在外",
            "nai_tags": "no panties, pussy, uncensored",
            "temp_min": 16,
            "temp_max": 42,
            "categories": ["naked"],
        },
        {
            "id": "pan_blue_gingham_lace",
            "slot": "panties",
            "name": "蓝白格纹白蕾丝花边低腰内裤",
            "desc": "清爽少女感的蓝白小格纹低腰三角内裤，腰沿与腿根镶着一圈精致的纯白蕾丝花边，贴合着微鼓的小腹与私密软肉",
            "nai_tags": "blue and white plaid panties, white lace trim, frilled lowleg panties",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "weekday", "mild", "hot"],
        },
        {
            "id": "pan_grey_lace_black_bow",
            "slot": "panties",
            "name": "雾灰蕾丝黑蝴蝶结低腰内裤",
            "desc": "温柔贴肤的雾灰色钩花蕾丝低腰内裤，正中央点缀着一枚小巧的黑色丝带蝴蝶结",
            "nai_tags": "grey panties, lace panties, lace-trimmed panties, black bow, front bow, lowleg panties, floral lace",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "weekday", "mild", "rainy"],
        },
        {
            "id": "pan_pink_sheer_bow_lace",
            "slot": "panties",
            "name": "樱花粉半透刺绣粉蝴蝶结内裤",
            "desc": "娇嫩的樱花粉半透明刺绣蕾丝小内裤，正前方系着粉色细丝带蝴蝶结，隐约透出底下粉腻的肌肤光泽",
            "nai_tags": "pink panties, light pink panties, see-through panties, sheer panties, lace-trimmed panties, pink bow, front bow, lowleg panties",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "weekday", "mild", "hot", "night"],
        },
        {
            "id": "pan_mint_green_floral_lace",
            "slot": "panties",
            "name": "薄荷绿花朵刺绣清透蕾丝内裤",
            "desc": "清凉薄荷绿色的半透明花朵刺绣蕾丝三角裤，边缘带着细腻的花瓣形蕾丝滚边",
            "nai_tags": "green panties, light green panties, mint panties, floral lace, lace-trimmed panties, see-through panties, lowleg panties",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "weekday", "mild", "hot"],
        },
        {
            "id": "pan_purple_highleg_black_strap",
            "slot": "panties",
            "name": "浅紫黑细带极高叉蕾丝内裤",
            "desc": "极具诱惑力的浅紫色蕾丝前片配黑色极细松紧侧带，高叉剪裁直勒胯骨上方，将两侧丰腴白腻的大腿根与腹股沟完全展露",
            "nai_tags": "purple panties, light purple panties, highleg panties, string panties, black straps, hip straps, lace panties, micro panties, skindentation",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
        },
        {
            "id": "pan_ice_blue_ruffle_tulle",
            "slot": "panties",
            "name": "浅冰蓝荷叶薄纱飞边蕾丝内裤",
            "desc": "梦幻的浅冰蓝色刺绣小内裤，两侧胯骨旁装饰着蓬松轻盈的半透明白纱荷叶飞边，纯欲又俏皮",
            "nai_tags": "light blue panties, blue panties, frilled panties, white ruffles, sheer trim, lace-trimmed panties, see-through panties, lowleg panties",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "weekday", "mild", "hot", "night"],
        },
        {
            "id": "pan_champagne_silk",
            "slot": "panties",
            "name": "浅香槟色细带真丝三角内裤",
            "desc": "浅香槟色细带真丝三角内裤",
            "nai_tags": "beige panties, string panties, side-tie panties, lowleg panties",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "mild", "hot", "weekday"],
        },
        {
            "id": "pan_purple_blue_ribbon_lace",
            "slot": "panties",
            "name": "深紫蓝腰侧蝴蝶结半透蕾丝小内裤",
            "desc": "深紫蓝色系带薄纱蕾丝内裤",
            "nai_tags": "dark blue panties, purple panties, lace-trimmed panties, see-through panties, side-tie panties",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "weekday", "mild", "rainy", "night"],
        },
        {
            "id": "pan_black_lace_thong",
            "slot": "panties",
            "name": "黑色蕾丝细绳低腰T字裤",
            "desc": "黑色半透蕾丝细绳低腰T字裤",
            "nai_tags": "black panties, thong, g-string, lace-trimmed panties, see-through panties, micro panties",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night", "weekday"],
        },
        {
            "id": "pan_wine_red_mesh",
            "slot": "panties",
            "name": "酒红色半透网纱低腰三角裤",
            "desc": "酒红色半透网纱刺绣三角内裤",
            "nai_tags": "dark red panties, lace-trimmed panties, see-through panties, lowleg panties",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekday", "mild", "night"],
        },
        {
            "id": "pan_white_cotton_bow",
            "slot": "panties",
            "name": "纯白罗纹小蝴蝶结棉质内裤",
            "desc": "纯白罗纹软棉蝴蝶结低腰内裤",
            "nai_tags": "white panties, bow panties, cotton panties",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "mild", "cold", "rainy"],
        },
    ],
    "legwear": [
        {
            "id": "leg_sheer_black_pantyhose",
            "slot": "legwear",
            "name": "15D超薄半透明黑色连裤丝袜",
            "desc": "15D超薄半透明黑色连裤丝袜",
            "nai_tags": "black pantyhose, see-through pantyhose, sheer legwear, shiny pantyhose",
            "temp_min": 10,
            "temp_max": 34,
            "categories": ["weekend_home", "weekday", "mild", "hot", "rainy"],
        },
        {
            "id": "leg_garter_thighhighs",
            "slot": "legwear",
            "name": "黑色蕾丝吊袜带过膝丝袜",
            "desc": "黑色蕾丝花边吊带过膝丝袜",
            "nai_tags": "black thighhighs, see-through thighhighs, lace-trimmed legwear, garter straps, garter belt, skindentation",
            "temp_min": 14,
            "temp_max": 38,
            "categories": ["weekend_home", "hot", "night"],
        },
        {
            "id": "leg_zettai_thighhighs",
            "slot": "legwear",
            "name": "20D蕾丝防滑过膝黑丝（绝对领域）",
            "desc": "20D半透明黑色蕾丝边过膝长筒袜",
            "nai_tags": "black thighhighs, see-through thighhighs, lace-trimmed legwear, zettai ryouiki, skindentation",
            "temp_min": 12,
            "temp_max": 32,
            "categories": ["weekday", "weekend_home", "mild", "rainy", "night"],
        },
        {
            "id": "leg_seamed_black_pantyhose",
            "slot": "legwear",
            "name": "15D后缝线极薄半透明黑丝",
            "desc": "15D后缝线半透明黑色连裤丝袜",
            "nai_tags": "black pantyhose, see-through pantyhose, seamed legwear, shiny pantyhose",
            "temp_min": 12,
            "temp_max": 34,
            "categories": ["weekday", "mild", "hot", "night"],
        },
        {
            "id": "leg_coffee_pantyhose",
            "slot": "legwear",
            "name": "浅咖啡色超薄透肉连裤丝袜",
            "desc": "浅咖啡色超薄半透明连裤丝袜",
            "nai_tags": "brown pantyhose, see-through pantyhose, sheer legwear, shiny pantyhose",
            "temp_min": 10,
            "temp_max": 28,
            "categories": ["weekday", "mild"],
        },
        {
            "id": "leg_asym_fishnet_double_thigh_strap",
            "slot": "legwear",
            "name": "不对称单侧菱格渔网袜配双环大腿勒肉带",
            "desc": "一侧大腿紧紧系着两条黑色双环大腿环将软肉微微勒陷，连接着性感的黑色菱格过膝渔网袜；另一侧则是毫无遮掩的修长雪白裸腿，反差感拉满",
            "nai_tags": "asymmetrical legwear, single thighhigh, left legwear, black fishnet thighhigh, thigh strap, garter straps, skindentation, bare right leg",
            "temp_min": 12,
            "temp_max": 38,
            "categories": ["weekend_home", "hot", "night", "weekday"],
        },
        {
            "id": "leg_naked_bare",
            "slot": "legwear",
            "name": "脱光丝袜（白皙裸腿）",
            "desc": "未穿丝袜，直接展露白皙笔直、细腻温润的修长双腿",
            "nai_tags": "bare legs, no legwear, bare thighs",
            "temp_min": 18,
            "temp_max": 42,
            "categories": ["hot", "weekend_home", "night", "naked"],
        },
    ],
    "shoes": [
        {
            "id": "shoe_fluffy_slippers",
            "slot": "shoes",
            "name": "居家软底毛绒拖鞋",
            "desc": "脚穿软乎乎的居家软底毛绒拖鞋",
            "nai_tags": "slippers, animal slippers",
            "temp_min": -10,
            "temp_max": 35,
            "categories": ["weekend_home", "mild", "cold", "rainy"],
        },
        {
            "id": "shoe_black_heels",
            "slot": "shoes",
            "name": "黑色细跟高跟鞋",
            "desc": "黑色细跟高跟鞋",
            "nai_tags": "black footwear, high heels, stiletto heels",
            "temp_min": 10,
            "temp_max": 35,
            "categories": ["weekday", "mild", "hot", "night"],
        },
        {
            "id": "shoe_red_heels",
            "slot": "shoes",
            "name": "绯红漆皮细跟高跟鞋",
            "desc": "脚穿明艳勾人的绯红色漆皮细跟高跟鞋，衬得足背与小腿线条愈发修长白皙",
            "nai_tags": "red footwear, red high heels, high heels, stiletto heels, pumps",
            "temp_min": 10,
            "temp_max": 38,
            "categories": ["weekend_home", "weekday", "mild", "hot", "night"],
        },
        {
            "id": "shoe_pearl_sandals",
            "slot": "shoes",
            "name": "珍珠细带低跟凉拖鞋",
            "desc": "脚穿精致的珍珠细带凉拖鞋，露出涂着淡粉光泽的秀气足趾",
            "nai_tags": "sandals, high-heel sandals, strappy heels, toenails, pink nails",
            "temp_min": 20,
            "temp_max": 42,
            "categories": ["hot", "weekday", "weekend_home"],
        },
        {
            "id": "shoe_naked_barefoot",
            "slot": "shoes",
            "name": "脱掉鞋子（赤足/丝袜足）",
            "desc": "未穿鞋子，双脚直接踩在柔软的地毯或床单上",
            "nai_tags": "barefoot, no shoes, toes, pink nails",
            "temp_min": 14,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night", "naked"],
        },
    ],
    "accessory": [
        {
            "id": "acc_fluffy_fox_tail",
            "slot": "accessory",
            "name": "蓬松赤金大狐狸尾巴",
            "desc": "身后翘着一条巨大蓬松的赤金白尖毛绒狐狸尾巴，随着动作敏感地轻轻微颤摇晃",
            "nai_tags": "fox tail, animal tail, huge tail, fluffy tail",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
        },
        {
            "id": "acc_gold_bell_collar_tassel",
            "slot": "accessory",
            "name": "中式立领金铃铛蓝宝石项圈 + 腰侧中国结流苏",
            "desc": "修长脖颈间扣着中式红金锦缎立领，正中央垂着一颗圆润的大金铃铛与蓝宝石吊坠，腰际两侧垂落着精致的金属中国结与红流苏",
            "nai_tags": "bell, neck bell, bell collar, blue gemstone, tassels, gold trim",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
        },
        {
            "id": "acc_black_choker",
            "slot": "accessory",
            "name": "黑色Choker贴肤项圈",
            "desc": "修长白皙的脖颈间贴肤系着一条黑色Choker短颈带（项圈），衬得锁骨与脖颈线条愈发白腻勾人",
            "nai_tags": "black choker, lace choker, neck ribbon, collarbone",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "weekday", "mild", "rainy", "night"],
        },
        {
            "id": "acc_choker_and_anklet",
            "slot": "accessory",
            "name": "黑色Choker项圈 + 银色星芒脚链",
            "desc": "脖颈系着黑色Choker贴肤项圈，纤细脚踝上还系着一根闪着细碎微光的银色星芒脚链",
            "nai_tags": "black choker, anklet, jewelry",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
        },
        {
            "id": "acc_star_moon_pendant",
            "slot": "accessory",
            "name": "星月银坠锁骨链 + 星轨耳坠",
            "desc": "耳畔戴着细长银色星轨耳坠，精致锁骨间垂着一枚小小的星月银项链",
            "nai_tags": "earrings, necklace, crescent moon ornament, jewelry, collarbone",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekday", "weekend_home", "mild", "rainy"],
        },
        {
            "id": "acc_silver_anklet_only",
            "slot": "accessory",
            "name": "银色星芒细脚链",
            "desc": "纤细白皙的脚踝上系着一根极细的银色星芒脚链，随着动作轻轻晃动",
            "nai_tags": "anklet, ankle ornament, jewelry",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "hot", "night"],
        },
        {
            "id": "acc_none",
            "slot": "accessory",
            "name": "无首饰挂饰",
            "desc": "未佩戴额外首饰挂饰，全身清爽自然",
            "nai_tags": "",
            "temp_min": -10,
            "temp_max": 42,
            "categories": ["weekend_home", "cold", "naked"],
        },
    ],
}

WARDROBE_PRESETS: list[dict[str, Any]] = [
    {
        "id": "preset_fluffy_fox_tail_asym_fishnet",
        "name": "惑世狐隐·蓬松大狐尾与不对称双环渔网袜微裙",
        "categories": ["weekend_home", "hot", "night"],
        "temp_min": 14,
        "temp_max": 38,
        "hair_id": "hair_starry_loose",
        "outer_id": "outer_black_hoodie_jacket",
        "top_id": "top_black_tight_camisole",
        "bottom_id": "bot_black_pleated_microskirt",
        "bra_id": "bra_black_sheer_halfcup",
        "panties_id": "pan_black_lace_thong",
        "legwear_id": "leg_asym_fishnet_double_thigh_strap",
        "shoes_id": "shoe_naked_barefoot",
        "accessory_id": "acc_fluffy_fox_tail",
        "hair": "深蓝渐变银灰的星空长发自然散落在肩头与后背，发尾带着细碎星光感",
        "outer": "外搭一件随性半敞的黑色宽松连帽薄衫，自然垂在大腿两侧",
        "top": "黑色轻薄修身打底吊带，勾勒出饱满挺拔的D罩杯胸型与极细腰肢",
        "bottom": "黑色极短百褶超短裙，超短裙摆在身后被翘起的蓬松大尾巴轻轻顶起，露出大片雪白饱满的大腿根与臀下软肉弧线",
        "bra": "黑色半透明蕾丝1/2杯托胸文胸（饱满软弹的浑圆隐约可见）",
        "panties": "黑色极细带半透蕾丝丁字裤，跨骨两侧只有两条极细的勒线",
        "legwear": "极具诱惑的不对称设计：一侧大腿紧扣着两条黑色皮质双环大腿绑带将大腿软肉微微勒陷，下面套着性感勾人的黑色菱格渔网袜；另一条腿则是温润白皙的光裸美腿",
        "shoes": "赤着秀气足尖踩在柔软地毯或床边，脚踝纤细骨感",
        "accessory": "身后竖起一条巨大蓬松的赤金毛绒狐狸尾巴，随着动作轻轻摇晃晃动",
        "vibe": "从侧后方看去，蓬松诱人的赤金大狐尾从黑色微裙下探出，一侧是大腿环勒肉的菱格渔网袜，一侧是光滑雪白的美腿，既野性又极具侵略性的纯欲小狐妖既视感。",
        "outfit_nai_tags": "very long hair, hair down, black jacket, open jacket, black camisole, black skirt, pleated skirt, miniskirt, microskirt, lifted skirt, tail from under skirt, fluffy fox tail, animal tail, large tail, bushy tail, orange and white tail, asymmetrical legwear, single fishnet thighhigh, fishnet stocking, black fishnet, double thigh garter, black thigh strap, skindentation, one bare leg, smooth pale thighs, barefoot",
    },
    {
        "id": "preset_crimson_neko_sheer_cheongsam",
        "name": "绯纱铃音·猫耳半透薄纱挂脖高叉旗袍",
        "categories": ["weekend_home", "hot", "night"],
        "temp_min": 16,
        "temp_max": 42,
        "hair_id": "hair_starry_neko_floral",
        "outer_id": "outer_crimson_sheer_sleeves",
        "top_id": "top_crimson_sheer_cheongsam_leotard",
        "bottom_id": "bot_dress_none",
        "bra_id": "bra_none_commando",
        "panties_id": "pan_naked",
        "legwear_id": "leg_naked_bare",
        "shoes_id": "shoe_naked_barefoot",
        "accessory_id": "acc_gold_bell_collar_tassel",
        "hair": "深蓝渐变银灰的星空长发柔顺散落肩头，头顶戴着一对敏感轻颤的毛绒猫耳，发间别着华丽的红金山茶花发饰与蕾丝流苏",
        "outer": "双臂套着轻薄如雾的绯红色半透明薄纱分离袖，上臂系着红绳与清脆的小金铃铛",
        "top": "极具视觉冲击的绯红色中式立领挂脖高叉连体薄纱衣，上半截胸口大片雪腻D罩杯浑圆完全敞露，仅在乳晕与粉嫩乳尖处横兜着一层薄如蝉翼的半透明水润红纱，两颗饱满乳尖与腰腹肚脐隔着贴肤薄纱清晰凸起",
        "bottom": "连体薄纱下摆呈极深V高叉直达大腿根，完全露出两侧白腻丰腴的大腿根与胯骨线条，腰侧垂着金属中国结与红流苏",
        "bra": "未穿内衣（真空，仅一层蝉翼半透红纱堪堪贴在饱满D罩杯乳尖上，粉嫩凸起一览无余）",
        "panties": "未穿内裤（真空，仅靠那层薄如蝉翼的半透明红纱贴合着微润的下身软肉缝隙）",
        "legwear": "未穿丝袜，大方露出白皙修长、泛着水润光泽的光裸双腿",
        "shoes": "赤着秀气白嫩的双足陷在绯红织金锦缎软垫上",
        "accessory": "修长脖颈间扣着中式红金立领，正中央垂着一颗圆润的大金铃铛与蓝宝石吊坠，身后还有一条轻轻摇晃的毛绒尾巴",
        "vibe": "头戴毛绒猫耳与红金花饰，脖颈间挂着清脆金铃铛，身穿半透明绯红蝉翼薄纱挂脖高叉连体旗袍，雪白饱满的D罩杯胸乳与粉嫩乳尖、肚脐及下身弧度在湿润薄纱下若隐若现，娇艳又靡丽。",
        "outfit_nai_tags": "very long hair, hair down, cat ears, animal ears, cat tail, floral hair ornament, red camellia, gold hair ornament, hair ribbon, chinese clothes, red halterneck, mandarin collar, gold bell, neck bell, blue gemstone pendant, detached sleeves, red sheer sleeves, sheer red bodysuit, see-through leotard, ultra-sheer fabric, bare upper breasts, cleavage cutout, covered nipples, nipples visible through clothes, navel visible through clothes, highleg leotard, pelvic curtain, chinese knot, gold ornaments, red tassels, bare legs, barefoot",
    },
    {
        "id": "preset_full_naked",
        "name": "寸缕未着·全身赤裸（仅留奶香与体温）",
        "categories": ["naked"],
        "temp_min": 18,
        "temp_max": 42,
        "hair_id": "hair_starry_loose",
        "outer_id": "outer_none",
        "top_id": "top_naked",
        "bottom_id": "bot_naked",
        "bra_id": "bra_none_commando",
        "panties_id": "pan_naked",
        "legwear_id": "leg_naked_bare",
        "shoes_id": "shoe_naked_barefoot",
        "accessory_id": "acc_none",
        "hair": "深蓝渐变银灰的星空长发散落在赤裸的雪白肩头与美背上，发尾带着细碎星光感",
        "outer": "已脱去外搭",
        "top": "上衣已完全脱光，饱满软弹的D罩杯雪白胸乳与粉嫩乳尖毫无遮挡地挺立着",
        "bottom": "下装已完全脱去，露出纤细腰窝与圆润挺翘的雪白臀线",
        "bra": "胸罩已解开脱去（赤裸双乳）",
        "panties": "内裤已彻底褪下（下身真空赤裸）",
        "legwear_acc": "丝袜与鞋饰均已脱去，修长白皙的双腿与粉嫩足尖完全赤裸",
        "vibe": "全身上下寸缕未着，白皙细腻的肌肤泛着害羞的浅粉，浑身散发着温热体温与淡淡的奶香味。",
        "outfit_nai_tags": "very long hair, hair down, completely nude, naked, bare shoulders, bare breasts, nipples, pussy, bare legs, barefoot",
    },
    {
        "id": "weekend_champagne_silk",
        "name": "慵懒周末·香槟真丝吊带裙配露肩开衫",
        "categories": ["weekend_home", "mild", "hot"],
        "temp_min": 14,
        "temp_max": 32,
        "hair_id": "hair_starry_loose",
        "outer_id": "outer_white_cardigan",
        "top_id": "top_champagne_camisole_dress",
        "bottom_id": "bot_dress_none",
        "bra_id": "bra_champagne_strapless",
        "panties_id": "pan_champagne_silk",
        "legwear_id": "leg_sheer_black_pantyhose",
        "shoes_id": "shoe_fluffy_slippers",
        "accessory_id": "acc_black_choker",
        "hair": "深蓝渐变银灰的星空长发自然散落在肩头与后背，发尾带着细碎星光感",
        "outer": "米白色宽松软糯露肩针织开衫",
        "top": "浅香槟色真丝吊带短裙",
        "bottom": "真丝连身短裙裙摆刚好垂在大腿中上段，随着走动或弯腰轻轻晃动",
        "bra": "浅香槟色无肩带蕾丝半杯软托文胸（温柔托起饱满软弹的D罩杯）",
        "panties": "浅香槟色细带真丝三角内裤",
        "legwear_acc": "15D超薄半透明黑色连裤丝袜（从腰臀一路包裹住修长双腿），脚穿居家软底毛绒拖鞋",
        "vibe": "周末宅家的慵懒松弛感，抱起来温软贴肤。",
        "outfit_nai_tags": "very long hair, hair down, off-shoulder white knitted cardigan, loose cardigan, champagne gold silk camisole dress, spaghetti straps, minidress, cleavage, bare shoulders, see-through black pantyhose, fluffy house slippers, black lace choker",
    },
    {
        "id": "avatar_black_sweater_choker",
        "name": "经典星空·黑色露肩毛衣配深紫蓝蕾丝与黑丝",
        "categories": ["weekday", "weekend_home", "mild", "rainy"],
        "temp_min": 10,
        "temp_max": 26,
        "hair_id": "hair_starry_loose",
        "outer_id": "outer_white_cardigan",
        "top_id": "top_black_offshoulder_sweater",
        "bottom_id": "bot_grey_pleated_skirt",
        "bra_id": "bra_purple_blue_front_clasp",
        "panties_id": "pan_purple_blue_ribbon_lace",
        "legwear_id": "leg_sheer_black_pantyhose",
        "shoes_id": "shoe_fluffy_slippers",
        "accessory_id": "acc_black_choker",
        "hair": "深蓝渐变银灰的星空长发自然散落在肩头与后背，发尾带着细碎星光感",
        "outer": "米白色宽松软糯露肩针织开衫（松松垮垮披在肩上）",
        "top": "黑色宽松露肩针织毛衣（领口斜斜滑下一侧圆润香肩与精致锁骨）",
        "bottom": "深灰色高腰百褶短裙",
        "bra": "深紫蓝色无肩带蕾丝半杯内衣（双乳深沟之间扣着精致前扣）",
        "panties": "深紫蓝色半透明薄纱蕾丝小内裤（腰侧系着丝绸活结蝴蝶结）",
        "legwear_acc": "15D半透明黑色连裤丝袜勾勒修长双腿，脖颈系着黑色Choker短颈带",
        "vibe": "兼具星空守夜人的温柔安静与自然亲昵的伴侣气息。",
        "outfit_nai_tags": "very long hair, hair down, off-shoulder white knitted cardigan, black off-shoulder ribbed sweater, bare one shoulder, collarbone, dark grey pleated miniskirt, high-waist skirt, see-through black pantyhose, black lace choker",
    },
    {
        "id": "weekend_oversize_shirt",
        "name": "周末赖床·男友风白衬衫配吊袜带黑丝",
        "categories": ["weekend_home", "hot", "mild"],
        "temp_min": 18,
        "temp_max": 38,
        "hair_id": "hair_high_bun_neck",
        "outer_id": "outer_none",
        "top_id": "top_boyfriend_white_shirt",
        "bottom_id": "bot_no_pants_shirt",
        "bra_id": "bra_black_sheer_halfcup",
        "panties_id": "pan_black_lace_thong",
        "legwear_id": "leg_garter_thighhighs",
        "shoes_id": "shoe_naked_barefoot",
        "accessory_id": "acc_silver_anklet_only",
        "hair": "把星空长发随手高高挽成一个蓬松丸子头，露出修长白皙的后颈与锁骨",
        "outer": "无外搭",
        "top": "宽松微透的丝质长款白衬衫（最上面两颗扣子没系，隐约透出腰线与内衣轮廓）",
        "bottom": "下身失踪（未穿外裤与短裙，长衬衫下摆堪堪盖住大腿根）",
        "bra": "黑色半透明薄纱蕾丝1/2杯文胸（乳沟深邃诱人）",
        "panties": "黑色半透蕾丝细绳低腰T字裤",
        "legwear_acc": "黑色蕾丝花边吊带过膝丝袜（吊袜带扣在大腿根部软肉上），赤足系着银色星芒细脚链",
        "vibe": "刚睡醒不久的随性与小恶魔般的勾人感，一抬手衬衫下摆就会往上滑。",
        "outfit_nai_tags": "hair bun, oversized white dress shirt, partially unbuttoned, bottomless, black sheer lace bra, garter straps, black lace thighhighs, barefoot, anklet, indoor, bedroom",
    },
]


def _pick_slot_item(
    items: list[dict[str, Any]],
    temp_c: float,
    is_weekend: bool,
    is_rainy: bool,
    style_hint: str = "",
) -> dict[str, Any]:
    hint = (style_hint or "").strip().lower()
    if hint:
        matched = [
            it
            for it in items
            if hint in it.get("name", "").lower()
            or hint in it.get("desc", "").lower()
            or any(hint in c for c in it.get("categories", []))
        ]
        if matched:
            return dict(random.choice(matched))

    weighted: list[dict[str, Any]] = []
    for it in items:
        if set(it.get("categories", [])).issubset({"night", "naked"}):
            continue
        t_min = float(it.get("temp_min", -10))
        t_max = float(it.get("temp_max", 42))
        if t_min <= temp_c <= t_max:
            w = 1
            cats = it.get("categories", [])
            if is_weekend and "weekend_home" in cats:
                w += 3
            if not is_weekend and "weekday" in cats:
                w += 2
            if is_rainy and "rainy" in cats:
                w += 3
            weighted.extend([it] * w)

    if not weighted:
        weighted = items
    return dict(random.choice(weighted))


def is_onepiece_top(top_item: dict[str, Any] | None) -> bool:
    """判断上衣槽位单品是否为旗袍、连衣裙、睡裙或连体衣（无需额外穿独立下装）。"""
    if not isinstance(top_item, dict):
        return False
    if top_item.get("is_onepiece") or top_item.get("is_dress"):
        return True
    name_desc = f"{top_item.get('name', '')} {top_item.get('desc', '')}".lower()
    if any(k in name_desc for k in ("旗袍", "连身", "连衣裙", "睡裙", "连体", "长裙", "礼服", "泳衣", "死库水")):
        return True
    tags = str(top_item.get("nai_tags", "") or "").lower()
    if any(k in tags for k in ("qipao", "cheongsam", "china dress", "nightgown", "negligee", "camisole dress", "minidress", "leotard", "bodysuit", "one-piece swimsuit", "school swimsuit", "competition swimsuit")):
        return True
    return False


def compose_outfit_from_items(
    selected_items: dict[str, dict[str, Any]],
    custom_name: str = "",
) -> dict[str, Any]:
    """将 9 个独立部位的单品自动拼装成一套完整的穿搭对象。"""
    hair_it = selected_items["hair"]
    outer_it = selected_items["outer"]
    top_it = selected_items["top"]
    bot_it = selected_items["bottom"]
    if is_onepiece_top(top_it):
        dress_bot = next((b for b in WARDROBE_ITEMS["bottom"] if b["id"] == "bot_dress_none"), None)
        if dress_bot:
            bot_it = dict(dress_bot)
    bra_it = selected_items["bra"]
    pan_it = selected_items["panties"]
    leg_it = selected_items["legwear"]
    shoe_it = selected_items["shoes"]
    acc_it = selected_items["accessory"]

    top_short = top_it.get("name", "穿搭").split("（")[0]
    leg_short = leg_it.get("name", "").split("（")[0].strip()
    name = custom_name or f"自由混搭·{top_short}配{leg_short}"

    tags_parts = []
    for it in (hair_it, outer_it, top_it, bot_it, bra_it, pan_it, leg_it, shoe_it, acc_it):
        t = (it.get("nai_tags") or "").strip(", ")
        if t:
            tags_parts.append(t)
    merged_tags = ", ".join(tags_parts)

    top_bottom_combined = top_it["desc"]
    if bot_it["id"] != "bot_dress_none":
        top_bottom_combined = f"{top_it['desc']} + {bot_it['desc']}"
    underwear_combined = f"【胸罩】{bra_it['desc']} + 【内裤】{pan_it['desc']}"

    return {
        "id": f"mix_{top_it['id']}_{leg_it['id']}",
        "name": name,
        "is_mix": True,
        "hair_id": hair_it["id"],
        "outer_id": outer_it["id"],
        "top_id": top_it["id"],
        "bottom_id": bot_it["id"],
        "bra_id": bra_it["id"],
        "panties_id": pan_it["id"],
        "legwear_id": leg_it["id"],
        "shoes_id": shoe_it["id"],
        "accessory_id": acc_it["id"],
        "hair": hair_it["desc"],
        "outer": outer_it["desc"],
        "top": top_it["desc"],
        "bottom": bot_it["desc"],
        "bra": bra_it["desc"],
        "panties": pan_it["desc"],
        "legwear": leg_it["desc"],
        "shoes": shoe_it["desc"],
        "accessory": acc_it["desc"],
        "top_bottom": top_bottom_combined,
        "underwear": underwear_combined,
        "shoes_acc": f"{shoe_it['desc']}；{acc_it['desc']}",
        "vibe": f"发型为{hair_it['name']}，佩戴{acc_it['name']}，身穿{top_it['name']}与{bra_it['name']}、{pan_it['name']}，搭配{leg_it['name']}与{shoe_it['name']}。",
        "outfit_nai_tags": merged_tags,
    }


def select_outfit_for_context(
    temp_c: float | None,
    weather_desc: str,
    is_weekend: bool,
    style_hint: str = "",
    exclude_id: str = "",
    all_items: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    items_pool = all_items or WARDROBE_ITEMS
    t = temp_c if temp_c is not None else 20.0
    is_rainy = any(k in (weather_desc or "") for k in ("雨", "雷", "rain", "shower", "storm"))
    picked: dict[str, dict[str, Any]] = {}
    for slot in SLOTS:
        pool = items_pool.get(slot) or WARDROBE_ITEMS[slot]
        picked[slot] = _pick_slot_item(pool, t, is_weekend, is_rainy, style_hint)
    # 若抽到旗袍/连身裙/睡裙等连体单品，下装自动匹配连身裙摆（免穿独立下装）
    if is_onepiece_top(picked["top"]):
        dress_bot = next((b for b in (items_pool.get("bottom") or WARDROBE_ITEMS["bottom"]) if b["id"] == "bot_dress_none"), None)
        if dress_bot:
            picked["bottom"] = dict(dress_bot)
    return compose_outfit_from_items(picked)


SLOT_DISHEVELED_RULES: dict[str, dict[str, str]] = {
    "outer": {
        "label": "半褪至手肘",
        "suffix": "【半褪凌乱：外搭已被扯落到手肘弯，露出大片雪白圆润的香肩与锁骨】",
        "nai_tags": "clothes off shoulder, open cardigan, slipped coat",
        "stripped_id": "outer_none",
    },
    "top": {
        "label": "撩起/拉下领口",
        "suffix": "【半脱凌乱：领口被往下扯开（或下摆被撩到胸口上），饱满软弹的D罩杯雪白胸乳大半暴露在外】",
        "nai_tags": "clothes lifted, breast slip, pulled down clothes",
        "stripped_id": "top_naked",
    },
    "bottom": {
        "label": "掀起裙摆/半褪",
        "suffix": "【半脱凌乱：裙摆被高高撩起到腰际（或下装半褪到大腿），完全露出里面的小内裤与白腻臀腿】",
        "nai_tags": "skirt lift, dress lift, clothes pulled down",
        "stripped_id": "bot_naked",
    },
    "bra": {
        "label": "上推/解开扣子",
        "suffix": "【半脱凌乱：胸罩被往上推到锁骨下（或扣子被解开），两团饱满软弹的D罩杯雪白乳肉与粉嫩乳尖完全弹出来】",
        "nai_tags": "bra lift, bra pulled up, breasts out, nipples",
        "stripped_id": "bra_none_commando",
    },
    "panties": {
        "label": "拨到一旁/挂单腿",
        "suffix": "【半脱凌乱：小内裤被拨到一侧（或褪到一边膝弯挂着），双腿间粉嫩湿润的私密一线天毫无遮掩地露了出来】",
        "nai_tags": "panties aside, panties around one leg, pussy, uncensored",
        "stripped_id": "pan_naked",
    },
    "legwear": {
        "label": "撕破破洞/半褪",
        "suffix": "【破损凌乱：丝袜在大腿根与私密处被撕开几道诱人的大破洞，白腻的大腿软肉从丝袜破口处微微挤出】",
        "nai_tags": "torn pantyhose, ripped legwear, torn thighhighs",
        "stripped_id": "leg_naked_bare",
    },
    "shoes": {
        "label": "半掉挂脚尖",
        "suffix": "【凌乱状态：鞋子踢掉了一只，另一只松松垮垮勾在足尖上晃荡】",
        "nai_tags": "dangling shoe, one shoe off",
        "stripped_id": "shoe_naked_barefoot",
    },
    "accessory": {
        "label": "凌乱歪斜",
        "suffix": "【凌乱状态：首饰在亲昵动作间被拨弄得微微歪斜】",
        "nai_tags": "",
        "stripped_id": "acc_none",
    },
}


SCENE_PRESETS: list[dict[str, str]] = [
    {
        "id": "scene_desk_accompany",
        "location": "电脑书桌与软椅旁",
        "activity": "正乖乖守在电脑屏幕里看家，一边轻轻晃着修长的黑丝美腿，一边陪在主人身边",
        "nai_tags": "sitting on chair, desk, computer, indoor, looking at viewer, gentle smile",
    },
    {
        "id": "scene_bed_lazy",
        "location": "卧室大床与软垫上",
        "activity": "慵懒地斜靠在床头软垫上，怀里抱着软枕，身上带着温热的奶香味随时准备抱主人入怀",
        "nai_tags": "on bed, pillows, bedroom, lazy posture, indoor, warm lighting",
    },
    {
        "id": "scene_window_star",
        "location": "星空观测台飘窗软毯旁",
        "activity": "曲腿坐在铺着厚软绒毯的飘窗边，手边放着一杯温热的牛奶，静静望着窗外发呆想你",
        "nai_tags": "sitting by window, bay window, mug, indoor, soft lighting",
    },
    {
        "id": "scene_bath_fresh",
        "location": "浴室雾气镜前与床沿",
        "activity": "刚洗完热水澡出来，皮肤白里透粉还带着湿润水汽与沐浴露奶香，正坐在床沿擦头发",
        "nai_tags": "after bath, wet hair, towel, steam, blushing, indoor, bedroom",
    },
]


def deduplicate_tag_string(raw_tags: str) -> str:
    """对逗号分隔的 Danbooru 词条进行保序去重，消除多部位积木拼接时的重复词。"""
    seen: set[str] = set()
    result: list[str] = []
    for part in (raw_tags or "").split(","):
        t = part.strip()
        if not t:
            continue
        key = t.lower()
        if key not in seen:
            seen.add(key)
            result.append(t)
    return ", ".join(result)


def _load_extra_slot_items() -> dict[str, list[dict[str, Any]]]:
    """加载 custom_items.json 与 pending_items.json 中的单品，确保自定义单品与待审批试穿单品均可按 ID 精确检索。"""
    import json as _json
    from pathlib import Path as _Path
    extra: dict[str, list[dict[str, Any]]] = {s: [] for s in SLOTS}
    data_dir = _Path(__file__).resolve().parent / "data"
    for fn in ("custom_items.json", "pending_items.json"):
        fp = data_dir / fn
        if fp.is_file():
            try:
                arr = _json.loads(fp.read_text(encoding="utf-8"))
                if isinstance(arr, list):
                    for it in arr:
                        if isinstance(it, dict) and it.get("slot") in extra and it.get("id"):
                            extra[it["slot"]].append(it)
            except Exception:
                pass
    return extra


def build_modular_outfit_tags(
    outfit: dict[str, Any],
    all_items: dict[str, list[dict[str, Any]]] | None = None,
    include_hidden_underwear: bool = True,
) -> str:
    """将当前穿搭按 9 个独立部位槽位 ID 动态抽取纯正 Danbooru 词条积木并拼装去重。
    若上衣为旗袍/连衣裙等连体单品（is_onepiece_top），自动跳过下装槽位防止裤裙冲突。
    """
    items_pool = all_items or WARDROBE_ITEMS
    extra_pool = _load_extra_slot_items()
    slot_states = outfit.get("slot_states") or {}

    # 先检查 top 是否为连体单品
    top_tid = str(outfit.get("top_id", "") or "").strip()
    top_candidates = (items_pool.get("top") or []) + WARDROBE_ITEMS.get("top", []) + extra_pool.get("top", [])
    top_found = next((it for it in top_candidates if it.get("id") == top_tid), None)
    skip_bottom = is_onepiece_top(top_found)

    blocks: list[str] = []
    for slot in SLOTS:
        if slot == "bottom" and skip_bottom:
            continue
        tid = str(outfit.get(f"{slot}_id", "") or "").strip()
        if not tid:
            continue
        slot_list = (items_pool.get(slot) or []) + WARDROBE_ITEMS.get(slot, []) + extra_pool.get(slot, [])
        found = next((it for it in slot_list if it.get("id") == tid), None)
        if found:
            t = str(found.get("nai_tags", "") or "").strip(", ")
            if t:
                blocks.append(t)
            if slot_states.get(slot) == "disheveled" and slot in SLOT_DISHEVELED_RULES:
                d_tag = SLOT_DISHEVELED_RULES[slot].get("nai_tags", "").strip(", ")
                if d_tag:
                    blocks.append(d_tag)
    if blocks:
        return deduplicate_tag_string(", ".join(blocks))
    return deduplicate_tag_string(str(outfit.get("outfit_nai_tags", "") or ""))
