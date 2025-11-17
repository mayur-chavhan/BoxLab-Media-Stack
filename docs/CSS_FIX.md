# CSS Error Fix

## Issue

When running the application, a CSS parsing error occurred:

```
Error at dashboard.py in DashboardScreen.CSS:41:19
│ 41 │   │   margin: 2 auto;
Invalid value for the margin property
└── Supply 1, 2 or 4 integers separated by a space
```

## Root Cause

Textual CSS doesn't support the `auto` keyword for margin values like standard CSS does. The line:

```css
margin: 2 auto;
```

was attempting to center the button horizontally using `auto`, which is not supported in Textual.

## Solution

Instead of using CSS `auto` margins, we use Textual's layout containers to achieve centering:

### Before (Broken):

```python
services_list.mount(
    Button("Create New Stack", id="create-stack-button", variant="primary")
)
```

```css
DashboardScreen #create-stack-button {
  margin: 2 auto; /* ❌ Not supported in Textual */
  width: 30;
}
```

### After (Fixed):

```python
from textual.containers import Center

container = Vertical(classes="no-stack-container")
container.mount(Label("No stack configured yet.", classes="no-services"))
container.mount(Label("Get started by creating your first stack:", classes="no-services"))
container.mount(
    Center(  # ✅ Use Center container for horizontal centering
        Button("Create New Stack", id="create-stack-button", variant="primary")
    )
)
services_list.mount(container)
```

```css
DashboardScreen .no-stack-container {
  height: 100%;
  width: 100%;
  align: center middle; /* ✅ Center the entire container */
}

DashboardScreen #create-stack-button {
  margin-top: 2; /* ✅ Valid margin value */
  width: 30;
}
```

## Key Learnings

1. **Textual CSS is not standard CSS** - It has its own subset of properties and values
2. **Use layout containers for alignment** - Instead of CSS tricks like `margin: auto`, use Textual's `Center`, `Horizontal`, `Vertical` containers
3. **Margin values must be integers** - Valid formats:
   - `margin: 1;` (all sides)
   - `margin: 1 2;` (vertical, horizontal)
   - `margin: 1 2 3 4;` (top, right, bottom, left)
   - `margin-top: 2;` (individual sides)

## Files Modified

- `src/arr_stack_manager/screens/dashboard.py`
  - Changed button mounting to use `Center` container
  - Updated CSS to use valid Textual properties
  - Added `no-stack-container` class for proper layout

## Testing

Run the application to verify:

```bash
python -m arr_stack_manager
```

The dashboard should now load without CSS errors, and the "Create New Stack" button should be properly centered.
