# WAN2GP Hide UI Plugin v2

This is a plugin for the [WAN2GP](https://github.com/deepbeepmeep/Wan2GP) application that adds a floating menu to the user interface. This menu allows you to toggle the visibility of various UI elements with a streamlined **Normal Mode** for everyday use and a powerful **Edit Mode** for advanced customization.

## Version 2 Update: Complete Overhaul

The Version 2 update introduces a complete overhaul of the plugin, moving from a static list of toggles to a fully customizable management system. You can now add any UI element on the fly using our new interactive picker, rename items to suit your workflow, and reorder them exactly how you like.

Image of the new menu hiding lots of the main ui
![2025-12-20 11_41_59-App1 - Antigravity - Concept txt●](https://github.com/user-attachments/assets/31014e63-4421-4a67-8f9f-cd99f5311ffa)

Image of the editing view addind a new custom element
![2025-12-20 11_42_37-App1 - Antigravity - Concept txt●](https://github.com/user-attachments/assets/fe341db5-d8c0-4109-a944-4061c73d7103)

## Features

### Two-Tiered Interface
- **Normal Mode** - Clean, simplified view for everyday use:
  - **Show Default** - Large primary button to reset UI to your preferred state.
  - **Show/Hide All** - Quickly toggle everything on or off.
  - **Edit** - Switch to management mode for deep customization.
  - **Smart Indicators** - ⭐ icons show at a glance which items are set to start visible.
  
- **Edit Mode** - Full-featured management interface:
  - **Drag-and-Drop** (≡) - Change the order of elements instantly.
  - **Default Configuration** (⭐/☆) - Choose exactly which modules enable when the plugin loads.
  - **Element Picker** (➕) - Interactively select any part of the UI to add as a new toggle.
  - **Quick Rename** (✏️) - Give any element a friendly name.
  - **Caching System** - "Cached" badges show which changes are currently stored in your browser's local storage.

### Core Capabilities
- **Floating Menu** - Convenient, collapsible menu that stays out of your way.
- **Interactive Element Picker** - Click "➕ Add New Element" to enter picker mode, hover to highlight any UI component, and click to add it to your list.
- **Unified Management** - All 13 default elements plus any custom elements are fully editable.
- **Configuration Persistence** - Uses `config.json` for base settings and localStorage for your personalized tweaks.
- **Safe Hiding Logic** - Elements are safely hidden, and their parent containers are intelligently collapsed to maximize your screen real estate.

## How it Works: Default Modules

The core purpose of the plugin is to allow you to define exactly what your interface looks like when it first loads. 

- **Starting Visible (⭐)**: Elements marked with a filled star in Edit Mode will be enabled (visible) by default when the plugin loads or when you click "Show Default".
- **Starting Hidden (☆)**: Elements marked with an empty star will be disabled (hidden) by default.
- **Customizing Defaults**: In **Edit Mode**, simply click the star icon next to any element to toggle its default state. These states are saved to your browser and can be exported to your `config.json` for permanent use.

## Installation

1. Clone the repository or create a folder called `wan2gp-hideUI` in the WAN2GP plugins folder.
2. Place `plugin.py` and `config.json` into the folder.
3. Restart the WAN2GP application.

## Usage Guide

### Opening the Menu
Click the **☰ UI** button in the bottom right corner. Click **✕ Close** to close the menu.

### Normal Mode (Daily Use)
1. **Show Default**: Resets all elements to the specific state you've chosen as "default".
2. **Toggle List**: Check or uncheck boxes to hide/show elements immediately.

### Edit Mode (Setup & Management)
1. **Add Element**: Click the blue plus button, then click any part of the WAN2GP interface to add it to your toggle list.
2. **Reorder**: Drag the ≡ handle to move items up or down.
3. **Rename/Delete**: Use the yellow pencil to rename or the red X to delete.
4. **Export**: Use the **📤 Export** button to get a JSON snippet of your custom setup. Paste this into `config.json` to make your changes permanent across all browsers.

## Storage & Persistence

The plugin uses a hybrid storage system:
- **`config.json`**: This is the source of truth for the plugin. When you restart the app or click "Reset", the plugin reloads from this file.
- **LocalStorage**: Your real-time edits (new elements, renamed items, custom order) are saved in your browser. These are marked with **"Cached"** badges in Edit Mode until they are exported to the JSON file.

---
*Created for the [WAN2GP](https://github.com/deepbeepmeep/Wan2GP) community.*
