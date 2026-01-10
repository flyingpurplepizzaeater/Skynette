# Phase 3: UI Foundation - Integration Design

**Date:** 2026-01-10
**Status:** Approved
**Target:** v0.3.0
**Estimated Duration:** 9 days (3 sprints)

## Overview

Phase 3 integrates the existing Flet-based UI code with the Phase 2 workflow engine. The UI skeleton exists but hasn't been tested or connected to the backend. This design outlines a progressive implementation strategy that delivers a working MVP quickly, then expands to full feature parity.

## Current State Analysis

### What Exists (Untested)
- ✅ Application shell (`src/ui/app.py`) - 2,146 lines
- ✅ Workflow list view with cards
- ✅ Simple mode editor (step-by-step)
- ✅ Advanced mode editor (visual canvas)
- ✅ Node palette with categories
- ✅ Properties panel
- ✅ Settings page
- ✅ Theme system (`SkynetteTheme`)
- ✅ Execution controls UI

### What's Missing
- ❌ Integration with Phase 2 storage (`WorkflowStorage`)
- ❌ Integration with Phase 2 executor (`WorkflowExecutor`)
- ❌ Real workflow loading/saving
- ❌ Actual workflow execution
- ❌ Node registry integration
- ❌ Testing of any UI components
- ❌ Error handling in UI layer

## Implementation Strategy

### Approach: MVP-First Progressive Enhancement

**Philosophy:** Get one complete user flow working end-to-end first, then expand systematically.

**Why this approach:**
1. **Early validation** - Know if Phase 2/3 integration works within days, not weeks
2. **Risk mitigation** - Discover integration issues early when fixes are cheap
3. **Demonstrable progress** - Working demo motivates and validates architecture
4. **Incremental complexity** - Each sprint builds on proven foundation

## Sprint Breakdown

### Sprint 1: Critical Path MVP (Days 1-3)

**Goal:** One complete user journey working end-to-end

**User Story:** "As a user, I can create a simple 2-node workflow (Manual Trigger → Log Debug) and run it successfully, seeing the results."

#### 1.1 Application Bootstrap (Day 1 Morning)

**Files to modify:**
- `src/ui/app.py` (fix imports, test initialization)
- `src/main.py` (ensure Flet app starts)

**Tasks:**
- Fix import paths for Phase 2 modules
- Test that `WorkflowStorage` initializes correctly
- Test that `NodeRegistry` loads builtin nodes
- Test that `WorkflowExecutor` can be instantiated
- Add error handling for initialization failures

**Success criteria:**
- App launches without crashes
- Console shows successful storage/registry initialization
- No import errors

#### 1.2 Workflow List View Integration (Day 1 Afternoon)

**Files to modify:**
- `src/ui/app.py::_build_workflows_view()`
- `src/ui/app.py::_create_new_workflow()`
- `src/ui/app.py::_open_workflow()`
- `src/ui/app.py::_delete_workflow()`

**Tasks:**
- Connect `storage.list_workflows()` to UI
- Connect `storage.save_workflow()` to create dialog
- Connect `storage.load_workflow()` to open action
- Connect `storage.delete_workflow()` to delete action
- Add error handling for storage operations
- Test with empty database
- Test with existing workflows from Phase 2

**Success criteria:**
- Workflow list displays existing workflows
- Can create new workflow via dialog
- Can delete workflow with confirmation
- Workflow cards show correct metadata

#### 1.3 Simple Mode Editor Core (Day 2)

**Files to modify:**
- `src/ui/views/simple_mode.py` (complete implementation)
- `src/ui/app.py::_build_simple_editor_content()`
- `src/ui/app.py::_save_current_workflow()`

**Tasks:**
- Implement trigger selection from `NodeRegistry`
- Implement step addition from available nodes
- Implement step configuration via properties panel
- Connect save button to `storage.save_workflow()`
- Build workflow model from UI state
- Validate workflow has required nodes

**Success criteria:**
- Can select Manual Trigger as trigger
- Can add Log Debug node as step
- Can configure step properties
- Save creates valid Workflow model
- Saved workflow appears in list view

