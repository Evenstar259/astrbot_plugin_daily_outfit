"""NAI 生图历史相册的纯逻辑层。

这一层刻意与 AstrBot 运行环境解耦：只依赖 ``pathlib`` / ``Pillow`` / ``PyYAML``，
方便在宿主机上直接单测（见 ``tests/test_gallery_core.py``）。
"""

from __future__ import annotations

import base64
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import yaml

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")
PARAM_SUFFIXES = (".yaml", ".yml", ".json")
MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

DEFAULT_THUMB_SIDE = 420
MIN_THUMB_SIDE = 96
MAX_THUMB_SIDE = 1280
THUMB_QUALITY = 84

#: 历史文件名形如 ``nai_1789003463644578639.png``，参数文件共用同一个 stem。
NAME_PREFIX = "nai_"

#: 单次列表返回的最大条目数，防止历史无限膨胀时把面板拖死。
MAX_LIST_ITEMS = 600


class GalleryError(Exception):
    """相册层的可预期错误，携带对外可见的 HTTP 状态码。"""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def clamp_thumb_side(value: Any, default: int = DEFAULT_THUMB_SIDE) -> int:
    """把外部传入的缩略图边长夹到安全区间，非法值回落到默认值。"""

    try:
        side = int(value)
    except (TypeError, ValueError):
        return default
    if side < MIN_THUMB_SIDE or side > MAX_THUMB_SIDE:
        return default
    return side


def is_safe_entry_name(name: Any) -> bool:
    """判断逻辑文件名是否安全：只允许单层、非隐藏、带已知图片后缀的名字。"""

    if not isinstance(name, str):
        return False
    stripped = name.strip()
    if not stripped or stripped != name:
        return False
    if len(name) > 128:
        return False
    if name.startswith("."):
        return False
    if "/" in name or "\\" in name or "\x00" in name:
        return False
    if any(part == ".." for part in name.split(".")):
        return False
    if not name.lower().endswith(IMAGE_SUFFIXES):
        return False
    return True


def resolve_entry(root: Path, name: str, *, must_exist: bool = True) -> Path:
    """把逻辑文件名解析为 ``root`` 下的真实路径，越界或非法名字一律拒绝。"""

    if not is_safe_entry_name(name):
        raise GalleryError("文件名不合法，已拒绝访问", 400)

    root_resolved = Path(root).resolve(strict=False)
    candidate = (root_resolved / name).resolve(strict=False)
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:  # pragma: no cover - 防御性分支
        raise GalleryError("路径越界，已拒绝访问", 400) from exc

    if must_exist and not candidate.is_file():
        raise GalleryError("这条历史已经不在本地了", 404)
    return candidate


def _param_path(root: Path, stem: str) -> Path | None:
    """返回与图片同 stem 的参数文件路径，没有则返回 ``None``。"""

    for suffix in PARAM_SUFFIXES:
        candidate = Path(root) / f"{stem}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def load_params(root: Path, stem: str) -> dict[str, Any]:
    """读取一次生成的参数文件，损坏或缺失时安静地返回空字典。"""

    path = _param_path(root, stem)
    if path is None:
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(raw)
        else:
            data = yaml.safe_load(raw)
    except (yaml.YAMLError, json.JSONDecodeError, ValueError):
        return {"_broken": True}
    return data if isinstance(data, dict) else {}


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ("" if value is None else str(value))


def summarize_params(params: dict[str, Any]) -> dict[str, Any]:
    """从原始参数里挑出面板需要展示的小字段，避免整包塞进列表响应。"""

    tag = _text(params.get("tag")).strip()
    return {
        "tag": tag,
        "tag_preview": tag[:120],
        "model": _text(params.get("model")).strip(),
        "size": _text(params.get("size")).strip(),
        "steps": params.get("steps"),
        "scale": params.get("scale"),
        "cfg": params.get("cfg"),
        "sampler": _text(params.get("sampler")).strip(),
        "broken": bool(params.get("_broken")),
    }


def _probe_dimensions(path: Path) -> tuple[int | None, int | None]:
    """只读文件头拿宽高，失败时返回 ``(None, None)``。"""

    try:
        from PIL import Image

        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except Exception:
        return None, None


def scan_entries(root: Path) -> list[dict[str, Any]]:
    """扫描历史目录，返回按时间倒序排列的条目列表。"""

    root_path = Path(root)
    if not root_path.is_dir():
        return []

    entries: list[dict[str, Any]] = []
    for path in root_path.iterdir():
        try:
            if not path.is_file():
                continue
        except OSError:
            continue
        name = path.name
        if name.startswith(".") or not name.lower().endswith(IMAGE_SUFFIXES):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue

        stem = path.stem
        params = load_params(root_path, stem)
        width, height = (None, None)
        if stat.st_size > 0:
            width, height = _probe_dimensions(path)

        entries.append(
            {
                "name": name,
                "stem": stem,
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "width": width,
                "height": height,
                "has_params": _param_path(root_path, stem) is not None,
                "empty": stat.st_size == 0,
                "params": summarize_params(params),
            }
        )

    entries.sort(key=lambda item: item["mtime"], reverse=True)
    return entries[:MAX_LIST_ITEMS]


