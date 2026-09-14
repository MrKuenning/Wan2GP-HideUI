# Changelog

All notable changes to the **Wan2GP HideUI Plugin** are documented in this file.

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
