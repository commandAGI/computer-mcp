# Full Accessibility Tree Implementation - Strategic Plan

## Executive Summary

This document outlines the strategic plan for implementing full, native accessibility tree support across Windows, macOS, and Linux platforms. Currently, the codebase has simplified/fallback implementations that provide basic window information. This plan details the work required to achieve comprehensive accessibility tree extraction with full element hierarchies, properties, and states.

## Current State Analysis

### Windows
- **Current Implementation**: Basic window info only (title, bounds, PID, process name)
- **Location**: `computer_mcp/actions/accessibility_tree.py` (lines 16-62)
- **Limitations**: 
  - Only top-level window information
  - No child elements
  - No control properties or states
  - Note indicates UI Automation is needed

### macOS
- **Current Implementation**: AppleScript-based fallback
- **Location**: `computer_mcp/actions/accessibility_tree.py` (lines 64-122)
- **Limitations**:
  - Limited to 20 top-level elements
  - Only extracts name and role
  - No bounds, states, or nested hierarchy
  - Note indicates pyobjc is needed for native support

### Linux
- **Current Implementation**: Partial AT-SPI support via PyGObject
- **Location**: `computer_mcp/actions/accessibility_tree.py` (lines 124-206)
- **Status**: Already has recursive tree walking
- **Limitations**:
  - Could extract more attributes (states, actions, interfaces)
  - No filtering for ignored nodes
  - No depth limits (potential infinite recursion)
  - Always starts from desktop root, not focused window

## Implementation Strategy

### Phase 1: Windows UI Automation Implementation

#### Dependencies
- ✅ `pywin32>=306` (already in `[windows]` extras)
- No additional dependencies needed

#### Technical Approach
1. **Use Windows UI Automation (UIA) COM Interface**
   - Access via `win32com.client.Dispatch('UIAutomation.UIAutomation')`
   - Alternative: `comtypes` for more type-safe COM interop

2. **Core Implementation Steps**
   ```python
   # Pseudo-code structure:
   - Get IUIAutomation COM object
   - Get root element: GetRootElement()
   - Get focused window: root.FindFirst(TreeScope_Children, condition)
   - Walk tree recursively:
     * GetChildren() or FindAll() for elements
     * Extract properties: CurrentName, CurrentControlType, 
       CurrentBoundingRectangle, CurrentClassName, 
       CurrentIsEnabled, CurrentIsOffscreen, etc.
   ```

3. **Key UI Automation Properties to Extract**
   - `CurrentName`: Element name/label
   - `CurrentControlType`: Button, Text, Window, etc. (as ControlType enum)
   - `CurrentBoundingRectangle`: Bounds as RECT structure
   - `CurrentClassName`: Native class name
   - `CurrentIsEnabled`: Boolean enabled state
   - `CurrentIsOffscreen`: Visibility state
   - `CurrentAutomationId`: Unique identifier
   - `CurrentValue`: For value-bearing controls
   - `CurrentRole`: Accessibility role

4. **Tree Walking Strategy**
   - Use `TreeScope_Children` for immediate children
   - Use `TreeScope_Descendants` for full subtree (with depth limit)
   - Implement depth limit (suggested: 20-30 levels)
   - Handle virtualized elements (e.g., list items)
   - Filter or mark offscreen/invisible elements

5. **Error Handling**
   - Handle COM exceptions gracefully
   - Fall back to current basic implementation if UIA unavailable
   - Timeout protection for slow applications

6. **Performance Considerations**
   - Cache property values to avoid repeated COM calls
   - Limit tree depth to prevent excessive recursion
   - Consider lazy evaluation for large trees
   - Timeout for slow/unresponsive applications

#### Implementation Files
- **Primary**: `computer_mcp/actions/accessibility_tree.py` (Windows section)
- **Backup Handler**: `computer_mcp/handlers/accessibility_tree.py` (sync changes)

#### Testing Requirements
- Test with various applications (notepad, browsers, complex apps)
- Verify tree structure matches actual UI
- Test with minimized/offscreen windows
- Performance testing with large trees (e.g., file explorers)

---

### Phase 2: macOS AXUIElement Native Implementation

#### Dependencies
- ✅ `pyobjc-framework-Quartz>=10.0` (already in `[macos]` extras)
- No additional dependencies needed

#### Technical Approach
1. **Use Apple Accessibility API via PyObjC**
   - Import Quartz framework
   - Use `AXUIElement` API for element access
   - Use `AXUIElementCreateApplication(pid)` to get app element