def filter_entries(
    entries: list[dict[str, Any]],
    *,
    keyword: str = "",
    order: str = "newest",
    hide_broken: bool = False,
) -> list[dict[str, Any]]:
    """按关键词与排序偏好筛选条目；关键词会匹配文件名、tag、模型。"""

    needle = (keyword or "").strip().lower()
    result = entries
    if needle:
        def _hit(item: dict[str, Any]) -> bool:
            params = item.get("params") or {}
            haystack = " ".join(
                [
                    _text(item.get("name")),
                    _text(params.get("tag")),
                    _text(params.get("tag_preview")),
                    _text(params.get("model")),
                ]
            ).lower()
            return needle in haystack

        result = [item for item in result if _hit(item)]

    if hide_broken:
        result = [item for item in result if not item.get("empty")]

    if order == "oldest":
        return list(reversed(result))
    return list(result)


def read_image_bytes(path: Path) -> bytes:
    """读取原始图片字节。"""

    try:
        data = path.read_bytes()
    except OSError as exc:
        raise GalleryError("读取图片失败，文件可能已被移走", 500) from exc
    if not data:
        raise GalleryError("这条历史是空文件，当年那次出图没写成功", 409)
    return data


def mime_for(path: Path) -> str:
    return MIME_BY_SUFFIX.get(path.suffix.lower(), "application/octet-stream")


def to_data_url(mime: str, data: bytes) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _flatten_for_jpeg(image: Any) -> Any:
    """把带透明通道或调色板的图转成可存 JPEG 的 RGB，透明处垫白底。"""

    from PIL import Image

    if image.mode in ("RGBA", "LA", "P"):
        converted = image.convert("RGBA")
        canvas = Image.new("RGB", converted.size, (255, 255, 255))
        canvas.paste(converted, mask=converted.split()[-1])
        return canvas
    return image.convert("RGB")


def render_thumbnail_bytes(path: Path, max_side: int = DEFAULT_THUMB_SIDE) -> bytes:
    """生成等比缩放的 JPEG 缩略图字节。"""

    from PIL import Image, ImageOps

    try:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image)
            prepared = _flatten_for_jpeg(image)
            prepared.thumbnail((max_side, max_side), Image.LANCZOS)
            buffer = io.BytesIO()
            prepared.save(buffer, format="JPEG", quality=THUMB_QUALITY, optimize=True)
            return buffer.getvalue()
    except GalleryError:
        raise
    except Exception as exc:
        raise GalleryError(f"生成缩略图失败: {exc}", 500) from exc


def delete_entry(root: Path, name: str) -> list[str]:
    """删除一条历史及其同名参数文件，返回真正被删掉的文件名列表。"""

    root_path = Path(root)
    image_path = resolve_entry(root_path, name)
    removed: list[str] = []

    for target in (image_path, _param_path(root_path, image_path.stem)):
        if target is None or not target.is_file():
            continue
        try:
            target.unlink()
        except OSError as exc:
            raise GalleryError(f"删除失败: {exc}", 500) from exc
        removed.append(target.name)

    return removed


def delete_entries(root: Path, names: list[str]) -> dict[str, Any]:
    """批量删除多条历史，逐条独立处理：坏掉的名字只记进 failed，不打断其余删除。

    返回 ``{"removed": [...], "failed": [{"name": ..., "reason": ...}]}``。
    """

    root_path = Path(root)
    removed: list[str] = []
    failed: list[dict[str, str]] = []
    seen: set[str] = set()

    for raw in names:
        name = raw if isinstance(raw, str) else str(raw)
        if name in seen:
            continue
        seen.add(name)
        try:
            removed.extend(delete_entry(root_path, name))
        except GalleryError as exc:
            failed.append({"name": name, "reason": exc.message})
        except Exception as exc:  # pragma: no cover - 兜底，避免一条异常拖垮整批
            failed.append({"name": name, "reason": f"删除失败: {exc}"})

    return {"removed": removed, "failed": failed}


def build_zip_bytes(
    root: Path, names: list[str], *, with_params: bool = True
) -> dict[str, Any]:
    """把勾选的图片（可选带同名参数文件）打进一个 zip，返回字节与统计。

    与批量删除同款策略：逐条独立收集，非法或已丢失的名字只记进 ``skipped``，
    不影响其余条目；全部失败则抛 ``GalleryError``，避免回一个空包。
    """

    root_path = Path(root)
    buffer = io.BytesIO()
    packed: list[str] = []
    skipped: list[dict[str, str]] = []
    seen: set[str] = set()

    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for raw in names:
            name = raw if isinstance(raw, str) else str(raw)
            if name in seen:
                continue
            seen.add(name)
            try:
                image_path = resolve_entry(root_path, name)
                zf.write(image_path, arcname=image_path.name)
                packed.append(image_path.name)
                if with_params:
                    param_path = _param_path(root_path, image_path.stem)
                    if param_path is not None:
                        zf.write(param_path, arcname=param_path.name)
                        packed.append(param_path.name)
            except GalleryError as exc:
                skipped.append({"name": name, "reason": exc.message})
            except OSError as exc:
                skipped.append({"name": name, "reason": f"打包失败: {exc}"})

    if not packed:
        raise GalleryError("勾选的历史都不在了，没什么可打包的", 404)

    return {"data": buffer.getvalue(), "packed": packed, "skipped": skipped}


def directory_overview(root: Path) -> dict[str, Any]:
    """给面板顶部统计用的汇总信息。"""

    entries = scan_entries(root)
    total_bytes = sum(int(item["size"]) for item in entries)
    with_params = sum(1 for item in entries if item["has_params"])
    return {
        "count": len(entries),
        "total_bytes": total_bytes,
        "with_params": with_params,
        "empty": sum(1 for item in entries if item["empty"]),
    }
