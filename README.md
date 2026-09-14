# WAN2GP Hide UI Plugin v4

This is a plugin for the [WAN2GP](https://github.com/deepbeepmeep/Wan2GP) application that adds a floating menu to the user interface. This menu allows you to toggle the visibility and compactness of various UI elements with a streamlined **Normal Mode** for everyday use and a powerful **Edit Mode** for advanced customization.

## Version 4 Update: Multi-Target Resolution, Compact Mode & Search

The Version 4 update brings major enhancements and fixes based on the latest WAN2GP updates:
- **Multi-Target Resolution**: Targets can now define an array of `componentId`s, `cssSelector`, `buttonText`, or multiple `labels` to reliably match complex nested blocks, multi-button rows (e.g. Settings, Apply/Refresh, LoRA controls), and newer Gradio layouts.
- **Compact Mode Support**: Toggles can be configured as either `Hide` (complete display collapse) or `Compact` (minimizes padding, heights, and font sizes for a slim, power-user overview without completely removing the widget).
- **Instant Search / Filter**: Easily search through dozens of toggles in real-time right inside the floating menu.
- **Preserved Scroll State**: Reordering items via `▲`/`▼` or drag-and-drop preserves your exact scroll position without annoying jumping.
- **Reliable Startup Defaults**: Default module settings (configured with ⭐) are faithfully respected whenever you open a new browser session or launch WAN2GP.
- **Functional Groups**: Elements can be tagged with functional groups (e.g. `Interface`, `Model`, `Generation`, `Sampling & Steps`, `Settings`, `LoRAs`).

Image of the menu hiding lots of the main UI:
![2025-12-20 11_41_59-App1 - Antigravity - Concept txt●](https://github.com/user-attachments/assets/31014e63-4421-4a67-8f9f-cd99f5311ffa)

Image of the editing view adding a new custom element:
![2025-12-20 11_42_37-App1 - Antigravity - Concept txt●](https://github.com/user-attachments/assets/fe341db5-d8c0-4109-a944-4061c73d7103)

## Features

### Two-Tiered Interface
- **Normal Mode** - Clean, simplified view for everyday use:
  - **Show Default** - Large primary button to reset UI to your preferred default state.
  - **Show/Hide All** - Quickly toggle everything on or off.
  - **Edit** - Switch to management mode for deep customization.
  - **Search Filter** - Quick text search to find any element instantly.
  - **Smart Indicators** - ⭐ icons show which items start visible; `Compact` badges indicate compact toggles.
  
- **Edit Mode** - Full-featured management interface:
  - **Reorder** - Drag-and-drop (`≡`) or tap mobile arrow buttons (`▲`/`▼`) to reorder rows effortlessly without scrolling jumps.
  - **Mode Toggle** (`Hide` vs `Compact`) - Choose whether an item completely hides or collapses into a dense compact view.
  - **Default Configuration** (⭐/☆) - Choose exactly which modules enable when the plugin loads.
  - **Element Picker** (➕) - Interactively select any part of the UI to add as a new toggle.
  - **Quick Rename** (✏️) - Give any element a friendly custom name.
  - **Caching System** - "Cached" badges show which changes are currently stored in your browser's local storage.
  - **Export / Reset** - Side-by-side buttons to export your configuration directly into `config.json` or reset to defaults.

### Schema Flexibility in `config.json`
Each entry in `config.json` supports:
- `id`: unique identifier
- `name`: user-friendly display name
- `componentId`: string or array of strings (e.g. `["wangp-system-stats", "component-41"]`)
- `labels`: array of text strings to match against block titles or field labels (case-insensitive & whitespace normalized)
- `cssSelector`: optional CSS selector for advanced targeting
- `buttonText`: optional button text matching for isolated button rows
- `group`: category tag for visual organization
- `mode`: `"hide"` (default) or `"compact"`
- `default`: boolean (`true` to start visible, `false` to start hidden/compact)

## Installation

1. Clone or copy this repository into your WAN2GP plugins folder: `plugins/Wan2GP-HideUI` (or `MobileToggleHelper`).
2. Ensure `plugin.py` and `config.json` are in the folder.
3. Restart the WAN2GP application.

## Usage Guide

### Opening the Menu
Click the **☰ UI** button in the bottom right corner. Click **✕ Close** to close the menu.

### Normal Mode (Daily Use)
1. **Show Default**: Resets all elements to the specific state you've chosen as "default".
2. **Toggle List**: Check or uncheck boxes to hide/show/compact elements immediately.
3. **Filter**: Type in the search box to find specific controls quickly.

### Edit Mode (Setup & Management)
1. **Add Element**: Click the blue plus button, then click any part of the WAN2GP interface to add it to your toggle list.
2. **Reorder**: Drag the `≡` handle or tap `▲`/`▼` to move items up or down.
3. **Mode**: Tap the mode badge (`Hide` / `Compact`) to switch how that element toggles.
4. **Default State**: Tap ⭐/☆ to toggle whether that element begins enabled when WAN2GP opens.
5. **Rename/Delete**: Use ✏️ to rename or ✕ to delete.
6. **Import**: Use the **📥 Import** button to hot-reload edits made to `config.json` without restarting WAN2GP.
7. **Export**: Use the **📤 Export** button to get the JSON to save directly into `config.json`.

## Changelog
See [CHANGELOG.md](file:///c:/Users/Brady/Projects/AI%20-%20WebUI%20Extentions/AI%20-%20Extention%20Wan2GP%20-%20Wan2GP-HideUI/App1/CHANGELOG.md) for full version history and detailed release notes.

---
*Created for the [WAN2GP](https://github.com/deepbeepmeep/Wan2GP) community.*
