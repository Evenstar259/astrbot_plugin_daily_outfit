// 每日穿搭衣柜 WebUI 面板逻辑（支持五部位单品自由拼装 + 整套预设收藏）
(function () {
  "use strict";

  const CATEGORY_NAMES = {
    weekend_home: "周末宅家",
    weekday: "日常/通勤",
    mild: "春秋舒适",
    hot: "晴热清凉",
    cold: "微凉保暖",
    rainy: "雨天静谧",
    night: "深夜私密",
    naked: "赤裸/未穿",
  };

  const SLOT_NAMES = {
    hair: "发型",
    outer: "外搭 / 外套",
    top: "上衣 / 连衣裙",
    bottom: "下装 / 裙裤",
    bra: "贴身胸罩",
    panties: "贴身内裤",
    legwear: "腿部 / 丝袜",
    shoes: "鞋履 / 足部",
    accessory: "首饰 / 挂饰",
  };

  const state = {
    data: null,
    itemsBySlot: {},
    presets: [],
    pendingItems: [],
    editingPresetMeta: null,
    fullNaiTags: "",
    activeSlot: "outer",
    keyword: "",
    galleryItems: [],
    galleryOrder: "newest",
    galleryKeyword: "",
    viewerIndex: -1,
  };

  function escapeHtml(str) {
    const span = document.createElement("span");
    span.textContent = String(str == null ? "" : str);
    return span.innerHTML;
  }

  const el = {
    weatherText: document.getElementById("weatherText"),
    showcaseImgBox: document.getElementById("showcaseImgBox"),
    showcaseImg: document.getElementById("showcaseImg"),
    showcaseEmptyHint: document.getElementById("showcaseEmptyHint"),
    pickShowcaseBtn: document.getElementById("pickShowcaseBtn"),
    currVibeInfo: document.getElementById("currVibeInfo"),
    viewerSetShowcaseBtn: document.getElementById("viewerSetShowcaseBtn"),
    showcasePickerModal: document.getElementById("showcasePickerModal"),
    closeShowcasePickerBtn: document.getElementById("closeShowcasePickerBtn"),
    showcasePickerGrid: document.getElementById("showcasePickerGrid"),
    reloadStateBtn: document.getElementById("reloadStateBtn"),
    refreshWeatherBtn: document.getElementById("refreshWeatherBtn"),
    randomEquipBtn: document.getElementById("randomEquipBtn"),
    stripAllBtn: document.getElementById("stripAllBtn"),
    newItemBtn: document.getElementById("newItemBtn"),
    newPresetBtn: document.getElementById("newPresetBtn"),
    saveCurrAsPresetBtn: document.getElementById("saveCurrAsPresetBtn"),
    toast: document.getElementById("toast"),
    currName: document.getElementById("currName"),
    currDateInfo: document.getElementById("currDateInfo"),
    currHair: document.getElementById("currHair"),
    currOuter: document.getElementById("currOuter"),
    currTop: document.getElementById("currTop"),
    currBottom: document.getElementById("currBottom"),
    currBra: document.getElementById("currBra"),
    currPanties: document.getElementById("currPanties"),
    currLegwear: document.getElementById("currLegwear"),
    currShoes: document.getElementById("currShoes"),
    currAccessory: document.getElementById("currAccessory"),
    statusInput: document.getElementById("statusInput"),
    saveStatusBtn: document.getElementById("saveStatusBtn"),
    toggleEditCurrBtn: document.getElementById("toggleEditCurrBtn"),
    inlineEditBox: document.getElementById("inlineEditBox"),
    editCurrHair: document.getElementById("editCurrHair"),
    editCurrOuter: document.getElementById("editCurrOuter"),
    editCurrAccessory: document.getElementById("editCurrAccessory"),
    editCurrTop: document.getElementById("editCurrTop"),
    editCurrBottom: document.getElementById("editCurrBottom"),
    editCurrBra: document.getElementById("editCurrBra"),
    editCurrPanties: document.getElementById("editCurrPanties"),
    editCurrLeg: document.getElementById("editCurrLeg"),
    editCurrShoes: document.getElementById("editCurrShoes"),
    editCurrTags: document.getElementById("editCurrTags"),
    saveCurrDetailsBtn: document.getElementById("saveCurrDetailsBtn"),
    currNaiTags: document.getElementById("currNaiTags"),
    copyNaiBtn: document.getElementById("copyNaiBtn"),
    historyList: document.getElementById("historyList"),
    tabModularBtn: document.getElementById("tabModularBtn"),
    tabPresetsBtn: document.getElementById("tabPresetsBtn"),
    tabGalleryBtn: document.getElementById("tabGalleryBtn"),
    modularView: document.getElementById("modularView"),
    presetsView: document.getElementById("presetsView"),
    galleryView: document.getElementById("galleryView"),
    polaroidStrip: document.getElementById("polaroidStrip"),
    openFullGalleryBtn: document.getElementById("openFullGalleryBtn"),
    galleryStats: document.getElementById("galleryStats"),
    searchGalleryInput: document.getElementById("searchGalleryInput"),
    sortGalleryBtn: document.getElementById("sortGalleryBtn"),
    reloadGalleryBtn: document.getElementById("reloadGalleryBtn"),
    galleryGrid: document.getElementById("galleryGrid"),
    photoViewerModal: document.getElementById("photoViewerModal"),
    viewerTitle: document.getElementById("viewerTitle"),
    viewerPrevBtn: document.getElementById("viewerPrevBtn"),
    viewerNextBtn: document.getElementById("viewerNextBtn"),
    closeViewerBtn: document.getElementById("closeViewerBtn"),
    viewerImg: document.getElementById("viewerImg"),
    viewerMetaText: document.getElementById("viewerMetaText"),
    viewerPromptPre: document.getElementById("viewerPromptPre"),
    viewerCopyTagBtn: document.getElementById("viewerCopyTagBtn"),
    viewerDownloadBtn: document.getElementById("viewerDownloadBtn"),
    viewerDeleteBtn: document.getElementById("viewerDeleteBtn"),
    slotItemList: document.getElementById("slotItemList"),
    searchPreset: document.getElementById("searchPreset"),
    presetGrid: document.getElementById("presetGrid"),
    // 单品弹窗
    itemModal: document.getElementById("itemModal"),
    itemModalTitle: document.getElementById("itemModalTitle"),
    closeItemModalBtn: document.getElementById("closeItemModalBtn"),
    cancelItemModalBtn: document.getElementById("cancelItemModalBtn"),
    saveItemFormBtn: document.getElementById("saveItemFormBtn"),
    itemFormId: document.getElementById("itemFormId"),
    itemFormSlot: document.getElementById("itemFormSlot"),
    itemFormName: document.getElementById("itemFormName"),
    itemFormTempMin: document.getElementById("itemFormTempMin"),
    itemFormTempMax: document.getElementById("itemFormTempMax"),
    itemFormCats: document.getElementById("itemFormCats"),
    itemFormDesc: document.getElementById("itemFormDesc"),
    itemFormNaiTags: document.getElementById("itemFormNaiTags"),
    // 套装弹窗
    presetModal: document.getElementById("presetModal"),
    modalTitle: document.getElementById("modalTitle"),
    closeModalBtn: document.getElementById("closeModalBtn"),
    cancelModalBtn: document.getElementById("cancelModalBtn"),
    savePresetBtn: document.getElementById("savePresetBtn"),
    formId: document.getElementById("formId"),
    formName: document.getElementById("formName"),
    formTempMin: document.getElementById("formTempMin"),
    formTempMax: document.getElementById("formTempMax"),
    formCategories: document.getElementById("formCategories"),
    formOuter: document.getElementById("formOuter"),
    formTopBottom: document.getElementById("formTopBottom"),
    formUnderwear: document.getElementById("formUnderwear"),
    formLegwear: document.getElementById("formLegwear"),
    formShoes: document.getElementById("formShoes"),
    formVibe: document.getElementById("formVibe"),
    formNaiTags: document.getElementById("formNaiTags"),
  };

  let bridge = null;
  let toastTimer = null;

  async function getBridge() {
    const deadline = Date.now() + 5000;
    while (!window.AstrBotPluginPage && Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 100));
    }
    if (!window.AstrBotPluginPage) {
      throw new Error("未检测到 AstrBot 插件页 Bridge，请从后台插件管理面板打开");
    }
    await window.AstrBotPluginPage.ready();
    return window.AstrBotPluginPage;
  }

  function showToast(msg) {
    if (!msg) return;
    el.toast.textContent = msg;
    el.toast.classList.remove("hidden");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      el.toast.classList.add("hidden");
    }, 3200);
  }

  function renderCurrent() {
    const s = state.data || {};
    const outfit = s.outfit || {};
    const w = s.weather || {};

    el.weatherText.textContent =
      (w.city || "本地") + " · " + (w.desc || "舒适") + " · " + (w.temp_c !== undefined ? w.temp_c + "°C" : "--");

    el.currName.textContent = outfit.name || "今日穿搭";
    el.currDateInfo.textContent =
      "📅 " + (s.logical_date || "--") + " (" + (s.weekday_cn || "") + ") · 📍 " + (s.location || "电脑书桌与软椅旁");
    renderShowcaseImage();

    function getSlotShortLabel(slotKey, fallbackText) {
      const sid = outfit[slotKey + "_id"] || "";
      const list = (state.itemsBySlot && state.itemsBySlot[slotKey]) || [];
      const hit = list.find((x) => x.id === sid);
      const stMode = (outfit.slot_states || {})[slotKey] || "normal";
      const suffix = stMode === "disheveled" ? " [半脱]" : (stMode === "stripped" ? " [脱下]" : "");
      const maxLen = slotKey === "hair" ? 24 : 13;
      const baseName = (hit && hit.name) ? String(hit.name).split("（")[0] : String(fallbackText || "--");
      const clipped = baseName.length > maxLen ? baseName.slice(0, maxLen) + "…" : baseName;
      return clipped + suffix;
    }

    function setSlotEl(domEl, slotKey, fullDesc) {
      if (!domEl) return;
      domEl.textContent = getSlotShortLabel(slotKey, fullDesc);
      domEl.title = fullDesc || "";
    }

    setSlotEl(el.currHair, "hair", outfit.hair || "星空长发自然披肩");
    setSlotEl(el.currOuter, "outer", outfit.outer || "无");
    setSlotEl(el.currTop, "top", outfit.top || outfit.top_bottom || "--");
    setSlotEl(el.currBottom, "bottom", outfit.bottom || "--");
    setSlotEl(el.currBra, "bra", outfit.bra || outfit.underwear || "--");
    setSlotEl(el.currPanties, "panties", outfit.panties || "--");
    setSlotEl(el.currLegwear, "legwear", outfit.legwear || outfit.legwear_acc || "--");
    setSlotEl(el.currShoes, "shoes", outfit.shoes || "--");
    setSlotEl(el.currAccessory, "accessory", outfit.accessory || "--");

    el.statusInput.value = s.status_note || "";
    if (el.editCurrHair) el.editCurrHair.value = outfit.hair || "";
    if (el.editCurrOuter) el.editCurrOuter.value = outfit.outer || "";
    if (el.editCurrAccessory) el.editCurrAccessory.value = outfit.accessory || "";
    if (el.editCurrTop) el.editCurrTop.value = outfit.top || outfit.top_bottom || "";
    if (el.editCurrBottom) el.editCurrBottom.value = outfit.bottom || "";
    if (el.editCurrBra) el.editCurrBra.value = outfit.bra || "";
    if (el.editCurrPanties) el.editCurrPanties.value = outfit.panties || "";
    if (el.editCurrLeg) el.editCurrLeg.value = outfit.legwear || outfit.legwear_acc || "";
    if (el.editCurrShoes) el.editCurrShoes.value = outfit.shoes || "";
    if (el.editCurrTags) el.editCurrTags.value = outfit.outfit_nai_tags || "";

    el.currNaiTags.textContent = state.fullNaiTags || outfit.outfit_nai_tags || "";
    const slotStates = outfit.slot_states || {};
    document.querySelectorAll("[data-slot-ctrl]").forEach((grp) => {
      const slot = grp.getAttribute("data-slot-ctrl");
      const currMode = slotStates[slot] || "normal";
      grp.querySelectorAll(".mini-btn").forEach((b) => {
        b.classList.toggle("active", b.getAttribute("data-mode") === currMode);
      });
    });

    el.historyList.innerHTML = "";
    const hist = Array.isArray(s.history_notes) ? s.history_notes : [];
    if (!hist.length) {
      const li = document.createElement("li");
      li.textContent = "今日暂无状态变更记录（保持初始穿戴）";
      el.historyList.appendChild(li);
    } else {
      hist.slice().reverse().forEach((item) => {
        const li = document.createElement("li");
        li.textContent = "[" + (item.time || "--") + "] " + (item.status || "");
        el.historyList.appendChild(li);
      });
    }
  }

  function renderSlotItems() {
    el.slotItemList.innerHTML = "";
    const slot = state.activeSlot || "outer";
    const items = (state.itemsBySlot && state.itemsBySlot[slot]) || [];
    const outfit = ((state.data || {}).outfit) || {};
    const currSlotItemId = outfit[slot + "_id"] || "";

    document.querySelectorAll(".slot-tab").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-slot") === slot);
    });

    items.forEach((it) => {
      const isEquipped = it.id === currSlotItemId || it.desc === outfit[slot];
      const card = document.createElement("div");
      card.className = "preset-card" + (isEquipped ? " active-preset" : "");

      const top = document.createElement("div");
      top.className = "preset-top";
      const title = document.createElement("div");
      title.className = "preset-title";
      title.textContent = (isEquipped ? "✦ " : "") + (it.name || it.id);
      top.appendChild(title);

      const tempSpan = document.createElement("span");
      tempSpan.className = "tag-pill";
      tempSpan.textContent = (it.temp_min ?? 10) + "°C ~ " + (it.temp_max ?? 35) + "°C";
      top.appendChild(tempSpan);
      card.appendChild(top);

      const meta = document.createElement("div");
      meta.className = "preset-meta";
      (it.categories || []).forEach((c) => {
        const pill = document.createElement("span");
        pill.className = "tag-pill";
        pill.textContent = CATEGORY_NAMES[c] || c;
        meta.appendChild(pill);
      });
      card.appendChild(meta);

      if (it.desc && it.desc !== it.name) {
        const desc = document.createElement("div");
        desc.className = "preset-desc single-line-ellipsis";
        const rawD = String(it.desc || "");
        desc.textContent = rawD.length > 26 ? rawD.slice(0, 26) + "…" : rawD;
        desc.title = rawD;
        card.appendChild(desc);
      }

      const actions = document.createElement("div");
      actions.className = "preset-actions";

      const editBtn = document.createElement("button");
      editBtn.type = "button";
      editBtn.className = "btn ghost small";
      editBtn.textContent = "编辑";
      editBtn.addEventListener("click", () => openItemModal(it));
      actions.appendChild(editBtn);

      if (!it.builtin) {
        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.className = "btn ghost danger small";
        delBtn.textContent = "删除";
        delBtn.addEventListener("click", () => deleteItem(it.id, it.name));
        actions.appendChild(delBtn);
      }

      const equipBtn = document.createElement("button");
      equipBtn.type = "button";
      equipBtn.className = "btn primary small";
      equipBtn.textContent = isEquipped ? "当前穿戴中" : "换上这件";
      equipBtn.addEventListener("click", () => equipSinglePart(slot, it.id));
      actions.appendChild(equipBtn);

      card.appendChild(actions);
      el.slotItemList.appendChild(card);
    });
  }

  function renderPresets() {
    el.presetGrid.innerHTML = "";
    const currId = ((state.data || {}).outfit || {}).id || "";
    const kw = (state.keyword || "").trim().toLowerCase();

    const list = state.presets.filter((p) => {
      if (!kw) return true;
      const blob = [p.name, p.outer, p.top_bottom, p.underwear, p.legwear, p.vibe].join(" ").toLowerCase();
      return blob.includes(kw);
    });

    list.forEach((p) => {
      const card = document.createElement("div");
      card.className = "preset-card" + (p.id === currId ? " active-preset" : "");

      const top = document.createElement("div");
      top.className = "preset-top";
      const title = document.createElement("div");
      title.className = "preset-title";
      title.textContent = (p.id === currId ? "✦ " : "") + (p.name || p.id);
      top.appendChild(title);

      const tempSpan = document.createElement("span");
      tempSpan.className = "tag-pill";
      tempSpan.textContent = (p.temp_min ?? 10) + "°C ~ " + (p.temp_max ?? 32) + "°C";
      top.appendChild(tempSpan);
      card.appendChild(top);

      const meta = document.createElement("div");
      meta.className = "preset-meta";
      (p.categories || []).forEach((c) => {
        const pill = document.createElement("span");
        pill.className = "tag-pill";
        pill.textContent = CATEGORY_NAMES[c] || c;
        meta.appendChild(pill);
      });
      card.appendChild(meta);

      const d1 = document.createElement("div");
      d1.className = "preset-desc single-line-ellipsis";
      const rawV = String(p.vibe || p.top || p.top_bottom || "");
      d1.textContent = rawV.length > 26 ? rawV.slice(0, 26) + "…" : rawV;
      d1.title = rawV;
      card.appendChild(d1);

      const actions = document.createElement("div");
      actions.className = "preset-actions";

      const editBtn = document.createElement("button");
      editBtn.type = "button";
      editBtn.className = "btn ghost small";
      editBtn.textContent = "编辑";
      editBtn.addEventListener("click", () => openModal(p));
      actions.appendChild(editBtn);

      if (!p.builtin) {
        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.className = "btn ghost danger small";
        delBtn.textContent = "删除";
        delBtn.addEventListener("click", () => deletePreset(p.id, p.name));
        actions.appendChild(delBtn);
      }

      const equipBtn = document.createElement("button");
      equipBtn.type = "button";
      equipBtn.className = "btn primary small";
      equipBtn.textContent = p.id === currId ? "当前穿着" : "整套换上";
      equipBtn.addEventListener("click", () => equipPreset(p.id));
      actions.appendChild(equipBtn);

      card.appendChild(actions);
      el.presetGrid.appendChild(card);
    });
  }

  async function loadAll() {
    try {
      const resp = await bridge.apiGet("wardrobe/status");
      state.data = resp.state || {};
      state.fullNaiTags = resp.full_nai_tags || "";
      state.itemsBySlot = resp.items_by_slot || {};
      state.presets = Array.isArray(resp.presets) ? resp.presets : [];
      state.pendingItems = Array.isArray(resp.pending_items) ? resp.pending_items : [];
      const titleEl = document.getElementById("wardrobeMainTitle");
      if (titleEl && resp.config && resp.config.persona_name) {
        titleEl.textContent = resp.config.persona_name + "的每日穿搭衣柜";
      }
      renderCurrent();
      renderSlotItems();
      renderPresets();
      renderPending();
    } catch (err) {
      showToast("读取衣柜失败：" + (err.message || err));
    }
  }

  async function equipSinglePart(slot, itemId) {
    try {
      const payload = {};
      payload[slot + "_id"] = itemId;
      const resp = await bridge.apiPost("wardrobe/equip_parts", payload);
      state.data = resp.state || {};
      state.fullNaiTags = resp.full_nai_tags || "";
      renderCurrent();
      renderSlotItems();
      renderPresets();
      showToast("已更换【" + (SLOT_NAMES[slot] || slot) + "】并重新拼装全身穿搭！");
    } catch (err) {
      showToast("更换单品失败：" + (err.message || err));
    }
  }

  async function equipPreset(presetId) {
    try {
      const resp = await bridge.apiPost("wardrobe/equip", { preset_id: presetId || "" });
      state.data = resp.state || {};
      state.fullNaiTags = resp.full_nai_tags || "";
      renderCurrent();
      renderSlotItems();
      renderPresets();
      showToast("已换上：" + ((state.data.outfit || {}).name || "新穿搭"));
    } catch (err) {
      showToast("换装失败：" + (err.message || err));
    }
  }

  async function saveStatus(statusText) {
    try {
      const resp = await bridge.apiPost("wardrobe/update_state", {
        status_note: statusText,
      });
      state.data = resp.state || {};
      state.fullNaiTags = resp.full_nai_tags || "";
      renderCurrent();
      showToast("已同步实时衣着状态！");
    } catch (err) {
      showToast("更新状态失败：" + (err.message || err));
    }
  }

  async function saveInlineDetails() {
    try {
      const resp = await bridge.apiPost("wardrobe/update_state", {
        status_note: el.statusInput.value,
        hair: el.editCurrHair ? el.editCurrHair.value : "",
        outer: el.editCurrOuter ? el.editCurrOuter.value : "",
        accessory: el.editCurrAccessory ? el.editCurrAccessory.value : "",
        top: el.editCurrTop ? el.editCurrTop.value : "",
        bottom: el.editCurrBottom ? el.editCurrBottom.value : "",
        bra: el.editCurrBra ? el.editCurrBra.value : "",
        panties: el.editCurrPanties ? el.editCurrPanties.value : "",
        legwear: el.editCurrLeg ? el.editCurrLeg.value : "",
        shoes: el.editCurrShoes ? el.editCurrShoes.value : "",
        outfit_nai_tags: el.editCurrTags ? el.editCurrTags.value : "",
      });
      state.data = resp.state || {};
      state.fullNaiTags = resp.full_nai_tags || "";
      renderCurrent();
      el.inlineEditBox.classList.add("hidden");
      showToast("已保存今日穿着细节！");
    } catch (err) {
      showToast("保存失败：" + (err.message || err));
    }
  }

  function openItemModal(item) {
    const it = item || {};
    el.itemModalTitle.textContent = it.id ? "编辑单件衣物" : "添置单件衣物";
    el.itemFormId.value = it.id || "";
    el.itemFormSlot.value = it.slot || state.activeSlot || "outer";
    el.itemFormName.value = it.name || "";
    el.itemFormTempMin.value = it.temp_min ?? 10;
    el.itemFormTempMax.value = it.temp_max ?? 35;
    el.itemFormCats.value = Array.isArray(it.categories) ? it.categories.join(", ") : "weekend_home, weekday, mild";
    el.itemFormDesc.value = it.desc || "";
    el.itemFormNaiTags.value = it.nai_tags || "";
    el.itemModal.classList.remove("hidden");
  }

  function closeItemModal() {
    el.itemModal.classList.add("hidden");
  }

  async function saveItemForm() {
    try {
      const payload = {
        id: el.itemFormId.value.trim(),
        slot: el.itemFormSlot.value,
        name: el.itemFormName.value.trim(),
        temp_min: Number(el.itemFormTempMin.value),
        temp_max: Number(el.itemFormTempMax.value),
        categories: el.itemFormCats.value,
        desc: el.itemFormDesc.value.trim(),
        nai_tags: el.itemFormNaiTags.value.trim(),
      };
      const resp = await bridge.apiPost("wardrobe/save_item", payload);
      state.itemsBySlot = resp.items_by_slot || state.itemsBySlot;
      state.activeSlot = payload.slot;
      renderSlotItems();
      closeItemModal();
      showToast("已保存单件衣物到【" + (SLOT_NAMES[payload.slot] || payload.slot) + "】！");
    } catch (err) {
      showToast("保存单品失败：" + (err.message || err));
    }
  }

  async function deleteItem(id, name) {
    try {
      const resp = await bridge.apiPost("wardrobe/delete_item", { id: id });
      state.itemsBySlot = resp.items_by_slot || state.itemsBySlot;
      renderSlotItems();
      showToast("已删除单品：" + (name || id));
    } catch (err) {
      showToast("删除失败：" + (err.message || err));
    }
  }

  function openModal(preset) {
    const p = preset || {};
    state.editingPresetMeta = p;
    el.modalTitle.textContent = p.id ? "编辑整套穿搭" : "保存为整套穿搭";
    el.formId.value = p.id || "";
    el.formName.value = p.name || "";
    el.formTempMin.value = p.temp_min ?? 12;
    el.formTempMax.value = p.temp_max ?? 30;
    el.formCategories.value = Array.isArray(p.categories) ? p.categories.join(", ") : "weekend_home, mild";
    el.formOuter.value = p.outer || "";
    el.formTopBottom.value = p.top_bottom || [p.top, p.bottom].filter(Boolean).join("；") || "";
    el.formUnderwear.value = p.underwear || [p.bra, p.panties].filter(Boolean).join("；") || "";
    el.formLegwear.value = p.legwear || "";
    el.formShoes.value = p.shoes_acc || [p.shoes, p.accessory].filter(Boolean).join("；") || "";
    el.formVibe.value = p.vibe || "";
    el.formNaiTags.value = p.outfit_nai_tags || "";
    el.presetModal.classList.remove("hidden");
  }

  function closeModal() {
    el.presetModal.classList.add("hidden");
  }

  async function savePresetForm() {
    try {
      const meta = state.editingPresetMeta || {};
      const payload = {
        id: el.formId.value.trim(),
        name: el.formName.value.trim(),
        temp_min: Number(el.formTempMin.value),
        temp_max: Number(el.formTempMax.value),
        categories: el.formCategories.value,
        hair: meta.hair || "",
        outer: el.formOuter.value.trim(),
        top: meta.top || "",
        bottom: meta.bottom || "",
        bra: meta.bra || "",
        panties: meta.panties || "",
        shoes: meta.shoes || "",
        accessory: meta.accessory || "",
        top_bottom: el.formTopBottom.value.trim(),
        underwear: el.formUnderwear.value.trim(),
        legwear: el.formLegwear.value.trim(),
        shoes_acc: el.formShoes.value.trim(),
        vibe: el.formVibe.value.trim(),
        outfit_nai_tags: el.formNaiTags.value.trim(),
        hair_id: meta.hair_id || "",
        outer_id: meta.outer_id || "",
        top_id: meta.top_id || "",
        bottom_id: meta.bottom_id || "",
        bra_id: meta.bra_id || "",
        panties_id: meta.panties_id || "",
        legwear_id: meta.legwear_id || "",
        shoes_id: meta.shoes_id || "",
        accessory_id: meta.accessory_id || "",
      };
      const resp = await bridge.apiPost("wardrobe/save_preset", payload);
      state.presets = Array.isArray(resp.presets) ? resp.presets : state.presets;
      renderPresets();
      closeModal();
      showToast("已保存到套装收藏夹！");
    } catch (err) {
      showToast("保存套装失败：" + (err.message || err));
    }
  }

  async function deletePreset(id, name) {
    try {
      const resp = await bridge.apiPost("wardrobe/delete_preset", { id: id });
      state.presets = Array.isArray(resp.presets) ? resp.presets : state.presets;
      renderPresets();
      showToast("已从套装库移除：" + (name || id));
    } catch (err) {
      showToast("删除失败：" + (err.message || err));
    }
  }


  function fmtTimeShort(seconds) {
    const d = new Date((Number(seconds) || 0) * 1000);
    if (Number.isNaN(d.getTime())) return "--";
    const pad = (v) => String(v).padStart(2, "0");
    return (d.getMonth() + 1) + "-" + pad(d.getDate()) + " " + pad(d.getHours()) + ":" + pad(d.getMinutes());
  }

  async function fetchThumbInto(imgEl, name) {
    try {
      const resp = await bridge.apiGet("wardrobe/gallery_thumb", { name: name, side: 360 });
      if (resp && resp.data_url) imgEl.src = resp.data_url;
    } catch (_) { }
  }


  function getActiveShowcaseName() {
    const saved = ((state.data || {}).showcase_image || "").trim();
    if (saved) {
      return saved;
    }
    // 若未设置固定展示图，默认固定取相册中最早的一张定妆照，绝不随新生成的图片自动替换
    if (state.galleryItems.length > 0) {
      return state.galleryItems[state.galleryItems.length - 1].name;
    }
    return "";
  }

  async function renderShowcaseImage() {
    if (!el.showcaseImg || !el.showcaseEmptyHint) return;
    const targetName = getActiveShowcaseName();
    if (!targetName) {
      el.showcaseImg.classList.add("hidden");
      el.showcaseEmptyHint.classList.remove("hidden");
      return;
    }
    if (el.showcaseImg.dataset.loadedName === targetName && el.showcaseImg.src) {
      el.showcaseImg.classList.remove("hidden");
      el.showcaseEmptyHint.classList.add("hidden");
      return;
    }
    try {
      const resp = await bridge.apiGet("wardrobe/gallery_thumb", { name: targetName, side: 560 });
      if (resp && resp.data_url) {
        el.showcaseImg.src = resp.data_url;
        el.showcaseImg.dataset.loadedName = targetName;
        el.showcaseImg.classList.remove("hidden");
        el.showcaseEmptyHint.classList.add("hidden");
      } else {
        el.showcaseImg.classList.add("hidden");
        el.showcaseEmptyHint.classList.remove("hidden");
      }
    } catch (_) {
      el.showcaseImg.classList.add("hidden");
      el.showcaseEmptyHint.classList.remove("hidden");
    }
  }

  async function setShowcaseImage(photoName) {
    if (!photoName) return;
    try {
      const resp = await bridge.apiPost("wardrobe/update_state", {
        showcase_image: photoName,
      });
      state.data = resp.state || state.data;
      if (el.showcaseImg) el.showcaseImg.dataset.loadedName = "";
      await renderShowcaseImage();
      if (el.showcasePickerModal) el.showcasePickerModal.classList.add("hidden");
      showToast("已将「" + photoName + "」设为左上角展示图！");
    } catch (err) {
      showToast("设置展示图失败：" + (err.message || err));
    }
  }

  function openShowcasePicker() {
    if (!el.showcasePickerModal || !el.showcasePickerGrid) return;
    el.showcasePickerModal.classList.remove("hidden");
    el.showcasePickerGrid.innerHTML = "";
    const currName = getActiveShowcaseName();
    if (!state.galleryItems.length) {
      el.showcasePickerGrid.innerHTML = '<div class="muted" style="grid-column:1/-1;">相册暂无历史照片</div>';
      return;
    }
    state.galleryItems.forEach((item) => {
      const isCurr = item.name === currName;
      const card = document.createElement("div");
      card.className = "gallery-item";
      if (isCurr) {
        card.style.borderColor = "var(--accent)";
        card.style.boxShadow = "0 0 12px rgba(245, 196, 105, 0.35)";
      }
      const th = document.createElement("div");
      th.className = "gallery-thumb";
      const img = document.createElement("img");
      img.loading = "lazy";
      th.appendChild(img);
      const cap = document.createElement("div");
      cap.className = "gallery-caption";
      cap.textContent = (isCurr ? "✦ 当前展示 · " : "") + fmtTimeShort(item.mtime);
      card.appendChild(th);
      card.appendChild(cap);
      card.addEventListener("click", () => setShowcaseImage(item.name));
      el.showcasePickerGrid.appendChild(card);
      fetchThumbInto(img, item.name);
    });
  }

  function renderPolaroids() {
    if (!el.polaroidStrip) return;
    el.polaroidStrip.innerHTML = "";
    const recent = state.galleryItems.slice(0, 3);
    if (!recent.length) {
      el.polaroidStrip.innerHTML = '<div class="muted" style="grid-column:1/-1;">暂无历史生图照片</div>';
      return;
    }
    recent.forEach((item, idx) => {
      const card = document.createElement("div");
      card.className = "polaroid-card";
      const tape = document.createElement("div");
      tape.className = "polaroid-tape";
      const th = document.createElement("div");
      th.className = "polaroid-thumb";
      const img = document.createElement("img");
      img.alt = item.name;
      th.appendChild(img);
      const tm = document.createElement("div");
      tm.className = "polaroid-time";
      tm.textContent = fmtTimeShort(item.mtime);
      card.appendChild(tape);
      card.appendChild(th);
      card.appendChild(tm);
      card.addEventListener("click", () => openPhotoViewer(idx));
      el.polaroidStrip.appendChild(card);
      fetchThumbInto(img, item.name);
    });
  }

  function renderGalleryGrid() {
    if (!el.galleryGrid) return;
    el.galleryGrid.innerHTML = "";
    if (!state.galleryItems.length) {
      el.galleryGrid.innerHTML = '<div class="muted" style="grid-column:1/-1;">没有找到符合条件的照片</div>';
      return;
    }
    state.galleryItems.forEach((item, idx) => {
      const card = document.createElement("div");
      card.className = "gallery-item";
      const th = document.createElement("div");
      th.className = "gallery-thumb";
      const img = document.createElement("img");
      img.loading = "lazy";
      th.appendChild(img);
      const cap = document.createElement("div");
      cap.className = "gallery-caption";
      cap.textContent = fmtTimeShort(item.mtime);
      card.appendChild(th);
      card.appendChild(cap);
      card.addEventListener("click", () => openPhotoViewer(idx));
      el.galleryGrid.appendChild(card);
      fetchThumbInto(img, item.name);
    });
  }

  async function loadGallery() {
    try {
      const resp = await bridge.apiGet("wardrobe/gallery_list", {
        keyword: state.galleryKeyword,
        order: state.galleryOrder,
      });
      state.galleryItems = Array.isArray(resp.items) ? resp.items : [];
      if (el.galleryStats && resp.overview) {
        el.galleryStats.textContent = "共 " + resp.overview.count + " 张历史照片（已直连 NAI 生图历史目录）";
      }
      renderPolaroids();
      renderGalleryGrid();
      renderShowcaseImage();
    } catch (err) {
      if (el.galleryStats) el.galleryStats.textContent = "相册读取失败";
    }
  }

  async function openPhotoViewer(idx) {
    if (idx < 0 || idx >= state.galleryItems.length) return;
    state.viewerIndex = idx;
    const item = state.galleryItems[idx];
    el.photoViewerModal.classList.remove("hidden");
    el.viewerTitle.textContent = item.name;
    el.viewerImg.src = "";
    el.viewerPromptPre.textContent = "正在读取原图与生成参数…";
    try {
      const resp = await bridge.apiGet("wardrobe/gallery_full", { name: item.name });
      el.viewerImg.src = resp.data_url || "";
      if (el.viewerDownloadBtn) {
        el.viewerDownloadBtn.href = resp.data_url || "";
        el.viewerDownloadBtn.download = item.name;
      }
      const p = resp.params || {};
      const sizeText = p.size || p.resolution || (item.width && item.height ? item.width + "x" + item.height : "");
      el.viewerMetaText.textContent =
        "时间：" + fmtTimeShort(item.mtime) +
        (p.model ? " · 模型：" + p.model : "") +
        (sizeText ? " · 尺寸：" + sizeText : "");
      el.viewerPromptPre.textContent = p.tag || p.prompt || p.raw_prompt || "（该图片未附带参数记录文件）";
    } catch (err) {
      el.viewerPromptPre.textContent = "读取失败：" + (err.message || err);
    }
  }


  function renderPending() {
    const badge = document.getElementById("pendingBadge");
    const grid = document.getElementById("pendingGrid");
    const items = Array.isArray(state.pendingItems) ? state.pendingItems : [];
    if (badge) {
      badge.textContent = String(items.length);
      badge.classList.toggle("hidden", items.length === 0);
    }
    if (!grid) return;
    grid.innerHTML = "";
    if (!items.length) {
      grid.innerHTML = '<div class="muted" style="grid-column:1/-1; padding:18px 0;">当前没有待审批的新衣服。点击右上角「🎲 淘一件新衣试穿」，即可从 4,559 条 QuickTagCloud 词库里随机淘一套新衣服试穿~</div>';
      return;
    }
    items.forEach((it) => {
      const card = document.createElement("div");
      card.className = "preset-card";
      card.innerHTML =
        '<div class="preset-card-head">' +
        '<div>' +
        '<h3>🛍️ ' + escapeHtml(it.name || "待审批新衣") + '</h3>' +
        '<span class="muted">部位：' + escapeHtml(SLOT_NAMES[it.slot] || it.slot || "上衣") + ' · 来源：' + escapeHtml(it.source_volume || "QuickTagCloud") + '</span>' +
        '</div>' +
        '</div>' +
        '<div class="preset-meta">' +
        '<div><b>描述：</b>' + escapeHtml(it.desc || "") + '</div>' +
        '<div style="word-break:break-all;"><b>详细 NAI Tags：</b>' + escapeHtml(it.nai_tags || "") + '</div>' +
        '</div>';
      const actions = document.createElement("div");
      actions.className = "preset-actions";

      const rejBtn = document.createElement("button");
      rejBtn.type = "button";
      rejBtn.className = "btn danger small";
      rejBtn.textContent = "🗑️ 驳回丢弃";
      rejBtn.addEventListener("click", async () => {
        try {
          const resp = await bridge.apiPost("wardrobe/reject_pending", { id: it.id });
          state.pendingItems = Array.isArray(resp.pending_items) ? resp.pending_items : [];
          renderPending();
          showToast("已驳回丢弃：" + (it.name || ""));
        } catch (err) {
          showToast("操作失败：" + (err.message || err));
        }
      });

      const appBtn = document.createElement("button");
      appBtn.type = "button";
      appBtn.className = "btn primary small";
      appBtn.textContent = "✅ 通过入柜";
      appBtn.addEventListener("click", async () => {
        try {
          const resp = await bridge.apiPost("wardrobe/approve_pending", { id: it.id });
          state.pendingItems = Array.isArray(resp.pending_items) ? resp.pending_items : [];
          state.itemsBySlot = resp.items_by_slot || state.itemsBySlot;
          await loadAll();
          showToast("✅ 已正式收入永久衣柜：" + (it.name || ""));
        } catch (err) {
          showToast("审批失败：" + (err.message || err));
        }
      });

      actions.appendChild(rejBtn);
      actions.appendChild(appBtn);
      card.appendChild(actions);
      grid.appendChild(card);
    });
  }

  function switchRightTab(mode) {
    if (el.tabModularBtn) el.tabModularBtn.classList.toggle("active", mode === "modular");
    if (el.tabPresetsBtn) el.tabPresetsBtn.classList.toggle("active", mode === "presets");
    if (el.modularView) el.modularView.classList.toggle("hidden", mode !== "modular");
    if (el.presetsView) el.presetsView.classList.toggle("hidden", mode !== "presets");
  }

  function switchMainPage(page) {
    const navHome = document.getElementById("navHomeBtn");
    const navPending = document.getElementById("navPendingBtn");
    const navGallery = document.getElementById("navGalleryBtn");
    const pageHome = document.getElementById("pageHomeView");
    const pagePending = document.getElementById("pagePendingView");
    const pageGallery = document.getElementById("pageGalleryView");

    if (navHome) navHome.classList.toggle("active", page === "home");
    if (navPending) navPending.classList.toggle("active", page === "pending");
    if (navGallery) navGallery.classList.toggle("active", page === "gallery");

    if (pageHome) pageHome.classList.toggle("hidden", page !== "home");
    if (pagePending) pagePending.classList.toggle("hidden", page !== "pending");
    if (pageGallery) pageGallery.classList.toggle("hidden", page !== "gallery");
  }

  async function init() {
    try {
      bridge = await getBridge();
      await loadAll();
      await loadGallery();
    } catch (err) {
      showToast(err.message || String(err));
    }

    if (el.reloadStateBtn) {
      el.reloadStateBtn.addEventListener("click", async () => {
        await loadAll();
        await loadGallery();
        showToast("面板数据已刷新！");
      });
    }

    el.refreshWeatherBtn.addEventListener("click", async () => {
      showToast("正在重新拉取天气…");
      try {
        const resp = await bridge.apiPost("wardrobe/refresh_weather", {});
        state.data = resp.state || state.data;
        renderCurrent();
        showToast("天气已刷新！");
      } catch (err) {
        showToast("刷新天气失败：" + (err.message || err));
      }
    });

    el.randomEquipBtn.addEventListener("click", () => equipPreset(""));
    if (el.stripAllBtn) {
      el.stripAllBtn.addEventListener("click", () => equipPreset("preset_full_naked"));
    }
    el.newItemBtn.addEventListener("click", () => openItemModal(null));
    el.closeItemModalBtn.addEventListener("click", closeItemModal);
    el.cancelItemModalBtn.addEventListener("click", closeItemModal);
    el.saveItemFormBtn.addEventListener("click", saveItemForm);
    const autoSearchBtn = document.getElementById("autoSearchItemTagsBtn");
    const quickTagResBox = document.getElementById("itemQuickTagResults");
    if (autoSearchBtn) {
      autoSearchBtn.addEventListener("click", async () => {
        const nameVal = (el.itemFormName && el.itemFormName.value || "").trim();
        const descVal = (el.itemFormDesc && el.itemFormDesc.value || "").trim();
        const existVal = (el.itemFormNaiTags && el.itemFormNaiTags.value || "").trim();
        if (!nameVal && !descVal) {
          showToast("请先填写衣物名称或中文穿戴描写，再点击找详细Tag~");
          return;
        }
        try {
          const resp = await bridge.apiPost("wardrobe/search_tags", {
            query: nameVal,
            name: nameVal,
            desc: descVal,
            existing: existVal,
          });
          if (resp.auto_detailed_tags && el.itemFormNaiTags) {
            el.itemFormNaiTags.value = resp.auto_detailed_tags;
          }
          if (quickTagResBox) {
            const items = Array.isArray(resp.items) ? resp.items : [];
            if (!items.length) {
              quickTagResBox.innerHTML = "已按部位词典生成详细Tag（QuickTagCloud无额外同名条目）";
            } else {
              quickTagResBox.innerHTML = items.map((it) => (
                '<div style="padding:4px 0; border-bottom:1px dashed rgba(255,255,255,0.1); cursor:pointer;" title="点击采用此词条Tag" data-tags="' +
                String(it.clean_tags || "").replace(/"/g, "&quot;") +
                '"><b>[' + escapeHtml(it.volume || "词库") + '] ' + escapeHtml(it.title || "") + '</b>：' +
                escapeHtml(String(it.clean_tags || "").slice(0, 95)) + '...</div>'
              )).join("");
              quickTagResBox.querySelectorAll("[data-tags]").forEach((row) => {
                row.addEventListener("click", () => {
                  if (el.itemFormNaiTags) el.itemFormNaiTags.value = row.getAttribute("data-tags") || "";
                  showToast("已填入该词条的详细 NAI Tag！");
                });
              });
            }
          }
          showToast("已从 QuickTagCloud 词库匹配并填入详细 Tag！");
        } catch (err) {
          showToast("检索 Tag 失败：" + (err.message || err));
        }
      });
    }

    if (el.newPresetBtn) {
      el.newPresetBtn.addEventListener("click", () => openModal(null));
    }
    if (el.saveCurrAsPresetBtn) {
      el.saveCurrAsPresetBtn.addEventListener("click", () => {
        const curr = ((state.data || {}).outfit) || {};
        openModal({
          name: curr.name || "我的自定义混搭套装",
          hair: curr.hair || "",
          outer: curr.outer || "",
          top: curr.top || "",
          bottom: curr.bottom || "",
          bra: curr.bra || "",
          panties: curr.panties || "",
          legwear: curr.legwear || "",
          shoes: curr.shoes || "",
          accessory: curr.accessory || "",
          top_bottom: curr.top_bottom || [curr.top, curr.bottom].filter(Boolean).join("；") || "",
          underwear: curr.underwear || [curr.bra, curr.panties].filter(Boolean).join("；") || "",
          shoes_acc: curr.shoes_acc || [curr.shoes, curr.accessory].filter(Boolean).join("；") || "",
          vibe: curr.vibe || "",
          outfit_nai_tags: curr.outfit_nai_tags || "",
          hair_id: curr.hair_id || "",
          outer_id: curr.outer_id || "",
          top_id: curr.top_id || "",
          bottom_id: curr.bottom_id || "",
          bra_id: curr.bra_id || "",
          panties_id: curr.panties_id || "",
          legwear_id: curr.legwear_id || "",
          shoes_id: curr.shoes_id || "",
          accessory_id: curr.accessory_id || "",
        });
      });
    }

    el.closeModalBtn.addEventListener("click", closeModal);
    el.cancelModalBtn.addEventListener("click", closeModal);
    el.savePresetBtn.addEventListener("click", savePresetForm);

    el.tabModularBtn.addEventListener("click", () => switchRightTab("modular"));
    el.tabPresetsBtn.addEventListener("click", () => switchRightTab("presets"));
    const navHomeBtn = document.getElementById("navHomeBtn");
    const navPendingBtn = document.getElementById("navPendingBtn");
    const navGalleryBtn = document.getElementById("navGalleryBtn");
    if (navHomeBtn) navHomeBtn.addEventListener("click", () => switchMainPage("home"));
    if (navPendingBtn) navPendingBtn.addEventListener("click", () => switchMainPage("pending"));
    if (navGalleryBtn) navGalleryBtn.addEventListener("click", () => switchMainPage("gallery"));
    const weatherBadge = document.getElementById("weatherBadge");
    if (weatherBadge && el.refreshWeatherBtn) {
      weatherBadge.addEventListener("click", () => el.refreshWeatherBtn.click());
    }
    const discoverNewBtn = document.getElementById("discoverNewBtn");
    const discoverHintInput = document.getElementById("discoverHintInput");
    if (discoverNewBtn) {
      discoverNewBtn.addEventListener("click", async () => {
        const hint = (discoverHintInput && discoverHintInput.value || "").trim();
        try {
          const resp = await bridge.apiPost("wardrobe/discover_new", { style_hint: hint, try_on: true });
          state.data = resp.state || state.data;
          state.fullNaiTags = resp.full_nai_tags || state.fullNaiTags;
          state.pendingItems = Array.isArray(resp.pending_items) ? resp.pending_items : state.pendingItems;
          renderCurrent();
          renderPending();
          showToast("🛍️ 已从词库淘出新衣【" + ((resp.candidate || {}).name || "") + "】并试穿！请审批是否入柜~");
        } catch (err) {
          showToast("淘新衣失败：" + (err.message || err));
        }
      });
    }
    if (el.openFullGalleryBtn) el.openFullGalleryBtn.addEventListener("click", () => switchMainPage("gallery"));
    if (el.reloadGalleryBtn) el.reloadGalleryBtn.addEventListener("click", () => loadGallery());
    if (el.sortGalleryBtn) {
      el.sortGalleryBtn.addEventListener("click", () => {
        state.galleryOrder = state.galleryOrder === "newest" ? "oldest" : "newest";
        el.sortGalleryBtn.textContent = state.galleryOrder === "newest" ? "新 → 旧" : "旧 → 新";
        loadGallery();
      });
    }
    if (el.searchGalleryInput) {
      el.searchGalleryInput.addEventListener("input", () => {
        state.galleryKeyword = el.searchGalleryInput.value;
        loadGallery();
      });
    }
    if (el.closeViewerBtn) el.closeViewerBtn.addEventListener("click", () => el.photoViewerModal.classList.add("hidden"));
    if (el.viewerPrevBtn) el.viewerPrevBtn.addEventListener("click", () => openPhotoViewer(state.viewerIndex - 1));
    if (el.viewerNextBtn) el.viewerNextBtn.addEventListener("click", () => openPhotoViewer(state.viewerIndex + 1));
    if (el.viewerCopyTagBtn) {
      el.viewerCopyTagBtn.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(el.viewerPromptPre.textContent || "");
          showToast("已复制该照片的 Prompt！");
        } catch (_) { }
      });
    }
    if (el.pickShowcaseBtn) {
      el.pickShowcaseBtn.addEventListener("click", openShowcasePicker);
    }
    if (el.closeShowcasePickerBtn) {
      el.closeShowcasePickerBtn.addEventListener("click", () => {
        el.showcasePickerModal.classList.add("hidden");
      });
    }
    if (el.showcaseImgBox) {
      el.showcaseImgBox.addEventListener("click", () => {
        const currName = getActiveShowcaseName();
        if (!currName) {
          openShowcasePicker();
          return;
        }
        const idx = state.galleryItems.findIndex((it) => it.name === currName);
        if (idx >= 0) {
          openPhotoViewer(idx);
        } else {
          openShowcasePicker();
        }
      });
    }
    if (el.viewerSetShowcaseBtn) {
      el.viewerSetShowcaseBtn.addEventListener("click", async () => {
        const item = state.galleryItems[state.viewerIndex];
        if (!item) return;
        await setShowcaseImage(item.name);
      });
    }
    if (el.viewerDeleteBtn) {
      el.viewerDeleteBtn.addEventListener("click", async () => {
        const item = state.galleryItems[state.viewerIndex];
        if (!item) return;
        try {
          await bridge.apiPost("wardrobe/gallery_delete", { name: item.name });
          el.photoViewerModal.classList.add("hidden");
          await loadGallery();
          showToast("已删除照片：" + item.name);
        } catch (err) {
          showToast("删除失败：" + (err.message || err));
        }
      });
    }

    document.querySelectorAll(".slot-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.activeSlot = btn.getAttribute("data-slot") || "outer";
        renderSlotItems();
      });
    });

    document.querySelectorAll("[data-slot-ctrl] .mini-btn").forEach((btn) => {
      btn.addEventListener("click", async (ev) => {
        ev.stopPropagation();
        const grp = btn.closest("[data-slot-ctrl]");
        const slot = grp ? grp.getAttribute("data-slot-ctrl") : "";
        const mode = btn.getAttribute("data-mode") || "normal";
        if (!slot) return;
        try {
          const resp = await bridge.apiPost("wardrobe/slot_action", { slot: slot, mode: mode });
          state.data = resp.state || {};
          state.fullNaiTags = resp.full_nai_tags || "";
          renderCurrent();
          renderSlotItems();
          showToast("已更新【" + (SLOT_NAMES[slot] || slot) + "】状态！");
        } catch (err) {
          showToast("操作失败：" + (err.message || err));
        }
      });
    });

    document.querySelectorAll("[data-jump-slot]").forEach((card) => {
      card.addEventListener("click", () => {
        const slot = card.getAttribute("data-jump-slot");
        if (slot) {
          switchRightTab("modular");
          state.activeSlot = slot;
          renderSlotItems();
        }
      });
    });

    el.saveStatusBtn.addEventListener("click", () => {
      saveStatus(el.statusInput.value);
    });

    document.querySelectorAll(".chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const st = chip.getAttribute("data-status") || "";
        el.statusInput.value = st;
        saveStatus(st);
      });
    });

    el.toggleEditCurrBtn.addEventListener("click", () => {
      el.inlineEditBox.classList.toggle("hidden");
    });

    el.saveCurrDetailsBtn.addEventListener("click", saveInlineDetails);

    el.copyNaiBtn.addEventListener("click", async (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      try {
        await navigator.clipboard.writeText(el.currNaiTags.textContent || "");
        showToast("已复制完整 NAI 生图 Tags！");
      } catch (_) {
        showToast("复制失败，请手动选中复制");
      }
    });

    el.searchPreset.addEventListener("input", () => {
      state.keyword = el.searchPreset.value;
      renderPresets();
    });
  }

  init();
})();