#### 1.4 Workflow Execution Integration (Day 3)

**Files to modify:**
- `src/ui/app.py::_run_current_workflow()`
- `src/ui/app.py::_run_workflow()`
- `src/ui/app.py::_build_execution_indicator()`
- `src/ui/app.py::_show_execution_details()`

**Tasks:**
- Connect run button to `executor.execute()`
- Handle async execution in Flet (use `page.run_task()`)
- Show execution progress indicator
- Display success/failure in snackbar
- Save execution to storage
- Show execution results dialog
- Handle execution errors gracefully

**Success criteria:**
- Run button executes workflow
- Execution completes successfully
- Results shown in dialog with node outputs
- Execution saved to history
- Errors shown with helpful messages

**Sprint 1 Deliverable:** Working MVP - can create, save, and run simple workflows.

---

### Sprint 2: Advanced Editor & Expansion (Days 4-6)

**Goal:** Full feature parity with all Phase 2 nodes and advanced visual editor

#### 2.1 Visual Canvas Editor (Day 4)

**Files to modify:**
- `src/ui/app.py::_build_advanced_editor_content()`
- `src/ui/app.py::_build_canvas_node()`
- `src/ui/app.py::_add_node_to_workflow()`
- `src/ui/app.py::_build_connection_lines()`

**Tasks:**
- Render node palette from `NodeRegistry.get_all_definitions()`
- Implement node addition to canvas on click
- Calculate automatic node positioning
- Render nodes with correct styling
- Implement node selection
- Display connection lines between nodes

**Success criteria:**
- Node palette shows all registered nodes by category
- Can add nodes to canvas via palette
- Nodes render at non-overlapping positions
- Can select nodes by clicking
- Connections render as visual lines

#### 2.2 Connection System (Day 5 Morning)

**Files to modify:**
- `src/ui/app.py::_add_connection()`
- `src/ui/app.py::_build_properties_panel()`
- `src/ui/app.py::_build_connection_lines()`

**Tasks:**
- Implement connection via dropdown in properties panel
- Validate connections (no cycles, valid targets)
- Update `WorkflowConnection` models
- Render connection arrows
- Show connection ports on nodes

**Success criteria:**
- Can connect nodes via properties panel
- Connections stored in workflow model
- Visual feedback for connections
- Invalid connections prevented

#### 2.3 Complete Node Configuration (Day 5 Afternoon - Day 6)

**Files to modify:**
- `src/ui/app.py::_build_properties_panel()`
- `src/ui/app.py::_update_node_config()`

**Tasks:**
- Generate form fields from node definitions
- Support all field types (text, number, boolean, select, code)
- Add expression hints for template syntax
- Implement configuration validation
- Test all 5 Phase 2 nodes:
  - Manual Trigger with test data
  - HTTP Request with all methods
  - If/Else with all operators
  - Set Variable with type conversion
  - Log Debug with levels

**Success criteria:**
- All node types configurable via UI
- Form fields match node input definitions
- Configuration saves correctly
- Expression hints visible
- Validation prevents invalid configs

**Sprint 2 Deliverable:** Full-featured visual editor with all Phase 2 nodes working.

---

### Sprint 3: Polish & Production-Ready (Days 7-9)

**Goal:** Production-quality UX with theme support, settings, and comprehensive testing

#### 3.1 Settings & Theme Integration (Day 7)

**Files to modify:**
- `src/ui/app.py::_build_settings_view()`
- `src/ui/theme.py` (if needed for theme toggle)
- `src/data/storage.py` (settings persistence)

**Tasks:**
- Implement theme toggle (light/dark)
- Persist theme preference in storage
- Test update checker integration
- Add settings for default workflow execution
- Add keyboard shortcuts documentation

**Success criteria:**
- Theme toggle works instantly
- Theme preference persists across sessions
- Settings save to database
- Update checker shows current version

#### 3.2 UX Polish (Day 8)

**Files to modify:**
- Multiple files across `src/ui/`