2. **Core Implementation Steps**
   ```python
   # Pseudo-code structure:
   - Get focused application PID
   - Create AXUIElement for app: AXUIElementCreateApplication(pid)
   - Get root window: kAXMainWindowAttribute or kAXFocusedWindowAttribute
   - Walk tree recursively:
     * Get children: kAXChildrenAttribute
     * Extract attributes:
       - kAXRoleAttribute: Button, StaticText, Window, etc.
       - kAXTitleAttribute: Element title
       - kAXValueAttribute: For value-bearing elements
       - kAXBoundsAttribute: CGRect bounds
       - kAXEnabledAttribute: Boolean enabled state
       - kAXFocusedAttribute: Focus state
   ```

3. **Key Accessibility Attributes to Extract**
   - `kAXRoleAttribute`: Element role (button, text, window, etc.)
   - `kAXRoleDescriptionAttribute`: Human-readable role
   - `kAXTitleAttribute`: Element title/label
   - `kAXValueAttribute`: Element value (for sliders, text fields, etc.)
   - `kAXBoundsAttribute`: Position and size (CGRect)
   - `kAXPositionAttribute`: Element position
   - `kAXSizeAttribute`: Element size
   - `kAXEnabledAttribute`: Boolean enabled state
   - `kAXFocusedAttribute`: Focus state
   - `kAXChildrenAttribute`: Child elements
   - `kAXParentAttribute`: Parent element
   - `kAXHelpAttribute`: Tooltip/help text
   - `kAXDescriptionAttribute`: Element description

4. **Tree Walking Strategy**
   - Start from focused window or main window
   - Recursively extract children via `kAXChildrenAttribute`
   - Implement depth limit (suggested: 20-30 levels)
   - Handle ignored elements (some apps mark elements as ignored)
   - Extract attribute values using `AXUIElementCopyAttributeValue`

5. **Error Handling**
   - Handle kAXErrorAttributeNotFound gracefully
   - Fall back to AppleScript implementation if pyobjc unavailable
   - Handle permission issues (accessibility permissions required)
   - Timeout protection for slow queries

6. **Permission Requirements**
   - macOS requires accessibility permissions in System Preferences
   - Document permission setup in README
   - Provide helpful error messages if permissions denied

#### Implementation Files
- **Primary**: `computer_mcp/actions/accessibility_tree.py` (macOS section)
- **Backup Handler**: `computer_mcp/handlers/accessibility_tree.py` (sync changes)

#### Testing Requirements
- Test with various macOS applications
- Test with and without accessibility permissions
- Verify tree structure against Accessibility Inspector
- Performance testing with complex applications

---

### Phase 3: Linux AT-SPI Enhancement

#### Dependencies
- ✅ System packages: `python3-gi`, `gir1.2-atspi-2.0` (user-installed)
- ✅ Python package: `PyGObject>=3.44` (already in `[linux]` extras)

#### Technical Approach
1. **Enhance Existing AT-SPI Implementation**
   - Current implementation already walks the tree recursively
   - Need to extract more attributes and improve filtering

2. **Additional Attributes to Extract**
   - `Atspi.StateSet`: Element states (focused, enabled, visible, etc.)
   - `Atspi.Action`: Available actions (click, press, etc.)
   - `Atspi.RelationSet`: Relationships between elements
   - `Atspi.Text`: Text content and properties (for text elements)
   - `Atspi.Value`: Value for value-bearing elements
   - `Atspi.Document`: Document-related properties
   - `Atspi.Hypertext`: Hyperlink information
   - `Atspi.Table`: Table structure (rows, columns, headers)

3. **Improvements Needed**
   - **Depth Limiting**: Add configurable depth limit to prevent infinite recursion
   - **Focused Element**: Add option to get tree starting from focused window instead of desktop root
   - **Filtering**: Filter out ignored/uninteresting nodes
   - **State Extraction**: Extract and represent element states (enabled, focused, visible, etc.)
   - **Action Information**: Include available actions for interactive elements
   - **Performance**: Add timeout and size limits for large trees

4. **Tree Walking Enhancements**
   - Start from desktop (current behavior)
   - Add option to start from focused window
   - Implement configurable depth limit
   - Add node filtering based on states (e.g., skip invisible nodes)

5. **Error Handling**
   - Better error handling for missing interfaces
   - Graceful degradation if AT-SPI unavailable
   - Handle stale references (elements may become invalid)

#### Implementation Files
- **Primary**: `computer_mcp/actions/accessibility_tree.py` (Linux section, lines 124-206)
- **Backup Handler**: `computer_mcp/handlers/accessibility_tree.py` (sync changes)

#### Testing Requirements
- Test with various Linux desktop environments (GNOME, KDE)
- Verify against Orca screen reader compatibility
- Performance testing with complex applications
- Test with applications that don't support AT-SPI

---

## Unified Output Format

All platforms should produce a consistent tree structure:

```json
{
  "tree": {
    "name": "Element Name",
    "role": "Button" | "StaticText" | "Window" | ...,
    "control_type": "Button" (Windows-specific),
    "bounds": {
      "x": 100,
      "y": 200,
      "width": 150,
      "height": 30
    },
    "properties": {
      "enabled": true,
      "focused": false,
      "visible": true,
      "value": "Button Text" (if applicable),
      "description": "Help text",
      "automation_id": "button-id" (Windows),
      "class_name": "Button" (Windows),
      "states": ["enabled", "focusable"] (Linux)
    },
    "children": [
      // Recursive structure
    ]
  },
  "metadata": {
    "platform": "windows" | "darwin" | "linux",
    "depth_limit": 20,
    "total_elements": 150,
    "extraction_time_ms": 45
  }
}
```

## Implementation Phases

### Phase 1: Windows (Priority: High)
- **Estimated Effort**: 2-3 days
- **Complexity**: Medium-High (COM interop complexity)
- **Dependencies**: ✅ Available
- **Testing**: Extensive (multiple apps, edge cases)

### Phase 2: macOS (Priority: High)
- **Estimated Effort**: 2-3 days
- **Complexity**: Medium (PyObjC API learning curve)
- **Dependencies**: ✅ Available
- **Testing**: Extensive (permissions, various apps)

### Phase 3: Linux Enhancement (Priority: Medium)
- **Estimated Effort**: 1-2 days
- **Complexity**: Low-Medium (enhancement of existing code)
- **Dependencies**: ✅ Available
- **Testing**: Moderate (verify enhancements work)

## Backward Compatibility

- All implementations must maintain fallback to current simplified versions
- If native APIs unavailable or fail, gracefully fall back
- Configuration option could allow forcing simplified mode
- No breaking changes to existing API

## Documentation Updates

After implementation, update:
1. **README.md**: 
   - Update platform support section
   - Document new capabilities
   - Add examples of full tree output

2. **Code Comments**:
   - Add comprehensive docstrings
   - Document platform-specific behaviors
   - Document permission requirements (macOS)

3. **Examples**:
   - Add example scripts showing full tree output
   - Add troubleshooting guide for common issues

## Performance Considerations

### Depth Limits
- Default: 20 levels (configurable)
- Prevent infinite recursion in malformed apps
- Balance between completeness and performance

### Timeout Protection
- Default: 5 seconds per tree extraction
- Prevent hanging on slow/unresponsive apps
- Return partial tree if timeout occurs

### Size Limits
- Warn if tree exceeds reasonable size (e.g., 10,000 elements)
- Consider lazy evaluation for very large trees
- Option to limit total element count

## Security & Privacy

- Accessibility APIs require elevated permissions on some platforms
- Document permission requirements clearly
- Consider privacy implications (accessibility trees may contain sensitive UI data)
- No data should be logged or transmitted without user consent

## Testing Strategy

### Unit Tests
- Mock COM/Accessibility APIs where possible
- Test tree walking logic
- Test error handling and fallbacks

### Integration Tests
- Test with real applications on each platform
- Test with various application types (browsers, text editors, complex apps)
- Test permission scenarios (macOS)
- Test with minimized/offscreen windows

### Performance Tests
- Measure extraction time for large trees
- Verify timeout handling
- Test memory usage with deep trees

## Success Criteria

1. ✅ Full recursive tree structure with all child elements
2. ✅ Extraction of key properties (bounds, states, roles)
3. ✅ Graceful fallback to simplified version if dependencies unavailable
4. ✅ Performance acceptable (<5s for typical applications)
5. ✅ Works with major applications on each platform
6. ✅ Consistent output format across platforms
7. ✅ Comprehensive error handling
8. ✅ Documentation complete

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| COM interop complexity (Windows) | High | Extensive testing, fallback to current implementation |
| Permission issues (macOS) | Medium | Clear error messages, documentation |
| Performance with large trees | Medium | Depth limits, timeouts, lazy evaluation |
| Platform API changes | Low | Version pinning, comprehensive testing |
| Stale element references | Medium | Error handling, reference validation |

## Timeline Estimate

- **Phase 1 (Windows)**: 2-3 days
- **Phase 2 (macOS)**: 2-3 days  
- **Phase 3 (Linux)**: 1-2 days
- **Testing & Documentation**: 1-2 days
- **Total**: 6-10 days

## Next Steps

1. ✅ Review and approve this plan
2. Create feature branch: `feature/full-accessibility-tree`
3. Implement Phase 1 (Windows)
4. Implement Phase 2 (macOS)
5. Implement Phase 3 (Linux enhancements)
6. Update documentation
7. Comprehensive testing
8. Merge to main

## References

- Windows UI Automation: https://learn.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32
- macOS Accessibility API: https://developer.apple.com/documentation/applicationservices/accessibility
- Linux AT-SPI: https://developer.gnome.org/libatspi/stable/
- PyObjC Documentation: https://pyobjc.readthedocs.io/
- PyGObject Documentation: https://pygobject.readthedocs.io/

