# astrbot_plugin_daily_outfit — 9-Slot Modular Wardrobe & Outfit Codex for AstrBot

## Overview (English)

**`astrbot_plugin_daily_outfit`** is an open-source, modular 9-slot daily outfit & visual tag management plugin for [AstrBot](https://github.com/AstrBotDevs/AstrBot) AI companions.

- **9-Slot Modular Wardrobe Architecture**: Independently manages `hair`, `outer`, `top`, `bottom`, `bra`, `panties`, `legwear`, `shoes`, and `accessory` slots with automatic conflict resolution (e.g., one-piece dresses/cheongsams vs. separate bottoms) and per-slot disheveled/stripped state rules.
- **Offline QuickTag Clothing Codex**: Ships with **4,559+ curated Danbooru / NovelAI clothing & styling tag combinations** for zero-latency local search and automatic high-detail prompt completion.
- **Weather-Aware Daily Outfit Engine**: Automatically composes context-appropriate outfits based on local temperature, weather conditions, and weekday/weekend schedules.
- **Interactive WebUI Control Panel**: Features a responsive glassmorphism WebUI (`pages/wardrobe/`) for browsing slot items, approving AI-discovered clothing candidates, managing custom presets, and previewing synchronized character galleries.
- **Primary Maintainer**: [@Evenstar259](https://github.com/Evenstar259)
- **License**: [MIT License](./LICENSE)

---

# 👗 每日穿搭衣柜 (`astrbot_plugin_daily_outfit` v2.0.0)

面向 AstrBot 的 **9 部位模块化每日穿搭衣柜插件**。支持实时天气感知自动配装、单部位衣损/穿脱状态控制、内置 **4,559 条 QuickTagCloud 服饰词库** 增强与可视化 WebUI 换装管理面板，并可与 `astrbot_plugin_nai_image` (NAI 生图插件) 无缝联动。

---

## ✨ 核心功能

1. **🧩 9 部位模块化拼装引擎**
   - 细分为：`hair`（发型）、`outer`（外搭）、`top`（上衣/连衣裙）、`bottom`（下装）、`bra`（胸罩）、`panties`（内裤）、`legwear`（丝袜/腿饰）、`shoes`（鞋履）、`accessory`（首饰/配饰）。
   - 自动识别连体衣/连衣裙遮挡逻辑，动态拼装并去重生成纯正的 Danbooru / NovelAI 英文原子 Tag 串。

2. **🌤️ 真实天气感知与睡眠跨日换装**
   - 自动识别所在城市实时气温与天气（晴/雨/冷/热）以及工作日/周末/夜间场景，每日睡醒后自动挑选匹配的穿搭。
   - 支持设置「凌晨换日时间」与「跨日睡眠静默间隔」，防止熬夜聊天中途突然变装。

3. **🪄 单部位穿脱 / 半脱微乱状态控制**
   - WebUI 面板与 AI 工具均支持对任意单个部位切换 **「穿好 / 半脱微乱 / 脱下」** 状态，自动附加对应的 NAI 状态词条（如 `open clothes, off shoulder, clothes around ankles` 等）。

4. **📚 内置 4,559 条 QuickTagCloud 服饰词库 & 新衣审批池**
   - AI 调用 `add_wardrobe_clothing_item` 添置新衣或每日淘新衣时，自动检索内置的 4,559 条服饰标准词库补全高细节结构 Tag。
   - 支持开启「新衣入柜需审批」，新衣服先进入【待审批试穿池】临时试穿，通过 `/审批新衣 通过` 或在 WebUI 点击通过后才写入永久衣柜。

5. **⚙️ 全参数可自定义（零硬编码）**
   - 后台支持自由配置：`persona_name`（角色名称）、`owner_id`（私聊白名单）、`character_base_tags`（角色固定外貌底模）、`custom_body_traits`（角色附加设定）等，适配任意角色人设。

---

## 🛠️ 聊天指令与 AI 工具

### 聊天指令
- `/穿搭`：查看当前角色今日穿搭与实时衣着状态。
- `/换装 [风格关键词]`：让角色按指定风格（如：睡裙/白衬衫/针织裙/随机）重新换装。
- `/审批新衣 [通过|驳回|清空]`：查看或审核待审批池中的新衣服。

### AI 工具 (LLM Tools)
- `update_daily_outfit_state`：在互动中弄乱、脱下或局部更换衣物时实时同步状态。
- `switch_wardrobe_outfit`：从衣柜中重新挑选并换上一套新穿搭。
- `add_wardrobe_clothing_item`：按用户明确要求定制新衣物单品并补全标准 NAI Tag。