**Tasks:**
- Add loading states for async operations
- Smooth transitions between views
- Improve empty states (no workflows, no nodes)
- Add confirmation dialogs for destructive actions
- Improve error messages with actionable guidance
- Add tooltips for complex features
- Keyboard navigation support

**Success criteria:**
- No jarring UI jumps
- Clear feedback for all actions
- Helpful empty states guide users
- Destructive actions confirmed
- Errors explain what happened and how to fix

#### 3.3 Integration Testing & Bug Fixes (Day 9)

**Test scenarios:**
1. **Empty Start** - First launch, create first workflow, run it
2. **Complex Workflow** - Multi-node workflow with branching
3. **Error Cases** - Invalid configs, failed executions, network errors
4. **CRUD Operations** - Create, read, update, delete workflows
5. **Mode Switching** - Toggle between simple/advanced modes
6. **Persistence** - Close app, reopen, verify state preserved

**Files to create:**
- `tests/ui/test_workflows_integration.py`
- `tests/ui/test_editor_integration.py`
- `tests/ui/test_execution_integration.py`

**Tasks:**
- Write integration tests for critical paths
- Manual testing of all UI flows
- Fix bugs discovered during testing
- Document known limitations
- Performance testing with many workflows

**Success criteria:**
- All integration tests pass
- No critical bugs in core flows
- Performance acceptable (< 1s for most operations)
- Known issues documented

**Sprint 3 Deliverable:** Production-ready UI with comprehensive testing.

---

## Technical Architecture

### Component Integration Points

```
┌─────────────────────────────────────────────────┐
│                 Flet UI Layer                    │
│  (src/ui/app.py, src/ui/views/*.py)             │
└─────────────┬───────────────────────────────────┘
              │
              ├─> WorkflowStorage (CRUD)
              │   └─> SQLite Database
              │
              ├─> WorkflowExecutor (Run)
              │   └─> NodeRegistry (Get Nodes)
              │       └─> Built-in Nodes
              │
              └─> ExpressionParser (Validate)
```

### Data Flow

**Workflow Creation:**
1. UI: User clicks "New Workflow"
2. UI: Dialog captures name/description
3. UI: Creates `Workflow` model
4. Storage: `save_workflow()` persists to DB + YAML
5. UI: Refreshes workflow list

**Workflow Execution:**
1. UI: User clicks "Run"
2. UI: Calls `executor.execute(workflow)`
3. Executor: Runs nodes in topological order
4. Executor: Returns `WorkflowExecution` model
5. Storage: `save_execution()` logs to DB
6. UI: Displays results in dialog

**Node Configuration:**
1. UI: User selects node
2. UI: Fetches `NodeDefinition` from registry
3. UI: Generates form fields from definition
4. UI: User edits config
5. UI: Updates `WorkflowNode.config`
6. Storage: Save triggers on "Save Workflow"

### Error Handling Strategy

**Layers:**
1. **Storage Layer** - Raises `StorageError`, `DataNotFoundError`
2. **Execution Layer** - Raises `WorkflowExecutionError`, `NodeExecutionError`
3. **UI Layer** - Catches all, shows user-friendly messages

**UI Error Handling Pattern:**
```python
try:
    result = await executor.execute(workflow)
    # Show success
except WorkflowExecutionError as e:
    # Show execution error with node details
except Exception as e:
    # Show generic error with suggestion to check logs
finally:
    # Hide loading indicator
```

## Testing Strategy

### Unit Tests (Existing from Phase 2)
- ✅ 90 tests for Phase 2 engine
- ✅ All passing

### Integration Tests (New for Phase 3)
- UI → Storage integration
- UI → Executor integration
- UI → Registry integration
- End-to-end user flows

### Manual Testing Checklist
- [ ] Create workflow in simple mode
- [ ] Create workflow in advanced mode
- [ ] Edit existing workflow
- [ ] Delete workflow
- [ ] Run workflow successfully
- [ ] Run workflow with errors
- [ ] Switch between simple/advanced modes
- [ ] Configure all node types
- [ ] Create connections
- [ ] Theme toggle
- [ ] Settings persistence
- [ ] App restart preserves state

