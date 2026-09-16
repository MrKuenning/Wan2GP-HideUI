# Changelog

All notable changes to the **Wan2GP HideUI Plugin** are documented in this file.

---

## [4.5.3] - 2026-09-15

### Fixed
- **Media Info / Late Post Processing Accordion Filter Exemption**: In `filterSafeTargets`, tabs detection previously rejected any element containing tabs to protect top-level page rows. Because the "Media Info / Late Post Processing / Import Media" accordion embeds internal sub-tabs (`video_info_tabs`), it was being rejected. Restricted the sub-tabs rejection check strictly to layout `.row` and `.column` containers, allowing accordions and details containing internal tabs to toggle properly.

---

## [4.5.2] - 2026-09-15

### Fixed
- **Model Info & Attention Mode Full Group Targeting**: Scoped `model_info` strictly to `.header-markdown-group` (which wraps both the model description/popup button and the Attention Mode status line), eliminating child-selector conflicts that previously left Attention Mode visible.
- **Presets Dropdown Target Resolution**: Keyed presets row targeting to the persistent `"Apply"` button (`buttonText: ["apply"]`) and unwrapped directly to the enclosing presets row (`.closest(".row").parentElement.closest(".row")`), bypassing hidden modal containers that are absent from initial DOM rendering.
- **Media Drop Box Full Container**: Scoped `media_drop_box` to `.adv-media-gallery` alone (which encapsulates both the drop box gallery and `.amg-controls`), preventing the filter from pruning the gallery column and leaving only buttons hidden.
- **Enhance Prompt Complete Row**: Added `cssSelector: ".row:has(.btn_centered)"` and row unwrapping so button "Write", dropdown "Enhance Prompt using a LLM", and checkbox "Think" hide together as a complete row.
- **Resolution Options Complete Row**: Scoped `resolution_options` selector to `.row:has(#wangp-resolution)` so both "Category" and "Resolution Budget" hide together.
- **Settings Buttons Complete Row**: Added row unwrapping for `"set settings as default"`, `"export settings to file"`, and `"reset settings"` so all three buttons hide together.
- **Lora URL Complete Row**: Added selector `.row:has(input[aria-label*='Lora URL']), .group:has(input[aria-label*='Lora URL'])` and row container unwrapping so the Lora URL textbox and "Download Lora" button hide together.
- **Media Info / Late Post Processing Accordion**: Added substring label matching for labels containing slashes and added exact label `"media info / late post processing / import media"`, successfully targeting the accordion container.
- **Smart Pruning in `filterSafeTargets`**: Restricted parent pruning strictly to `.row` and `.column` containers, ensuring component wrappers and groups are never unintentionally stripped.

---

## [4.5.1] - 2026-09-15

### Fixed
- **Media Drop Box Layout Isolation**: Removed `.row:has(.adv-media-gallery)` which previously matched top-level layout rows (`#component-44`) and caused the entire page to disappear. Narrowed selector strictly to `.adv-media-gallery, .amg-controls`.
- **Input Options Full Row Scope**: Updated `input_options` selector to `.row:has(> * > .cbx_centered), .row:has(.cbx_centered), .group:has(.cbx_centered)` with innermost container matching so both the radio options ("Location") and the "End Image(s)" checkbox (`.cbx_centered`) are hidden together as a complete row.
- **Model Info & Attention Mode**: Grouped `.header-markdown-group` into `model_info` alongside `.wangp-model-info-host`, ensuring the "Attention mode" status line and model info popup toggle together seamlessly.
- **Presets Dropdown Target Resolution**: Added sibling selector `#image-modal-container + .row, #image-modal-container + div.row` and button text hooks (`"Go Ahead Save it !"`, `"Go Ahead Delete it !"`) that unwrap to the enclosing presets row, allowing the presets dropdown and buttons row to toggle cleanly without numeric component IDs.
- **Page Layout Safeguards in `filterSafeTargets`**: Added checks to prevent hiding main layout rows (`component-42`, `component-44`, `.app`, `.fillable`, or any element containing tabs/tabitems), and added an innermost-element filter so broad `:has()` queries never bubble up to page-level rows.

---

## [4.5.0] - 2026-09-15

### Added
- **Resilient Multi-Method Resolution**: Enhanced `findTargetsForElement` in `plugin.py` to support `aria-label`, `input[placeholder]`, `data-testid="block-info"`, button text, and accordions/details. Ensures 100% reliable targeting of Gradio Dropdowns, Checkboxes, Textboxes, Sliders, and Accordions.
- **Durable Semantic CSS Selectors**: Replaced numeric IDs with persistent semantic CSS selectors where available (`.row:has(#model_list)`, `.adv-media-gallery`, `.wangp-progress-container`, `#wangp-resolution`, `h1:has(sup)`).

