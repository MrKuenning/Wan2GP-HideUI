import gradio as gr
from shared.utils.plugins import WAN2GPPlugin
import json
import os

PlugIn_Name = "Mobile Toggle Helper"
PlugIn_Id = "MobileToggleHelper"

class MobileTogglePlugin(WAN2GPPlugin):
    def __init__(self):
        super().__init__()
        self.name = PlugIn_Name
        self.version = "4.0"
        self.description = "Floating menu to toggle and compact UI elements, optimized for desktop and mobile."

    def load_config(self):
        """Load configuration from config.json if it exists"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Wan2GP-HideUI] Error loading config.json: {e}")
                return {"elements": [], "order": []}
        return {"elements": [], "order": []}

    def save_config(self, elements, order, prefs=None):
        """Save configuration to config.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        config_data = {
            "elements": elements,
            "order": order
        }
        if prefs is not None:
            config_data["prefs"] = prefs
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            return {"status": "success"}
        except Exception as e:
            print(f"[Wan2GP-HideUI] Error saving config.json: {e}")
            return {"status": "error", "message": str(e)}

    def setup_ui(self):
        self.add_custom_js(self.inject_floating_buttons_js())

    def inject_floating_buttons_js(self) -> str:
        config = self.load_config()
        config_json = json.dumps(config)

        js_code = r"""
        (function(){
            const STORAGE_KEY_CUSTOM = "wan2gp_hideui_custom";
            const STORAGE_KEY_PREFS  = "wan2gp_hideui_prefs";
            const STORAGE_KEY_ORDER  = "wan2gp_hideui_order";
            const STORAGE_KEY_EDIT   = "wan2gp_hideui_editMode";
            const STORAGE_KEY_OPEN   = "wan2gp_hideui_open";
            const SESSION_KEY_INIT   = "wan2gp_hideui_session_init";

            const FILE_CONFIG = __CONFIG_JSON_PLACEHOLDER__;

            let allTargets = [];
            let originalConfig = FILE_CONFIG;
            let editMode = localStorage.getItem(STORAGE_KEY_EDIT) === 'true';
            let menuOpen = localStorage.getItem(STORAGE_KEY_OPEN) === 'true';
            let pickerMode = false;
            let highlightOverlay = null;
            let uiMounted = false;
            let searchQuery = "";

            // --- STORAGE INITIALIZATION & HELPERS ---

            function loadCustomElements() {
                try {
                    const saved = localStorage.getItem(STORAGE_KEY_CUSTOM);
                    if (saved) {
                        const parsed = JSON.parse(saved);
                        if (Array.isArray(parsed) && parsed.length > 0) {
                            return parsed;
                        }
                    }
                } catch (e) {
                    console.warn("[Wan2GP-HideUI] Failed to load custom elements:", e);
                }
                const initial = FILE_CONFIG.elements || [];
                saveCustomElements(initial);
                return JSON.parse(JSON.stringify(initial));
            }

            function saveCustomElements(elements) {
                try {
                    localStorage.setItem(STORAGE_KEY_CUSTOM, JSON.stringify(elements));
                } catch (e) {
                    console.error("[Wan2GP-HideUI] Failed to save custom elements:", e);
                }
            }

            function loadPreferences() {
                try {
                    // Fresh session initialization: default states are respected on first load
                    const isSessionInit = sessionStorage.getItem(SESSION_KEY_INIT);
                    if (!isSessionInit) {
                        sessionStorage.setItem(SESSION_KEY_INIT, "true");
                        const defaultPrefs = {};
                        allTargets.forEach(t => {
                            defaultPrefs[t.id] = (t.default !== false);
                        });
                        localStorage.setItem(STORAGE_KEY_PREFS, JSON.stringify(defaultPrefs));
                        return defaultPrefs;
                    }
                    const saved = localStorage.getItem(STORAGE_KEY_PREFS);
                    return saved ? JSON.parse(saved) : {};
                } catch (e) {
                    return {};
                }
            }

            function savePreferences() {
                const prefs = {};
                allTargets.forEach(target => {
                    const cb = document.getElementById(`cb-${target.id}`);
                    if (cb) {
                        prefs[target.id] = cb.checked;
                    }
                });
                try {
                    localStorage.setItem(STORAGE_KEY_PREFS, JSON.stringify(prefs));
                } catch (e) {
                    console.error("[Wan2GP-HideUI] Failed to save preferences:", e);
                }
            }

            function loadElementOrder() {
                try {
                    const saved = localStorage.getItem(STORAGE_KEY_ORDER);
                    if (saved) {
                        const parsed = JSON.parse(saved);
                        if (Array.isArray(parsed) && parsed.length > 0) {
                            return parsed;
                        }
                    }
                } catch (e) {
                    console.warn("[Wan2GP-HideUI] Failed to load order:", e);
                }
                const initialOrder = (FILE_CONFIG.order && FILE_CONFIG.order.length > 0)
                    ? FILE_CONFIG.order
                    : (FILE_CONFIG.elements || []).map(e => e.id);
                saveElementOrder(initialOrder);
                return initialOrder.slice();
            }

            function saveElementOrder(order) {
                try {
                    const list = order || allTargets.map(t => t.id);
                    localStorage.setItem(STORAGE_KEY_ORDER, JSON.stringify(list));
                } catch (e) {
                    console.error("[Wan2GP-HideUI] Failed to save order:", e);
                }
            }

            function syncTargetsFromStorage() {
                allTargets = loadCustomElements();
                const savedOrder = loadElementOrder();
                if (savedOrder.length > 0) {
                    allTargets.sort((a, b) => {
                        const aIdx = savedOrder.indexOf(a.id);
                        const bIdx = savedOrder.indexOf(b.id);
                        if (aIdx === -1 && bIdx === -1) return 0;
                        if (aIdx === -1) return 1;
                        if (bIdx === -1) return -1;
                        return aIdx - bIdx;
                    });
                }
            }

            function isElementModified(target) {
                const orig = (originalConfig.elements || []).find(e => e.id === target.id);
                if (!orig) return true; // New custom element
                if (orig.name !== target.name) return true; // Renamed
                if ((orig.default !== false) !== (target.default !== false)) return true; // Default changed
                if ((orig.mode || 'hide') !== (target.mode || 'hide')) return true; // Mode changed
                return false;
            }

            // --- STYLES INJECTION ---

            function injectStyles() {
                if (document.getElementById("wan2gp-hideui-styles")) return;
                const style = document.createElement("style");
                style.id = "wan2gp-hideui-styles";
                style.textContent = `
                    #floating-toggle-container {
                        position: fixed;
                        bottom: calc(16px * var(--wangp-ui-scale, 1));
                        right: calc(16px * var(--wangp-ui-scale, 1));
                        z-index: 999999;
                        display: flex;
                        flex-direction: column;
                        align-items: flex-end;
                        gap: 8px;
                        font-family: inherit;
                        user-select: none;
                        -webkit-user-select: none;
                    }
                    #floating-menu {
                        background: rgba(10, 16, 26, 0.95);
                        border: 1px solid var(--studio-border, #467eaf);
                        border-radius: var(--block-radius, 10px);
                        padding: 12px;
                        display: none;
                        flex-direction: column;
                        gap: 8px;
                        min-width: 300px;
                        max-width: min(390px, calc(100vw - 32px));
                        max-height: 80vh;
                        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.05);
                        color: var(--studio-button-text, #e6f2fc);
                        backdrop-filter: blur(18px) saturate(1.2);
                        -webkit-backdrop-filter: blur(18px) saturate(1.2);
                        box-sizing: border-box;
                    }
                    #floating-toggle-btn {
                        padding: calc(9px * var(--wangp-ui-scale, 1)) calc(18px * var(--wangp-ui-scale, 1));
                        border-radius: 24px;
                        background: var(--studio-button, #205786);
                        color: var(--studio-button-text, #e6f2fc);
                        border: 1px solid var(--studio-border, #467eaf);
                        cursor: pointer;
                        font-size: calc(13px * var(--wangp-ui-scale, 1));
                        font-weight: 600;
                        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
                        display: inline-flex;
                        align-items: center;
                        gap: 6px;
                        transition: background 0.15s ease, filter 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
                    }
                    #floating-toggle-btn:hover {
                        background: var(--studio-button-hover, #2b6ba8);
                        filter: brightness(1.12);
                        transform: translateY(-1px);
                        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
                    }
                    #floating-toggle-btn:active {
                        transform: translateY(0);
                    }
                    .hideui-btn {
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        gap: 4px;
                        border-radius: 5px;
                        border: 1px solid var(--studio-border, #467eaf);
                        background: var(--studio-button, #205786);
                        color: var(--studio-button-text, #e6f2fc);
                        font-size: 12px;
                        padding: 6px 10px;
                        cursor: pointer;
                        font-weight: 500;
                        box-sizing: border-box;
                        transition: background 0.15s ease, filter 0.15s ease, border-color 0.15s ease;
                        font-family: inherit;
                    }
                    .hideui-btn:hover {
                        background: var(--studio-button-hover, #2b6ba8);
                        filter: brightness(1.08);
                    }
                    .hideui-btn:disabled {
                        background: var(--studio-disabled, #283443);
                        color: var(--studio-disabled-text, #97a3b2);
                        border-color: var(--studio-disabled, #283443);
                        cursor: not-allowed;
                    }
                    .hideui-btn-primary {
                        background: #2563eb;
                        color: #ffffff;
                        font-weight: 600;
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
                    }
                    .hideui-btn-primary:hover {
                        background: #1d4ed8;
                        filter: brightness(1.08);
                    }
                    .hideui-btn-success {
                        background: #16a34a;
                        color: #ffffff;
                        font-weight: 600;
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        box-shadow: 0 2px 8px rgba(22, 163, 74, 0.3);
                    }
                    .hideui-btn-success:hover {
                        background: #15803d;
                        filter: brightness(1.08);
                    }
                    .hideui-btn-info {
                        background: #0284c7;
                        color: #ffffff;
                        font-weight: 600;
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.3);
                    }
                    .hideui-btn-info:hover {
                        background: #0369a1;
                        filter: brightness(1.08);
                    }
                    .hideui-btn-icon {
                        background: transparent;
                        border: none;
                        padding: 3px 5px;
                        cursor: pointer;
                        border-radius: 4px;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        color: var(--studio-label, #a4cef0);
                        transition: background 0.15s ease, color 0.15s ease;
                    }
                    .hideui-btn-icon:hover {
                        background: var(--studio-soft, #1b3c59);
                        color: var(--studio-button-text, #e6f2fc);
                    }
                    .hideui-search-input {
                        width: 100%;
                        box-sizing: border-box;
                        background: rgba(6, 11, 18, 0.85);
                        border: 1px solid var(--studio-border, #467eaf);
                        border-radius: 5px;
                        padding: 6px 10px;
                        color: var(--studio-button-text, #e6f2fc);
                        font-size: 12px;
                        outline: none;
                        font-family: inherit;
                    }
                    .hideui-search-input:focus {
                        border-color: var(--studio-accent, #69a8df);
                        background: rgba(6, 11, 18, 0.98);
                        box-shadow: 0 0 0 1px var(--studio-accent, #69a8df);
                    }
                    .hideui-search-input::placeholder {
                        color: var(--studio-disabled-text, #97a3b2);
                    }
                    .hideui-list {
                        display: flex;
                        flex-direction: column;
                        gap: 2px;
                        overflow-y: auto;
                        max-height: 52vh;
                        padding-right: 4px;
                    }
                    .hideui-list::-webkit-scrollbar {
                        width: 5px;
                    }
                    .hideui-list::-webkit-scrollbar-thumb {
                        background: var(--studio-border, #467eaf);
                        border-radius: 3px;
                    }
                    .hideui-row {
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        padding: 4px 6px;
                        border-radius: 5px;
                        background: transparent;
                        transition: background 0.15s ease;
                        font-size: 13px;
                        color: var(--studio-button-text, #e6f2fc);
                    }
                    .hideui-row:hover {
                        background: rgba(70, 126, 175, 0.2);
                    }
                    .hideui-row.is-edit {
                        background: rgba(32, 87, 134, 0.18);
                        border: 1px dashed var(--studio-border, #467eaf);
                        padding: 5px 6px;
                    }
                    .hideui-row input[type="checkbox"] {
                        accent-color: var(--studio-accent, #69a8df);
                        cursor: pointer;
                    }
                    .hideui-badge-cached {
                        font-size: 9px;
                        font-weight: 700;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        background: #f59e0b;
                        color: #0f172a;
                        padding: 1px 5px;
                        border-radius: 3px;
                    }
                    .hideui-badge-mode {
                        font-size: 9px;
                        font-weight: 600;
                        padding: 1px 5px;
                        border-radius: 3px;
                        cursor: pointer;
                        border: none;
                    }
                    .hideui-badge-mode.mode-compact {
                        background: rgba(56, 189, 248, 0.2);
                        color: #38bdf8;
                        border: 1px solid rgba(56, 189, 248, 0.4);
                    }
                    .hideui-badge-mode.mode-hide {
                        background: var(--studio-disabled, #283443);
                        color: var(--studio-disabled-text, #97a3b2);
                        border: 1px solid var(--studio-border, #467eaf);
                    }
                    .hideui-group-pill {
                        font-size: 9px;
                        color: var(--studio-label, #a4cef0);
                        background: var(--studio-soft, #1b3c59);
                        border: 1px solid var(--studio-border, #467eaf);
                        padding: 1px 4px;
                        border-radius: 3px;
                        margin-right: 2px;
                    }
                    .hideui-drag-handle {
                        cursor: grab;
                        color: var(--studio-label, #a4cef0);
                        font-size: 15px;
                        user-select: none;
                        padding: 0 2px;
                    }
                    .hideui-drag-handle:active {
                        cursor: grabbing;
                    }
                    .hideui-move-btn {
                        background: transparent;
                        border: none;
                        color: var(--studio-label, #a4cef0);
                        cursor: pointer;
                        font-size: 10px;
                        padding: 1px 3px;
                        border-radius: 2px;
                    }
                    .hideui-move-btn:hover {
                        color: var(--studio-button-text, #e6f2fc);
                        background: var(--studio-soft, #1b3c59);
                    }

                    /* --- COMPACT MODE STYLING --- */
                    .wangp-hideui-compact {
                        padding: 2px 6px !important;
                        margin: 1px 0 !important;
                        min-height: unset !important;
                        max-height: 54px !important;
                        overflow: hidden !important;
                        opacity: 0.88 !important;
                        transition: max-height 0.2s ease, opacity 0.2s ease !important;
                    }
                    .wangp-hideui-compact:hover {
                        opacity: 1 !important;
                    }
                    .wangp-hideui-compact input,
                    .wangp-hideui-compact select,
                    .wangp-hideui-compact button,
                    .wangp-hideui-compact textarea {
                        padding: 2px 6px !important;
                        height: 24px !important;
                        min-height: 24px !important;
                        font-size: 11px !important;
                    }
                    .wangp-hideui-compact [data-testid="block-info"],
                    .wangp-hideui-compact label {
                        font-size: 11px !important;
                        margin-bottom: 2px !important;
                    }
                    .wangp-hideui-compact .stats-container {
                        height: 38px !important;
                    }
                    .wangp-hideui-compact .stats-bar-background {
                        height: 18px !important;
                    }
                `;
                document.head.appendChild(style);
            }

            // --- SAFETY HIDE & SHOW LOGIC ---

            function safeHide(element) {
                if (!element) return;
                element.style.display = "none";
                element.dataset.wan2gpHidden = "true";

                let current = element.parentElement;
                let safetyCounter = 0;
                // Maximum 2 levels up, strictly preventing collapse of major layout containers
                while (current && safetyCounter < 2) {
                    if (
                        !current ||
                        current.tagName === "BODY" ||
                        current.tagName === "MAIN" ||
                        current.id === "root" ||
                        current.id === "component-0" ||
                        current.id === "component-6" ||
                        current.getAttribute("role") === "tabpanel" ||
                        current.classList.contains("tabitem") ||
                        current.classList.contains("tabs") ||
                        current.classList.contains("gradio-container") ||
                        current.classList.contains("fillable") ||
                        current.classList.contains("app") ||
                        (current.classList.contains("column") && current.classList.contains("gap"))
                    ) {
                        break;
                    }

                    const children = Array.from(current.children).filter(c =>
                        ["DIV", "BUTTON", "SPAN", "INPUT", "LABEL", "FORM", "FIELDSET", "SECTION", "DETAILS"].includes(c.tagName)
                    );

                    const allHidden = children.length > 0 && children.every(c =>
                        c.style.display === "none" || c.dataset.wan2gpHidden === "true"
                    );

                    if (allHidden) {
                        current.dataset.pluginHidden = "true";
                        current.style.display = "none";
                        current = current.parentElement;
                        safetyCounter++;
                    } else {
                        break;
                    }
                }
            }

            function safeShow(element) {
                if (!element) return;
                element.style.display = "";
                delete element.dataset.wan2gpHidden;

                let current = element.parentElement;
                let safetyCounter = 0;
                while (current && safetyCounter < 2) {
                    if (!current || current.tagName === "BODY") break;
                    if (current.dataset.pluginHidden === "true") {
                        current.style.display = "";
                        delete current.dataset.pluginHidden;
                        current = current.parentElement;
                        safetyCounter++;
                    } else {
                        break;
                    }
                }
            }

            // --- TARGET FINDING & VISIBILITY CONTROL ---

            function filterSafeTargets(elementsSet) {
                return Array.from(elementsSet).filter(el => {
                    if (!el) return false;
                    if (
                        el.id === "root" ||
                        el.id === "component-0" ||
                        el.id === "component-6" ||
                        el.tagName === "BODY" ||
                        el.tagName === "MAIN" ||
                        el.getAttribute("role") === "tabpanel" ||
                        el.classList.contains("tabitem") ||
                        el.classList.contains("tabs") ||
                        el.classList.contains("gradio-container") ||
                        el.closest("#floating-toggle-container") ||
                        el.closest("#wan2gp-modal-container") ||
                        el.closest("#wan2gp-picker-overlay")
                    ) {
                        return false;
                    }
                    return true;
                });
            }

            function findTargetsForElement(target) {
                const found = new Set();

                // 1. Explicit componentId has highest priority: if specified and found, use them!
                if (target.componentId) {
                    const ids = Array.isArray(target.componentId) ? target.componentId : [target.componentId];
                    ids.forEach(id => {
                        if (typeof id === "string" && id.trim()) {
                            const trimmedId = id.trim();
                            try {
                                const allWithId = document.querySelectorAll(`[id='${trimmedId}']`);
                                if (allWithId && allWithId.length > 0) {
                                    allWithId.forEach(el => found.add(el));
                                } else {
                                    const el = document.getElementById(trimmedId);
                                    if (el) found.add(el);
                                }
                            } catch (e) {
                                const el = document.getElementById(trimmedId);
                                if (el) found.add(el);
                            }
                        }
                    });
                    if (found.size > 0) {
                        return filterSafeTargets(found);
                    }
                }

                // 2. CSS Selector query
                if (target.cssSelector && typeof target.cssSelector === "string") {
                    try {
                        const matches = document.querySelectorAll(target.cssSelector);
                        matches.forEach(el => found.add(el));
                        if (found.size > 0) {
                            return filterSafeTargets(found);
                        }
                    } catch (e) {
                        // ignore selector syntax errors
                    }
                }

                // 3. Button Text matching
                if (target.buttonText) {
                    const btnTexts = Array.isArray(target.buttonText) ? target.buttonText : [target.buttonText];
                    const allBtns = Array.from(document.querySelectorAll("button"));
                    btnTexts.forEach(bt => {
                        const normBt = bt.toLowerCase().replace(/\s+/g, ' ').trim();
                        if (!normBt) return;
                        allBtns.forEach(btn => {
                            const txt = (btn.innerText || btn.textContent || "").toLowerCase().replace(/\s+/g, ' ').trim();
                            if (txt === normBt || txt.includes(normBt)) {
                                const comp = btn.closest("div[id^='component-'], div[id^='wangp'], button[id^='component-'], .block, .form") || btn;
                                found.add(comp);
                            }
                        });
                    });
                    if (found.size > 0) {
                        return filterSafeTargets(found);
                    }
                }

                // 4. Labels matching (fallback only when explicit IDs and selectors were not found)
                if (target.labels && target.labels.length > 0) {
                    const labelCandidates = Array.from(document.querySelectorAll(
                        "span[data-testid='block-info'], label[data-testid='block-label'], label, button.label-wrap"
                    ));
                    target.labels.forEach(lbl => {
                        const term = lbl.toLowerCase().replace(/\s+/g, ' ').trim();
                        if (!term || term.length < 3) return;
                        labelCandidates.forEach(node => {
                            const txt = (node.innerText || node.textContent || "").toLowerCase().replace(/\s+/g, ' ').trim();
                            const isMatch = (txt === term) || (txt.startsWith(term + " ") || txt.endsWith(" " + term) || txt.includes(" " + term + " "));
                            if (isMatch) {
                                const comp = node.closest("div[id^='component-'], div[id^='wangp'], button[id^='component-'], .block, .form, fieldset") || node;
                                found.add(comp);
                            }
                        });
                    });
                    if (found.size > 0) {
                        return filterSafeTargets(found);
                    }
                }

                // 5. Fallback: match by target.name
                if (target.name) {
                    const term = target.name.toLowerCase().replace(/\s+/g, ' ').trim();
                    const allLabels = Array.from(document.querySelectorAll("span[data-testid='block-info'], label[data-testid='block-label'], label, button.label-wrap"));
                    for (const lbl of allLabels) {
                        const txt = (lbl.textContent || "").toLowerCase().replace(/\s+/g, ' ').trim();
                        if (txt === term || txt.startsWith(term)) {
                            const comp = lbl.closest("div[id^='component-'], div[id^='wangp'], .wangp-studio-field, .block, .form");
                            if (comp) {
                                found.add(comp);
                                break;
                            }
                        }
                    }
                }

                return filterSafeTargets(found);
            }

            function setTargetVisibility(target, shouldShow) {
                const elements = findTargetsForElement(target);
                const isCompactMode = (target.mode === 'compact');

                elements.forEach(el => {
                    if (isCompactMode) {
                        if (shouldShow) {
                            // Normal expanded state
                            el.classList.remove("wangp-hideui-compact");
                            safeShow(el);
                        } else {
                            // Minimized compact state
                            el.classList.add("wangp-hideui-compact");
                            safeShow(el);
                        }
                    } else {
                        // Standard Hide state
                        el.classList.remove("wangp-hideui-compact");
                        if (shouldShow) {
                            safeShow(el);
                        } else {
                            safeHide(el);
                        }
                    }
                });
            }

            function applyVisibility() {
                const savedPrefs = loadPreferences();
                allTargets.forEach(target => {
                    const isChecked = savedPrefs.hasOwnProperty(target.id)
                        ? savedPrefs[target.id]
                        : (target.default !== false);

                    setTargetVisibility(target, isChecked);

                    const cb = document.getElementById(`cb-${target.id}`);
                    if (cb && cb.checked !== isChecked) {
                        cb.checked = isChecked;
                    }
                });
            }

            // --- ELEMENT PICKER ---

            function createHighlightOverlay() {
                let overlay = document.getElementById("wan2gp-picker-overlay");
                if (!overlay) {
                    overlay = document.createElement("div");
                    overlay.id = "wan2gp-picker-overlay";
                    Object.assign(overlay.style, {
                        position: "absolute",
                        pointerEvents: "none",
                        border: "2px solid var(--studio-accent, #69a8df)",
                        background: "rgba(105, 168, 223, 0.2)",
                        borderRadius: "4px",
                        zIndex: "999998",
                        display: "none",
                        transition: "all 0.08s ease"
                    });
                    document.body.appendChild(overlay);
                }
                return overlay;
            }

            function enterPickerMode() {
                pickerMode = true;
                document.body.style.cursor = "crosshair";
                if (!highlightOverlay) {
                    highlightOverlay = createHighlightOverlay();
                }

                const addBtn = document.getElementById("wan2gp-add-element-btn");
                if (addBtn) {
                    addBtn.textContent = "✕ Cancel Picker";
                    addBtn.className = "hideui-btn hideui-btn-primary";
                    addBtn.style.background = "#dc2626";
                }

                document.addEventListener("mouseover", onPickerHover);
                document.addEventListener("click", onPickerClick, true);
                document.addEventListener("keydown", onPickerKeyDown);
            }

            function exitPickerMode() {
                pickerMode = false;
                document.body.style.cursor = "";
                if (highlightOverlay) {
                    highlightOverlay.style.display = "none";
                }

                const addBtn = document.getElementById("wan2gp-add-element-btn");
                if (addBtn) {
                    addBtn.textContent = "➕ Add New Element";
                    addBtn.className = "hideui-btn hideui-btn-info";
                    addBtn.style.background = "";
                }

                document.removeEventListener("mouseover", onPickerHover);
                document.removeEventListener("click", onPickerClick, true);
                document.removeEventListener("keydown", onPickerKeyDown);
            }

            function onPickerKeyDown(e) {
                if (e.key === "Escape") {
                    exitPickerMode();
                }
            }

            function onPickerHover(e) {
                if (!pickerMode) return;
                const target = e.target;
                if (target.closest("#floating-toggle-container") || target.closest("#wan2gp-modal-container")) return;

                const component = target.closest("div[id^='component-'], div[id^='wangp'], .wangp-studio-field, .block, button");
                if (!component) {
                    highlightOverlay.style.display = "none";
                    return;
                }

                const rect = component.getBoundingClientRect();
                Object.assign(highlightOverlay.style, {
                    display: "block",
                    left: (rect.left + window.scrollX) + "px",
                    top: (rect.top + window.scrollY) + "px",
                    width: rect.width + "px",
                    height: rect.height + "px"
                });
            }

            function onPickerClick(e) {
                if (!pickerMode) return;
                const target = e.target;
                if (target.closest("#floating-toggle-container") || target.closest("#wan2gp-modal-container")) return;

                e.preventDefault();
                e.stopPropagation();

                const component = target.closest("div[id^='component-'], div[id^='wangp'], .wangp-studio-field, .block, button");
                if (!component) return;

                const componentId = component.id || "";
                const label = component.querySelector("label, span[data-testid='block-info'], span[data-testid='block-label']");
                let elementName = label ? label.textContent.trim() : "";

                if (!elementName) {
                    const firstText = component.querySelector("span, p, h1, h2, h3, button");
                    elementName = firstText ? firstText.textContent.trim().substring(0, 40) : (componentId ? `Element ${componentId}` : "Custom Element");
                }

                const customName = prompt("Enter a friendly name for this element:", elementName);
                if (!customName || !customName.trim()) {
                    exitPickerMode();
                    return;
                }

                const finalName = customName.trim();
                const customId = "custom_" + Date.now();
                const labels = [];
                if (elementName && elementName.length < 50) {
                    labels.push(elementName.toLowerCase());
                }

                const newElement = {
                    id: customId,
                    name: finalName,
                    labels: labels,
                    componentId: componentId,
                    mode: "hide",
                    isCustom: true,
                    default: true
                };

                const elements = loadCustomElements();
                elements.push(newElement);
                saveCustomElements(elements);

                const order = loadElementOrder();
                if (!order.includes(customId)) {
                    order.push(customId);
                    saveElementOrder(order);
                }

                exitPickerMode();
                syncTargetsFromStorage();
                renderMenu();
                applyVisibility();
            }

            // --- MODALS (EXPORT & RESET) ---

            function showExportModal() {
                const existing = document.getElementById("wan2gp-modal-container");
                if (existing) existing.remove();

                const config = {
                    elements: allTargets.map(t => ({
                        id: t.id,
                        name: t.name,
                        ...(t.componentId ? { componentId: t.componentId } : {}),
                        ...(t.labels && t.labels.length ? { labels: t.labels } : {}),
                        ...(t.cssSelector ? { cssSelector: t.cssSelector } : {}),
                        ...(t.buttonText ? { buttonText: t.buttonText } : {}),
                        ...(t.group ? { group: t.group } : {}),
                        mode: t.mode || "hide",
                        ...(t.isCustom ? { isCustom: true } : {}),
                        default: (t.default !== false)
                    })),
                    order: allTargets.map(t => t.id)
                };
                const jsonStr = JSON.stringify(config, null, 2);

                const modalContainer = document.createElement("div");
                modalContainer.id = "wan2gp-modal-container";
                Object.assign(modalContainer.style, {
                    position: "fixed",
                    inset: "0",
                    background: "rgba(0, 0, 0, 0.75)",
                    zIndex: "1000000",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "16px",
                    backdropFilter: "blur(6px)"
                });

                const modal = document.createElement("div");
                Object.assign(modal.style, {
                    background: "rgba(10, 16, 26, 0.98)",
                    border: "1px solid var(--studio-border, #467eaf)",
                    borderRadius: "10px",
                    padding: "20px",
                    width: "100%",
                    maxWidth: "600px",
                    boxShadow: "0 24px 48px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.05)",
                    color: "var(--studio-button-text, #e6f2fc)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px"
                });

                const title = document.createElement("h3");
                title.textContent = "📤 Export Configuration";
                title.style.margin = "0";
                title.style.fontSize = "16px";
                title.style.color = "var(--studio-label, #a4cef0)";
                modal.appendChild(title);

                const desc = document.createElement("p");
                desc.textContent = "Copy the JSON below and paste it into config.json to make your custom toggles, ordering, and default states permanent across all browsers and sessions.";
                Object.assign(desc.style, {
                    margin: "0",
                    fontSize: "12px",
                    color: "var(--studio-disabled-text, #97a3b2)",
                    lineHeight: "1.4"
                });
                modal.appendChild(desc);

                const textarea = document.createElement("textarea");
                textarea.value = jsonStr;
                textarea.readOnly = true;
                Object.assign(textarea.style, {
                    width: "100%",
                    height: "280px",
                    fontFamily: "ui-monospace, monospace",
                    fontSize: "12px",
                    padding: "10px",
                    background: "rgba(6, 11, 18, 0.92)",
                    color: "var(--studio-label, #a4cef0)",
                    border: "1px solid var(--studio-border, #467eaf)",
                    borderRadius: "6px",
                    resize: "vertical",
                    boxSizing: "border-box"
                });
                textarea.onclick = () => textarea.select();
                modal.appendChild(textarea);

                const btnRow = document.createElement("div");
                Object.assign(btnRow.style, {
                    display: "flex",
                    gap: "8px",
                    justifyContent: "flex-end"
                });

                const copyBtn = document.createElement("button");
                copyBtn.textContent = "📋 Copy to Clipboard";
                copyBtn.className = "hideui-btn hideui-btn-success";
                copyBtn.style.padding = "8px 16px";
                copyBtn.onclick = () => {
                    textarea.select();
                    navigator.clipboard.writeText(jsonStr).then(() => {
                        copyBtn.textContent = "✓ Copied!";
                        setTimeout(() => copyBtn.textContent = "📋 Copy to Clipboard", 2000);
                    }).catch(() => {
                        document.execCommand('copy');
                        copyBtn.textContent = "✓ Copied!";
                        setTimeout(() => copyBtn.textContent = "📋 Copy to Clipboard", 2000);
                    });
                };

                const closeBtn = document.createElement("button");
                closeBtn.textContent = "Close";
                closeBtn.className = "hideui-btn";
                closeBtn.style.padding = "8px 16px";
                closeBtn.onclick = () => modalContainer.remove();

                btnRow.appendChild(copyBtn);
                btnRow.appendChild(closeBtn);
                modal.appendChild(btnRow);

                modalContainer.onclick = (e) => {
                    if (e.target === modalContainer) modalContainer.remove();
                };

                modalContainer.appendChild(modal);
                document.body.appendChild(modalContainer);
                textarea.select();
            }

            function handleImportFromFile() {
                const fileInput = document.createElement("input");
                fileInput.type = "file";
                fileInput.accept = ".json";
                fileInput.style.display = "none";
                document.body.appendChild(fileInput);

                fileInput.onchange = (e) => {
                    const file = e.target.files[0];
                    if (!file) {
                        fileInput.remove();
                        return;
                    }
                    const reader = new FileReader();
                    reader.onload = (readEvent) => {
                        try {
                            const parsed = JSON.parse(readEvent.target.result);
                            if (parsed && Array.isArray(parsed.elements)) {
                                originalConfig = parsed;
                                saveCustomElements(parsed.elements);
                                const newOrder = (parsed.order && Array.isArray(parsed.order))
                                    ? parsed.order
                                    : parsed.elements.map(el => el.id);
                                saveElementOrder(newOrder);
                                localStorage.removeItem(STORAGE_KEY_PREFS);
                                sessionStorage.removeItem(SESSION_KEY_INIT);
                                syncTargetsFromStorage();
                                renderMenu();
                                applyVisibility();
                                alert(`✓ Successfully loaded ${parsed.elements.length} elements from ${file.name}!`);
                            } else {
                                alert("Invalid config format: expected an 'elements' array in JSON.");
                            }
                        } catch (err) {
                            alert("Error parsing JSON file: " + err.message);
                        } finally {
                            fileInput.remove();
                        }
                    };
                    reader.readAsText(file);
                };

                fileInput.click();
            }

            function handleResetFromFile() {
                if (!confirm("Reset all customizations and reload elements from config.json?\n\nNote: If you edited config.json while Wan2GP was running, restart Wan2GP or click '📥 Import File' to hot-reload the changes without restarting.")) {
                    return;
                }
                localStorage.removeItem(STORAGE_KEY_CUSTOM);
                localStorage.removeItem(STORAGE_KEY_PREFS);
                localStorage.removeItem(STORAGE_KEY_ORDER);
                sessionStorage.removeItem(SESSION_KEY_INIT);

                const initialElements = FILE_CONFIG.elements || [];
                const initialOrder = (FILE_CONFIG.order && FILE_CONFIG.order.length > 0)
                    ? FILE_CONFIG.order
                    : initialElements.map(e => e.id);

                saveCustomElements(initialElements);
                saveElementOrder(initialOrder);

                syncTargetsFromStorage();
                renderMenu();
                applyVisibility();
            }

            // --- MENU RENDERING ---

            function moveTargetIndex(fromIdx, toIdx) {
                if (fromIdx === toIdx || fromIdx < 0 || toIdx < 0 || fromIdx >= allTargets.length || toIdx >= allTargets.length) return;
                const item = allTargets.splice(fromIdx, 1)[0];
                allTargets.splice(toIdx, 0, item);
                saveCustomElements(allTargets);
                saveElementOrder(allTargets.map(t => t.id));
                renderMenu();
                applyVisibility();
            }

            function createRow(target, index, isChecked, isEdit) {
                const row = document.createElement("div");
                row.className = `hideui-row ${isEdit ? 'is-edit' : ''}`;
                row.dataset.targetId = target.id;
                row.dataset.targetName = target.name;
                row.dataset.targetGroup = target.group || "";
                row.draggable = isEdit;

                // Drag and drop for desktop
                if (isEdit) {
                    row.ondragstart = (e) => {
                        e.dataTransfer.effectAllowed = "move";
                        e.dataTransfer.setData("text/plain", index.toString());
                        row.style.opacity = "0.4";
                    };
                    row.ondragend = () => {
                        row.style.opacity = "1";
                    };
                    row.ondragover = (e) => {
                        e.preventDefault();
                        e.dataTransfer.dropEffect = "move";
                        row.style.borderTop = "2px solid var(--studio-accent, #69a8df)";
                    };
                    row.ondragleave = () => {
                        row.style.borderTop = "";
                    };
                    row.ondrop = (e) => {
                        e.preventDefault();
                        row.style.borderTop = "";
                        const fromIdx = parseInt(e.dataTransfer.getData("text/plain"), 10);
                        moveTargetIndex(fromIdx, index);
                    };

                    // Drag Handle
                    const dragHandle = document.createElement("span");
                    dragHandle.className = "hideui-drag-handle";
                    dragHandle.textContent = "≡";
                    dragHandle.title = "Drag to reorder";
                    row.appendChild(dragHandle);

                    // Mobile Move Up/Down buttons
                    const moveCol = document.createElement("div");
                    Object.assign(moveCol.style, {
                        display: "flex",
                        flexDirection: "column",
                        gap: "1px"
                    });

                    const upBtn = document.createElement("button");
                    upBtn.className = "hideui-move-btn";
                    upBtn.textContent = "▲";
                    upBtn.title = "Move Up";
                    upBtn.disabled = (index === 0);
                    upBtn.style.opacity = index === 0 ? "0.3" : "1";
                    upBtn.onclick = (e) => {
                        e.stopPropagation();
                        moveTargetIndex(index, index - 1);
                    };

                    const downBtn = document.createElement("button");
                    downBtn.className = "hideui-move-btn";
                    downBtn.textContent = "▼";
                    downBtn.title = "Move Down";
                    downBtn.disabled = (index === allTargets.length - 1);
                    downBtn.style.opacity = index === allTargets.length - 1 ? "0.3" : "1";
                    downBtn.onclick = (e) => {
                        e.stopPropagation();
                        moveTargetIndex(index, index + 1);
                    };

                    moveCol.appendChild(upBtn);
                    moveCol.appendChild(downBtn);
                    row.appendChild(moveCol);
                }

                // Checkbox
                const cb = document.createElement("input");
                cb.type = "checkbox";
                cb.id = `cb-${target.id}`;
                cb.checked = isChecked;
                Object.assign(cb.style, {
                    cursor: "pointer",
                    accentColor: "var(--studio-accent, #2563eb)",
                    width: "15px",
                    height: "15px",
                    flexShrink: "0"
                });
                cb.onclick = (e) => e.stopPropagation();
                cb.onchange = () => {
                    setTargetVisibility(target, cb.checked);
                    savePreferences();
                };
                row.appendChild(cb);

                // Group Pill (if any)
                if (target.group) {
                    const groupPill = document.createElement("span");
                    groupPill.className = "hideui-group-pill";
                    groupPill.textContent = target.group;
                    groupPill.title = `Group: ${target.group}`;
                    row.appendChild(groupPill);
                }

                // Target Name
                const nameSpan = document.createElement("span");
                nameSpan.textContent = target.name;
                nameSpan.title = target.name;
                Object.assign(nameSpan.style, {
                    flex: "1",
                    fontSize: "13px",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    cursor: isEdit ? "grab" : "default"
                });
                row.appendChild(nameSpan);

                // Cached badge in edit mode
                if (isEdit && isElementModified(target)) {
                    const badge = document.createElement("span");
                    badge.className = "hideui-badge-cached";
                    badge.textContent = "Cached";
                    badge.title = "Modified or added locally (click Export Config to save into config.json)";
                    row.appendChild(badge);
                }

                // Mode toggle badge (Hide vs Compact)
                const isCompact = (target.mode === 'compact');
                if (isEdit) {
                    const modeBadge = document.createElement("button");
                    modeBadge.className = `hideui-badge-mode ${isCompact ? 'mode-compact' : 'mode-hide'}`;
                    modeBadge.textContent = isCompact ? "Compact" : "Hide";
                    modeBadge.title = isCompact ? "Mode: Compact (click to switch to Hide)" : "Mode: Hide (click to switch to Compact)";
                    modeBadge.onclick = (e) => {
                        e.stopPropagation();
                        target.mode = isCompact ? 'hide' : 'compact';
                        const elements = loadCustomElements();
                        const idx = elements.findIndex(el => el.id === target.id);
                        if (idx !== -1) {
                            elements[idx].mode = target.mode;
                            saveCustomElements(elements);
                        }
                        renderMenu();
                        applyVisibility();
                    };
                    row.appendChild(modeBadge);
                } else if (isCompact) {
                    const modeIndicator = document.createElement("span");
                    modeIndicator.className = "hideui-badge-mode mode-compact";
                    modeIndicator.textContent = "Compact";
                    modeIndicator.title = "This toggle compacts rather than completely hides the element";
                    row.appendChild(modeIndicator);
                }

                // Default state indicator (Star)
                const isDefault = (target.default !== false);
                if (isEdit) {
                    const starBtn = document.createElement("button");
                    starBtn.className = "hideui-btn-icon";
                    starBtn.textContent = isDefault ? "⭐" : "☆";
                    starBtn.title = isDefault ? "Starts enabled by default on load (click to disable)" : "Starts hidden by default on load (click to enable)";
                    starBtn.style.fontSize = "15px";
                    starBtn.onclick = (e) => {
                        e.stopPropagation();
                        target.default = !isDefault;
                        const elements = loadCustomElements();
                        const idx = elements.findIndex(el => el.id === target.id);
                        if (idx !== -1) {
                            elements[idx].default = target.default;
                            saveCustomElements(elements);
                        }
                        renderMenu();
                    };
                    row.appendChild(starBtn);

                    // Rename button
                    const editBtn = document.createElement("button");
                    editBtn.className = "hideui-btn-icon";
                    editBtn.textContent = "✏️";
                    editBtn.title = "Rename element";
                    editBtn.style.fontSize = "13px";
                    editBtn.onclick = (e) => {
                        e.stopPropagation();
                        const newName = prompt(`Rename "${target.name}":`, target.name);
                        if (newName && newName.trim() && newName.trim() !== target.name) {
                            target.name = newName.trim();
                            const elements = loadCustomElements();
                            const idx = elements.findIndex(el => el.id === target.id);
                            if (idx !== -1) {
                                elements[idx].name = target.name;
                                saveCustomElements(elements);
                            }
                            renderMenu();
                        }
                    };
                    row.appendChild(editBtn);

                    // Delete button
                    const delBtn = document.createElement("button");
                    delBtn.className = "hideui-btn-icon";
                    delBtn.textContent = "✕";
                    delBtn.title = "Delete toggle";
                    delBtn.style.color = "#ef4444";
                    delBtn.style.fontSize = "15px";
                    delBtn.style.fontWeight = "bold";
                    delBtn.onclick = (e) => {
                        e.stopPropagation();
                        if (confirm(`Remove "${target.name}" from toggle list?`)) {
                            setTargetVisibility(target, true);
                            allTargets = allTargets.filter(t => t.id !== target.id);
                            saveCustomElements(allTargets);
                            saveElementOrder(allTargets.map(t => t.id));
                            renderMenu();
                        }
                    };
                    row.appendChild(delBtn);
                } else {
                    if (isDefault) {
                        const starSpan = document.createElement("span");
                        starSpan.textContent = "⭐";
                        starSpan.title = "Starts visible by default";
                        starSpan.style.fontSize = "13px";
                        row.appendChild(starSpan);
                    }
                }

                return row;
            }

            function filterRows() {
                const term = searchQuery.toLowerCase().trim();
                const rows = document.querySelectorAll(".hideui-row");
                rows.forEach(r => {
                    const name = (r.dataset.targetName || "").toLowerCase();
                    const group = (r.dataset.targetGroup || "").toLowerCase();
                    if (!term || name.includes(term) || group.includes(term)) {
                        r.style.display = "flex";
                    } else {
                        r.style.display = "none";
                    }
                });
            }

            function renderMenu() {
                const menu = document.getElementById("floating-menu");
                if (!menu) return;

                // Save list scroll position so it doesn't jump
                const existingList = menu.querySelector(".hideui-list");
                const prevScrollTop = existingList ? existingList.scrollTop : 0;

                menu.innerHTML = "";

                // --- HEADER SECTION ---
                const header = document.createElement("div");
                Object.assign(header.style, {
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                    borderBottom: "1px solid var(--studio-border, #467eaf)",
                    paddingBottom: "8px",
                    marginBottom: "2px"
                });

                if (editMode) {
                    const countRow = document.createElement("div");
                    Object.assign(countRow.style, {
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        fontSize: "11px",
                        color: "var(--studio-label, #a4cef0)",
                        fontWeight: "600",
                        textTransform: "uppercase",
                        letterSpacing: "0.5px"
                    });
                    countRow.textContent = `Edit Mode • ${allTargets.length} Elements`;
                    header.appendChild(countRow);

                    // Finished Editing button
                    const finishedBtn = document.createElement("button");
                    finishedBtn.id = "wan2gp-finish-edit-btn";
                    finishedBtn.className = "hideui-btn hideui-btn-success";
                    finishedBtn.textContent = "✔️ Finished Editing";
                    finishedBtn.style.width = "100%";
                    finishedBtn.style.fontSize = "12px";
                    finishedBtn.onclick = (e) => {
                        e.stopPropagation();
                        if (pickerMode) exitPickerMode();
                        editMode = false;
                        localStorage.setItem(STORAGE_KEY_EDIT, 'false');
                        renderMenu();
                    };
                    header.appendChild(finishedBtn);

                    // Add Element button
                    const addBtn = document.createElement("button");
                    addBtn.id = "wan2gp-add-element-btn";
                    addBtn.className = "hideui-btn hideui-btn-info";
                    addBtn.textContent = pickerMode ? "✕ Cancel Picker" : "➕ Add New Element";
                    addBtn.style.width = "100%";
                    addBtn.onclick = (e) => {
                        e.stopPropagation();
                        if (pickerMode) {
                            exitPickerMode();
                        } else {
                            enterPickerMode();
                        }
                    };
                    header.appendChild(addBtn);

                    // Import, Export & Reset buttons
                    const subRow = document.createElement("div");
                    Object.assign(subRow.style, {
                        display: "flex",
                        gap: "4px"
                    });

                    const importBtn = document.createElement("button");
                    importBtn.className = "hideui-btn";
                    importBtn.textContent = "📥 Import";
                    importBtn.title = "Hot-reload config.json directly from your computer without restarting Wan2GP";
                    importBtn.style.flex = "1";
                    importBtn.onclick = (e) => {
                        e.stopPropagation();
                        handleImportFromFile();
                    };

                    const exportBtn = document.createElement("button");
                    exportBtn.className = "hideui-btn";
                    exportBtn.textContent = "📤 Export";
                    exportBtn.title = "Export current configuration as JSON";
                    exportBtn.style.flex = "1";
                    exportBtn.onclick = (e) => {
                        e.stopPropagation();
                        showExportModal();
                    };

                    const resetBtn = document.createElement("button");
                    resetBtn.className = "hideui-btn";
                    resetBtn.textContent = "🔄 Reset";
                    resetBtn.title = "Reset to original startup config.json";
                    resetBtn.style.flex = "1";
                    resetBtn.onclick = (e) => {
                        e.stopPropagation();
                        handleResetFromFile();
                    };

                    subRow.appendChild(importBtn);
                    subRow.appendChild(exportBtn);
                    subRow.appendChild(resetBtn);
                    header.appendChild(subRow);

                } else {
                    // Normal Mode Header
                    const showDefaultBtn = document.createElement("button");
                    showDefaultBtn.id = "wan2gp-show-default-btn";
                    showDefaultBtn.className = "hideui-btn hideui-btn-primary";
                    showDefaultBtn.textContent = "Show Default";
                    showDefaultBtn.style.width = "100%";
                    showDefaultBtn.style.padding = "8px 12px";
                    showDefaultBtn.title = "Reset toggles to your default saved configuration";
                    showDefaultBtn.onclick = (e) => {
                        e.stopPropagation();
                        allTargets.forEach(target => {
                            const defaultState = (target.default !== false);
                            setTargetVisibility(target, defaultState);
                            const cb = document.getElementById(`cb-${target.id}`);
                            if (cb) cb.checked = defaultState;
                        });
                        savePreferences();
                    };
                    header.appendChild(showDefaultBtn);

                    const actionRow = document.createElement("div");
                    Object.assign(actionRow.style, {
                        display: "flex",
                        gap: "6px"
                    });

                    const toggleAllBtn = document.createElement("button");
                    toggleAllBtn.className = "hideui-btn";
                    toggleAllBtn.textContent = "Show/Hide All";
                    toggleAllBtn.style.flex = "1";
                    let allHidden = false;
                    toggleAllBtn.onclick = (e) => {
                        e.stopPropagation();
                        allHidden = !allHidden;
                        allTargets.forEach(target => {
                            setTargetVisibility(target, !allHidden);
                            const cb = document.getElementById(`cb-${target.id}`);
                            if (cb) cb.checked = !allHidden;
                        });
                        savePreferences();
                    };

                    const editBtn = document.createElement("button");
                    editBtn.className = "hideui-btn";
                    editBtn.textContent = "Edit";
                    editBtn.style.flex = "1";
                    editBtn.onclick = (e) => {
                        e.stopPropagation();
                        editMode = true;
                        localStorage.setItem(STORAGE_KEY_EDIT, 'true');
                        renderMenu();
                    };

                    actionRow.appendChild(toggleAllBtn);
                    actionRow.appendChild(editBtn);
                    header.appendChild(actionRow);
                }

                // Search Filter input
                const searchInput = document.createElement("input");
                searchInput.type = "text";
                searchInput.className = "hideui-search-input";
                searchInput.placeholder = "🔍 Search toggles...";
                searchInput.value = searchQuery;
                searchInput.oninput = (e) => {
                    searchQuery = e.target.value;
                    filterRows();
                };
                header.appendChild(searchInput);

                menu.appendChild(header);

                // --- LIST OF TARGET ELEMENTS ---
                const list = document.createElement("div");
                list.className = "hideui-list";

                const savedPrefs = loadPreferences();
                allTargets.forEach((target, idx) => {
                    const isChecked = savedPrefs.hasOwnProperty(target.id)
                        ? savedPrefs[target.id]
                        : (target.default !== false);

                    const row = createRow(target, idx, isChecked, editMode);
                    list.appendChild(row);
                });

                menu.appendChild(list);

                // Restore list scroll position
                requestAnimationFrame(() => {
                    if (list) list.scrollTop = prevScrollTop;
                    if (searchQuery) filterRows();
                });
            }

            // --- UI MOUNTING ---

            function mountUI() {
                if (document.getElementById("floating-toggle-container")) {
                    return; // Mounted already
                }

                injectStyles();
                syncTargetsFromStorage();

                const container = document.createElement("div");
                container.id = "floating-toggle-container";

                const menu = document.createElement("div");
                menu.id = "floating-menu";
                menu.style.display = menuOpen ? "flex" : "none";
                menu.onclick = (e) => e.stopPropagation();

                const toggleBtn = document.createElement("button");
                toggleBtn.id = "floating-toggle-btn";
                toggleBtn.textContent = menuOpen ? "✕ Close" : "☰ UI";
                toggleBtn.onclick = (e) => {
                    e.stopPropagation();
                    const isHidden = (menu.style.display === "none");
                    menu.style.display = isHidden ? "flex" : "none";
                    toggleBtn.textContent = isHidden ? "✕ Close" : "☰ UI";
                    menuOpen = isHidden;
                    localStorage.setItem(STORAGE_KEY_OPEN, menuOpen ? 'true' : 'false');
                    if (!isHidden && pickerMode) {
                        exitPickerMode();
                    }
                };

                container.appendChild(menu);
                container.appendChild(toggleBtn);
                document.body.appendChild(container);

                uiMounted = true;
                renderMenu();
                applyVisibility();
                console.log(`[Wan2GP-HideUI] v4.0 Mounted successfully with ${allTargets.length} elements.`);
            }

            // --- PERIODIC APPLIER FOR DYNAMIC GRADIO COMPONENTS ---
            let checks = 0;
            const checkInterval = setInterval(() => {
                checks++;
                if (!document.getElementById("floating-toggle-container")) {
                    mountUI();
                } else {
                    applyVisibility();
                }
                if (checks >= 10) clearInterval(checkInterval);
            }, 600);

            // Listen for Gradio and DOM ready events
            window.addEventListener("gradioLoaded", () => setTimeout(mountUI, 200));
            document.addEventListener("DOMContentLoaded", () => setTimeout(mountUI, 300));
            window.addEventListener("load", () => setTimeout(mountUI, 400));
            setTimeout(mountUI, 100);
        })();
        """

        return js_code.replace("__CONFIG_JSON_PLACEHOLDER__", config_json)