## Success Criteria

### Sprint 1 (MVP)
- ✅ App launches without errors
- ✅ Can create simple workflow
- ✅ Can save workflow to database
- ✅ Can run workflow and see results
- ✅ Basic error handling works

### Sprint 2 (Full Features)
- ✅ Visual editor functional
- ✅ All 5 node types configurable
- ✅ Connections can be created
- ✅ Properties panel dynamic
- ✅ Mode switching works

### Sprint 3 (Production)
- ✅ Theme toggle works
- ✅ Settings persist
- ✅ UX polished (no jarring transitions)
- ✅ Integration tests pass
- ✅ No critical bugs

## Risk Mitigation

### Identified Risks

1. **Async/UI Threading Issues**
   - **Risk:** Flet async not compatible with asyncio
   - **Mitigation:** Use `page.run_task()` for async operations
   - **Testing:** Test execution early in Sprint 1

2. **State Management Complexity**
   - **Risk:** UI state gets out of sync with models
   - **Mitigation:** Single source of truth (Workflow model)
   - **Testing:** Test mode switching extensively

3. **Performance with Many Nodes**
   - **Risk:** Canvas rendering slow with 50+ nodes
   - **Mitigation:** Lazy rendering, viewport culling
   - **Testing:** Performance test in Sprint 3

4. **Theme System Conflicts**
   - **Risk:** Flet theme vs SkynetteTheme clash
   - **Mitigation:** Use Flet theme as base, override with SkynetteTheme
   - **Testing:** Theme toggle tested early

## Deliverables

### Documentation
- [x] This design document
- [ ] Updated README with UI screenshots
- [ ] User guide for workflow creation
- [ ] Developer guide for adding UI features

### Code
- [ ] All UI integration code (src/ui/)
- [ ] Integration tests (tests/ui/)
- [ ] Bug fixes from testing

### Release Artifacts
- [ ] v0.3.0 tag
- [ ] CHANGELOG.md updated
- [ ] Release notes with screenshots
- [ ] Binaries for Windows/Mac/Linux

## Timeline

| Sprint | Days | Deliverable | Risk |
|--------|------|-------------|------|
| Sprint 1 | 1-3 | Working MVP | Medium - First integration |
| Sprint 2 | 4-6 | Full Features | Low - Building on working base |
| Sprint 3 | 7-9 | Production Polish | Low - Refinement only |

**Total:** 9 days
**Buffer:** +2 days for unexpected issues
**Target Release:** v0.3.0 by Day 11

## Post-Phase 3 Roadmap

After Phase 3 completes, next priorities:
1. **Phase 4:** AI Integration (AI nodes, model hub)
2. **Phase 5:** Advanced Nodes (triggers, loops, data transformation)
3. **Phase 6:** Skynet Assistant (natural language workflow creation)

## Appendix

### File Change Summary

**Modified (Heavy):**
- `src/ui/app.py` - Main integration work
- `src/ui/views/simple_mode.py` - Simple editor completion
- `src/ui/views/workflow_editor.py` - Advanced editor completion

**Modified (Light):**
- `src/ui/theme.py` - Theme toggle support
- `src/main.py` - Initialization fixes

**Created:**
- `tests/ui/test_workflows_integration.py`
- `tests/ui/test_editor_integration.py`
- `tests/ui/test_execution_integration.py`
- `docs/plans/2026-01-10-phase3-ui-integration-design.md` (this file)

### Dependencies

**Required from Phase 2:**
- `WorkflowStorage` - Fully implemented ✅
- `WorkflowExecutor` - Fully implemented ✅
- `NodeRegistry` - Fully implemented ✅
- All 5 basic nodes - Fully implemented ✅

**External:**
- Flet 0.24+ (already in pyproject.toml)
- Python 3.10+ (already required)

---

**Design Status:** ✅ Approved
**Ready for Implementation:** Yes
**Next Step:** Create git worktree for isolated development
