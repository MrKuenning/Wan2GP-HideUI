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
        self.version = "4.1"
        self.description = "Floating menu to toggle and compact UI elements, optimized for desktop and mobile."
        self.request_component("generate_btn")

    def load_config(self):
        """Load configuration from config.json if it exists"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Wan2GP-HideUI] Error loading config.json: {e}")
                return {"elements": [], "order": [], "presets": {}, "activePreset": "1"}
        return {"elements": [], "order": [], "presets": {}, "activePreset": "1"}

    def save_config(self, elements, order, presets=None, activePreset="1", prefs=None):
        """Save configuration directly to config.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        config_data = {
            "activePreset": str(activePreset or "1"),
            "presets": presets or {},
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

    def post_ui_setup(self, components: dict) -> dict:
        try:
            def create_bridge():
                with gr.Row(visible=False, elem_id="wan2gp_hideui_bridge_row"):
                    bridge_save_input = gr.Textbox(elem_id="wan2gp_hideui_bridge_save_input", visible=False)
                    bridge_save_btn = gr.Button(elem_id="wan2gp_hideui_bridge_save_btn", visible=False)
                    bridge_reload_btn = gr.Button(elem_id="wan2gp_hideui_bridge_reload_btn", visible=False)
                    bridge_output = gr.Textbox(elem_id="wan2gp_hideui_bridge_output", visible=False)

                def handle_save(payload):
                    try:
                        data = json.loads(payload)
                        res = self.save_config(
                            elements=data.get("elements", []),
                            order=data.get("order", []),
                            presets=data.get("presets", {}),
                            activePreset=str(data.get("activePreset", "1")),
                            prefs=data.get("prefs")
                        )
                        if res.get("status") == "success":
                            return json.dumps({"action": "save", "status": "success"})
                        else:
                            return json.dumps({"action": "save", "status": "error", "message": res.get("message")})
                    except Exception as e:
                        print(f"[Wan2GP-HideUI] Error saving config.json: {e}")
                        return json.dumps({"action": "save", "status": "error", "message": str(e)})

                def handle_reload():
                    try:
                        cfg = self.load_config()
                        return json.dumps({"action": "reload", "status": "success", "config": cfg})
                    except Exception as e:
                        print(f"[Wan2GP-HideUI] Error reloading config.json: {e}")
                        return json.dumps({"action": "reload", "status": "error", "message": str(e)})

                bridge_save_btn.click(
                    fn=handle_save,
                    inputs=[bridge_save_input],
                    outputs=[bridge_output],
                    show_progress="hidden"
                )

                bridge_reload_btn.click(
                    fn=handle_reload,
                    inputs=[],
                    outputs=[bridge_output],
                    show_progress="hidden"
                )

                bridge_output.change(
                    fn=None,
                    inputs=[bridge_output],
                    js="""(responseStr) => {
                        if (window.wgp_hideui_handle_bridge_response) {
                            window.wgp_hideui_handle_bridge_response(responseStr);
                        }
                    }""",
                    show_progress="hidden"
                )

                return bridge_save_input

            self.insert_after(
                target_component_id="generate_btn",
                new_component_constructor=create_bridge
            )
        except Exception as e:
            print(f"[Wan2GP-HideUI] Error in post_ui_setup: {e}")
            import traceback
            traceback.print_exc()

        return {}

    def inject_floating_buttons_js(self) -> str:
        config = self.load_config()
        config_json = json.dumps(config)

        js_code = r"""
        (function(){
            const STORAGE_KEY_EDIT     = "wan2gp_hideui_editMode";
            const STORAGE_KEY_OPEN     = "wan2gp_hideui_open";

            // Purge legacy browser-cached configuration so config.json is the single source of truth
            try {
                localStorage.removeItem("wan2gp_hideui_custom");
                localStorage.removeItem("wan2gp_hideui_prefs");
                localStorage.removeItem("wan2gp_hideui_order");
                localStorage.removeItem("wan2gp_hideui_presets");
                localStorage.removeItem("wan2gp_hideui_active_preset");
                sessionStorage.removeItem("wan2gp_hideui_session_init");
            } catch (e) {}

            const FILE_CONFIG = __CONFIG_JSON_PLACEHOLDER__;
            let runtimeConfig = JSON.parse(JSON.stringify(FILE_CONFIG || {}));
            if (!runtimeConfig.elements) runtimeConfig.elements = [];
            if (!runtimeConfig.order) runtimeConfig.order = runtimeConfig.elements.map(e => e.id);
            if (!runtimeConfig.presets) runtimeConfig.presets = {};
            if (!runtimeConfig.activePreset) runtimeConfig.activePreset = "1";
            if (!runtimeConfig.prefs) runtimeConfig.prefs = {};

            let allTargets = [];
            let editMode = localStorage.getItem(STORAGE_KEY_EDIT) === 'true';
            let menuOpen = localStorage.getItem(STORAGE_KEY_OPEN) === 'true';
            let pickerMode = false;
            let highlightOverlay = null;
            let uiMounted = false;
            let searchQuery = "";
            let diskSyncTimer = null;

            // --- DIRECT-TO-DISK CONFIGURATION HELPERS ---

            function getDefaultPresets() {
                if (runtimeConfig.presets && typeof runtimeConfig.presets === "object" && Object.keys(runtimeConfig.presets).length > 0) {
                    return JSON.parse(JSON.stringify(runtimeConfig.presets));
                }
                const p1States = {};
                allTargets.forEach(t => { p1States[t.id] = (t.default !== false); });
                return {
                    "1": { "name": "Standard", "states": Object.assign({}, p1States) },
                    "2": { "name": "Minimal", "states": Object.assign({}, p1States) },
                    "3": { "name": "Full Focus", "states": Object.assign({}, p1States) }
                };
            }

            function loadPresets() {
                if (runtimeConfig.presets && typeof runtimeConfig.presets === "object" && Object.keys(runtimeConfig.presets).length > 0) {
                    return runtimeConfig.presets;
                }
                const defaults = getDefaultPresets();
                runtimeConfig.presets = defaults;
                return defaults;
            }

            function savePresets(presets) {
                runtimeConfig.presets = presets;
                syncConfigToDisk();
            }

            function getActivePresetId() {
                const presets = loadPresets();
                const active = runtimeConfig.activePreset;
                if (active && presets[active]) return String(active);
                return "1";
            }

            function setActivePresetId(id) {
                runtimeConfig.activePreset = String(id);
                syncConfigToDisk();
            }

            function applyPreset(presetId) {
                const presets = loadPresets();
                const preset = presets[presetId];
                if (!preset || !preset.states) return;

                setActivePresetId(presetId);
                const states = preset.states;

                allTargets.forEach(target => {
                    const shouldShow = (states[target.id] !== undefined)
                        ? states[target.id]
                        : (target.default !== false);

                    setTargetVisibility(target, shouldShow);
                    const cb = document.getElementById(`cb-${target.id}`);
                    if (cb) cb.checked = shouldShow;
                });

                savePreferences();
                updatePresetButtonsUI();
            }

            function saveCurrentToActivePreset() {
                const activeId = getActivePresetId();
                const presets = loadPresets();
                if (!presets[activeId]) {
                    presets[activeId] = { name: `Preset ${activeId}`, states: {} };
                }

                const currentStates = {};
                allTargets.forEach(target => {
                    const cb = document.getElementById(`cb-${target.id}`);
                    if (cb) currentStates[target.id] = cb.checked;
                });

                presets[activeId].states = currentStates;
                savePresets(presets);
                return activeId;
            }

            function updatePresetButtonsUI() {
                const activeId = getActivePresetId();
                const presets = loadPresets();
                const pBtns = document.querySelectorAll(".hideui-preset-btn");
                pBtns.forEach(btn => {
                    const pid = btn.dataset.presetId;
                    if (pid === activeId) {
                        btn.classList.add("is-active");
                    } else {
                        btn.classList.remove("is-active");
                    }
                });
                const saveBtn = document.getElementById("wan2gp-save-preset-btn");
                if (saveBtn) {
                    const pData = presets[activeId] || { name: `P${activeId}` };
                    saveBtn.textContent = `💾 Save P${activeId}`;
                    saveBtn.title = `Save current toggle states into Preset ${activeId} (${pData.name})`;
                }
            }

            function loadCustomElements() {
                return runtimeConfig.elements || [];
            }

            function saveCustomElements(elements) {
                runtimeConfig.elements = elements;
                syncConfigToDisk();
            }

            function loadPreferences() {
                const activeId = getActivePresetId();
                const presets = loadPresets();
                const activePreset = presets[activeId];
                const prefs = {};
                allTargets.forEach(t => {
                    if (activePreset && activePreset.states && activePreset.states[t.id] !== undefined) {
                        prefs[t.id] = activePreset.states[t.id];
                    } else if (runtimeConfig.prefs && runtimeConfig.prefs[t.id] !== undefined) {
                        prefs[t.id] = runtimeConfig.prefs[t.id];
                    } else {
                        prefs[t.id] = (t.default !== false);
                    }
                });
                return prefs;
            }

            function savePreferences() {
                const prefs = {};
                allTargets.forEach(target => {
                    const cb = document.getElementById(`cb-${target.id}`);
                    if (cb) {
                        prefs[target.id] = cb.checked;
                    }
                });
                runtimeConfig.prefs = prefs;
                syncConfigToDisk();
            }

            function loadElementOrder() {
                if (runtimeConfig.order && Array.isArray(runtimeConfig.order) && runtimeConfig.order.length > 0) {
                    return runtimeConfig.order.slice();
                }
                const initial = (runtimeConfig.elements || []).map(e => e.id);
                runtimeConfig.order = initial;
                return initial.slice();
            }

            function saveElementOrder(order) {
                const list = order || allTargets.map(t => t.id);
                runtimeConfig.order = list;
                syncConfigToDisk();
            }

            function syncTargetsFromStorage() {
                allTargets = (runtimeConfig.elements || []).slice();
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
                        min-width: 360px;
                        max-width: min(460px, calc(100vw - 32px));
                        max-height: 82vh;
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
                    .hideui-preset-bar {
                        display: flex;
                        gap: 5px;
                        width: 100%;
                        margin-bottom: 2px;
                    }
                    .hideui-preset-btn {
                        flex: 1;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        gap: 3px;
                        padding: 7px 4px;
                        border-radius: 6px;
                        border: 1px solid var(--studio-border, #467eaf);
                        background: var(--studio-button, #205786);
                        color: var(--studio-button-text, #e6f2fc);
                        font-size: 11px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.15s ease;
                        text-align: center;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        box-sizing: border-box;
                    }
                    .hideui-preset-btn:hover {
                        background: var(--studio-button-hover, #2b6ba8);
                        filter: brightness(1.1);
                    }
                    .hideui-preset-btn.is-active {
                        background: #2563eb;
                        color: #ffffff;
                        border-color: #60a5fa;
                        box-shadow: 0 0 10px rgba(37, 99, 235, 0.45);
                    }
                    .hideui-save-preset-btn {
                        background: var(--studio-soft, #1b3c59);
                        color: var(--studio-label, #a4cef0);
                        border: 1px solid var(--studio-border, #467eaf);
                        font-weight: 600;
                        font-size: 11px;
                    }
                    .hideui-save-preset-btn:hover {
                        background: #16a34a;
                        color: #ffffff;
                        border-color: #22c55e;
                    }
                    .hideui-preset-edit-bar {
                        display: flex;
                        gap: 4px;
                        width: 100%;
                        margin-bottom: 2px;
                    }
                    .hideui-preset-edit-btn {
                        flex: 1;
                        font-size: 10px;
                        padding: 5px 3px;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
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
                    .hideui-badge-custom {
                        font-size: 9px;
                        font-weight: 700;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        background: rgba(2, 132, 199, 0.25);
                        border: 1px solid rgba(56, 189, 248, 0.4);
                        color: #7dd3fc;
                        padding: 1px 5px;
                        border-radius: 3px;
                    }
                    .hideui-status-badge {
                        font-size: 11px;
                        padding: 2px 8px;
                        border-radius: 12px;
                        background: rgba(22, 163, 74, 0.2);
                        border: 1px solid rgba(22, 163, 74, 0.4);
                        color: #4ade80;
                        transition: opacity 0.3s ease;
                        display: inline-flex;
                        align-items: center;
                        gap: 4px;
                    }
                    .hideui-status-badge.is-error {
                        background: rgba(239, 68, 68, 0.2);
                        border-color: rgba(239, 68, 68, 0.4);
                        color: #f87171;
                    }
                    .hideui-row-presets {
                        display: inline-flex;
                        gap: 3px;
                        align-items: center;
                        margin: 0 4px;
                    }
                    .hideui-row-preset-btn {
                        width: 22px;
                        height: 22px;
                        padding: 0;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 700;
                        line-height: 1;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        cursor: pointer;
                        border: 1px solid var(--studio-border, #467eaf);
                        transition: all 0.15s ease;
                        box-sizing: border-box;
                    }
                    .hideui-row-preset-btn.is-enabled {
                        background: #2563eb;
                        color: #ffffff;
                        border-color: #60a5fa;
                        box-shadow: 0 0 6px rgba(37, 99, 235, 0.4);
                    }
                    .hideui-row-preset-btn.is-disabled {
                        background: rgba(16, 35, 56, 0.8);
                        color: var(--studio-disabled-text, #97a3b2);
                        border-color: rgba(70, 126, 175, 0.3);
                        opacity: 0.55;
                    }
                    .hideui-row-preset-btn.is-disabled:hover {
                        background: var(--studio-soft, #1b3c59);
                        color: var(--studio-button-text, #e6f2fc);
                        opacity: 1;
                        border-color: var(--studio-border, #467eaf);
                    }
                    .hideui-row-preset-btn.is-enabled:hover {
                        background: #1d4ed8;
                        filter: brightness(1.1);
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
                const list = Array.from(elementsSet).filter(el => {
                    if (!el) return false;
                    if (
                        el.id === "root" ||
                        el.id === "component-0" ||
                        el.id === "component-6" ||
                        el.id === "component-42" ||
                        el.id === "component-44" ||
                        el.tagName === "BODY" ||
                        el.tagName === "MAIN" ||
                        el.getAttribute("role") === "tabpanel" ||
                        el.classList.contains("tabitem") ||
                        el.classList.contains("tabs") ||
                        el.classList.contains("gradio-container") ||
                        el.classList.contains("app") ||
                        el.classList.contains("fillable") ||
                        el.closest("#floating-toggle-container") ||
                        el.closest("#wan2gp-modal-container") ||
                        el.closest("#wan2gp-picker-overlay")
                    ) {
                        return false;
                    }
                    if (!el.classList.contains("accordion") && el.tagName !== "DETAILS" && (el.classList.contains("row") || el.classList.contains("column"))) {
                        if (el.querySelector(".tabs, .tabitem, [role='tablist']")) {
                            return false;
                        }
                    }
                    return true;
                });
                // Prune outer row/column if an inner row/column was also matched, preventing layout bubbling
                return list.filter(el => {
                    if (el.classList.contains("row") || el.classList.contains("column")) {
                        return !list.some(other => other !== el && (other.classList.contains("row") || other.classList.contains("column")) && el.contains(other));
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
                    const allBtns = Array.from(document.querySelectorAll("button, input[type='button'], input[type='submit']"));
                    btnTexts.forEach(bt => {
                        const normBt = bt.toLowerCase().replace(/\s+/g, ' ').trim();
                        if (!normBt) return;
                        allBtns.forEach(btn => {
                            const txt = (btn.innerText || btn.textContent || btn.value || "").toLowerCase().replace(/\s+/g, ' ').trim();
                            const isMatch = (txt === normBt) || (normBt.length > 5 && txt.includes(normBt));
                            if (isMatch) {
                                if (target.id === "presets_dropdown" || normBt === "apply" || normBt.includes("go ahead save") || normBt.includes("go ahead delete")) {
                                    const presetRow = btn.closest(".row")?.parentElement?.closest(".row");
                                    if (presetRow) {
                                        found.add(presetRow);
                                        return;
                                    }
                                }
                                if (target.id === "settings_buttons" || target.id === "enhance_prompt" || target.id === "lora_url") {
                                    const enclosingRow = btn.closest(".row, .gr-group, div[class*='group']");
                                    if (enclosingRow) {
                                        found.add(enclosingRow);
                                        return;
                                    }
                                }
                                const comp = btn.closest(".block, div[id^='wangp'], .accordion, details, .form, fieldset, .row") || btn;
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
                        "span[data-testid='block-info'], label[data-testid='block-label'], label, button.label-wrap, .label-wrap, summary, .accordion, details, input[aria-label], select[aria-label], textarea[aria-label], input[placeholder], textarea[placeholder]"
                    ));
                    target.labels.forEach(lbl => {
                        const term = lbl.toLowerCase().replace(/\s+/g, ' ').trim();
                        if (!term || term.length < 3) return;
                        labelCandidates.forEach(node => {
                            const aria = (node.getAttribute && node.getAttribute("aria-label")) ? node.getAttribute("aria-label").toLowerCase().replace(/\s+/g, ' ').trim() : "";
                            const ph = (node.getAttribute && node.getAttribute("placeholder")) ? node.getAttribute("placeholder").toLowerCase().replace(/\s+/g, ' ').trim() : "";
                            const txt = (node.innerText || node.textContent || "").toLowerCase().replace(/\s+/g, ' ').trim();
                            const isMatch = (txt === term) || (txt.startsWith(term + " ") || txt.endsWith(" " + term) || txt.includes(" " + term + " ")) ||
                                            (term.length >= 6 && txt.includes(term)) ||
                                            (aria === term) || (aria.startsWith(term + " ") || aria.endsWith(" " + term) || aria.includes(" " + term + " ")) ||
                                            (term.length >= 6 && aria.includes(term)) ||
                                            (ph === term) || (ph.startsWith(term + " ") || ph.endsWith(" " + term) || ph.includes(" " + term + " "));
                            if (isMatch) {
                                if (target.id === "lora_url" || target.id === "enhance_prompt" || target.id === "settings_buttons") {
                                    const enclosingRow = node.closest(".row, .gr-group, div[class*='group']");
                                    if (enclosingRow) {
                                        found.add(enclosingRow);
                                        return;
                                    }
                                }
                                const comp = node.closest(".block, div[id^='wangp'], .accordion, details, .form, fieldset") || node;
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
                    const allLabels = Array.from(document.querySelectorAll(
                        "span[data-testid='block-info'], label[data-testid='block-label'], label, button.label-wrap, .label-wrap, summary, input[aria-label], select[aria-label], textarea[aria-label]"
                    ));
                    for (const lbl of allLabels) {
                        const aria = (lbl.getAttribute && lbl.getAttribute("aria-label")) ? lbl.getAttribute("aria-label").toLowerCase().replace(/\s+/g, ' ').trim() : "";
                        const txt = (lbl.textContent || "").toLowerCase().replace(/\s+/g, ' ').trim();
                        if (txt === term || txt.startsWith(term) || aria === term || aria.startsWith(term)) {
                            const comp = lbl.closest(".block, div[id^='wangp'], .accordion, details, .wangp-studio-field, .form");
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
                elements.forEach(el => {
                    el.classList.remove("wangp-hideui-compact");
                    if (shouldShow) {
                        safeShow(el);
                    } else {
                        safeHide(el);
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

                const currentPresets = loadPresets();
                ["1", "2", "3"].forEach(pid => {
                    if (currentPresets[pid] && currentPresets[pid].states) {
                        currentPresets[pid].states[customId] = true;
                    }
                });
                savePresets(currentPresets);

                exitPickerMode();
                syncTargetsFromStorage();
                renderMenu();
                applyVisibility();
            }

            // --- DIRECT-TO-DISK SYNC & BRIDGE ---

            function showStatusBadge(text, isError = false) {
                const badge = document.getElementById("wan2gp-save-status-pill");
                if (!badge) return;
                badge.textContent = text;
                badge.style.display = "inline-flex";
                if (isError) {
                    badge.classList.add("is-error");
                } else {
                    badge.classList.remove("is-error");
                }
                badge.style.opacity = "1";
                if (!isError && text !== "Saving..." && text !== "Reloading...") {
                    setTimeout(() => {
                        badge.style.opacity = "0";
                        setTimeout(() => {
                            if (badge.style.opacity === "0") badge.style.display = "none";
                        }, 400);
                    }, 2500);
                }
            }

            function syncConfigToDisk() {
                clearTimeout(diskSyncTimer);
                diskSyncTimer = setTimeout(() => {
                    const payload = {
                        activePreset: getActivePresetId(),
                        presets: loadPresets(),
                        elements: (runtimeConfig.elements || allTargets).map(t => ({
                            id: t.id,
                            name: t.name,
                            ...(t.componentId ? { componentId: t.componentId } : {}),
                            ...(t.labels && t.labels.length ? { labels: t.labels } : {}),
                            ...(t.cssSelector ? { cssSelector: t.cssSelector } : {}),
                            ...(t.buttonText ? { buttonText: t.buttonText } : {}),
                            ...(t.group ? { group: t.group } : {}),
                            ...(t.isCustom ? { isCustom: true } : {}),
                            default: (t.default !== false)
                        })),
                        order: runtimeConfig.order || allTargets.map(t => t.id),
                        prefs: runtimeConfig.prefs || {}
                    };
                    const bridgeInput = document.querySelector('#wan2gp_hideui_bridge_save_input textarea') ||
                                        document.querySelector('#wan2gp_hideui_bridge_save_input input');
                    const bridgeBtn = document.getElementById('wan2gp_hideui_bridge_save_btn');
                    if (bridgeInput && bridgeBtn) {
                        bridgeInput.value = JSON.stringify(payload);
                        bridgeInput.dispatchEvent(new Event('input', { bubbles: true }));
                        bridgeBtn.click();
                        showStatusBadge("Saving...");
                    } else {
                        console.warn("[Wan2GP-HideUI] Gradio bridge not found; config not written to disk.");
                    }
                }, 250);
            }

            function handleReloadFromDisk() {
                const bridgeBtn = document.getElementById('wan2gp_hideui_bridge_reload_btn');
                if (bridgeBtn) {
                    showStatusBadge("Reloading...");
                    bridgeBtn.click();
                } else {
                    alert("Gradio backend bridge not found. Please restart Wan2GP to reload config.json.");
                }
            }

            function applyLoadedConfig(newConfig) {
                if (!newConfig || !Array.isArray(newConfig.elements)) return;
                runtimeConfig = JSON.parse(JSON.stringify(newConfig));
                if (!runtimeConfig.order) runtimeConfig.order = runtimeConfig.elements.map(e => e.id);
                if (!runtimeConfig.presets) runtimeConfig.presets = {};
                if (!runtimeConfig.activePreset) runtimeConfig.activePreset = "1";
                if (!runtimeConfig.prefs) runtimeConfig.prefs = {};

                syncTargetsFromStorage();
                applyPreset(getActivePresetId());
                renderMenu();
            }

            window.wgp_hideui_handle_bridge_response = function(responseStr) {
                try {
                    if (!responseStr) return;
                    const res = JSON.parse(responseStr);
                    if (res.action === "save") {
                        if (res.status === "success") {
                            showStatusBadge("✓ Saved to config.json");
                        } else {
                            showStatusBadge("⚠️ " + (res.message || "Save error"), true);
                        }
                    } else if (res.action === "reload") {
                        if (res.status === "success" && res.config) {
                            applyLoadedConfig(res.config);
                            showStatusBadge("✓ Reloaded from disk");
                        } else {
                            showStatusBadge("⚠️ " + (res.message || "Reload error"), true);
                        }
                    }
                } catch (e) {
                    console.error("[Wan2GP-HideUI] Error handling bridge response:", e);
                }
            };

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

                // Group Pill (if any, hidden in edit mode to save space)
                if (target.group && !isEdit) {
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

                // Custom badge in edit mode
                if (isEdit && target.isCustom) {
                    const badge = document.createElement("span");
                    badge.className = "hideui-badge-custom";
                    badge.textContent = "Custom";
                    badge.title = "Custom added element (saved to config.json)";
                    row.appendChild(badge);
                }

                if (isEdit) {
                    // Three preset toggles [ 1 ] [ 2 ] [ 3 ]
                    const presetsWrapper = document.createElement("div");
                    presetsWrapper.className = "hideui-row-presets";

                    const currentPresets = loadPresets();
                    ["1", "2", "3"].forEach(pid => {
                        const pData = currentPresets[pid] || { name: `Preset ${pid}`, states: {} };
                        const isPresetEnabled = (pData.states && pData.states[target.id] !== undefined)
                            ? pData.states[target.id]
                            : (target.default !== false);

                        const pToggle = document.createElement("button");
                        pToggle.className = `hideui-row-preset-btn ${isPresetEnabled ? 'is-enabled' : 'is-disabled'}`;
                        pToggle.textContent = pid;
                        pToggle.title = `Preset ${pid} (${pData.name}): ${isPresetEnabled ? 'Enabled' : 'Disabled'} (click to toggle)`;
                        pToggle.onclick = (e) => {
                            e.stopPropagation();
                            if (!pData.states) pData.states = {};
                            const newState = !isPresetEnabled;
                            pData.states[target.id] = newState;
                            currentPresets[pid] = pData;
                            savePresets(currentPresets);

                            if (pid === "1") {
                                target.default = newState;
                                const elements = loadCustomElements();
                                const idx = elements.findIndex(el => el.id === target.id);
                                if (idx !== -1) {
                                    elements[idx].default = newState;
                                    saveCustomElements(elements);
                                }
                            }

                            if (getActivePresetId() === pid) {
                                setTargetVisibility(target, newState);
                                const currentCb = document.getElementById(`cb-${target.id}`);
                                if (currentCb) currentCb.checked = newState;
                                savePreferences();
                            }

                            renderMenu();
                        };
                        presetsWrapper.appendChild(pToggle);
                    });
                    row.appendChild(presetsWrapper);

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

                            const currentPresets = loadPresets();
                            ["1", "2", "3"].forEach(pid => {
                                if (currentPresets[pid] && currentPresets[pid].states) {
                                    delete currentPresets[pid].states[target.id];
                                }
                            });
                            savePresets(currentPresets);

                            renderMenu();
                        }
                    };
                    row.appendChild(delBtn);
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

                    const countTitle = document.createElement("span");
                    countTitle.textContent = `Edit Mode • ${allTargets.length} Elements`;
                    countRow.appendChild(countTitle);

                    const statusPill = document.createElement("span");
                    statusPill.id = "wan2gp-save-status-pill";
                    statusPill.className = "hideui-status-badge";
                    statusPill.style.display = "none";
                    countRow.appendChild(statusPill);

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

                    // Action buttons row: Add Element & Reload from Disk
                    const editActionRow = document.createElement("div");
                    Object.assign(editActionRow.style, {
                        display: "flex",
                        gap: "6px"
                    });

                    const addBtn = document.createElement("button");
                    addBtn.id = "wan2gp-add-element-btn";
                    addBtn.className = "hideui-btn hideui-btn-info";
                    addBtn.textContent = pickerMode ? "✕ Cancel Picker" : "➕ Add Element";
                    addBtn.style.flex = "1.2";
                    addBtn.onclick = (e) => {
                        e.stopPropagation();
                        if (pickerMode) {
                            exitPickerMode();
                        } else {
                            enterPickerMode();
                        }
                    };

                    const reloadBtn = document.createElement("button");
                    reloadBtn.className = "hideui-btn";
                    reloadBtn.textContent = "🔄 Reload Disk";
                    reloadBtn.title = "Reload config.json directly from disk without restarting Wan2GP";
                    reloadBtn.style.flex = "0.8";
                    reloadBtn.onclick = (e) => {
                        e.stopPropagation();
                        handleReloadFromDisk();
                    };

                    editActionRow.appendChild(addBtn);
                    editActionRow.appendChild(reloadBtn);
                    header.appendChild(editActionRow);

                    // Preset Rename Bar in Edit Mode
                    const presetEditBar = document.createElement("div");
                    presetEditBar.className = "hideui-preset-edit-bar";
                    const currentPresets = loadPresets();
                    ["1", "2", "3"].forEach(pid => {
                        const pData = currentPresets[pid] || { name: `Preset ${pid}` };
                        const pBtn = document.createElement("button");
                        pBtn.className = "hideui-btn hideui-preset-edit-btn";
                        pBtn.textContent = `✏️ P${pid}: ${pData.name}`;
                        pBtn.title = `Click to rename Preset ${pid}`;
                        pBtn.onclick = (e) => {
                            e.stopPropagation();
                            const newName = prompt(`Rename Preset ${pid}:`, pData.name);
                            if (newName && newName.trim() && newName.trim() !== pData.name) {
                                currentPresets[pid].name = newName.trim();
                                savePresets(currentPresets);
                                renderMenu();
                            }
                        };
                        presetEditBar.appendChild(pBtn);
                    });
                    header.appendChild(presetEditBar);

                } else {
                    // Normal Mode Header: Status & Preset Buttons Row
                    const topRow = document.createElement("div");
                    Object.assign(topRow.style, {
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        minHeight: "16px",
                        padding: "0 2px"
                    });

                    const presetTitle = document.createElement("span");
                    presetTitle.textContent = "Presets";
                    Object.assign(presetTitle.style, {
                        fontSize: "10px",
                        color: "var(--studio-label, #a4cef0)",
                        fontWeight: "700",
                        textTransform: "uppercase",
                        letterSpacing: "0.5px"
                    });
                    topRow.appendChild(presetTitle);

                    const statusPill = document.createElement("span");
                    statusPill.id = "wan2gp-save-status-pill";
                    statusPill.className = "hideui-status-badge";
                    statusPill.style.display = "none";
                    topRow.appendChild(statusPill);

                    header.appendChild(topRow);

                    const presetBar = document.createElement("div");
                    presetBar.className = "hideui-preset-bar";
                    const currentPresets = loadPresets();
                    const activePresetId = getActivePresetId();

                    ["1", "2", "3"].forEach(pid => {
                        const pData = currentPresets[pid] || { name: `Preset ${pid}` };
                        const pBtn = document.createElement("button");
                        pBtn.className = `hideui-preset-btn ${pid === activePresetId ? "is-active" : ""}`;
                        pBtn.dataset.presetId = pid;
                        pBtn.textContent = `${pid}: ${pData.name}`;
                        pBtn.title = `Switch to Preset ${pid}: ${pData.name}`;
                        pBtn.onclick = (e) => {
                            e.stopPropagation();
                            applyPreset(pid);
                        };
                        presetBar.appendChild(pBtn);
                    });
                    header.appendChild(presetBar);

                    const actionRow = document.createElement("div");
                    Object.assign(actionRow.style, {
                        display: "flex",
                        gap: "5px"
                    });

                    // Save to Current Preset Button
                    const savePresetBtn = document.createElement("button");
                    savePresetBtn.id = "wan2gp-save-preset-btn";
                    savePresetBtn.className = "hideui-btn hideui-save-preset-btn";
                    savePresetBtn.style.flex = "1.1";
                    const curPData = currentPresets[activePresetId] || { name: `Preset ${activePresetId}` };
                    savePresetBtn.textContent = `💾 Save P${activePresetId}`;
                    savePresetBtn.title = `Save current toggle states into Preset ${activePresetId} (${curPData.name})`;
                    savePresetBtn.onclick = (e) => {
                        e.stopPropagation();
                        const savedId = saveCurrentToActivePreset();
                        savePresetBtn.textContent = `✓ Saved P${savedId}!`;
                        setTimeout(() => {
                            updatePresetButtonsUI();
                        }, 1800);
                    };

                    // Show All Button (Toggle All ON)
                    const showAllBtn = document.createElement("button");
                    showAllBtn.id = "wan2gp-show-all-btn";
                    showAllBtn.className = "hideui-btn";
                    showAllBtn.textContent = "Show All";
                    showAllBtn.title = "Toggle all elements ON (make everything visible)";
                    showAllBtn.style.flex = "1";
                    showAllBtn.onclick = (e) => {
                        e.stopPropagation();
                        allTargets.forEach(target => {
                            setTargetVisibility(target, true);
                            const cb = document.getElementById(`cb-${target.id}`);
                            if (cb) cb.checked = true;
                        });
                        savePreferences();
                    };

                    // Hide All Button (Toggle All OFF)
                    const hideAllBtn = document.createElement("button");
                    hideAllBtn.id = "wan2gp-hide-all-btn";
                    hideAllBtn.className = "hideui-btn";
                    hideAllBtn.textContent = "Hide All";
                    hideAllBtn.title = "Toggle all elements OFF (hide everything)";
                    hideAllBtn.style.flex = "1";
                    hideAllBtn.onclick = (e) => {
                        e.stopPropagation();
                        allTargets.forEach(target => {
                            setTargetVisibility(target, false);
                            const cb = document.getElementById(`cb-${target.id}`);
                            if (cb) cb.checked = false;
                        });
                        savePreferences();
                    };

                    // Edit Button
                    const editBtn = document.createElement("button");
                    editBtn.className = "hideui-btn";
                    editBtn.textContent = "⚙️ Edit";
                    editBtn.title = "Manage and customize toggles";
                    editBtn.style.flex = "0.9";
                    editBtn.onclick = (e) => {
                        e.stopPropagation();
                        editMode = true;
                        localStorage.setItem(STORAGE_KEY_EDIT, 'true');
                        renderMenu();
                    };

                    actionRow.appendChild(savePresetBtn);
                    actionRow.appendChild(showAllBtn);
                    actionRow.appendChild(hideAllBtn);
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