### Removed
- **Zero Component-### Dependencies**: Completely purged all fragile `component-###` auto-generated Gradio IDs across `config.json`. Prevents presets and toggles from breaking when Gradio renumbers components after app updates or model switches.

---

## [4.4.0] - 2026-09-15

### Added
- **Direct-to-Disk Persistence**: Connected a Gradio backend bridge (`post_ui_setup` via `insert_after("generate_btn")`) enabling the UI to save changes directly to `config.json` on disk via Python without requiring manual export or clipboard copy-paste.
- **Auto-Save with Visual Indicator**: Every modification (custom additions, renaming, deletion, reordering, preset switching, per-element 1/2/3 preset toggles, and "Save to Preset") automatically debounces and writes directly to `config.json`, displaying a sleek `✓ Saved to config.json` status pill.
- **Reload from Disk Action**: Added a **🔄 Reload Disk** button in Edit Mode that queries Python to re-read `config.json` fresh from disk on demand, allowing instant hot-reloading if edited externally in a text editor.
- **Clean Element ID Standardization**: Renamed all element IDs across `config.json` (element definitions, presets 1/2/3, and display order) to match their friendly display names directly (e.g., `header` → `title`, `model_selection` → `model_selector`, `res_group` → `resolution_options`, `inf_steps` → `inference_steps`, `frames` → `number_of_frames`, `load_vid` → `load_from_video_settings`, `late_post_processing` → `model_info_late_post_processing`).

### Removed
- **Browser LocalStorage Layer**: Eliminated reliance on browser `localStorage` for configuration (`custom`, `order`, `presets`, `prefs`, `activePreset`). Automatically purges legacy browser keys on launch so that `config.json` is always the single source of truth across all devices and browsers.
- **Export Modal & Clipboard Helper**: Removed the Export button and modal since all changes now save directly to disk.
- **Browser File Import**: Replaced the browser `<input type="file">` file picker with the direct disk reload bridge.
- **"Cached" Badges**: Replaced "Cached" labels with a clear "Custom" tag for user-added elements.

---

## [4.3.0] - 2026-09-14

### Added
- **Multi-Preset System (Presets 1, 2, 3)**:
  - Added dedicated Preset switching buttons at the top of the menu:
    - **1: Standard**: Everyday workflow with balanced generation parameters.
    - **2: Minimal**: Essential generation controls only (model selection, presets, video-to-video, media drop, resolution, frames, queue).
    - **3: Full Focus**: Clean, ultra-minimal workspace showing only prompt inputs and queue generate.
  - **Active Preset Indicator**: Vivid blue glow (`#2563eb`, `box-shadow`) highlighting which preset is currently active.
  - **Instant Preset Switching**: Tap any preset button to instantly toggle all 21 elements and checkboxes without page reload or scroll jumping.
  - **Save to Preset Button**: Directly save your current toggle configuration into the active preset (`[💾 Save to P{id}]`) with instant visual confirmation (`✓ Saved P{id}!`).
  - **Edit Mode Preset Renaming**: Edit Mode features a top preset bar (`[✏️ P1: Name] [✏️ P2: Name] [✏️ P3: Name]`) to quickly rename any preset.
  - **Config & Session Persistence**: Full support for `activePreset` and `presets` in `config.json`, browser `localStorage`, and `sessionStorage`.
  - **Wider Menu Layout**: Expanded `#floating-menu` width to `min-width: 360px; max-width: min(460px, calc(100vw - 32px))` to provide generous breathing room for preset names and action buttons without text truncation.
  - **Dedicated "Show All" (Toggle All On) & "Hide All"**: Replaced ambiguous `Show/Hide All` toggle with two dedicated, explicit action buttons:
    - **`[ Show All ]`**: Instantly enables all 21 elements and turns every checkbox ON.
    - **`[ Hide All ]`**: Instantly hides all 21 elements and turns every checkbox OFF.
  - **Per-Element 1 2 3 Preset Toggles in Edit Mode**: Replaced the default star icon with three interactive preset buttons (`[ 1 ]`, `[ 2 ]`, `[ 3 ]`) on every row in Edit Mode. Tap any number to immediately toggle whether that element is enabled for that preset, with live visibility updates if that preset is currently active.
  - **Removed Hide/Compact Toggle**: Streamlined element control to standard hide/show behavior, removing the compact badge toggle for a simpler, more predictable experience.
  - **Compact Space-Saving Edit Mode**: Group pills are now hidden in Edit Mode to give element names, 1-2-3 toggles, and action buttons maximum breathing room.
  - **Export & Import Sync**: Configuration exports and imports faithfully save and restore all 3 preset names and toggle states without `prefs` pollution.
  - **Reset from File**: Resetting restores initial default presets and active preset from `config.json`.

