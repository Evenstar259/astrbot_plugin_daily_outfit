from __future__ import annotations

import datetime
import json
import re
import time
from pathlib import Path
from typing import Any

import aiohttp

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star, StarTools
from astrbot.api.web import error_response, json_response
from astrbot.api.web import request as web_request

try:
    from .wardrobe import (
        STARRY_BASE_APPEARANCE_TAGS,
        WARDROBE_ITEMS,
        WARDROBE_PRESETS,
        SCENE_PRESETS,
        SLOT_DISHEVELED_RULES,
        build_modular_outfit_tags,
        compose_outfit_from_items,
        deduplicate_tag_string,
        is_onepiece_top,
        select_outfit_for_context,
    )
except ImportError:
    from wardrobe import (
        STARRY_BASE_APPEARANCE_TAGS,
        WARDROBE_ITEMS,
        WARDROBE_PRESETS,
        SCENE_PRESETS,
        SLOT_DISHEVELED_RULES,
        build_modular_outfit_tags,
        compose_outfit_from_items,
        deduplicate_tag_string,
        is_onepiece_top,
        select_outfit_for_context,
    )


try:
    from .gallery_core import (
        DEFAULT_THUMB_SIDE,
        GalleryError,
        clamp_thumb_side,
        delete_entry,
        directory_overview,
        filter_entries,
        load_params,
        mime_for,
        read_image_bytes,
        render_thumbnail_bytes,
        resolve_entry,
        scan_entries,
        to_data_url,
    )
except ImportError:
    from gallery_core import (
        DEFAULT_THUMB_SIDE,
        GalleryError,
        clamp_thumb_side,
        delete_entry,
        directory_overview,
        filter_entries,
        load_params,
        mime_for,
        read_image_bytes,
        render_thumbnail_bytes,
        resolve_entry,
        scan_entries,
        to_data_url,
    )

try:
    from .quicktag_service import (
        QUICKTAG_WEB_URL,
        auto_generate_detailed_nai_tags,
        discover_new_outfit_candidate,
        search_quicktag_clothing,
    )
except ImportError:
    from quicktag_service import (
        QUICKTAG_WEB_URL,
        auto_generate_detailed_nai_tags,
        discover_new_outfit_candidate,
        search_quicktag_clothing,
    )

PLUGIN_NAME = "astrbot_plugin_daily_outfit"
API_PREFIX = f"/{PLUGIN_NAME}/wardrobe"
LOG_TAG = "[DailyOutfit]"

WEEKDAY_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
SLOTS = ("hair", "outer", "top", "bottom", "bra", "panties", "legwear", "shoes", "accessory")

WMO_CODE_MAP = {
    0: "晴朗",
    1: "晴间多云",
    2: "多云",
    3: "阴天",
    45: "有雾",
    48: "雾凇",
    51: "毛毛雨",
    53: "小雨",
    55: "绵密小雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "阵雨",
    81: "中阵雨",
    82: "强阵雨",
    95: "雷阵雨",
    96: "雷阵雨伴冰雹",
    99: "强雷雨",
}


