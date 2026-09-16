# WAN2GP Hide UI Plugin v4

This is a plugin for the [WAN2GP](https://github.com/deepbeepmeep/Wan2GP) application that adds a floating menu to the user interface. This menu allows you to toggle the visibility and compactness of various UI elements with a streamlined **Normal Mode** for everyday use and a powerful **Edit Mode** for advanced customization.

## Version 4 Update: Multi-Preset System, Multi-Target Resolution & Compact Mode

The Version 4 update brings major enhancements and fixes based on the latest WAN2GP updates:
- **Multi-Preset System (Presets 1, 2, 3)**: Switch on the fly between three distinct UI configurations right at the top of the menu:
  - **1: Standard**: Everyday workflow with balanced generation parameters.
  - **2: Minimal**: Essential generation controls only (model selection, presets, video-to-video, media drop, resolution, frames, queue).
  - **3: Full Focus**: Clean, ultra-minimal workspace showing only prompt inputs and queue generate.
- **Save to Preset Button**: Modify any checkboxes and immediately commit them to your active preset (`[💾 Save to P{id}]`).
- **Edit Mode Preset Renaming**: Rename presets anytime (`[✏️ P1: Name] [✏️ P2: Name] [✏️ P3: Name]`) directly inside Edit Mode.
- **Multi-Target Resolution**: Targets can now define an array of `componentId`s, `cssSelector`, `buttonText`, or multiple `labels` to reliably match complex nested blocks, multi-button rows (e.g. Settings, Apply/Refresh, LoRA controls), and newer Gradio layouts.
- **Compact Mode Support**: Toggles can be configured as either `Hide` (complete display collapse) or `Compact` (minimizes padding, heights, and font sizes for a slim, power-user overview without completely removing the widget).
- **Instant Search / Filter**: Easily search through dozens of toggles in real-time right inside the floating menu.
- **Preserved Scroll State**: Reordering items via `▲`/`▼` or drag-and-drop preserves your exact scroll position without annoying jumping.
- **Reliable Startup Defaults**: Presets and startup defaults are faithfully respected whenever you open a new browser session or launch WAN2GP.
- **Functional Groups**: Elements can be tagged with functional groups (e.g. `Interface`, `Model`, `Generation`, `Sampling & Steps`, `Settings`, `LoRAs`).

Image of the menu hiding lots of the main UI:
![2025-12-20 11_41_59-App1 - Antigravity - Concept txt●](https://github.com/user-attachments/assets/31014e63-4421-4a67-8f9f-cd99f5311ffa)

Image of the editing view adding a new custom element:
![2025-12-20 11_42_37-App1 - Antigravity - Concept txt●](https://github.com/user-attachments/assets/fe341db5-d8c0-4109-a944-4061c73d7103)

## Features

### Two-Tiered Interface
- **Normal Mode** - Clean, simplified view for everyday use:
  - **Preset Buttons (1, 2, 3)** - Top bar to instantly toggle between your 3 custom workflows with active blue glow.
  - **Save to Preset (`💾 Save P{id}`)** - Commits current checkbox states directly to the active preset with visual feedback.
  - **Show All** - Dedicated button to toggle all elements ON (make everything visible).
  - **Hide All** - Dedicated button to toggle all elements OFF (hide everything).
  - **Edit (`⚙️ Edit`)** - Switch to management mode for deep customization.
  - **Search Filter** - Quick text search to find any element instantly.
  - **Category Pills** - Clean badges indicating functional group categories.
  
- **Edit Mode** - Full-featured management interface:
  - **Preset Renaming** - Tap `[✏️ P1: Name]`, `[✏️ P2: Name]`, or `[✏️ P3: Name]` in the top bar to rename presets.
  - **Per-Element Preset Toggles (`[ 1 ] [ 2 ] [ 3 ]`)** - Three interactive mini-toggles on every row to directly enable or disable that element across Presets 1, 2, and 3.
  - **Reorder** - Drag-and-drop (`≡`) or tap mobile arrow buttons (`▲`/`▼`) to reorder rows effortlessly without scrolling jumps.
  - **Streamlined Layout** - Group category pills are hidden in Edit Mode to maximize horizontal space for controls and names.
  - **Element Picker** (➕) - Interactively select any part of the UI to add as a new toggle.
  - **Quick Rename** (✏️) - Give any element a friendly custom name.
  - **Delete** (✕) - Remove unnecessary toggles from your list.
  - **Direct Disk Persistence** - All modifications, reorders, custom additions, and preset changes save directly to `config.json` via a backend bridge. No manual export or local storage desyncs!
  - **Reload from Disk** - Hot-reload `config.json` freshly from disk at any time without restarting WAN2GP.

### Schema Flexibility in `config.json`
`config.json` supports:
- `activePreset`: string (`"1"`, `"2"`, or `"3"`)
- `presets`: dictionary mapping preset IDs to `{ "name": string, "states": { "<element_id>": boolean } }`
- `elements`: array of target definitions:
  - `id`: unique identifier
  - `name`: user-friendly display name
  - `componentId`: string or array of strings (e.g. `["wangp-system-stats", "component-41"]`)
  - `labels`: array of text strings to match against block titles or field labels (case-insensitive & whitespace normalized)
  - `cssSelector`: optional CSS selector for advanced targeting
  - `buttonText`: optional button text matching for isolated button rows
  - `group`: category tag for visual organization
  - `mode`: `"hide"` (default) or `"compact"`
  - `default`: boolean (`true` to start visible, `false` to start hidden/compact)
- `order`: array of element IDs defining menu display order

## Installation

1. Clone or copy this repository into your WAN2GP plugins folder: `plugins/Wan2GP-HideUI` (or `MobileToggleHelper`).
2. Ensure `plugin.py` and `config.json` are in the folder.
3. Restart the WAN2GP application.

## Usage Guide

### Opening the Menu
Click the **☰ UI** button in the bottom right corner. Click **✕ Close** to close the menu.

### Normal Mode (Daily Use)
1. **Switch Presets**: Tap **1: Standard**, **2: Minimal**, or **3: Full Focus** to switch UI configurations instantly.
2. **Customize a Preset**: Check/uncheck boxes as desired, then click **💾 Save to P{id}** to store them in that preset.
3. **Toggle List**: Check or uncheck boxes to hide/show elements immediately.
4. **Filter**: Type in the search box to find specific controls quickly.

### Edit Mode (Setup & Management)
1. **Rename Presets**: Tap `[✏️ P1]`, `[✏️ P2]`, or `[✏️ P3]` in Edit Mode to give presets custom names.
2. **Configure Presets (1, 2, 3)**: Click the `[1]`, `[2]`, or `[3]` toggle buttons directly on any row to turn that element on or off for that preset.
3. **Add Element**: Click the blue plus button, then click any part of the WAN2GP interface to add it to your toggle list.
4. **Reorder**: Drag the `≡` handle or tap `▲`/`▼` to move items up or down.
5. **Rename/Delete**: Use ✏️ to rename or ✕ to delete.
6. **Automatic Saving**: Any change you make automatically saves to `config.json` with a visual `✓ Saved to config.json` status indicator.
7. **Reload Disk**: Click **🔄 Reload Disk** to instantly reload changes made externally to `config.json` without restarting WAN2GP.

## Changelog
See [CHANGELOG.md](file:///c:/Users/Brady/Projects/AI%20-%20WebUI%20Extentions/AI%20-%20Extention%20Wan2GP%20-%20Wan2GP-HideUI/App1/CHANGELOG.md) for full version history and detailed release notes.

---
*Created for the [WAN2GP](https://github.com/deepbeepmeep/Wan2GP) community.*