---

## [4.2.0] - 2026-09-13

### Added
- **Wan2GP Studio CSS Theming**: Floating button and secondary controls now consume Wan2GP's native `--studio-*` CSS variables (`--studio-button`, `--studio-button-hover`, `--studio-button-text`, `--studio-border`, `--studio-label`, `--studio-soft`, `--studio-input`, `--studio-disabled`), dynamically adapting when theme presets change.
- **Deep Dark Menu Styling**: Enhanced `#floating-menu` with a sleek, high-contrast dark glass backdrop (`rgba(10, 16, 26, 0.95)` with 18px backdrop blur and ambient shadow).
- **Vibrant Action Button Styling**: Restored punchy, purposeful colors for key actions:
  - **Show Default**: Vivid Blue (`#2563eb`) with white text.
  - **Finished Editing**: Vivid Green (`#16a34a`) with white text.
  - **Add New Element**: Sky Blue (`#0284c7`) with white text.
  - **Cancel Picker**: Danger Red (`#dc2626`).
  - **Cached Badge**: Amber Gold (`#f59e0b`).
  - **Compact Mode Badge**: Cyan (`#38bdf8`).
- **New Target Elements**:
  - **Status Bar** (`component-716`, Group: `Queue`, Compact mode supported).
  - **Presets Dropdown** (`component-52`, Group: `Generation`, Compact mode supported).
  - **Control Video / Frames Injection** (`component-109`, Group: `Generation`).
- **Direct `[📥 Import]` Hot-Loader**: Added an Import button to Edit Mode allowing instant reloading of `config.json` directly from disk without restarting Wan2GP.

### Fixed
- **Resolution Options Target Fix**: Fixed bug where toggling `res_group` only hid the Resolution Category dropdown but left the Resolution Budget dropdown visible. Added `component-287`, `component-1465`, and `wangp-resolution` to target both controls across tabs.
- **Cross-Tab Element Resolution**: Updated `findTargetsForElement` to use `querySelectorAll([id='...'])` for `componentId` so elements with repeated IDs in Gradio across tabs (e.g. `wangp-resolution`) are all captured and toggled together.
- **Export Redundancy**: Removed deprecated `prefs: { ... }` block from export modal output so exports produce clean, lean `elements` and `order` definitions.
- **ID Streamlining**: Cleaned up element IDs in `config.json` (`resource_bars`, `number_of_images_to_generate`, `loras_info`, `lora_url`, `media_drop`).

---

## [4.1.0] - 2026-09-13

### Added
- **Compact Mode**: Added dual toggle behavior (`Hide` vs `Compact`) configured per element. In Compact Mode, unchecking an element minimizes it into a slim strip with reduced height and padding instead of completely removing it.
- **Instant Search / Filter**: Added a live search box (`🔍 Search toggles...`) to filter elements in real-time.
- **Scroll Preservation**: Reordering elements via drag-and-drop or `▲`/`▼` mobile buttons now preserves the list's exact scroll position.
- **Four New Selectors**:
  - `audio_source` (`component-214`)
  - `audio_refinement_extra_phase` (`component-270`)
  - `late_post_processing` (`component-744`, `component-1758`)
  - `queue_management` (`component-879`, `component-1893`)

### Fixed
- **Model Selector Page Dissolve Bug**: Fixed critical issue where unchecking Model Selector caused the entire page to disappear. Replaced loose keyword label matching with strict priority matching (`componentId` -> `cssSelector` -> `buttonText` -> exact `labels`) and added layout container safety guards protecting major tabpanels.

---

## [4.0.0] - 2026-09-12

### Added
- **Multi-Target Resolution**: Expanded `config.json` schema to support arrays of `componentId`, CSS selectors, button text matching, and functional groupings.
- **Default Persistence**: Added session-aware default state initialization respecting ⭐ defaults on clean page loads.
- **Mobile Reordering Controls**: Added dedicated up/down arrow buttons for mobile touch devices where drag-and-drop is awkward.
