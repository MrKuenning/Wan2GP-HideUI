# Changelog

All notable changes to the **Wan2GP HideUI Plugin** are documented in this file.

---

## [4.4.0] - 2026-09-15

### Added
- **Direct-to-Disk Persistence**: Connected a Gradio backend bridge (`post_ui_setup` via `insert_after("generate_btn")`) enabling the UI to save changes directly to `config.json` on disk via Python without requiring manual export or clipboard copy-paste.
- **Auto-Save with Visual Indicator**: Every modification (custom additions, renaming, deletion, reordering, preset switching, per-element 1/2/3 preset toggles, and "Save to Preset") automatically debounces and writes directly to `config.json`, displaying a sleek `✓ Saved to config.json` status pill.
- **Reload from Disk Action**: Added a **🔄 Reload Disk** button in Edit Mode that queries Python to re-read `config.json` fresh from disk on demand, allowing instant hot-reloading if edited externally in a text editor.

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