class DailyOutfitPlugin(Star):
    """每日穿搭衣柜插件：支持分部位单品自由拼装、整套预设、天气联动与 WebUI 换装室。"""

    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        self.config: dict[str, Any] = config if isinstance(config, dict) else {}
        self.data_dir = Path(__file__).resolve().parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / "outfit_state.json"
        self.custom_file = self.data_dir / "custom_wardrobe.json"
        self.custom_items_file = self.data_dir / "custom_items.json"
        self.pending_items_file = self.data_dir / "pending_items.json"
        self.nai_history_dir = StarTools.get_data_dir("astrbot_plugin_nai_image") / "image_history"
        self.thumb_dir = self.data_dir / "thumbs"
        self.thumb_dir.mkdir(parents=True, exist_ok=True)
        self.state: dict[str, Any] = self._load_state()
        self._register_web_apis()

    def _register_web_apis(self) -> None:
        try:
            self.context.register_web_api(
                f"{API_PREFIX}/status",
                self._api_status,
                ["GET"],
                "每日衣柜：获取今日穿搭、单品库与预设列表",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/equip",
                self._api_equip,
                ["POST"],
                "每日衣柜：切换整套预设或随机混搭换装",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/slot_action",
                self._api_slot_action,
                ["POST"],
                "每日衣柜：切换单部位完好/半脱破损/脱下状态",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/equip_parts",
                self._api_equip_parts,
                ["POST"],
                "每日衣柜：按五部位单品自由拼装换装",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/update_state",
                self._api_update_state,
                ["POST"],
                "每日衣柜：实时修改当前衣着细节与状态",

            )
            self.context.register_web_api(
                f"{API_PREFIX}/refresh_weather",
                self._api_refresh_weather,
                ["POST"],
                "每日衣柜：刷新天气信息",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/save_item",
                self._api_save_item,
                ["POST"],
                "每日衣柜：新增或编辑单件衣物",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/delete_item",
                self._api_delete_item,
                ["POST"],
                "每日衣柜：删除自定义单件衣物",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/save_preset",
                self._api_save_preset,
                ["POST"],
                "每日衣柜：新增或编辑套装预设",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/delete_preset",
                self._api_delete_preset,
                ["POST"],
                "每日衣柜：删除自定义套装预设",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/search_tags",
                self._api_search_tags,
                ["GET", "POST"],
                "每日衣柜：从 QuickTagCloud 词库检索或自动生成详细服饰 Tag",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/discover_new",
                self._api_discover_new,
                ["POST"],
                "每日衣柜：从 QuickTagCloud 自动淘一件新衣放入待审批池并试穿",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/approve_pending",
                self._api_approve_pending,
                ["POST"],
                "每日衣柜：审批通过待审核新衣正式入柜",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/reject_pending",
                self._api_reject_pending,
                ["POST"],
                "每日衣柜：驳回并丢弃待审核新衣",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/gallery_list",
                self._api_gallery_list,
                ["GET"],
                "每日衣柜：获取生图相册列表",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/gallery_thumb",
                self._api_gallery_thumb,
                ["GET"],
                "每日衣柜：获取相册缩略图",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/gallery_full",
                self._api_gallery_full,
                ["GET"],
                "每日衣柜：获取相册原图與参数",
            )
            self.context.register_web_api(
                f"{API_PREFIX}/gallery_delete",
                self._api_gallery_delete,
                ["POST"],
                "每日衣柜：删除相册图片",
            )
            logger.info(f"{LOG_TAG} WebUI API 已就绪 | prefix={API_PREFIX}")
        except Exception as e:
            logger.warning(f"{LOG_TAG} 注册 Web API 失败: {e}")

    async def initialize(self) -> None:
        self._register_web_apis()

    def _get_cfg(self, key: str, default: Any) -> Any:
        val = self.config.get(key, default)
        return default if val is None else val

    def _load_state(self) -> dict[str, Any]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"{LOG_TAG} 读取穿搭状态文件失败，将重新初始化: {e}")
        return {}

    def _save_state(self) -> None:
        try:
            self.state_file.write_text(
                json.dumps(self.state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"{LOG_TAG} 保存穿搭状态文件失败: {e}")


    def _load_pending_items(self) -> list[dict[str, Any]]:
        if self.pending_items_file.exists():
            try:
                data = json.loads(self.pending_items_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except Exception as e:
                logger.warning(f"{LOG_TAG} 读取待审批衣物文件失败: {e}")
        return []

    def _save_pending_items(self, items: list[dict[str, Any]]) -> None:
        try:
            self.pending_items_file.write_text(
                json.dumps(items, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"{LOG_TAG} 保存待审批衣物失败: {e}")

    def _load_custom_items(self) -> list[dict[str, Any]]:
        if self.custom_items_file.exists():
            try:
                data = json.loads(self.custom_items_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except Exception as e:
                logger.warning(f"{LOG_TAG} 读取自定义单品失败: {e}")
        return []

    def _save_custom_items(self, items: list[dict[str, Any]]) -> None:
        try:
            self.custom_items_file.write_text(
                json.dumps(items, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"{LOG_TAG} 保存自定义单品失败: {e}")

    def get_all_items_by_slot(self) -> dict[str, list[dict[str, Any]]]:
        custom = self._load_custom_items()
        custom_map = {it.get("id"): it for it in custom if isinstance(it, dict) and it.get("id")}
        result: dict[str, list[dict[str, Any]]] = {s: [] for s in SLOTS}
        builtin_ids = set()

        for slot in SLOTS:
            for it in WARDROBE_ITEMS.get(slot, []):
                iid = it["id"]
                builtin_ids.add(iid)
                merged = dict(it)
                if iid in custom_map:
                    merged.update(custom_map[iid])
                merged["builtin"] = True
                result[slot].append(merged)

        for it in custom:
            if not isinstance(it, dict):
                continue
            iid = it.get("id")
            slot = it.get("slot")
            if iid and iid not in builtin_ids and slot in result:
                merged = dict(it)
                merged["builtin"] = False
                result[slot].append(merged)

        return result

    def _load_custom_presets(self) -> list[dict[str, Any]]:
        if self.custom_file.exists():
            try:
                data = json.loads(self.custom_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except Exception as e:
                logger.warning(f"{LOG_TAG} 读取自定义衣柜失败: {e}")
        return []

    def _save_custom_presets(self, presets: list[dict[str, Any]]) -> None:
        try:
            self.custom_file.write_text(
                json.dumps(presets, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"{LOG_TAG} 保存自定义衣柜失败: {e}")

    def get_all_presets(self) -> list[dict[str, Any]]:
        custom = self._load_custom_presets()
        custom_map = {p.get("id"): p for p in custom if isinstance(p, dict) and p.get("id")}
        merged: list[dict[str, Any]] = []
        builtin_ids = set()
        for p in WARDROBE_PRESETS:
            pid = p["id"]
            builtin_ids.add(pid)
            item = dict(p)
            if pid in custom_map:
                item.update(custom_map[pid])
            item["builtin"] = True
            merged.append(item)
        for p in custom:
            if isinstance(p, dict) and p.get("id") and p["id"] not in builtin_ids:
                item = dict(p)
                item["builtin"] = False
                merged.append(item)
        return merged

    def _get_logical_date_str(self, now: datetime.datetime) -> str:
        refresh_hour = int(self._get_cfg("refresh_hour", 5))
        refresh_hour = max(0, min(12, refresh_hour))
        logical_dt = now - datetime.timedelta(hours=refresh_hour)
        return logical_dt.strftime("%Y-%m-%d")

    async def _fetch_weather(self) -> dict[str, Any]:
        configured_city = str(self._get_cfg("city", "")).strip()
        timeout = aiohttp.ClientTimeout(total=3.5)

        city_name = configured_city
        lat: float | None = None
        lon: float | None = None

        async with aiohttp.ClientSession(timeout=timeout) as session:
            if not city_name:
                try:
                    async with session.get("http://ip-api.com/json/?lang=zh-CN") as resp:
                        if resp.status == 200:
                            ip_data = await resp.json()
                            if ip_data.get("status") == "success":
                                city_name = ip_data.get("city") or ip_data.get("regionName") or ""
                                lat = ip_data.get("lat")
                                lon = ip_data.get("lon")
                except Exception as e:
                    logger.debug(f"{LOG_TAG} IP 自动定位跳过: {e}")

            if city_name and (lat is None or lon is None):
                try:
                    geo_url = (
                        f"https://geocoding-api.open-meteo.com/v1/search"
                        f"?name={city_name}&count=1&language=zh&format=json"
                    )
                    async with session.get(geo_url) as resp:
                        if resp.status == 200:
                            geo_data = await resp.json()
                            results = geo_data.get("results") or []
                            if results:
                                lat = results[0].get("latitude")
                                lon = results[0].get("longitude")
                                city_name = results[0].get("name") or city_name
                except Exception as e:
                    logger.debug(f"{LOG_TAG} 城市经纬度解析跳过: {e}")

            if lat is not None and lon is not None:
                try:
                    meteo_url = (
                        f"https://api.open-meteo.com/v1/forecast"
                        f"?latitude={lat}&longitude={lon}"
                        f"&current=temperature_2m,apparent_temperature,weather_code"
                        f"&daily=temperature_2m_max,temperature_2m_min"
                        f"&timezone=Asia%2FShanghai&forecast_days=1"
                    )
                    async with session.get(meteo_url) as resp:
                        if resp.status == 200:
                            m_data = await resp.json()
                            curr = m_data.get("current") or {}
                            daily = m_data.get("daily") or {}
                            temp_c = curr.get("temperature_2m")
                            w_code = int(curr.get("weather_code", 0))
                            w_desc = WMO_CODE_MAP.get(w_code, "晴间多云")
                            t_max_list = daily.get("temperature_2m_max") or []
                            t_min_list = daily.get("temperature_2m_min") or []
                            t_max = t_max_list[0] if t_max_list else temp_c
                            t_min = t_min_list[0] if t_min_list else temp_c
                            return {
                                "city": city_name or "本地",
                                "temp_c": float(temp_c) if temp_c is not None else 20.0,
                                "temp_min": t_min,
                                "temp_max": t_max,
                                "desc": w_desc,
                                "source": "open-meteo",
                            }
                except Exception as e:
                    logger.debug(f"{LOG_TAG} Open-Meteo 请求跳过: {e}")

            try:
                target = city_name if city_name else ""
                wttr_url = f"https://wttr.in/{target}?format=j1&lang=zh-cn"
                async with session.get(wttr_url) as resp:
                    if resp.status == 200:
                        w_data = await resp.json()
                        curr = (w_data.get("current_condition") or [{}])[0]
                        temp_c = float(curr.get("temp_C", 20.0))
                        lang_zh = curr.get("lang_zh-cn") or curr.get("weatherDesc") or [{}]
                        w_desc = lang_zh[0].get("value", "多云") if lang_zh else "多云"
                        return {
                            "city": city_name or "本地",
                            "temp_c": temp_c,
                            "temp_min": temp_c - 3,
                            "temp_max": temp_c + 4,
                            "desc": w_desc,
                            "source": "wttr.in",
                        }
            except Exception as e:
                logger.debug(f"{LOG_TAG} wttr.in 备用天气请求跳过: {e}")

        month = datetime.datetime.now().month
        if month in (12, 1, 2):
            fallback_temp, fallback_desc = 8.0, "冬日微凉"
        elif month in (6, 7, 8):
            fallback_temp, fallback_desc = 29.0, "夏日晴朗"
        else:
            fallback_temp, fallback_desc = 20.0, "春秋舒适"
        return {
            "city": city_name or "本地",
            "temp_c": fallback_temp,
            "temp_min": fallback_temp - 3,
            "temp_max": fallback_temp + 3,
            "desc": fallback_desc,
            "source": "seasonal_fallback",
        }

    def _should_refresh_for_new_day(self, now: datetime.datetime, now_ts: float) -> bool:
        if not self.state or not self.state.get("outfit"):
            return True

        current_logical_date = self._get_logical_date_str(now)
        saved_logical_date = self.state.get("logical_date", "")

        if current_logical_date == saved_logical_date:
            return False

        last_msg_ts = float(self.state.get("last_message_ts", 0.0))
        sleep_gap_hours = float(self._get_cfg("sleep_gap_hours", 3.0))
        if last_msg_ts > 0 and (now_ts - last_msg_ts) < sleep_gap_hours * 3600:
            logger.info(
                f"{LOG_TAG} 已过换日线 ({current_logical_date})，但距离上条消息仅 "
                f"{(now_ts - last_msg_ts) / 60:.1f} 分钟（未满 {sleep_gap_hours} 小时睡眠间隔），"
                f"判定为熬夜连续对话，保持当前穿搭不变。"
            )

            return False

        return True

    async def ensure_today_outfit(
        self,
        force_reroll: bool = False,
        style_hint: str = "",
        preset_id: str = "",
    ) -> dict[str, Any]:
        disk_state = self._load_state()
        if disk_state:
            self.state = disk_state
        now = datetime.datetime.now()
        now_ts = time.time()

        if force_reroll or preset_id or self._should_refresh_for_new_day(now, now_ts):
            weather = (
                self.state.get("weather")
                if (not self._should_refresh_for_new_day(now, now_ts) and self.state.get("weather"))
                else await self._fetch_weather()
            )
            is_weekend = now.weekday() >= 5
            all_presets = self.get_all_presets()
            all_items = self.get_all_items_by_slot()
            prev_id = (self.state.get("outfit") or {}).get("id", "")

            chosen: dict[str, Any] | None = None
            if preset_id:
                for p in all_presets:
                    if p.get("id") == preset_id:
                        chosen = dict(p)
                        break

            if not chosen:
                chosen = select_outfit_for_context(
                    temp_c=weather.get("temp_c"),
                    weather_desc=weather.get("desc", ""),
                    is_weekend=is_weekend,
                    style_hint=style_hint,
                    exclude_id=prev_id,
                    all_items=all_items,
                )
                # 若开启了「每日换装自动淘新衣」开关，则自动从 QuickTagCloud 词库淘一件新衣试穿并放入待审批列表
                if bool(self._get_cfg("enable_auto_discover_outfit", False)):
                    cand = discover_new_outfit_candidate(
                        temp_c=float(weather.get("temp_c") or 20.0),
                        style_hint=style_hint,
                    )
                    if cand:
                        pending_list = self._load_pending_items()
                        pending_list.insert(0, cand)
                        self._save_pending_items(pending_list[:30])
                        chosen["name"] = f"今日淘新试穿·{cand['name']}（待主人审批入柜）"
                        chosen["top"] = cand["desc"]
                        chosen["top_bottom"] = f"{cand['desc']} + {chosen.get('bottom', '')}"
                        chosen["outfit_nai_tags"] = deduplicate_tag_string(
                            f"{cand['nai_tags']}, {chosen.get('outfit_nai_tags', '')}"
                        )
                        chosen["pending_candidate_id"] = cand["id"]

            logical_date = self._get_logical_date_str(now)
            prev_showcase = str((self.state or {}).get("showcase_image") or "")
            self.state = {
                "logical_date": logical_date,
                "showcase_image": prev_showcase,
                "real_date": now.strftime("%Y-%m-%d"),
                "weekday_cn": WEEKDAY_CN[now.weekday()],
                "is_weekend": is_weekend,
                "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "last_message_ts": now_ts,
                "weather": weather,
                "outfit": chosen,
                "status_note": "穿戴整洁完好（初始状态）",
                "history_notes": [
                    {
                        "time": now.strftime("%H:%M:%S"),
                        "status": f"换上【{chosen.get('name', '新穿搭')}】",
                    }
                ],
            }
            self._save_state()
        else:
            # 补齐旧存档里的单品 ID 默认映射
            outfit = self.state.setdefault("outfit", {})
            outfit.setdefault("hair_id", "hair_starry_loose")
            outfit.setdefault("outer_id", "outer_white_cardigan")
            outfit.setdefault("top_id", "top_champagne_camisole_dress")
            outfit.setdefault("bottom_id", "bot_dress_none")
            outfit.setdefault("bra_id", "bra_champagne_strapless")
            outfit.setdefault("panties_id", "pan_champagne_silk")
            outfit.setdefault("legwear_id", "leg_sheer_black_pantyhose")
            outfit.setdefault("shoes_id", "shoe_fluffy_slippers")
            outfit.setdefault("accessory_id", "acc_black_choker")
            outfit.setdefault("hair", "深蓝渐变银灰的星空长发自然散落在肩头与后背，发尾带着细碎星光感")
            outfit.setdefault("top", outfit.get("top_bottom", "浅香槟色真丝吊带短裙"))
            outfit.setdefault("bottom", "真丝连身短裙裙摆刚好垂在大腿中上段")
            outfit.setdefault("bra", "浅香槟色无肩带蕾丝半杯软托文胸")
            outfit.setdefault("panties", "浅香槟色细带真丝三角内裤")
            outfit.setdefault("legwear", "15D超薄半透明黑色连裤丝袜（从腰臀一路包裹住修长双腿）")
            outfit.setdefault("shoes", "脚穿软乎乎的居家软底毛绒拖鞋")
            outfit.setdefault("accessory", "修长白皙的脖颈间贴肤系着一条黑色Choker短颈带（项圈）")
            self.state["last_message_ts"] = now_ts
            self._save_state()

        return self.state

    def _persona_name(self) -> str:
        return str(self._get_cfg("persona_name", "伴侣") or "伴侣").strip()

    def _build_full_nai_tags(self, outfit: dict[str, Any]) -> str:
        """按【固定身体底模词条包 + 9部位单品积木词条包】动态拼装并保序去重。"""
        base_tags = str(self._get_cfg("character_base_tags", "") or "").strip(", ")
        modular_outfit_tags = build_modular_outfit_tags(outfit, self.get_all_items_by_slot())
        if modular_outfit_tags:
            outfit["outfit_nai_tags"] = modular_outfit_tags
            return deduplicate_tag_string(f"{base_tags}, {modular_outfit_tags}" if base_tags else modular_outfit_tags)
        raw_outfit_tags = str(outfit.get("outfit_nai_tags", "") or "").strip(", ")
        if raw_outfit_tags:
            return deduplicate_tag_string(f"{base_tags}, {raw_outfit_tags}" if base_tags else raw_outfit_tags)
        return deduplicate_tag_string(base_tags)

    def format_outfit_prompt_block(self, state: dict[str, Any], full_detail: bool = False) -> str:
        outfit = state.get("outfit") or {}
        weather = state.get("weather") or {}
        full_nai_tags = self._build_full_nai_tags(outfit)
        status_note = state.get("status_note", "穿戴整洁完好")
        p_name = self._persona_name()

        pending_count = len(self._load_pending_items())
        pending_hint = f"- 【待主人审批新衣】：当前待审批池中有 {pending_count} 件新衣等待主人审核（主人可发 `/审批新衣` 或在面板审批）。\n" if pending_count > 0 else ""
        nai_tag_rule = (
            pending_hint
            + "- 【新增衣物触发边界与审批铁律】：主人平时正常转发瑟图、穿搭图或日常图片时，**严禁**自作主张调用 `add_wardrobe_clothing_item` 往衣柜塞衣服！**只有当主人明确提出“把这件加进衣柜 / 我想看你穿这套 / 买一件这个”的需求时**，才可调用工具创建新衣（默认先进待审批试穿池，待主人审批通过后再正式入库）。\n"
            + "- 【新增/更换衣物 NAI Tag 铁律】：每当有新衣服加入衣柜或调用 `update_daily_outfit_state` 换穿新衣物时，"
            "必须结合 QuickTagCloud (novelai.quicktagcloud.com) 词库编写高度细分、纯正标准的 Danbooru / NovelAI 英文原子 Tag 组合（严禁笼统长句），"
            "须完整涵盖：服装品类、颜色材质、领口/裙摆剪裁、不对称(asymmetrical legwear)/勒肉(skindentation)/半透(see-through)等结构锁死词及穿戴位置，确保多次生图效果稳定一致。\n"
        )

        if not full_detail:
            return (
                "\n\n<daily_outfit_context>\n"
                f"【{p_name}衣柜静默背景（{state.get('real_date', '')} · 普通日常对话模式）】\n"
                f"- 今日天气：{weather.get('city', '本地')} · {weather.get('desc', '舒适')}（约 {weather.get('temp_c', 20)}°C）\n"
                f"- 当前衣着状态：{status_note}（当前为普通日常聊天/情感陪伴，衣柜单品已静默隐藏；严禁在动作描写或台词中主动提及任何衣服、口袋、丝袜、高跟鞋或胸围尺寸！）\n"
                f"- 角色块1（{p_name}外貌+当前穿搭基底，NAI_Generate_Image底层已自动挂载）：{full_nai_tags}\n"
                f"- NAI V4.5 角色块生图规范：调用 NAI_Generate_Image 时采用分块模式——`prompt` 只填全局人数（1girl, solo 或 1girl, 1boy）、背景环境、光影氛围与镜头视角；`char1_prompt` 只填{p_name}当前的姿势、表情与局部衣着动作（底层会自动合并上面的外貌+穿搭基底；若需临时换穿其他特定服装则将 use_wardrobe 设为 false 并在 char1_prompt 中写完整穿搭）；双人互动时在 `char2_prompt` 中填写男主（主人）的体态与互动动作（如 1boy, faceless male, target#...）。\n"
                + nai_tag_rule
                + "</daily_outfit_context>"
            )

        body_traits = str(self._get_cfg("custom_body_traits", "") or "").strip()
        traits_line = f"- 专属体质与设定：{body_traits}\n" if body_traits else ""
        return (
            "\n\n<daily_outfit_context>\n"
            f"【{p_name}今日穿搭与实时衣着状态（{state.get('real_date', '')} {state.get('weekday_cn', '')}）】\n"
            f"- 今日天气：{weather.get('city', '本地')} · {weather.get('desc', '舒适')}（约 {weather.get('temp_c', 20)}°C）\n"
            f"- 穿搭主题：{outfit.get('name', '日常穿搭')}\n"
            f"- 发型：{outfit.get('hair', '自然披肩长发')}\n"
            f"- 外搭/外套：{outfit.get('outer', '无')}\n"
            f"- 上衣/连身裙：{outfit.get('top', outfit.get('top_bottom', ''))}\n"
            f"- 下装/裙裤：{outfit.get('bottom', '')}\n"
            f"- 贴身胸罩：{outfit.get('bra', outfit.get('underwear', ''))}\n"
            f"- 贴身内裤：{outfit.get('panties', '')}\n"
            f"- 腿部/丝袜：{outfit.get('legwear', '')}\n"
            f"- 鞋履/足部：{outfit.get('shoes', '')}\n"
            f"- 首饰/挂饰：{outfit.get('accessory', '')}\n"
            f"- 当前衣着实时状态：{status_note}\n"
            + traits_line
            + f"- 配套 NAI 生图 Tags（如需自拍或画图请直接采用）：{full_nai_tags}\n"
            + nai_tag_rule
            + "提示：仅在涉及衣着或亲密互动时自然带出相关细节，严禁像报菜名一样堆砌所有部位。若衣服被弄乱、半脱或更换，可调用 `update_daily_outfit_state` 记录。\n"
            "</daily_outfit_context>"
        )

    # ------------------------------------------------------------------ Web API

    async def _api_status(self) -> Any:
        try:
            state = await self.ensure_today_outfit()
            outfit = state.get("outfit") or {}
            return json_response(
                {
                    "status": "ok",
                    "state": state,
                    "full_nai_tags": self._build_full_nai_tags(outfit),
                    "items_by_slot": self.get_all_items_by_slot(),
                    "presets": self.get_all_presets(),
                    "pending_items": self._load_pending_items(),
                    "scenes": SCENE_PRESETS,
                    "config": {
                        "persona_name": self._persona_name(),
                        "refresh_hour": int(self._get_cfg("refresh_hour", 5)),
                        "sleep_gap_hours": float(self._get_cfg("sleep_gap_hours", 3.0)),
                        "city": str(self._get_cfg("city", "")),
                    },
                }
            )
        except Exception as e:
            logger.error(f"{LOG_TAG} [_api_status] 错误: {e}", exc_info=True)
            return error_response(f"读取衣柜状态失败: {e}", status_code=500)

    async def _api_equip(self) -> Any:
        body = await web_request.json(default={})
        preset_id = str(body.get("preset_id", "") or "").strip()
        style_hint = str(body.get("style_hint", "") or "").strip()
        try:
            state = await self.ensure_today_outfit(
                force_reroll=True,
                style_hint=style_hint,
                preset_id=preset_id,
            )
            outfit = state.get("outfit") or {}
            return json_response(
                {
                    "status": "ok",
                    "state": state,
                    "full_nai_tags": self._build_full_nai_tags(outfit),
                }
            )
        except Exception as e:
            logger.error(f"{LOG_TAG} [_api_equip] 错误: {e}", exc_info=True)
            return error_response(f"换装失败: {e}", status_code=500)


    async def _api_slot_action(self) -> Any:
        """切换单个部位的状态：normal(完好) / disheveled(半脱·破损) / stripped(脱下)。"""
        body = await web_request.json(default={})
        slot = str((body or {}).get("slot", "") or "").strip()
        mode = str((body or {}).get("mode", "normal") or "normal").strip()
        if slot not in SLOTS:
            return error_response("无效部位", status_code=400)

        try:
            state = await self.ensure_today_outfit()
            curr_outfit = state.setdefault("outfit", {})
            all_items = self.get_all_items_by_slot()
            slot_states: dict[str, str] = curr_outfit.setdefault("slot_states", {})
            prev_orig_ids: dict[str, str] = curr_outfit.setdefault("orig_slot_ids", {})

            rule = SLOT_DISHEVELED_RULES.get(slot, {})
            stripped_id = rule.get("stripped_id", "")

            # 记录脱下前的原始单品 ID，方便点“完好”或“半脱”时恢复原衣物
            curr_id = str(curr_outfit.get(f"{slot}_id", "") or "")
            if curr_id and curr_id != stripped_id:
                prev_orig_ids[slot] = curr_id

            if mode == "stripped" and stripped_id:
                curr_outfit[f"{slot}_id"] = stripped_id
                slot_states[slot] = "stripped"
            else:
                if curr_id == stripped_id and prev_orig_ids.get(slot):
                    curr_outfit[f"{slot}_id"] = prev_orig_ids[slot]
                slot_states[slot] = mode

            # 重新根据 9 个部位组装基础穿搭
            selected: dict[str, dict[str, Any]] = {}
            for s in SLOTS:
                tid = str(curr_outfit.get(f"{s}_id", "") or "")
                s_list = all_items.get(s) or []
                found = next((it for it in s_list if it.get("id") == tid), None)
                if not found and s_list:
                    found = s_list[0]
                selected[s] = dict(found) if found else {"id": "none", "name": "无", "desc": "无", "nai_tags": ""}

            # 叠加 disheveled 半脱/破损描述与 NAI Tag
            active_notes: list[str] = []
            for s, st_mode in list(slot_states.items()):
                if st_mode == "disheveled" and s in SLOT_DISHEVELED_RULES and s in selected:
                    r = SLOT_DISHEVELED_RULES[s]
                    selected[s]["desc"] = f"{selected[s]['desc']} {r['suffix']}"
                    extra_tag = r.get("nai_tags", "")
                    if extra_tag:
                        selected[s]["nai_tags"] = f"{selected[s].get('nai_tags', '')}, {extra_tag}".strip(", ")
                    active_notes.append(f"{selected[s]['name']}{r['label']}")
                elif st_mode == "stripped" and s in selected:
                    active_notes.append(f"{selected[s]['name']}")

            composed = compose_outfit_from_items(selected, custom_name=curr_outfit.get("name", ""))
            composed["slot_states"] = slot_states
            composed["orig_slot_ids"] = prev_orig_ids
            state["outfit"] = composed

            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            if active_notes:
                summary = "当前局部状态：" + "；".join(active_notes)
            else:
                summary = "全身衣物已整理恢复完好"
            state["status_note"] = summary
            state.setdefault("history_notes", []).append({"time": now_str, "status": summary})
            self._save_state()

            return json_response(
                {
                    "status": "ok",
                    "state": state,
                    "full_nai_tags": self._build_full_nai_tags(composed),
                }
            )
        except Exception as e:
            logger.error(f"{LOG_TAG} [_api_slot_action] 错误: {e}", exc_info=True)
            return error_response(f"操作失败: {e}", status_code=500)

    async def _api_equip_parts(self) -> Any:
        """按 5 个部位的单品 ID 自由拼装并立即换上（支持只传某一个部位 ID 单独换单件）。"""
        body = await web_request.json(default={})
        if not isinstance(body, dict):
            return error_response("参数错误", status_code=400)

        try:
            state = await self.ensure_today_outfit()
            curr_outfit = state.get("outfit") or {}
            all_items = self.get_all_items_by_slot()

            selected: dict[str, dict[str, Any]] = {}
            for slot in SLOTS:
                req_id = str(body.get(f"{slot}_id", "") or "").strip()
                target_id = req_id or str(curr_outfit.get(f"{slot}_id", "") or "")
                slot_list = all_items.get(slot) or []
                found = next((it for it in slot_list if it.get("id") == target_id), None)
                if not found and slot_list:
                    found = slot_list[0]
                selected[slot] = found or {"id": "none", "name": "无", "desc": "无", "nai_tags": ""}

            custom_name = str(body.get("custom_name", "") or "").strip()
            composed = compose_outfit_from_items(selected, custom_name=custom_name)
            now = datetime.datetime.now()
            state["outfit"] = composed
            state["generated_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
            state["status_note"] = f"刚在衣柜自由拼装换上：{composed['name']}"
            history = state.setdefault("history_notes", [])
            history.append(
                {
                    "time": now.strftime("%H:%M:%S"),
                    "status": f"单品拼装换上【{composed['name']}】",
                }
            )
            self._save_state()
            return json_response(
                {
                    "status": "ok",
                    "state": state,
                    "full_nai_tags": self._build_full_nai_tags(composed),
                }
            )
        except Exception as e:
            logger.error(f"{LOG_TAG} [_api_equip_parts] 错误: {e}", exc_info=True)
            return error_response(f"拼装换装失败: {e}", status_code=500)


    async def _api_save_item(self) -> Any:
        body = await web_request.json(default={})
        if not isinstance(body, dict):
            return error_response("参数错误", status_code=400)
        slot = str(body.get("slot", "") or "").strip()
        if slot not in SLOTS:
            return error_response("无效的部位分类", status_code=400)
        name = str(body.get("name", "") or "").strip()
        desc = str(body.get("desc", "") or "").strip()
        if not name or not desc:
            return error_response("请填写单品名称与描述", status_code=400)

        item_id = str(body.get("id", "") or "").strip() or f"item_{slot}_{int(time.time())}"
        cats = body.get("categories")
        if isinstance(cats, str):
            cats = [c.strip() for c in cats.split(",") if c.strip()]
        elif not isinstance(cats, list) or not cats:
            cats = ["weekend_home", "weekday", "mild"]

        raw_nai_tags = str(body.get("nai_tags", "") or "").strip()
        # 若未填写详细 Tag 或少于 3 个词，自动去 QuickTagCloud 服饰词库检索并按详细标准 Tag 补全
        if len([x for x in raw_nai_tags.split(",") if x.strip()]) < 3:
            raw_nai_tags = auto_generate_detailed_nai_tags(name, desc, raw_nai_tags)

        new_item = {
            "id": item_id,
            "slot": slot,
            "name": name,
            "desc": desc,
            "nai_tags": raw_nai_tags,
            "temp_min": float(body.get("temp_min", 10)),
            "temp_max": float(body.get("temp_max", 35)),
            "categories": cats,
        }
        custom = self._load_custom_items()
        replaced = False
        for i, it in enumerate(custom):
            if isinstance(it, dict) and it.get("id") == item_id:
                custom[i] = new_item
                replaced = True
                break
        if not replaced:
            custom.append(new_item)
        self._save_custom_items(custom)
        return json_response(
            {
                "status": "ok",
                "item": new_item,
                "items_by_slot": self.get_all_items_by_slot(),
            }
        )

    async def _api_delete_item(self) -> Any:
        body = await web_request.json(default={})
        item_id = str((body or {}).get("id", "") or "").strip()
        if not item_id:
            return error_response("缺少单品 ID", status_code=400)
        custom = [it for it in self._load_custom_items() if isinstance(it, dict) and it.get("id") != item_id]
        self._save_custom_items(custom)
        return json_response({"status": "ok", "items_by_slot": self.get_all_items_by_slot()})

    async def _api_update_state(self) -> Any:
        body = await web_request.json(default={})
        if not isinstance(body, dict):
            return error_response("参数格式错误", status_code=400)
        try:
            state = await self.ensure_today_outfit()
            outfit = state.setdefault("outfit", {})
            status_note = str(body.get("status_note", "") or "").strip()
            if body.get("location"):
                state["location"] = str(body["location"]).strip()
            if body.get("activity"):
                state["activity"] = str(body["activity"]).strip()
            if status_note:
                state["status_note"] = status_note
                history = state.setdefault("history_notes", [])
                history.append(
                    {
                        "time": datetime.datetime.now().strftime("%H:%M:%S"),
                        "status": status_note,
                    }
                )
            for field in ("name", "hair", "outer", "top", "bottom", "bra", "panties", "legwear", "shoes", "accessory", "top_bottom", "underwear", "shoes_acc", "vibe", "outfit_nai_tags"):
                if field in body and body[field] is not None:
                    val = str(body[field]).strip()
                    if val:
                        outfit[field] = val
            self._save_state()
            return json_response(
                {
                    "status": "ok",
                    "state": state,
                    "full_nai_tags": self._build_full_nai_tags(outfit),
                }
            )
        except Exception as e:
            logger.error(f"{LOG_TAG} [_api_update_state] 错误: {e}", exc_info=True)
            return error_response(f"更新状态失败: {e}", status_code=500)

    async def _api_refresh_weather(self) -> Any:
        try:
            state = await self.ensure_today_outfit()
            weather = await self._fetch_weather()
            state["weather"] = weather
            self._save_state()
            return json_response({"status": "ok", "weather": weather, "state": state})
        except Exception as e:
            return error_response(f"刷新天气失败: {e}", status_code=500)

    async def _api_save_preset(self) -> Any:
        body = await web_request.json(default={})
        if not isinstance(body, dict):
            return error_response("参数错误", status_code=400)
        name = str(body.get("name", "") or "").strip()
        if not name:
            return error_response("请填写穿搭名称", status_code=400)
        preset_id = str(body.get("id", "") or "").strip() or f"custom_{int(time.time())}"
        cats = body.get("categories")
        if isinstance(cats, str):
            cats = [c.strip() for c in cats.split(",") if c.strip()]
        elif not isinstance(cats, list) or not cats:
            cats = ["weekend_home", "weekday", "mild"]

        new_preset = {
            "id": preset_id,
            "name": name,
            "categories": cats,
            "temp_min": float(body.get("temp_min", 10)),
            "temp_max": float(body.get("temp_max", 32)),
            "outer": str(body.get("outer", "无外套") or "").strip(),
            "top_bottom": str(body.get("top_bottom", "") or "").strip(),
            "underwear": str(body.get("underwear", "") or "").strip(),
            "legwear": str(body.get("legwear", "") or "").strip(),
            "shoes_acc": str(body.get("shoes_acc", "") or "").strip(),
            "vibe": str(body.get("vibe", "") or "").strip(),
            "outfit_nai_tags": (
                str(body.get("outfit_nai_tags", "") or "").strip()
                if len([x for x in str(body.get("outfit_nai_tags", "") or "").split(",") if x.strip()]) >= 4
                else auto_generate_detailed_nai_tags(
                    name,
                    f"{body.get('outer', '')} {body.get('top_bottom', '')} {body.get('underwear', '')} {body.get('legwear', '')} {body.get('shoes_acc', '')}",
                    str(body.get("outfit_nai_tags", "") or "").strip(),
                )
            ),
        }
        custom = self._load_custom_presets()
        replaced = False
        for i, item in enumerate(custom):
            if isinstance(item, dict) and item.get("id") == preset_id:
                custom[i] = new_preset
                replaced = True
                break
        if not replaced:
            custom.append(new_preset)
        self._save_custom_presets(custom)
        return json_response(
            {
                "status": "ok",
                "preset": new_preset,
                "presets": self.get_all_presets(),
                    "scenes": SCENE_PRESETS,
            }
        )

    async def _api_delete_preset(self) -> Any:
        body = await web_request.json(default={})
        preset_id = str((body or {}).get("id", "") or "").strip()
        if not preset_id:
            return error_response("缺少预设 ID", status_code=400)
        custom = [p for p in self._load_custom_presets() if isinstance(p, dict) and p.get("id") != preset_id]
        self._save_custom_presets(custom)
        return json_response({"status": "ok", "presets": self.get_all_presets()})




    async def _api_discover_new(self) -> Any:
        """从 QuickTagCloud 词库自动淘出一件新衣服放入待审批池，并可选择立即试穿。"""
        body = await web_request.json(default={})
        style_hint = str((body or {}).get("style_hint", "") or "").strip()
        try_on = bool((body or {}).get("try_on", True))
        state = await self.ensure_today_outfit()
        weather = state.get("weather") or {}
        cand = discover_new_outfit_candidate(
            temp_c=float(weather.get("temp_c") or 20.0),
            style_hint=style_hint,
        )
        if not cand:
            return error_response("词库为空，无法自动淘新衣", status_code=404)
        pending_list = self._load_pending_items()
        pending_list.insert(0, cand)
        self._save_pending_items(pending_list[:30])
        if try_on:
            outfit = state.setdefault("outfit", {})
            outfit["name"] = f"试穿新衣·{cand['name']}（待审批）"
            outfit["top"] = cand["desc"]
            outfit["top_bottom"] = cand["desc"]
            outfit["outfit_nai_tags"] = deduplicate_tag_string(
                f"{cand['nai_tags']}, {outfit.get('outfit_nai_tags', '')}"
            )
            outfit["pending_candidate_id"] = cand["id"]
            state["status_note"] = f"正在试穿新淘来的【{cand['name']}】（等待主人审批是否入柜）"
            self._save_state()
        return json_response(
            {
                "status": "ok",
                "candidate": cand,
                "pending_items": pending_list[:30],
                "state": state,
                "full_nai_tags": self._build_full_nai_tags(state.get("outfit") or {}),
            }
        )

    async def _api_approve_pending(self) -> Any:
        """审批通过某件待审核新衣，正式写入永久单品库。"""
        body = await web_request.json(default={})
        target_id = str((body or {}).get("id", "") or "").strip()
        pending_list = self._load_pending_items()
        if not pending_list:
            return error_response("当前没有待审批的新衣服", status_code=404)
        chosen = None
        rest = []
        for it in pending_list:
            if not chosen and (not target_id or it.get("id") == target_id):
                chosen = it
            else:
                rest.append(it)
        if not chosen:
            return error_response("未找到指定的待审批衣物", status_code=404)
        self._save_pending_items(rest)
        slot_clean = str(chosen.get("slot") or "top").strip()
        if slot_clean not in SLOTS:
            slot_clean = "top"
        formal_item = {
            "id": f"custom_{slot_clean}_{int(time.time())}",
            "slot": slot_clean,
            "name": str(chosen.get("name") or "新衣物").strip(),
            "desc": str(chosen.get("desc") or "").strip(),
            "nai_tags": str(chosen.get("nai_tags") or "").strip(),
            "temp_min": float(chosen.get("temp_min", 10.0)),
            "temp_max": float(chosen.get("temp_max", 38.0)),
            "categories": chosen.get("categories") or ["weekend_home", "weekday", "mild", "hot", "night"],
        }
        if slot_clean == "top" and is_onepiece_top(formal_item):
            formal_item["is_onepiece"] = True
            formal_item["is_dress"] = True
        custom = self._load_custom_items()
        custom.append(formal_item)
        self._save_custom_items(custom)
        state = self._load_state()
        if isinstance(state.get("outfit"), dict) and state["outfit"].get(f"{slot_clean}_id") == chosen.get("id"):
            state["outfit"][f"{slot_clean}_id"] = formal_item["id"]
            self._save_state()
        return json_response(
            {
                "status": "ok",
                "approved_item": formal_item,
                "pending_items": rest,
                "items_by_slot": self.get_all_items_by_slot(),
            }
        )

    async def _api_reject_pending(self) -> Any:
        """驳回并删除待审核新衣。"""
        body = await web_request.json(default={})
        target_id = str((body or {}).get("id", "") or "").strip()
        pending_list = self._load_pending_items()
        if target_id == "all":
            rest = []
        elif target_id:
            rest = [it for it in pending_list if it.get("id") != target_id]
        else:
            rest = pending_list[1:] if pending_list else []
        self._save_pending_items(rest)
        return json_response({"status": "ok", "pending_items": rest})

    async def _api_search_tags(self) -> Any:
        """从 QuickTagCloud (novelai.quicktagcloud.com) 服饰词库检索详细 Tag 或根据名称描述一键生成详细 Tag。"""
        query = str(web_request.query.get("query", "") or "").strip()
        name = str(web_request.query.get("name", "") or "").strip()
        desc = str(web_request.query.get("desc", "") or "").strip()
        existing = str(web_request.query.get("existing", "") or "").strip()
        if not query and not name:
            body = await web_request.json(default={})
            if isinstance(body, dict):
                query = str(body.get("query", "") or "").strip()
                name = str(body.get("name", "") or "").strip()
                desc = str(body.get("desc", "") or "").strip()
                existing = str(body.get("existing", "") or "").strip()
        q_str = query or name or desc
        items = search_quicktag_clothing(q_str, limit=12) if q_str else []
        auto_tags = auto_generate_detailed_nai_tags(name or query, desc, existing) if (name or desc or query) else ""
        return json_response(
            {
                "status": "ok",
                "source_url": QUICKTAG_WEB_URL,
                "query": q_str,
                "items": items,
                "auto_detailed_tags": auto_tags,
            }
        )

    async def _api_gallery_list(self) -> Any:
        import asyncio
        keyword = str(web_request.query.get("keyword", "") or "")
        order = str(web_request.query.get("order", "newest") or "newest")
        try:
            self.nai_history_dir.mkdir(parents=True, exist_ok=True)
            entries = await asyncio.to_thread(scan_entries, self.nai_history_dir)
            items = filter_entries(entries, keyword=keyword, order=order, hide_broken=True)
            overview = await asyncio.to_thread(directory_overview, self.nai_history_dir)
            return json_response(
                {
                    "status": "ok",
                    "items": items,
                    "total": len(entries),
                    "overview": overview,
                }
            )
        except Exception as e:
            logger.warning(f"{LOG_TAG} [_api_gallery_list] 失败: {e}")
            return error_response(f"读取相册失败: {e}", status_code=500)

    async def _api_gallery_thumb(self) -> Any:
        import asyncio
        name = str(web_request.query.get("name", "") or "")
        side = clamp_thumb_side(web_request.query.get("side", 360), 360)
        try:
            image_path = await asyncio.to_thread(resolve_entry, self.nai_history_dir, name)
            thumb_path = self.thumb_dir / f"{image_path.stem}_{side}.jpg"
            if not (thumb_path.is_file() and thumb_path.stat().st_mtime >= image_path.stat().st_mtime):
                data = await asyncio.to_thread(render_thumbnail_bytes, image_path, side)
                await asyncio.to_thread(thumb_path.write_bytes, data)
            else:
                data = await asyncio.to_thread(thumb_path.read_bytes)
            return json_response(
                {
                    "status": "ok",
                    "name": name,
                    "data_url": to_data_url("image/jpeg", data),
                }
            )
        except Exception as e:
            return error_response(f"缩略图失败: {e}", status_code=404)

    async def _api_gallery_full(self) -> Any:
        import asyncio
        name = str(web_request.query.get("name", "") or "")
        try:
            image_path = await asyncio.to_thread(resolve_entry, self.nai_history_dir, name)
            data = await asyncio.to_thread(read_image_bytes, image_path)
            params = await asyncio.to_thread(load_params, self.nai_history_dir, image_path.stem)
            return json_response(
                {
                    "status": "ok",
                    "name": name,
                    "data_url": to_data_url(mime_for(image_path), data),
                    "params": params,
                }
            )
        except Exception as e:
            return error_response(f"读取原图失败: {e}", status_code=404)

    async def _api_gallery_delete(self) -> Any:
        import asyncio
        body = await web_request.json(default={})
        name = str((body or {}).get("name", "") or "").strip()
        if not name:
            return error_response("缺少文件名", status_code=400)
        try:
            removed = await asyncio.to_thread(delete_entry, self.nai_history_dir, name)
            return json_response({"status": "ok", "removed": removed})
        except Exception as e:
            return error_response(f"删除失败: {e}", status_code=500)

    # ------------------------------------------------------------------ Hooks & Tools

    @filter.on_llm_request(priority=300)
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest) -> None:
        if not bool(self._get_cfg("enable_inject", True)):
            return
        sender_id = str(event.get_sender_id() or "").strip()
        group_id = ""
        try:
            group_id = str(event.get_group_id() or "").strip()
        except Exception:
            pass
        owner_id = str(self._get_cfg("owner_id", "") or "").strip()
        allow_group = bool(self._get_cfg("allow_group_inject", False))
        if (group_id and not allow_group) or (owner_id and sender_id != owner_id):
            return
        try:
            state = await self.ensure_today_outfit()
            full_detail = bool(self._get_cfg("inject_full_detail", False))
            # 始终保持 system_prompt 固定不变以保护上游 Prefix Cache（绝不在头部动态翻转）
            block = self.format_outfit_prompt_block(state, full_detail=full_detail)
            req.system_prompt = (req.system_prompt or "") + block
        except Exception as e:
            logger.error(f"{LOG_TAG} 注入今日穿搭上下文失败: {e}", exc_info=True)

    @filter.llm_tool()
    async def update_daily_outfit_state(
        self,
        event: AstrMessageEvent,
        status_note: str,
        outer: str = "",
        top_bottom: str = "",
        underwear: str = "",
        legwear: str = "",
        outfit_nai_tags: str = "",
    ) -> str:
        """实时更新当前的衣着状态或更换局部/整套新衣物（在亲密互动弄乱衣服、脱下衣物或主人要求换上新衣服时调用）。

        Args:
            status_note(string): 必填，描述当前衣着的最新实时状态（例如：“针织开衫已滑落脱下，真丝吊带裙肩带被拉下一边，文胸扣子被解开”、“已换上暗夜黑蕾丝睡裙”）。
            outer(string): 可选，若外套发生变化则填入新的外套描述，不填则保持原状。
            top_bottom(string): 可选，若上衣/裙装发生变化则填入新的描述，不填则保持原状。
            underwear(string): 可选，若贴身内衣发生变化则填入新的描述，不填则保持原状。
            legwear(string): 可选，若丝袜/腿部穿戴发生变化（如撕破、褪至脚踝、更换）则填入新描述，不填保持原状。
            outfit_nai_tags(string): 可选，当加入新衣服或衣物状态发生明显变化时，必须填入纯正详细的 Danbooru / NovelAI 英文标准原子 Tag 组合（涵盖具体服装品类、色彩材质、领口裙摆版型、asymmetrical/skindentation/see-through等精细结构锁死词，确保多次生图稳定一致）。
        """
        state = await self.ensure_today_outfit()
        outfit = state.setdefault("outfit", {})

        state["status_note"] = status_note.strip()
        history = state.setdefault("history_notes", [])
        history.append(
            {
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "status": status_note.strip(),
            }
        )
        if outer.strip():
            outfit["outer"] = outer.strip()
        if top_bottom.strip():
            outfit["top_bottom"] = top_bottom.strip()
        if underwear.strip():
            outfit["underwear"] = underwear.strip()
        if legwear.strip():
            outfit["legwear"] = legwear.strip()
        if outfit_nai_tags.strip():
            outfit["outfit_nai_tags"] = outfit_nai_tags.strip()

        self._save_state()
        logger.info(f"{LOG_TAG} 已通过工具更新穿搭状态: {status_note}")
        return f"已更新当前衣着状态为：{status_note}"

    @filter.llm_tool()
    async def switch_wardrobe_outfit(
        self,
        event: AstrMessageEvent,
        style_hint: str = "",
    ) -> str:
        """从每日衣柜中重新挑选并拼装换上一套新穿搭（当主人明确要求去换一套衣服、换睡衣、换制服或刷新今日穿搭时调用）。

        Args:
            style_hint(string): 可选，主人指定的风格或关键词（如：睡裙、白衬衫、毛衣、御姐、夏装、雨天、随机）。
        """
        state = await self.ensure_today_outfit(force_reroll=True, style_hint=style_hint)
        outfit = state.get("outfit") or {}
        return (
            f"已换上新穿搭：【{outfit.get('name')}】\n"
            f"- 外搭：{outfit.get('outer')}\n"
            f"- 上衣/裙装：{outfit.get('top_bottom')}\n"
            f"- 内衣：{outfit.get('underwear')}\n"
            f"- 丝袜：{outfit.get('legwear')}\n"
            f"- NAI Tags：{self._build_full_nai_tags(outfit)}"
        )


    @filter.llm_tool()
    async def add_wardrobe_clothing_item(
        self,
        event: AstrMessageEvent,
        slot: str,
        name: str,
        desc: str,
        detailed_nai_tags: str = "",
        equip_now: bool = True,
    ) -> str:
        """【仅在主人明确提出想看角色穿某件新衣服、或明确要求将新衣服加入衣柜时调用！日常收到普通转发图片/瑟图严禁调用！】
        创建一件新衣服单品并结合 QuickTagCloud (novelai.quicktagcloud.com) 词库补全高精度 Danbooru 英文标准 Tag。
        若开启了审批开关（默认开启），新衣服会先进入【待审批试穿池】供主人审核，审核通过后才正式写入永久衣柜。

        Args:
            slot(string): 必填，部位槽位，可选值：hair(发型)/outer(外搭)/top(上衣或连衣裙)/bottom(下装裙裤)/bra(胸罩)/panties(内裤)/legwear(丝袜腿部)/shoes(鞋履)/accessory(首饰尾巴挂饰)。
            name(string): 必填，新衣物的中文名称（如：“黑色单侧双环渔网袜”、“绯红半透薄纱旗袍”）。
            desc(string): 必填，新衣物的详细中文穿戴与视觉描写。
            detailed_nai_tags(string): 必填，按照详细 Danbooru / NovelAI 标准编写的英文原子 Tag 组合（涵盖品类、颜色材质、领口裙摆版型、asymmetrical/skindentation/see-through等精细结构词；底层还会自动检索 QuickTagCloud 服饰词库进行增强合并）。
            equip_now(boolean): 是否立即临时试穿该新衣展示给主人看，默认 True。
        """
        slot_clean = (slot or "").strip().lower()
        if slot_clean not in SLOTS:
            return f"无效的部位槽位 {slot}，可选：{', '.join(SLOTS)}"
        merged_detailed_tags = auto_generate_detailed_nai_tags(name, desc, detailed_nai_tags)
        need_approval = bool(self._get_cfg("require_approval_for_new_clothes", True))

        if need_approval:
            cand_id = f"pending_{slot_clean}_{int(time.time())}"
            cand_item = {
                "id": cand_id,
                "kind": "item",
                "slot": slot_clean,
                "source_volume": "主人钦定定制",
                "source_category": slot_clean,
                "name": name.strip(),
                "desc": desc.strip(),
                "nai_tags": merged_detailed_tags,
                "temp_min": 10.0,
                "temp_max": 38.0,
                "categories": ["weekend_home", "weekday", "mild", "hot", "night"],
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            pending_list = self._load_pending_items()
            pending_list.insert(0, cand_item)
            self._save_pending_items(pending_list[:30])

            if slot_clean == "top" and is_onepiece_top(cand_item):
                cand_item["is_onepiece"] = True
                cand_item["is_dress"] = True
                self._save_pending_items(pending_list[:30])

            if equip_now:
                state = await self.ensure_today_outfit()
                curr_outfit = state.get("outfit") or {}
                all_items = self.get_all_items_by_slot()
                selected: dict[str, dict[str, Any]] = {}
                for s in SLOTS:
                    if s == slot_clean:
                        selected[s] = cand_item
                    else:
                        tid = str(curr_outfit.get(f"{s}_id", "") or "")
                        s_list = all_items.get(s) or []
                        found = next((it for it in s_list if it.get("id") == tid), None)
                        if not found and s_list:
                            found = s_list[0]
                        selected[s] = found or {"id": "none", "name": "无", "desc": "无", "nai_tags": ""}
                composed = compose_outfit_from_items(selected)
                composed["pending_candidate_id"] = cand_id
                state["outfit"] = composed
                state["status_note"] = f"正在临时试穿新定制的【{name.strip()}】（等待主人审批入柜）"
                self._save_state()

            return (
                f"已按主人要求制作新衣【{name}】（部位：{slot_clean}），并放入【待审批试穿池】（编号：{cand_id}）！\n"
                f"- 详细 NAI 标准 Tags：{merged_detailed_tags}\n"
                f"- 已临时试穿在身上，请告知主人：可发送 `/审批新衣 通过`（或在衣柜面板点通过）正式收入永久衣柜，发 `/审批新衣 驳回` 则丢弃。"
            )

        item_id = f"custom_{slot_clean}_{int(time.time())}"
        new_item = {
            "id": item_id,
            "slot": slot_clean,
            "name": name.strip(),
            "desc": desc.strip(),
            "nai_tags": merged_detailed_tags,
            "temp_min": 10.0,
            "temp_max": 38.0,
            "categories": ["weekend_home", "weekday", "mild", "hot", "night"],
        }
        custom = self._load_custom_items()
        custom.append(new_item)
        self._save_custom_items(custom)

        if equip_now:
            state = await self.ensure_today_outfit()
            curr_outfit = state.get("outfit") or {}
            all_items = self.get_all_items_by_slot()
            selected: dict[str, dict[str, Any]] = {}
            for s in SLOTS:
                tid = item_id if s == slot_clean else str(curr_outfit.get(f"{s}_id", "") or "")
                s_list = all_items.get(s) or []
                found = next((it for it in s_list if it.get("id") == tid), None)
                if not found and s_list:
                    found = s_list[0]
                selected[s] = found or {"id": "none", "name": "无", "desc": "无", "nai_tags": ""}
            composed = compose_outfit_from_items(selected)
            state["outfit"] = composed
            state["status_note"] = f"已新添并换上单品：【{name.strip()}】"
            self._save_state()

        return (
            f"已将新衣物【{name}】（部位：{slot_clean}）正式加入衣柜！\n"
            f"- 结合 QuickTagCloud 词库生成的详细 NAI Tags：{merged_detailed_tags}"
        )

    @filter.command("审批新衣")
    async def cmd_approve_new_clothes(self, event: AstrMessageEvent, action: str = ""):
        """查看或审批待入柜的新衣服。用法：/审批新衣 [通过|驳回|清空]"""
        act = (action or "").strip().lower()
        pending_list = self._load_pending_items()
        if not pending_list:
            yield event.plain_result("当前【待审批试穿池】是空的，没有等待审核的新衣服哦~")
            return
        nl = chr(10)
        if not act or act in {"列表", "查看", "list"}:
            lines = [f"🛍️ 当前共有 {len(pending_list)} 件待审批新衣："]
            for idx, it in enumerate(pending_list[:8], 1):
                lines.append(
                    f"{idx}. 【{it.get('name')}】({it.get('slot', 'top')} | 来源:{it.get('source_volume', '词库')}){nl}"
                    f"   描述：{it.get('desc')}{nl}"
                    f"   Tags：{str(it.get('nai_tags', ''))[:90]}..."
                )
            lines.append("💡 发送 `/审批新衣 通过` 即可将第1件正式收入衣柜，发送 `/审批新衣 驳回` 则丢弃。")
            yield event.plain_result(nl.join(lines))
            return
        if act in {"通过", "同意", "入库", "入柜", "ok", "yes", "approve"}:
            chosen = pending_list.pop(0)
            self._save_pending_items(pending_list)
            slot_clean = str(chosen.get("slot") or "top").strip()
            if slot_clean not in SLOTS:
                slot_clean = "top"
            formal_item = {
                "id": f"custom_{slot_clean}_{int(time.time())}",
                "slot": slot_clean,
                "name": str(chosen.get("name") or "新衣物").strip(),
                "desc": str(chosen.get("desc") or "").strip(),
                "nai_tags": str(chosen.get("nai_tags") or "").strip(),
                "temp_min": float(chosen.get("temp_min", 10.0)),
                "temp_max": float(chosen.get("temp_max", 38.0)),
                "categories": chosen.get("categories") or ["weekend_home", "weekday", "mild", "hot", "night"],
            }
            if slot_clean == "top" and is_onepiece_top(formal_item):
                formal_item["is_onepiece"] = True
                formal_item["is_dress"] = True
            custom = self._load_custom_items()
            custom.append(formal_item)
            self._save_custom_items(custom)
            state = self._load_state()
            if isinstance(state.get("outfit"), dict) and state["outfit"].get(f"{slot_clean}_id") == chosen.get("id"):
                state["outfit"][f"{slot_clean}_id"] = formal_item["id"]
                self._save_state()
            yield event.plain_result(
                f"✅ 审批通过！已将【{formal_item['name']}】（部位：{slot_clean}）正式收入永久衣柜！{nl}"
                f"剩余待审批：{len(pending_list)} 件。"
            )
            return
        if act in {"驳回", "拒绝", "丢弃", "删", "no", "reject"}:
            dropped = pending_list.pop(0)
            self._save_pending_items(pending_list)
            yield event.plain_result(f"🗑️ 已驳回并丢弃待审批新衣：【{dropped.get('name')}】。剩余待审批：{len(pending_list)} 件。")
            return
        if act in {"清空", "clear"}:
            self._save_pending_items([])
            yield event.plain_result("🗑️ 已清空所有待审批新衣。")
            return
        yield event.plain_result("用法：`/审批新衣` 查看列表，`/审批新衣 通过` 入库第1件，`/审批新衣 驳回` 丢弃第1件。")

    @filter.command("穿搭")
    async def cmd_view_outfit(self, event: AstrMessageEvent):
        """查看当前角色今日穿搭与实时衣着状态。用法：/穿搭"""
        state = await self.ensure_today_outfit()
        outfit = state.get("outfit") or {}
        weather = state.get("weather") or {}
        text = (
            f"{self._persona_name()}的今日衣柜（{state.get('real_date')} {state.get('weekday_cn')}）\n"
            f"当地天气：{weather.get('city', '本地')} {weather.get('desc', '')} {weather.get('temp_c', '')}°C\n"
            f"穿搭主题：{outfit.get('name')}\n"
            f"外搭：{outfit.get('outer')}\n"
            f"裙装/上装：{outfit.get('top_bottom')}\n"
            f"贴身内衣：{outfit.get('underwear')}\n"
            f"腿部/丝袜：{outfit.get('legwear')}\n"
            f"鞋饰：{outfit.get('shoes_acc')}\n"
            f"实时状态：{state.get('status_note')}\n"
            f"NAI Tags：{self._build_full_nai_tags(outfit)}"
        )
        yield event.plain_result(text)

    @filter.command("换装")
    async def cmd_change_outfit(self, event: AstrMessageEvent, style_hint: str = ""):
        """让角色换一套衣服。用法：/换装 [风格关键词，如：睡裙/白衬衫/御姐/针织裙]"""
        state = await self.ensure_today_outfit(force_reroll=True, style_hint=style_hint)
        outfit = state.get("outfit") or {}
        text = (
            f"换装完成！当前穿搭：【{outfit.get('name')}】\n"
            f"外搭：{outfit.get('outer')}\n"
            f"裙装/上装：{outfit.get('top_bottom')}\n"
            f"贴身内衣：{outfit.get('underwear')}\n"
            f"腿部/丝袜：{outfit.get('legwear')}\n"
            f"状态：{state.get('status_note')}"
        )
        yield event.plain_result(text)
