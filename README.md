# WAN2GP Hide UI Plugin

This is a plugin for the [WAN2GP](https://github.com/deepbeepmeep/Wan2GP) application that adds a floating menu to the user interface. This menu allows you to toggle the visibility of various UI elements with a streamlined **Normal Mode** for everyday use and a powerful **Edit Mode** for advanced customization.

![compact_example](https://github.com/user-attachments/assets/73dd5c32-4b60-48ae-8baf-db2423dc1b87)

## Features

### Two-Tiered Interface
- **Normal Mode** - Clean, simplified view for everyday use:
  - Large "Show Default" button to reset all elements to their default state
  - "Show/Hide All" and "Edit" buttons for quick access
  - Compact element list showing only checkboxes, names, and ⭐ for default-visible elements
  
- **Edit Mode** - Full-featured management interface:
  - Drag-and-drop reordering (≡) for all elements
  - Clickable star badges (⭐/☆) to set default visibility state
  - "Cached" badges showing localStorage-only changes
  - Edit (✏️) and Delete (✕) buttons for all elements
  - Add New Element, Export, and Clear Cached buttons

### Core Features
- **Floating Menu** - Convenient, collapsible menu in the bottom right corner
- **Interactive Element Picker** - Click "➕ Add New Element" to enter picker mode, hover to highlight elements, and click to add them
- **Unified Element Management** - All 13 default elements plus custom elements are fully editable (rename, delete, reorder)
- **Configuration Persistence** - All elements stored in `config.json` with localStorage for temporary changes
- **Smart Caching** - See which elements have been modified with "Cached" badges
- **Safe Hiding** - Elements are safely hidden and parent containers collapsed to reclaim screen space

## Installation

1. Clone the repository or create a folder called `wan2gp-hideUI` in the WAN2GP plugins folder
2. Place `plugin.py` and `config.json` into the folder
3. Restart the WAN2GP application

## How to Use

### Opening the Menu

Click the **☰ UI** button in the bottom right corner. Click **✕ Close** to close the menu.

### Normal Mode (Default)

Perfect for everyday use with a clean interface:

1. **Show Default** - Large blue button that resets all elements to their default visibility state (enables ⭐ elements, disables others)
2. **Show/Hide All** - Small grey button to toggle all elements at once
3. **Edit** - Small grey button to switch to Edit Mode for advanced features
4. **Element List** - Compact checkboxes with names and ⭐ indicators for default-visible elements

### Edit Mode

Access full management features by clicking the **Edit** button:

#### Managing Elements
- **Reorder** - Drag the ≡ handle to reorder elements
- **Rename** - Click the ✏️ button to rename any element
- **Delete** - Click the ✕ button to remove any element
- **Toggle Default State** - Click the star to set whether element starts visible (⭐) or hidden (☆)

#### Adding Custom Elements
1. Click **➕ Add New Element**
2. Hover over any UI element (highlighted with blue outline)
3. Click the element you want to add
4. Enter a custom name in the prompt
5. The new element appears in your list with "Cached" badge

#### Configuration Management
- **📤 Export** - Export current configuration to JSON (copy and paste into `config.json`)
- **🗑️ Clear Cached** - Remove all localStorage changes and reload from `config.json`

#### Visual Indicators
- **Cached** (yellow badge) - Element has been modified in localStorage but not saved to `config.json`
- **⭐** (filled star) - Element starts visible by default
- **☆** (empty star) - Element starts hidden by default

### Saving Your Configuration

The plugin uses a two-tier storage system:

1. **Temporary Changes** (localStorage):
   - All edits, additions, deletions, and reordering are saved here
   - Shown with "Cached" badges in Edit Mode
   - Persist between sessions but only in your browser

2. **Permanent Configuration** (`config.json`):
   - Click **📤 Export** to get JSON of your current configuration
   - Manually paste into `config.json` file
   - Click **🗑️ Clear Cached** to reload from file
   - Changes apply across all browsers and devices

## Configuration

### Default Elements

The plugin includes 13 pre-configured UI elements in `config.json`:
- Header
- Model Selector
- Prompt Options
- Controlnet
- More Options
- Image to Image
- Output Info
- Image Display
- IP Adapter
- Tools
- Edit Button
- Prompt Textbox
- Footer

Each element has:
- `id` - Unique identifier
- `name` - Display name in menu
- `labels` or `componentId` - How to find the element in the DOM
- `default` - Whether element starts visible (`true`) or hidden (`false`)

### Editing config.json

To change default visibility or add permanent custom elements:

```json
{
  "elements": [
    {
      "id": "header",
      "labels": ["deepbeepmeep"],
      "name": "Header",
      "default": false
    },
    // ... more elements
  ]
}
```

Change `default: true` to make an element visible by default, or `default: false` to hide it by default.

### localStorage Keys

- `wan2gp_hideui_custom` - Custom elements and modifications
- `wan2gp_hideui_prefs` - Visibility preferences for all elements
- `wan2gp_hideui_order` - Custom element ordering
- `wan2gp_hideui_editMode` - Whether Edit Mode is active

## Tips

- Use **Normal Mode** for daily use - it's faster and cleaner
- Switch to **Edit Mode** only when you need to customize
- Click the star (⭐/☆) in Edit Mode to set which elements appear by default
- Export your configuration regularly to save across devices
- The "Show Default" button is perfect for quickly resetting to a clean state
