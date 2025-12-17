# WAN2GP Hide UI Plugin

This is a plugin for the [WAN2GP](https://github.com/deepbeepmeep/Wan2GP) application that adds a floating menu to the user interface. This menu allows you to toggle the visibility of various UI elements, making it easier to focus on specific sections of the interface, especially on mobile devices.

![compact_example](https://github.com/user-attachments/assets/73dd5c32-4b60-48ae-8baf-db2423dc1b87)

## Features

- **Floating Menu:** A convenient, collapsible menu that floats on the bottom right of the screen.
- **Interactive Element Picker:** Click "➕ Add Element" to enter picker mode, hover to highlight elements, and click to add them to your toggle list.
- **Custom Element Management:** Add, rename, and delete custom UI elements with ease.
- **13 Default Elements:** Pre-configured toggles for common WAN2GP UI elements like Header, Model Selector, Prompt Options, etc.
- **localStorage Persistence:** All custom elements and visibility preferences are saved automatically and persist between sessions.
- **Show/Hide All:** Quickly toggle the visibility of all elements at once.
- **Safe Hiding:** The plugin safely hides elements and collapses empty parent containers to reclaim screen space without breaking the Gradio layout.
- **Element Counter:** See how many elements you have (default + custom) in the menu header.

## Installation

1.  Clone the repository or make a folder called wan2gp-hideUI in the plugins folder for wan2gp and place the `plugin.py` file into the folder.
2.  Restart the WAN2GP application.

## How to Use

Once installed, a "☰ UI" button will appear in the bottom right corner of the WAN2GP interface. Click this button to open the menu.

The menu contains checkboxes for all available UI elements (default and custom). Uncheck a box to hide the corresponding element, and check it to show it again. The "Show/Hide All" checkbox at the top of the menu can be used to toggle all elements at once.

Click the "✕ Close" button to close the menu.

### Adding Custom Elements

With the new interactive element picker, you can easily add any UI element to your toggle list:

1. **Open the menu** - Click the "☰ UI" button in the bottom right corner
2. **Enter picker mode** - Click the "➕ Add Element" button
3. **Select an element** - Hover over any UI element (it will be highlighted with a blue outline), then click it
4. **Name it** - Enter a custom name for the element in the prompt
5. **Done!** - The element will appear in your menu with a delete button (🗑️)

Your custom elements are automatically saved in browser localStorage and will persist between sessions.

### Managing Elements

- **Delete custom elements** - Click the 🗑️ button next to any custom element
- **Toggle visibility** - Check or uncheck the boxes to show/hide elements
- **Show/Hide All** - Use the toggle at the top to quickly show or hide all elements
- **View stats** - The menu header shows the total number of elements and how many are custom

All your preferences (which elements are shown/hidden) are automatically saved and restored when you reload the page.

### Changing Default Visibility

The plugin comes with 13 default UI elements pre-configured. If you want to change which default elements are visible or hidden by default, you can edit the `plugin.py` file.

In the `plugin.py` file, locate the `DEFAULT_TARGETS` list within the `inject_floating_buttons_js` function. For each element, the `default` property controls its initial state:
- `default: true` makes the item visible by default
- `default: false` makes the item hidden by default

For example, to make the "Header" visible by default, change:

```python
{ id: "header", labels: ["deepbeepmeep"], name: "Header", default: false },
// To:
{ id: "header", labels: ["deepbeepmeep"], name: "Header", default: true },
```

Save the file and restart the WAN2GP application for the changes to take effect.

## Configuration

The plugin stores two types of data in browser localStorage:

-   **`wan2gp_hideui_custom`**: Custom UI elements you've added using the element picker
-   **`wan2gp_hideui_prefs`**: Your visibility preferences for all elements

To reset everything, you can clear your browser's localStorage for the WAN2GP site, or delete custom elements individually using the 🗑️ button.

The `DEFAULT_TARGETS` list in `plugin.py` defines the pre-configured UI elements. You can modify this list to add more default elements or change their default visibility settings. For advanced users, you can also define elements using label-based matching (like the defaults) or component ID-based matching (like custom elements).
