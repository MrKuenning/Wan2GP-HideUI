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
        self.version = "3.2"
        self.description = "Floating menu. Safe blank-space removal using State Tags."

    def load_config(self):
        """Load configuration from config.json if it exists"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config.json: {e}")
                return {"elements": [], "prefs": {}, "order": []}
        return {"elements": [], "prefs": {}, "order": []}

    def save_config(self, elements, prefs, order):
        """Save configuration to config.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        config_data = {
            "elements": elements,
            "prefs": prefs,
            "order": order
        }
        try:
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            return {"status": "success"}
        except Exception as e:
            print(f"Error saving config.json: {e}")
            return {"status": "error", "message": str(e)}

    def setup_ui(self):
        self.add_custom_js(self.inject_floating_buttons_js())


    def inject_floating_buttons_js(self) -> str:
        # Load config from file
        config = self.load_config()
        config_json = json.dumps(config)
        
        js_code = r"""
        (function(){
            const STORAGE_KEY_CUSTOM = "wan2gp_hideui_custom";
            const STORAGE_KEY_PREFS = "wan2gp_hideui_prefs";
            const STORAGE_KEY_ORDER = "wan2gp_hideui_order";
            
            // Load config from Python (injected from config.json)
            const FILE_CONFIG = __CONFIG_JSON_PLACEHOLDER__;
            
            // ALWAYS load from file - file is source of truth
            localStorage.setItem(STORAGE_KEY_CUSTOM, JSON.stringify(FILE_CONFIG.elements || []));
            localStorage.setItem(STORAGE_KEY_PREFS, JSON.stringify(FILE_CONFIG.prefs || {}));
            localStorage.setItem(STORAGE_KEY_ORDER, JSON.stringify(FILE_CONFIG.order || []));
            
            console.log("WAN2GP HideUI: Loaded config from file", FILE_CONFIG);

            let pickerMode = false;
            let highlightOverlay = null;
            let allTargets = [];
            let originalConfig = FILE_CONFIG; // Track original for modification detection
            let editMode = localStorage.getItem('wan2gp_hideui_editMode') === 'true'; // Persist edit mode

            // --- STORAGE LOGIC ---

            function loadCustomElements() {
                try {
                    const saved = localStorage.getItem(STORAGE_KEY_CUSTOM);
                    return saved ? JSON.parse(saved) : [];
                } catch (e) {
                    console.warn("Failed to load custom elements:", e);
                    return [];
                }
            }

            function saveCustomElements(elements) {
                try {
                    localStorage.setItem(STORAGE_KEY_CUSTOM, JSON.stringify(elements));
                } catch (e) {
                    console.error("Failed to save custom elements:", e);
                }
            }

            function loadPreferences() {
                try {
                    const saved = localStorage.getItem(STORAGE_KEY_PREFS);
                    return saved ? JSON.parse(saved) : {};
                } catch (e) {
                    console.warn("Failed to load preferences:", e);
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
                    console.error("Failed to save preferences:", e);
                }
            }

            function loadElementOrder() {
                try {
                    const saved = localStorage.getItem(STORAGE_KEY_ORDER);
                    return saved ? JSON.parse(saved) : [];
                } catch (e) {
                    console.warn("Failed to load element order:", e);
                    return [];
                }
            }

            function saveElementOrder() {
                try {
                    const order = allTargets.map(t => t.id);
                    localStorage.setItem(STORAGE_KEY_ORDER, JSON.stringify(order));
                } catch (e) {
                    console.error("Failed to save element order:", e);
                }
            }

            // --- SAFETY LOGIC ---

            function safeHide(element) {
                element.style.display = "none";
                let current = element.parentElement;
                let safetyCounter = 0;

                while (current && safetyCounter < 5) {
                    if (current.tagName === "BODY" || current.classList.contains("gradio-container") || current.id === "root") break;

                    const children = Array.from(current.children).filter(c => 
                        ["DIV", "BUTTON", "SPAN", "INPUT", "LABEL", "FORM", "FIELDSET"].includes(c.tagName)
                    );

                    const allHidden = children.every(c => c.style.display === "none");

                    if (allHidden && children.length > 0) {
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
                element.style.display = "";
                let current = element.parentElement;
                let safetyCounter = 0;

                while (current && safetyCounter < 5) {
                    if (current.tagName === "BODY") break;

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

            // --- VISIBILITY LOGIC ---

            function setVisibilityByLabels(searchLabels, shouldShow) {
                const terms = Array.isArray(searchLabels) ? searchLabels : [searchLabels];
                const allElements = Array.from(document.querySelectorAll("div[id^='component-'], button[id^='component-']"));

                terms.forEach(term => {
                    const lbl = term.toLowerCase().trim();
                    const candidates = allElements.filter(el => {
                        const text = (el.innerText || el.textContent || "").replace(/\s+/g,' ').trim().toLowerCase();
                        return text.includes(lbl);
                    });

                    const targets = candidates.filter(el => {
                        const containsChildMatch = candidates.some(other => other !== el && el.contains(other));
                        return !containsChildMatch;
                    });

                    targets.forEach(el => {
                        if (shouldShow) {
                            safeShow(el);
                        } else {
                            safeHide(el);
                        }
                    });
                });
            }

            function setVisibilityByElement(element, shouldShow) {
                if (shouldShow) {
                    safeShow(element);
                } else {
                    safeHide(element);
                }
            }

            function setVisibilityByComponentId(componentId, shouldShow) {
                const element = document.getElementById(componentId);
                if (element) {
                    setVisibilityByElement(element, shouldShow);
                }
            }

            // --- ELEMENT PICKER ---

            function createHighlightOverlay() {
                const overlay = document.createElement("div");
                overlay.id = "wan2gp-picker-overlay";
                Object.assign(overlay.style, {
                    position: "absolute",
                    pointerEvents: "none",
                    border: "3px solid #0284c7",
                    background: "rgba(2, 132, 199, 0.1)",
                    zIndex: "999998",
                    display: "none",
                    transition: "all 0.1s ease"
                });
                document.body.appendChild(overlay);
                return overlay;
            }

            function enterPickerMode() {
                pickerMode = true;
                document.body.style.cursor = "crosshair";
                
                if (!highlightOverlay) {
                    highlightOverlay = createHighlightOverlay();
                }

                // Update button text
                const addBtn = document.getElementById("wan2gp-add-element-btn");
                if (addBtn) {
                    addBtn.textContent = "❌ Cancel";
                    addBtn.style.background = "#dc2626";
                }

                // Add status message
                let statusMsg = document.getElementById("wan2gp-picker-status");
                if (!statusMsg) {
                    statusMsg = document.createElement("div");
                    statusMsg.id = "wan2gp-picker-status";
                    Object.assign(statusMsg.style, {
                        fontSize: "12px",
                        color: "#60a5fa",
                        padding: "8px",
                        borderTop: "1px solid #555",
                        marginTop: "8px",
                        textAlign: "center"
                    });
                    statusMsg.textContent = "Click any element to add it...";
                    document.getElementById("floating-menu").appendChild(statusMsg);
                }

                document.addEventListener("mouseover", highlightElement);
                document.addEventListener("click", selectElement, true);
            }

            function exitPickerMode() {
                pickerMode = false;
                document.body.style.cursor = "";
                
                if (highlightOverlay) {
                    highlightOverlay.style.display = "none";
                }

                const addBtn = document.getElementById("wan2gp-add-element-btn");
                if (addBtn) {
                    addBtn.textContent = "➕ Add Element";
                    addBtn.style.background = "#16a34a";
                }

                const statusMsg = document.getElementById("wan2gp-picker-status");
                if (statusMsg) {
                    statusMsg.remove();
                }

                document.removeEventListener("mouseover", highlightElement);
                document.removeEventListener("click", selectElement, true);
            }

            function highlightElement(e) {
                if (!pickerMode) return;
                
                const target = e.target;
                
                // Skip our own UI
                if (target.closest("#floating-toggle-container")) return;
                
                // Find the closest component
                const component = target.closest("div[id^='component-']");
                if (!component) return;

                const rect = component.getBoundingClientRect();
                Object.assign(highlightOverlay.style, {
                    display: "block",
                    left: rect.left + window.scrollX + "px",
                    top: rect.top + window.scrollY + "px",
                    width: rect.width + "px",
                    height: rect.height + "px"
                });
            }

            function selectElement(e) {
                if (!pickerMode) return;
                
                e.preventDefault();
                e.stopPropagation();
                
                const target = e.target;
                
                // Skip our own UI
                if (target.closest("#floating-toggle-container")) return;
                
                const component = target.closest("div[id^='component-']");
                if (!component) return;

                // Get element info
                const componentId = component.id;
                const label = component.querySelector("label, span[data-testid='block-label']");
                let elementName = label ? label.textContent.trim() : "";
                
                if (!elementName) {
                    // Try to get any text
                    const firstText = component.querySelector("span, p, h1, h2, h3");
                    elementName = firstText ? firstText.textContent.trim().substring(0, 50) : `Component ${componentId}`;
                }

                // Prompt for custom name
                const customName = prompt("Enter a name for this element:", elementName);
                if (!customName) {
                    exitPickerMode();
                    return;
                }

                // Create custom element
                const customId = "custom_" + customName.toLowerCase().replace(/[^a-z0-9]/g, '_');
                const customElement = {
                    id: customId,
                    name: customName,
                    componentId: componentId,
                    isCustom: true,
                    default: true  // New custom elements start visible by default
                };

                // Save to storage
                const customElements = loadCustomElements();
                customElements.push(customElement);
                saveCustomElements(customElements);

                // Exit picker mode and refresh UI
                exitPickerMode();
                buildMenuContent(); // Rebuild menu content
            }

            // --- UI CREATION ---

            function createUI() {
                // Remove existing UI if present
                const existing = document.getElementById("floating-toggle-container");
                if (existing) existing.remove();

                // Load all elements from storage
                allTargets = loadCustomElements();
                
                // Apply saved order
                const savedOrder = loadElementOrder();
                if (savedOrder.length > 0) {
                    allTargets.sort((a, b) => {
                        const aIndex = savedOrder.indexOf(a.id);
                        const bIndex = savedOrder.indexOf(b.id);
                        if (aIndex === -1 && bIndex === -1) return 0;
                        if (aIndex === -1) return 1;
                        if (bIndex === -1) return -1;
                        return aIndex - bIndex;
                    });
                }

                // Load saved preferences
                const savedPrefs = loadPreferences();

                const container = document.createElement("div");
                container.id = "floating-toggle-container";
                Object.assign(container.style, {
                    position: "fixed", bottom: "16px", right: "16px", zIndex: "999999",
                    display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "10px"
                });

                const menu = document.createElement("div");
                menu.id = "floating-menu";
                Object.assign(menu.style, {
                    background: "rgba(30, 30, 30, 0.95)", border: "1px solid #444", borderRadius: "8px",
                    padding: "10px", display: "none", flexDirection: "column", gap: "8px",
                    minWidth: "220px", boxShadow: "0 4px 12px rgba(0,0,0,0.5)", color: "white",
                    maxHeight: "70vh", overflowY: "auto"
                });
                
                // Prevent clicks inside menu from bubbling up and closing it
                menu.onclick = (e) => e.stopPropagation();
                
                // Store global reference for buildMenuContent
                menuElement = menu;

                const createCheckbox = (target, index, onChange, isChecked=true, editMode=false) => {
                    // Check if element has been modified
                    const isModified = () => {
                        const originalElement = originalConfig.elements?.find(e => e.id === target.id);
                        if (!originalElement) return true; // New element
                        return originalElement.name !== target.name; // Renamed
                    };
                    
                    const wrapper = document.createElement("div");
                    wrapper.draggable = editMode; // Only draggable in edit mode
                    Object.assign(wrapper.style, {
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        padding: editMode ? "6px 4px" : "2px 4px",
                        background: editMode ? "#2a2f3a" : "transparent",
                        borderRadius: "4px",
                        marginBottom: editMode ? "4px" : "2px",
                        cursor: editMode ? "move" : "default"
                    });
                    
                    // Drag and drop (only in edit mode)
                    if (editMode) {
                        wrapper.ondragstart = (e) => {
                            e.dataTransfer.effectAllowed = "move";
                            e.dataTransfer.setData("text/plain", index.toString());
                            wrapper.style.opacity = "0.5";
                        };
                        wrapper.ondragend = (e) => {
                            wrapper.style.opacity = "1";
                        };
                        wrapper.ondragover = (e) => {
                            e.preventDefault();
                            e.dataTransfer.dropEffect = "move";
                            wrapper.style.borderTop = "2px solid #60a5fa";
                        };
                        wrapper.ondragleave = (e) => {
                            wrapper.style.borderTop = "none";
                        };
                        wrapper.ondrop = (e) => {
                            e.preventDefault();
                            wrapper.style.borderTop = "none";
                            const fromIndex = parseInt(e.dataTransfer.getData("text/plain"));
                            const toIndex = index;
                            if (fromIndex !== toIndex) {
                                const movedElement = allTargets[fromIndex];
                                allTargets.splice(fromIndex, 1);
                                allTargets.splice(toIndex, 0, movedElement);
                                saveElementOrder();
                                createUI();
                            }
                        };
                        
                        // Drag handle (only in edit mode)
                        const dragHandle = document.createElement("div");
                        dragHandle.textContent = "≡";
                        Object.assign(dragHandle.style, {
                            color: "#9ca3af",
                            fontSize: "16px",
                            cursor: "grab",
                            padding: "0 4px"
                        });
                        wrapper.appendChild(dragHandle);
                    }
                    
                    // Checkbox
                    const checkbox = document.createElement("input");
                    checkbox.type = "checkbox";
                    checkbox.id = `cb-${target.id}`;
                    checkbox.checked = isChecked;
                    checkbox.style.cursor = "pointer";
                    checkbox.onclick = (e) => e.stopPropagation();
                    checkbox.onchange = (e) => {
                        onChange(e.target.checked);
                        savePreferences();
                    };
                    wrapper.appendChild(checkbox);
                    
                    // Name
                    const nameSpan = document.createElement("span");
                    nameSpan.textContent = target.name;
                    Object.assign(nameSpan.style, {
                        flex: "1",
                        fontSize: "13px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        cursor: editMode ? "move" : "default"
                    });
                    wrapper.appendChild(nameSpan);
                    
                    // Cached badge (only in edit mode, before star for alignment)
                    if (editMode && isModified()) {
                        const badge = document.createElement("span");
                        badge.textContent = "Cached";
                        Object.assign(badge.style, {
                            fontSize: "10px",
                            background: "#eab308",
                            color: "#000",
                            padding: "2px 6px",
                            borderRadius: "3px",
                            fontWeight: "bold"
                        });
                        wrapper.appendChild(badge);
                    }
                    
                    // Default state indicator (clickable in edit mode)
                    const defaultBadge = document.createElement(editMode ? "button" : "span");
                    const isDefault = target.default !== false; // Default to true if undefined
                    
                    if (editMode) {
                        // In edit mode: clickable button showing filled/empty star
                        defaultBadge.textContent = isDefault ? "⭐" : "☆";
                        defaultBadge.title = isDefault ? "Starts visible (click to toggle)" : "Starts hidden (click to toggle)";
                        Object.assign(defaultBadge.style, {
                            background: "transparent",
                            border: "none",
                            color: isDefault ? "#fbbf24" : "#6b7280",
                            cursor: "pointer",
                            fontSize: "18px",
                            padding: "4px"
                        });
                        defaultBadge.onclick = (e) => {
                            e.stopPropagation();
                            target.default = !isDefault;
                            // Save to localStorage
                            let allElements = loadCustomElements();
                            const idx = allElements.findIndex(el => el.id === target.id);
                            if (idx !== -1) {
                                allElements[idx].default = target.default;
                                saveCustomElements(allElements);
                            }
                            // Update just this row instead of recreating entire UI
                            defaultBadge.textContent = target.default ? "⭐" : "☆";
                            defaultBadge.title = target.default ? "Starts visible (click to toggle)" : "Starts hidden (click to toggle)";
                            defaultBadge.style.color = target.default ? "#fbbf24" : "#6b7280";
                        };
                    } else {
                        // In normal mode: only show star if default=true
                        if (isDefault) {
                            defaultBadge.textContent = "⭐";
                            defaultBadge.title = "Starts visible by default";
                            Object.assign(defaultBadge.style, {
                                fontSize: "14px",
                                color: "#fbbf24"
                            });
                        } else {
                            // Don't show anything if not default in normal mode
                            defaultBadge.style.display = "none";
                        }
                    }
                    wrapper.appendChild(defaultBadge);
                    
                    // Edit and Delete buttons (only in edit mode)
                    if (editMode) {
                        // Edit button
                        const editBtn = document.createElement("button");
                        editBtn.textContent = "✏️";
                        editBtn.title = "Rename";
                        Object.assign(editBtn.style, {
                            background: "transparent",
                            border: "none",
                            color: "#fbbf24",
                            cursor: "pointer",
                            fontSize: "14px",
                            padding: "4px"
                        });
                        editBtn.onclick = (e) => {
                            e.stopPropagation();
                            const newName = prompt("Rename element:", target.name);
                            if (newName && newName !== target.name) {
                                target.name = newName;
                                let allElements = loadCustomElements();
                                const idx = allElements.findIndex(el => el.id === target.id);
                                if (idx !== -1) {
                                    allElements[idx].name = newName;
                                    saveCustomElements(allElements);
                                }
                                createUI();
                            }
                        };
                        wrapper.appendChild(editBtn);
                        
                        // Delete button (X)
                        const deleteBtn = document.createElement("button");
                        deleteBtn.textContent = "✕";
                        deleteBtn.title = "Delete";
                        Object.assign(deleteBtn.style, {
                            background: "transparent",
                            border: "none",
                            color: "#ef4444",
                            cursor: "pointer",
                            fontSize: "18px",
                            padding: "4px",
                            fontWeight: "bold"
                        });
                        deleteBtn.onclick = (e) => {
                            e.stopPropagation();
                            if (confirm(`Delete "${target.name}"?`)) {
                                let allElements = loadCustomElements();
                                allElements = allElements.filter(el => el.id !== target.id);
                                saveCustomElements(allElements);
                                createUI();
                            }
                        };
                        wrapper.appendChild(deleteBtn);
                    }
                    
                    return { wrapper, checkbox };
                };

                // Header
                const headerDiv = document.createElement("div");
                Object.assign(headerDiv.style,{
                    fontWeight: "bold",
                    borderBottom: "1px solid #555",
                    paddingBottom: "8px",
                    marginBottom: "4px"
                });
                
                if (editMode) {
                    // Edit mode: element count and action buttons at top
                    const countDiv = document.createElement("div");
                    countDiv.style.fontSize = "12px";
                    countDiv.style.opacity = "0.7";
                    countDiv.style.marginBottom = "8px";
                    countDiv.textContent = `${allTargets.length} elements`;
                    headerDiv.appendChild(countDiv);
                    
                    // Add Element button
                    const addBtn = document.createElement("button");
                    addBtn.id = "wan2gp-add-element-btn";
                    addBtn.textContent = "➕ Add New Element";
                    Object.assign(addBtn.style, {
                        width: "100%",
                        padding: "6px 12px",
                        fontSize: "12px",
                        background: "#2563eb",  // Blue
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        marginBottom: "4px"
                    });
                    addBtn.onclick = (e) => {
                        e.stopPropagation(); // Prevent menu from closing
                        if (pickerMode) {
                            exitPickerMode();
                        } else {
                            enterPickerMode();
                        }
                    };
                    headerDiv.appendChild(addBtn);

                    // Export and Reset buttons (side by side, grey)
                    const exportResetContainer = document.createElement("div");
                    Object.assign(exportResetContainer.style, {
                        display: "flex",
                        gap: "4px",
                        marginBottom: "8px"
                    });

                    // Export button
                    const exportBtn = document.createElement("button");
                    exportBtn.textContent = "📤 Export";
                    Object.assign(exportBtn.style, {
                        flex: "1",
                        padding: "6px 12px",
                        fontSize: "12px",
                        background: "#374151",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    });
                    exportBtn.onclick = (e) => {
                        e.stopPropagation(); // Prevent menu from closing
                        const config = {
                            elements: loadCustomElements(),
                            prefs: loadPreferences(),
                            order: loadElementOrder()
                        };
                        const jsonStr = JSON.stringify(config, null, 2);
                        
                        // Create modal to show JSON
                        const modal = document.createElement("div");
                        Object.assign(modal.style, {
                            position: "fixed",
                            top: "50%",
                            left: "50%",
                            transform: "translate(-50%, -50%)",
                            background: "#1f2937",
                            padding: "20px",
                            borderRadius: "8px",
                            boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
                            zIndex: "10001",
                            maxWidth: "600px",
                            width: "90%"
                        });
                        
                        const title = document.createElement("h3");
                        title.textContent = "Export Configuration";
                        title.style.marginTop = "0";
                        title.style.color = "white";
                        modal.appendChild(title);
                        
                        const instructions = document.createElement("p");
                        instructions.textContent = "Copy this JSON and paste it into config.json, then click Reset.";
                        instructions.style.color = "#9ca3af";
                        instructions.style.fontSize = "13px";
                        modal.appendChild(instructions);
                        
                        const textarea = document.createElement("textarea");
                        textarea.value = jsonStr;
                        textarea.readOnly = true;
                        Object.assign(textarea.style, {
                            width: "100%",
                            height: "300px",
                            fontFamily: "monospace",
                            fontSize: "12px",
                            padding: "10px",
                            background: "#111827",
                            color: "#f3f4f6",
                            border: "1px solid #374151",
                            borderRadius: "4px",
                            resize: "vertical"
                        });
                        textarea.onclick = () => textarea.select();
                        modal.appendChild(textarea);
                        
                        const btnContainer = document.createElement("div");
                        Object.assign(btnContainer.style, {
                            marginTop: "12px",
                            display: "flex",
                            gap: "8px"
                        });
                        
                        const copyBtn = document.createElement("button");
                        copyBtn.textContent = "📋 Copy";
                        Object.assign(copyBtn.style, {
                            flex: "1",
                            padding: "8px",
                            background: "#16a34a",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            cursor: "pointer"
                        });
                        copyBtn.onclick = () => {
                            textarea.select();
                            document.execCommand('copy');
                            copyBtn.textContent = "✓ Copied!";
                            setTimeout(() => copyBtn.textContent = "📋 Copy", 2000);
                        };
                        
                        const closeBtn = document.createElement("button");
                        closeBtn.textContent = "Close";
                        Object.assign(closeBtn.style, {
                            flex: "1",
                            padding: "8px",
                            background: "#6b7280",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            cursor: "pointer"
                        });
                        closeBtn.onclick = () => document.body.removeChild(modal);
                        
                        btnContainer.appendChild(copyBtn);
                        btnContainer.appendChild(closeBtn);
                        modal.appendChild(btnContainer);
                        
                        document.body.appendChild(modal);
                        textarea.select();
                    };
                    exportResetContainer.appendChild(exportBtn);

                    // Reset button
                    const resetBtn = document.createElement("button");
                    resetBtn.textContent = "🔄 Reset";
                    Object.assign(resetBtn.style, {
                        flex: "1",
                        padding: "6px 12px",
                        fontSize: "12px",
                        background: "#374151",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    });
                    resetBtn.onclick = (e) => {
                        e.stopPropagation(); // Prevent menu from closing
                        if (confirm("Clear all localStorage changes and reload from config.json?\\n\\nMake sure you've saved your Export first!")) {
                            localStorage.removeItem(STORAGE_KEY_CUSTOM);
                            localStorage.removeItem(STORAGE_KEY_PREFS);
                            localStorage.removeItem(STORAGE_KEY_ORDER);
                            location.reload();
                        }
                    };
                    exportResetContainer.appendChild(resetBtn);
                    headerDiv.appendChild(exportResetContainer);
                    
                    // Finished Editing button
                    const editToggleBtn = document.createElement("button");
                    editToggleBtn.textContent = "✔️ Finished Editing";
                    Object.assign(editToggleBtn.style, {
                        width: "100%",
                        padding: "6px 12px",
                        fontSize: "12px",  // Same as other buttons
                        background: "#16a34a",  // Green
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        marginBottom: "0",
                        fontWeight: "bold"
                    });
                    editToggleBtn.onclick = (e) => {
                        e.stopPropagation();
                        localStorage.setItem('wan2gp_hideui_editMode', 'false');
                        location.reload();  // Reload to rebuild UI in normal mode
                    };
                    headerDiv.appendChild(editToggleBtn);
                } else {
                    // Normal mode: Show Default button prominent, Edit button small and grey
                    
                    // Show Default button (large and colorful)
                    const hideDefaultBtn = document.createElement("button");
                    hideDefaultBtn.textContent = "Show Default";
                    Object.assign(hideDefaultBtn.style, {
                        width: "100%",
                        padding: "10px 12px",
                        fontSize: "14px",
                        background: "#6366f1",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        marginBottom: "8px",
                        fontWeight: "bold"
                    });
                    hideDefaultBtn.onclick = (e) => {
                        e.stopPropagation(); // Prevent menu from closing
                        allTargets.forEach(target => {
                            const cb = document.getElementById(`cb-${target.id}`);
                            if(cb) {
                                // Set to default state (true for starred, false for non-starred)
                                const defaultState = target.default !== false; // Default to true if undefined
                                cb.checked = defaultState;
                                if (target.labels) {
                                    setVisibilityByLabels(target.labels, defaultState);
                                } else if (target.componentId) {
                                    setVisibilityByComponentId(target.componentId, defaultState);
                                }
                            }
                        });
                        savePreferences();
                    };
                    headerDiv.appendChild(hideDefaultBtn);
                    
                    // Button container for Show/Hide All and Edit
                    const btnContainer = document.createElement("div");
                    Object.assign(btnContainer.style, {
                        display: "flex",
                        gap: "8px",
                        marginTop: "0"
                    });
                    
                    // Show/Hide All button (small grey)
                    const toggleAllBtn = document.createElement("button");
                    toggleAllBtn.textContent = "Show/Hide All";
                    Object.assign(toggleAllBtn.style, {
                        flex: "1",
                        padding: "6px 12px",
                        fontSize: "12px",
                        background: "#374151",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    });
                    let allHidden = false;
                    toggleAllBtn.onclick = (e) => {
                        e.stopPropagation(); // Prevent menu from closing
                        allHidden = !allHidden;
                        allTargets.forEach(target => {
                            const cb = document.getElementById(`cb-${target.id}`);
                            if(cb) {
                                cb.checked = !allHidden;
                                if (target.labels) {
                                    setVisibilityByLabels(target.labels, !allHidden);
                                } else if (target.componentId) {
                                    setVisibilityByComponentId(target.componentId, !allHidden);
                                }
                            }
                        });
                        savePreferences();
                    };
                    
                    // Edit button (small grey)
                    const editToggleBtn = document.createElement("button");
                    editToggleBtn.textContent = "Edit";
                    Object.assign(editToggleBtn.style, {
                        flex: "1",
                        padding: "6px 12px",
                        fontSize: "12px",
                        background: "#374151",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    });
                    editToggleBtn.onclick = (e) => {
                        e.stopPropagation();
                        localStorage.setItem('wan2gp_hideui_editMode', 'true');
                        location.reload();  // Reload to rebuild UI in edit mode
                    };
                    
                    btnContainer.appendChild(toggleAllBtn);
                    btnContainer.appendChild(editToggleBtn);
                    headerDiv.appendChild(btnContainer);
                }

                // Separator
                const separator1 = document.createElement("div");
                Object.assign(separator1.style, {
                    borderTop: "1px solid #555",
                    marginTop: "8px",
                    marginBottom: "8px"
                });
                headerDiv.appendChild(separator1);

                menu.appendChild(headerDiv);

                // Element checkboxes with management buttons
                allTargets.forEach((target, index) => {
                    const initialStatus = savedPrefs.hasOwnProperty(target.id) 
                        ? savedPrefs[target.id] 
                        : (target.default !== undefined ? target.default : true);
                    
                    const row = createCheckbox(
                        target,
                        index,
                        (checked) => {
                            if (target.labels) {
                                setVisibilityByLabels(target.labels, checked);
                            } else if (target.componentId) {
                                setVisibilityByComponentId(target.componentId, checked);
                            }
                        }, 
                        initialStatus,
                        editMode // Pass editMode parameter
                    );
                    
                    menu.appendChild(row.wrapper);
                    
                    // Apply initial visibility
                    if (target.labels) {
                        setVisibilityByLabels(target.labels, initialStatus);
                    } else if (target.componentId) {
                        setVisibilityByComponentId(target.componentId, initialStatus);
                    }
                });

                // Main toggle button
                const mainBtn = document.createElement("button");
                mainBtn.textContent = "☰ UI";
                Object.assign(mainBtn.style, {
                    padding: "10px 16px", borderRadius: "24px",
                    background: "#0284c7", color: "white", border: "none", cursor: "pointer",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.4)", fontWeight: "bold"
                });

                mainBtn.onclick = () => {
                    const isHidden = menu.style.display === "none";
                    menu.style.display = isHidden ? "flex" : "none";
                    mainBtn.textContent = isHidden ? "✕ Close" : "☰ UI";
                    
                    // Exit picker mode if menu is closed
                    if (!isHidden && pickerMode) {
                        exitPickerMode();
                    }
                };

                container.appendChild(menu);
                container.appendChild(mainBtn);
                document.body.appendChild(container);
                
                // Build the menu content
                buildMenuContent();

                console.log(`WAN2GP HideUI: ${allTargets.length} elements loaded`);
            }
            
            // Function to rebuild just the menu content (keeps menu open)
            let menuElement = null; // Global reference to menu
            
            function buildMenuContent() {
                if (!menuElement) return; // Menu not created yet
                
                // Clear existing content
                menuElement.innerHTML = '';
                
                // Load all elements from storage
                allTargets = loadCustomElements();
                
                // Apply saved order
                const savedOrder = loadElementOrder();
                if (savedOrder.length > 0) {
                    allTargets.sort((a, b) => {
                        const aIndex = savedOrder.indexOf(a.id);
                        const bIndex = savedOrder.indexOf(b.id);
                        if (aIndex === -1 && bIndex === -1) return 0;
                        if (aIndex === -1) return 1;
                        if (bIndex === -1) return -1;
                        return aIndex - bIndex;
                    });
                }

                // Load saved preferences
                const savedPrefs = loadPreferences();

                // Create checkbox function (same as before)
                const createCheckbox = (target, index, onChange, isChecked=true, editMode=false) => {
                    // Check if element has been modified
                    const isModified = () => {
                        const originalElement = originalConfig.elements?.find(e => e.id === target.id);
                        if (!originalElement) return true; // New element
                        return originalElement.name !== target.name; // Renamed
                    };
                    
                    const wrapper = document.createElement("div");
                    wrapper.draggable = editMode; // Only draggable in edit mode
                    Object.assign(wrapper.style, {
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        padding: editMode ? "6px 4px" : "2px 4px",
                        background: editMode ? "#2a2f3a" : "transparent",
                        borderRadius: "4px",
                        marginBottom: editMode ? "4px" : "2px",
                        cursor: editMode ? "move" : "default"
                    });
                    
                    // Drag and drop (only in edit mode)
                    if (editMode) {
                        wrapper.ondragstart = (e) => {
                            e.dataTransfer.effectAllowed = "move";
                            e.dataTransfer.setData("text/plain", index);
                            wrapper.style.opacity = "0.5";
                        };
                        
                        wrapper.ondragend = () => {
                            wrapper.style.opacity = "1";
                        };
                        
                        wrapper.ondragover = (e) => {
                            e.preventDefault();
                            e.dataTransfer.dropEffect = "move";
                        };
                        
                        wrapper.ondrop = (e) => {
                            e.preventDefault();
                            const fromIndex = parseInt(e.dataTransfer.getData("text/plain"));
                            const toIndex = index;
                            
                            if (fromIndex !== toIndex) {
                                const item = allTargets.splice(fromIndex, 1)[0];
                                allTargets.splice(toIndex, 0, item);
                                saveCustomElements(allTargets);
                                saveElementOrder();
                                buildMenuContent(); // Rebuild menu content
                            }
                        };
                        
                        // Drag handle (only in edit mode)
                        const dragHandle = document.createElement("span");
                        dragHandle.textContent = "≡";
                        Object.assign(dragHandle.style, {
                            cursor: "move",
                            color: "#888",
                            fontSize: "16px",
                            userSelect: "none"
                        });
                        wrapper.appendChild(dragHandle);
                    }
                    
                    // Checkbox
                    const checkbox = document.createElement("input");
                    checkbox.type = "checkbox";
                    checkbox.id = `cb-${target.id}`;
                    checkbox.checked = isChecked;
                    checkbox.onchange = () => {
                        onChange(checkbox.checked);
                        savePreferences();
                    };
                    Object.assign(checkbox.style, {
                        cursor: "pointer",
                        accentColor: "#0284c7"
                    });
                    wrapper.appendChild(checkbox);
                    
                    // Element name
                    const nameSpan = document.createElement("span");
                    nameSpan.textContent = target.name;
                    Object.assign(nameSpan.style, {
                        flex: "1",
                        fontSize: "13px",
                        cursor: "default"
                    });
                    wrapper.appendChild(nameSpan);
                    
                    // Cached badge (only in edit mode, before star for alignment)
                    if (editMode && isModified()) {
                        const badge = document.createElement("span");
                        badge.textContent = "Cached";
                        Object.assign(badge.style, {
                            fontSize: "10px",
                            background: "#eab308",
                            color: "#000",
                            padding: "2px 6px",
                            borderRadius: "3px",
                            fontWeight: "bold"
                        });
                        wrapper.appendChild(badge);
                    }
                    
                    // Default state indicator (clickable in edit mode)
                    const defaultBadge = document.createElement(editMode ? "button" : "span");
                    const isDefault = target.default !== false; // Default to true if undefined
                    
                    if (editMode) {
                        // In edit mode: clickable button showing filled/empty star
                        defaultBadge.textContent = isDefault ? "⭐" : "☆";
                        defaultBadge.title = isDefault ? "Starts visible (click to toggle)" : "Starts hidden (click to toggle)";
                        Object.assign(defaultBadge.style, {
                            background: "transparent",
                            border: "none",
                            color: isDefault ? "#fbbf24" : "#6b7280",
                            cursor: "pointer",
                            fontSize: "18px",
                            padding: "4px"
                        });
                        defaultBadge.onclick = (e) => {
                            e.stopPropagation();
                            target.default = !isDefault;
                            // Save to localStorage
                            let allElements = loadCustomElements();
                            const idx = allElements.findIndex(el => el.id === target.id);
                            if (idx !== -1) {
                                allElements[idx].default = target.default;
                                saveCustomElements(allElements);
                            }
                            // Update just this row instead of recreating entire UI
                            defaultBadge.textContent = target.default ? "⭐" : "☆";
                            defaultBadge.title = target.default ? "Starts visible (click to toggle)" : "Starts hidden (click to toggle)";
                            defaultBadge.style.color = target.default ? "#fbbf24" : "#6b7280";
                        };
                    } else {
                        // In normal mode: only show star if default=true
                        if (isDefault) {
                            defaultBadge.textContent = "⭐";
                            defaultBadge.title = "Starts visible by default";
                            Object.assign(defaultBadge.style, {
                                fontSize: "14px",
                                color: "#fbbf24"
                            });
                        } else {
                            // Don't show anything if not default in normal mode
                            defaultBadge.style.display = "none";
                        }
                    }
                    wrapper.appendChild(defaultBadge);
                    
                    // Edit and Delete buttons (only in edit mode)
                    if (editMode) {
                        const editBtn = document.createElement("button");
                        editBtn.textContent = "✏️";
                        editBtn.title = "Rename element";
                        Object.assign(editBtn.style, {
                            background: "transparent",
                            border: "none",
                            cursor: "pointer",
                            fontSize: "14px",
                            padding: "2px 4px"
                        });
                        editBtn.onclick = (e) => {
                            e.stopPropagation();
                            const newName = prompt(`Rename "${target.name}":`, target.name);
                            if (newName && newName !== target.name) {
                                target.name = newName;
                                let allElements = loadCustomElements();
                                const idx = allElements.findIndex(el => el.id === target.id);
                                if (idx !== -1) {
                                    allElements[idx].name = newName;
                                    saveCustomElements(allElements);
                                }
                                buildMenuContent(); // Rebuild menu content
                            }
                        };
                        wrapper.appendChild(editBtn);
                        
                        const deleteBtn = document.createElement("button");
                        deleteBtn.textContent = "✕";
                        deleteBtn.title = "Delete element";
                        Object.assign(deleteBtn.style, {
                            background: "transparent",
                            border: "none",
                            cursor: "pointer",
                            fontSize: "14px",
                            color: "#dc2626",
                            padding: "2px 4px"
                        });
                        deleteBtn.onclick = (e) => {
                            e.stopPropagation();
                            if (confirm(`Delete "${target.name}"?`)) {
                                let allElements = loadCustomElements();
                                allElements = allElements.filter(el => el.id !== target.id);
                                saveCustomElements(allElements);
                                buildMenuContent(); // Rebuild menu content
                            }
                        };
                        wrapper.appendChild(deleteBtn);
                    }
                    
                    return { wrapper, checkbox };
                };

                // Build header
                const headerDiv = document.createElement("div");
                Object.assign(headerDiv.style,{
                    fontWeight: "bold",
                    borderBottom: "1px solid #555",
                    paddingBottom: "8px",
                    marginBottom: "4px"
                });
                
                if (editMode) {
                    // Edit mode: element count and action buttons at top
                    const countDiv = document.createElement("div");
                    countDiv.style.fontSize = "12px";
                    countDiv.style.opacity = "0.7";
                    countDiv.style.marginBottom = "8px";
                    countDiv.textContent = `${allTargets.length} elements`;
                    headerDiv.appendChild(countDiv);
                    
                    // Add Element button
                    const addBtn = document.createElement("button");
                    addBtn.id = "wan2gp-add-element-btn";
                    addBtn.textContent = "➕ Add New Element";
                    Object.assign(addBtn.style, {
                        width: "100%",
                        padding: "6px 12px",
                        fontSize: "12px",
                        background: "#2563eb",  // Blue
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        marginBottom: "4px"
                    });
                    addBtn.onclick = (e) => {
                        e.stopPropagation(); // Prevent menu from closing
                        if (pickerMode) {
                            exitPickerMode();
                        } else {
                            enterPickerMode();
                        }
                    };
                    headerDiv.appendChild(addBtn);

                    // Export and Reset buttons (side by side, grey)
                    const exportResetContainer = document.createElement("div");
                    Object.assign(exportResetContainer.style, {
                        display: "flex",
                        gap: "4px",
                        marginBottom: "8px"
                    });

                    // Export button
                    const exportBtn = document.createElement("button");
                    exportBtn.textContent = "📤 Export";
                    Object.assign(exportBtn.style, {
                        flex: "1",
                        padding: "6px 12px",
                        fontSize: "12px",
                        background: "#374151",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    });
                    exportBtn.onclick = (e) => {
                        e.stopPropagation(); // Prevent menu from closing
                        const config = {
                            elements: loadCustomElements(),
                            prefs: loadPreferences(),
                            order: loadElementOrder()
                        };
                        const jsonStr = JSON.stringify(config, null, 2);
                        
                        // Create modal to show JSON
                        const modal = document.createElement("div");
                        Object.assign(modal.style, {
                            position: "fixed",
                            top: "50%",
                            left: "50%",
                            transform: "translate(-50%, -50%)",
                            background: "#1f2937",
                            padding: "20px",
                            borderRadius: "8px",
                            boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
                            zIndex: "10001",
                            maxWidth: "600px",
                            width: "90%"
                        });
                        
                        const title = document.createElement("h3");
                        title.textContent = "Export Configuration";
                        title.style.marginTop = "0";
                        title.style.color = "white";
                        modal.appendChild(title);
                        
                        const instructions = document.createElement("p");
                        instructions.textContent = "Copy this JSON and paste it into config.json, then click Reset.";
                        instructions.style.color = "#9ca3af";
                        instructions.style.fontSize = "13px";
                        modal.appendChild(instructions);
                        
                        const textarea = document.createElement("textarea");
                        textarea.value = jsonStr;
                        textarea.readOnly = true;
                        Object.assign(textarea.style, {
                            width: "100%",
                            height: "300px",
                            fontFamily: "monospace",
                            fontSize: "12px",
                            padding: "10px",
                            background: "#111827",
                            color: "#f3f4f6",
                            border: "1px solid #374151",
                            borderRadius: "4px",
                            resize: "vertical"
                        });
                        textarea.onclick = () => textarea.select();
                        modal.appendChild(textarea);
                        
                        const btnContainer = document.createElement("div");
                        Object.assign(btnContainer.style, {
                            marginTop: "12px",
                            display: "flex",
                            gap: "8px"
                        });
                        
                        const copyBtn = document.createElement("button");
                        copyBtn.textContent = "📋 Copy";
                        Object.assign(copyBtn.style, {
                            flex: "1",
                            padding: "8px",
                            background: "#16a34a",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            cursor: "pointer"
                        });
                        copyBtn.onclick = () => {
                            textarea.select();
                            document.execCommand('copy');
                            copyBtn.textContent = "✓ Copied!";
                            setTimeout(() => copyBtn.textContent = "📋 Copy", 2000);
                        };
                        
                        const closeBtn = document.createElement("button");
                        closeBtn.textContent = "Close";
                        Object.assign(closeBtn.style, {
                            flex: "1",
                            padding: "8px",
                            background: "#6b7280",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            cursor: "pointer"
                        });
                        closeBtn.onclick = () => document.body.removeChild(modal);
                        
                        btnContainer.appendChild(copyBtn);
                        btnContainer.appendChild(closeBtn);
                        modal.appendChild(btnContainer);
                        
                        document.body.appendChild(modal);
                        textarea.select();
                    };
                    exportResetContainer.appendChild(exportBtn);

                    // Reset button
                    const resetBtn = document.createElement("button");
                    resetBtn.textContent = "🗑️ Clear Cached";
                    Object.assign(resetBtn.style, {
                        flex: "1",
                        padding: "6px 12px",
                        fontSize: "12px",
                        background: "#374151",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    });
                    resetBtn.onclick = (e) => {
                        e.stopPropagation(); // Prevent menu from closing
                        if (confirm("Clear all localStorage changes and reload from config.json?\\n\\nMake sure you've saved your Export first!")) {
                            localStorage.removeItem(STORAGE_KEY_CUSTOM);
                            localStorage.removeItem(STORAGE_KEY_PREFS);
                            localStorage.removeItem(STORAGE_KEY_ORDER);
                            location.reload();
                        }
                    };
                    exportResetContainer.appendChild(resetBtn);
                    headerDiv.appendChild(exportResetContainer);
                    
                    // Finished Editing button
                    const editToggleBtn = document.createElement("button");
                    editToggleBtn.textContent = "✔️ Finished Editing";
                    Object.assign(editToggleBtn.style, {
                        width: "100%",
                        padding: "6px 12px",
                        fontSize: "12px",  // Same as other buttons
                        background: "#16a34a",  // Green
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        marginBottom: "0",
                        fontWeight: "bold"
                    });
                    editToggleBtn.onclick = (e) => {
                        e.stopPropagation();
                        localStorage.setItem('wan2gp_hideui_editMode', 'false');
                        editMode = false;
                        buildMenuContent(); // Rebuild menu content without closing
                    };
                    headerDiv.appendChild(editToggleBtn);
                } else {
                    // Normal mode: Show Default button prominent, Edit button small and grey
                    
                    // Show Default button (large and colorful)
                    const hideDefaultBtn = document.createElement("button");
                    hideDefaultBtn.textContent = "Show Default";
                    Object.assign(hideDefaultBtn.style, {
                        width: "100%",
                        padding: "10px 12px",
                        fontSize: "14px",
                        background: "#6366f1",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        marginBottom: "8px",
                        fontWeight: "bold"
                    });
                    hideDefaultBtn.onclick = (e) => {
                        e.stopPropagation(); // Prevent menu from closing
                        allTargets.forEach(target => {
                            const cb = document.getElementById(`cb-${target.id}`);
                            if(cb) {
                                // Set to default state (true for starred, false for non-starred)
                                const defaultState = target.default !== false; // Default to true if undefined
                                cb.checked = defaultState;
                                if (target.labels) {
                                    setVisibilityByLabels(target.labels, defaultState);
                                } else if (target.componentId) {
                                    setVisibilityByComponentId(target.componentId, defaultState);
                                }
                            }
                        });
                        savePreferences();
                    };
                    headerDiv.appendChild(hideDefaultBtn);
                    
                    // Button container for Show/Hide All and Edit
                    const btnContainer = document.createElement("div");
                    Object.assign(btnContainer.style, {
                        display: "flex",
                        gap: "8px",
                        marginTop: "0"
                    });
                    
                    // Show/Hide All button (small grey)
                    const toggleAllBtn = document.createElement("button");
                    toggleAllBtn.textContent = "Show/Hide All";
                    Object.assign(toggleAllBtn.style, {
                        flex: "1",
                        padding: "6px 12px",
                        fontSize: "12px",
                        background: "#374151",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    });
                    let allHidden = false;
                    toggleAllBtn.onclick = (e) => {
                        e.stopPropagation(); // Prevent menu from closing
                        allHidden = !allHidden;
                        allTargets.forEach(target => {
                            const cb = document.getElementById(`cb-${target.id}`);
                            if(cb) {
                                cb.checked = !allHidden;
                                if (target.labels) {
                                    setVisibilityByLabels(target.labels, !allHidden);
                                } else if (target.componentId) {
                                    setVisibilityByComponentId(target.componentId, !allHidden);
                                }
                            }
                        });
                        savePreferences();
                    };
                    
                    // Edit button (small grey)
                    const editToggleBtn = document.createElement("button");
                    editToggleBtn.textContent = "Edit";
                    Object.assign(editToggleBtn.style, {
                        flex: "1",
                        padding: "6px 12px",
                        fontSize: "12px",
                        background: "#374151",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    });
                    editToggleBtn.onclick = (e) => {
                        e.stopPropagation();
                        localStorage.setItem('wan2gp_hideui_editMode', 'true');
                        editMode = true;
                        buildMenuContent(); // Rebuild menu content without closing
                    };
                    
                    btnContainer.appendChild(toggleAllBtn);
                    btnContainer.appendChild(editToggleBtn);
                    headerDiv.appendChild(btnContainer);
                }

                // Separator
                const separator1 = document.createElement("div");
                Object.assign(separator1.style, {
                    borderTop: "1px solid #555",
                    marginTop: "8px",
                    marginBottom: "8px"
                });
                headerDiv.appendChild(separator1);

                menuElement.appendChild(headerDiv);

                // Element checkboxes with management buttons
                allTargets.forEach((target, index) => {
                    const initialStatus = savedPrefs.hasOwnProperty(target.id) 
                        ? savedPrefs[target.id] 
                        : (target.default !== undefined ? target.default : true);
                    
                    const row = createCheckbox(
                        target,
                        index,
                        (checked) => {
                            if (target.labels) {
                                setVisibilityByLabels(target.labels, checked);
                            } else if (target.componentId) {
                                setVisibilityByComponentId(target.componentId, checked);
                            }
                        }, 
                        initialStatus,
                        editMode // Pass editMode parameter
                    );
                    
                    menuElement.appendChild(row.wrapper);
                    
                    // Apply initial visibility
                    if (target.labels) {
                        setVisibilityByLabels(target.labels, initialStatus);
                    } else if (target.componentId) {
                        setVisibilityByComponentId(target.componentId, initialStatus);
                    }
                });
            }

            function init() { createUI(); }

            // Initialize on page load
            window.addEventListener("gradioLoaded", () => setTimeout(init, 300));
            document.addEventListener("DOMContentLoaded", () => setTimeout(init, 500));
            window.addEventListener("load", () => setTimeout(init, 700));

            let tries = 0;
            const interval = setInterval(() => {
                tries++;
                init();
                if (tries > 10) clearInterval(interval);
            }, 800);
            
            setTimeout(init, 100);
        })();
        """
        
        return js_code.replace("__CONFIG_JSON_PLACEHOLDER__", config_json)