"""Simple Mode Editor - Step-by-step workflow builder for beginners."""

from uuid import uuid4

import flet as ft

from src.core.nodes.registry import NodeRegistry
from src.core.workflow.models import Workflow, WorkflowConnection, WorkflowNode
from src.ui.theme import Theme


class SimpleModeView(ft.Column):
    """
    Simple step-by-step workflow builder.

    Presents workflows as a linear list of numbered steps,
    making it easier for beginners to understand and build workflows.
    """

    def __init__(self, workflow: Workflow = None, on_save=None, on_change=None):
        super().__init__()
        self.workflow = workflow
        self.on_save = on_save
        self.on_change = on_change
        self.expand = True
        self.selected_step_index = None
        self.registry = NodeRegistry()
        self._steps_column = None
        self._properties_container = None
        self._current_dialog = None  # Track current dialog for proper close

    def build(self):
        self._steps_column = ft.Column(
            controls=self._build_steps_list(),
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self._properties_container = ft.Container(
            content=self._build_step_properties(),
            expand=True,
        )

        return ft.Row(
            controls=[
                # Main steps area
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self._build_trigger_section(),
                            ft.Divider(color=Theme.BORDER, height=1),
                            ft.Container(
                                content=ft.Text(
                                    "Then do this:",
                                    size=14,
                                    weight=ft.FontWeight.W_600,
                                    color=Theme.TEXT_PRIMARY,
                                ),
                                padding=ft.Padding.only(left=16, top=16, bottom=8),
                            ),
                            self._steps_column,
                            self._build_add_step_button(),
                        ],
                        expand=True,
                        spacing=0,
                    ),
                    expand=True,
                    bgcolor=Theme.BG_PRIMARY,
                ),
                # Properties panel
                ft.Container(
                    content=self._properties_container,
                    width=320,
                    bgcolor=Theme.BG_SECONDARY,
                    border=ft.Border.only(left=ft.BorderSide(1, Theme.BORDER)),
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _build_trigger_section(self):
        """Build the trigger selection section."""
        trigger = self._get_trigger()

        if trigger:
            trigger_def = self.registry.get_definition(trigger.type)
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.BOLT,
                                size=20,
                                color=Theme.TEXT_PRIMARY,
                            ),
                            width=36,
                            height=36,
                            bgcolor=Theme.WARNING,
                            border_radius=18,
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "When this happens:",
                                    size=11,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                                ft.Text(
                                    trigger_def.name if trigger_def else trigger.type,
                                    size=14,
                                    weight=ft.FontWeight.W_600,
                                    color=Theme.TEXT_PRIMARY,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_size=18,
                            icon_color=Theme.TEXT_SECONDARY,
                            tooltip="Change trigger",
                            on_click=lambda e: self._show_trigger_picker(),
                        ),
                    ],
                    spacing=12,
                ),
                padding=16,
                bgcolor=Theme.BG_SECONDARY,
                border_radius=Theme.RADIUS_MD,
                margin=ft.margin.all(16),
                border=ft.Border.all(1, Theme.WARNING + "40"),
            )
        else:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.ADD_CIRCLE_OUTLINE,
                            size=32,
                            color=Theme.PRIMARY,
                        ),
                        ft.Text(
                            "Choose how your workflow starts",
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=Theme.TEXT_PRIMARY,
                        ),
                        ft.Text(
                            "Select a trigger to begin",
                            size=12,
                            color=Theme.TEXT_SECONDARY,
                        ),
                        ft.Container(height=8),
                        ft.Button(
                            "Choose Trigger",
                            icon=ft.Icons.BOLT,
                            bgcolor=Theme.PRIMARY,
                            color=Theme.TEXT_PRIMARY,
                            on_click=lambda e: self._show_trigger_picker(),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                padding=24,
                bgcolor=Theme.BG_SECONDARY,
                border_radius=Theme.RADIUS_MD,
                margin=ft.margin.all(16),
                border=ft.Border.all(2, Theme.BORDER),
                alignment=ft.Alignment(0, 0),
            )

    def _build_steps_list(self):
        """Build the list of workflow steps."""
        steps = self._get_ordered_steps()

        if not steps:
            return [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "No steps yet",
                                size=13,
                                color=Theme.TEXT_SECONDARY,
                            ),
                            ft.Text(
                                "Add steps to define what your workflow does",
                                size=11,
                                color=Theme.TEXT_MUTED,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    padding=24,
                    alignment=ft.Alignment(0, 0),
                ),
            ]

        step_cards = []
        for i, node in enumerate(steps):
            step_cards.append(self._build_step_card(i, node))
        return step_cards

    def _build_step_card(self, index: int, node: WorkflowNode):
        """Build a card for a single step."""
        node_def = self.registry.get_definition(node.type)
        is_selected = index == self.selected_step_index

        # Get node icon and color
        icon = ft.Icons.EXTENSION
        color = Theme.TEXT_SECONDARY
        if node_def:
            icon = self._get_node_icon(node_def.icon)
            color = node_def.color

        return ft.Container(
            content=ft.Row(
                controls=[
                    # Step number
                    ft.Container(
                        content=ft.Text(
                            str(index + 1),
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=Theme.TEXT_PRIMARY if is_selected else Theme.TEXT_SECONDARY,
                        ),
                        width=28,
                        height=28,
                        bgcolor=Theme.PRIMARY if is_selected else Theme.BG_TERTIARY,
                        border_radius=14,
                        alignment=ft.Alignment(0, 0),
                    ),
                    # Step content
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(icon, size=18, color=color),
                                    width=32,
                                    height=32,
                                    bgcolor=color + "20",
                                    border_radius=8,
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            node_def.name if node_def else node.type,
                                            size=13,
                                            weight=ft.FontWeight.W_500,
                                            color=Theme.TEXT_PRIMARY,
                                        ),
                                        ft.Text(
                                            self._get_step_summary(node),
                                            size=11,
                                            color=Theme.TEXT_SECONDARY,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.PopupMenuButton(
                                    icon=ft.Icons.MORE_VERT,
                                    icon_color=Theme.TEXT_SECONDARY,
                                    items=[
                                        ft.PopupMenuItem(
                                            text="Edit",
                                            icon=ft.Icons.EDIT,
                                            on_click=lambda e, idx=index: self._select_step(idx),
                                        ),
                                        ft.PopupMenuItem(
                                            text="Move Up",
                                            icon=ft.Icons.ARROW_UPWARD,
                                            on_click=lambda e, idx=index: self._move_step(idx, -1),
                                        ),
                                        ft.PopupMenuItem(
                                            text="Move Down",
                                            icon=ft.Icons.ARROW_DOWNWARD,
                                            on_click=lambda e, idx=index: self._move_step(idx, 1),
                                        ),
                                        ft.PopupMenuItem(),  # Divider
                                        ft.PopupMenuItem(
                                            text="Delete",
                                            icon=ft.Icons.DELETE,
                                            on_click=lambda e, idx=index: self._delete_step(idx),
                                        ),
                                    ],
                                ),
                            ],
                            spacing=12,
                        ),
                        bgcolor=Theme.BG_SECONDARY if is_selected else Theme.BG_PRIMARY,
                        border=ft.Border.all(
                            2 if is_selected else 1,
                            Theme.PRIMARY if is_selected else Theme.BORDER,
                        ),
                        border_radius=Theme.RADIUS_MD,
                        padding=12,
                        expand=True,
                        on_click=lambda e, idx=index: self._select_step(idx),
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=4),
        )

    def _build_add_step_button(self):
        """Build the add step button."""
        return ft.Container(
            content=ft.OutlinedButton(
                "Add Step",
                icon=ft.Icons.ADD,
                style=ft.ButtonStyle(
                    color=Theme.TEXT_SECONDARY,
                    side=ft.BorderSide(1, Theme.BORDER),
                ),
                on_click=lambda e: self._show_step_picker(),
            ),
            padding=ft.Padding.all(16),
            alignment=ft.Alignment(0, 0),
        )

    def _build_step_properties(self):
        """Build the properties panel for the selected step."""
        if self.selected_step_index is None:
            return ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "Step Properties",
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=Theme.TEXT_PRIMARY,
                        ),
                        padding=16,
                        border=ft.Border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.TOUCH_APP,
                                    size=48,
                                    color=Theme.TEXT_MUTED,
                                ),
                                ft.Text(
                                    "Select a step to edit",
                                    size=13,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        expand=True,
                        alignment=ft.Alignment(0, 0),
                    ),
                ],
                expand=True,
            )

        steps = self._get_ordered_steps()
        if self.selected_step_index >= len(steps):
            return ft.Container()

        node = steps[self.selected_step_index]
        node_def = self.registry.get_definition(node.type)

        if not node_def:
            return ft.Container(
                content=ft.Text("Unknown node type"),
                padding=16,
            )

        # Build property fields
        property_fields = []
        for field in node_def.inputs:
            property_fields.append(self._build_field_editor(field, node))

        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                f"Step {self.selected_step_index + 1}: {node_def.name}",
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=Theme.TEXT_PRIMARY,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=18,
                                icon_color=Theme.TEXT_SECONDARY,
                                on_click=lambda e: self._deselect_step(),
                            ),
                        ],
                    ),
                    padding=16,
                    border=ft.Border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                node_def.description,
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                            ft.Container(height=8),
                            *property_fields,
                        ]
                        if property_fields
                        else [
                            ft.Text(
                                node_def.description,
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                            ft.Container(height=16),
                            ft.Text(
                                "This step has no configurable options.",
                                size=12,
                                color=Theme.TEXT_MUTED,
                                italic=True,
                            ),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=16,
                    expand=True,
                ),
            ],
            expand=True,
        )

    def _build_field_editor(self, field, node: WorkflowNode):
        """Build an editor widget for a field."""
        current_value = node.config.get(field.name, field.default or "")

        label = ft.Text(
            f"{field.label}{'*' if field.required else ''}",
            size=12,
            weight=ft.FontWeight.W_500,
            color=Theme.TEXT_PRIMARY,
        )

        description = (
            ft.Text(
                field.description,
                size=11,
                color=Theme.TEXT_SECONDARY,
            )
            if field.description
            else None
        )

        # Create appropriate input based on field type
        from src.core.nodes.base import FieldType

        if field.type == FieldType.TEXT:
            input_widget = ft.TextField(
                value=str(current_value) if current_value else "",
                multiline=True,
                min_lines=3,
                max_lines=6,
                hint_text=field.placeholder,
                border_color=Theme.BORDER,
                on_change=lambda e, n=node, f=field.name: self._update_field(n, f, e.control.value),
            )
        elif field.type == FieldType.NUMBER:
            input_widget = ft.TextField(
                value=str(current_value) if current_value is not None else "",
                keyboard_type=ft.KeyboardType.NUMBER,
                hint_text=field.placeholder,
                border_color=Theme.BORDER,
                on_change=lambda e, n=node, f=field.name: self._update_field(
                    n, f, self._parse_number(e.control.value)
                ),
            )
        elif field.type == FieldType.BOOLEAN:
            input_widget = ft.Switch(
                value=bool(current_value),
                active_color=Theme.PRIMARY,
                on_change=lambda e, n=node, f=field.name: self._update_field(n, f, e.control.value),
            )
        elif field.type == FieldType.SELECT:
            dropdown = ft.Dropdown(
                value=str(current_value) if current_value else None,
                options=[
                    ft.dropdown.Option(opt.get("value"), opt.get("label")) for opt in field.options
                ],
                border_color=Theme.BORDER,
            )
            dropdown.on_change = lambda e, n=node, f=field.name: self._update_field(
                n, f, e.control.value
            )
            input_widget = dropdown
        elif field.type == FieldType.SECRET:
            input_widget = ft.TextField(
                value=str(current_value) if current_value else "",
                password=True,
                can_reveal_password=True,
                hint_text=field.placeholder,
                border_color=Theme.BORDER,
                on_change=lambda e, n=node, f=field.name: self._update_field(n, f, e.control.value),
            )
        else:  # STRING, EXPRESSION, JSON, FILE, etc.
            input_widget = ft.TextField(
                value=str(current_value) if current_value else "",
                hint_text=field.placeholder,
                border_color=Theme.BORDER,
                on_change=lambda e, n=node, f=field.name: self._update_field(n, f, e.control.value),
            )

        controls = [label]
        if description:
            controls.append(description)
        controls.append(ft.Container(height=4))
        controls.append(input_widget)

        return ft.Container(
            content=ft.Column(controls=controls, spacing=2),
            margin=ft.margin.only(bottom=16),
        )

    def _get_trigger(self) -> WorkflowNode | None:
        """Get the trigger node from workflow."""
        if not self.workflow:
            return None
        for node in self.workflow.nodes:
            node_def = self.registry.get_definition(node.type)
            if node_def and node_def.is_trigger:
                return node
        return None

    def _get_ordered_steps(self) -> list[WorkflowNode]:
        """Get non-trigger nodes in execution order."""
        if not self.workflow:
            return []

        # Get execution order
        try:
            order = self.workflow.get_execution_order()
        except Exception:
            order = [n.id for n in self.workflow.nodes]

        # Filter out triggers and return in order
        result = []
        for node_id in order:
            node = self.workflow.get_node(node_id)
            if node:
                node_def = self.registry.get_definition(node.type)
                if node_def and not node_def.is_trigger:
                    result.append(node)
        return result

    def _get_step_summary(self, node: WorkflowNode) -> str:
        """Get a human-readable summary of the step configuration."""
        if not node.config:
            return "Not configured"

        # Try to get a meaningful summary from config values
        summaries = []
        for key, value in node.config.items():
            if value and isinstance(value, str) and len(value) < 50:
                summaries.append(str(value))

        if summaries:
            return ", ".join(summaries[:2])
        return "Configured"

    def _get_node_icon(self, icon_name: str):
        """Convert node icon name to Flet icon."""
        icon_map = {
            "bolt": ft.Icons.BOLT,
            "schedule": ft.Icons.SCHEDULE,
            "webhook": ft.Icons.LINK,
            "http": ft.Icons.HTTP,
            "auto_awesome": ft.Icons.AUTO_AWESOME,
            "psychology": ft.Icons.PSYCHOLOGY,
            "smart_toy": ft.Icons.SMART_TOY,
            "description": ft.Icons.DESCRIPTION,
            "folder": ft.Icons.FOLDER,
            "storage": ft.Icons.STORAGE,
            "call_split": ft.Icons.CALL_SPLIT,
            "code": ft.Icons.CODE,
            "email": ft.Icons.EMAIL,
            "cloud": ft.Icons.CLOUD,
            "extension": ft.Icons.EXTENSION,
        }
        return icon_map.get(icon_name, ft.Icons.EXTENSION)

    def _show_trigger_picker(self):
        """Show dialog to pick a trigger."""
        triggers = self.registry.get_triggers()

        options = []
        for trigger in triggers:
            icon = self._get_node_icon(trigger.icon)
            options.append(
                ft.ListTile(
                    leading=ft.Container(
                        content=ft.Icon(icon, size=20, color=trigger.color),
                        width=36,
                        height=36,
                        bgcolor=trigger.color + "20",
                        border_radius=8,
                        alignment=ft.Alignment(0, 0),
                    ),
                    title=ft.Text(trigger.name, size=14),
                    subtitle=ft.Text(trigger.description, size=11, color=Theme.TEXT_SECONDARY),
                    on_click=lambda e, t=trigger: self._set_trigger(t.type),
                )
            )

        if hasattr(self, "page") and self.page:
            self._current_dialog = ft.AlertDialog(
                title=ft.Text("Choose a Trigger"),
                content=ft.Container(
                    content=ft.Column(controls=options, scroll=ft.ScrollMode.AUTO),
                    width=400,
                    height=300,
                ),
            )
            self.page.open(self._current_dialog)

    def _show_step_picker(self):
        """Show dialog to pick a step type."""
        categories = self.registry.categories

        tab_headers = []
        tab_contents = []
        for category in sorted(categories):
            if category == "trigger":
                continue  # Skip triggers in step picker

            nodes = self.registry.get_by_category(category)
            if not nodes:
                continue

            node_tiles = []
            for node in sorted(nodes, key=lambda n: n.name):
                icon = self._get_node_icon(node.icon)
                node_tiles.append(
                    ft.ListTile(
                        leading=ft.Container(
                            content=ft.Icon(icon, size=18, color=node.color),
                            width=32,
                            height=32,
                            bgcolor=node.color + "20",
                            border_radius=6,
                            alignment=ft.Alignment(0, 0),
                        ),
                        title=ft.Text(node.name, size=13),
                        subtitle=ft.Text(
                            node.description,
                            size=11,
                            color=Theme.TEXT_SECONDARY,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        dense=True,
                        on_click=lambda e, n=node: self._add_step(n.type),
                    )
                )

            # Add tab header (Flet 0.80+ API: Tab only has label, no content)
            tab_headers.append(ft.Tab(label=category.title()))
            # Add corresponding content
            tab_contents.append(
                ft.Container(
                    content=ft.Column(
                        controls=node_tiles,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=8,
                )
            )

        if hasattr(self, "page") and self.page:
            # Build tabs control using Flet 0.80+ pattern
            if tab_headers:
                tab_bar = ft.TabBar(tabs=tab_headers)
                tab_view = ft.TabBarView(controls=tab_contents, expand=True)
                tabs_control = ft.Tabs(
                    content=ft.Column(controls=[tab_bar, tab_view], expand=True),
                    length=len(tab_headers),
                    expand=True,
                )
            else:
                tabs_control = ft.Text("No nodes available")

            self._current_dialog = ft.AlertDialog(
                title=ft.Text("Add Step"),
                content=ft.Container(
                    content=tabs_control,
                    width=450,
                    height=350,
                ),
            )
            self.page.open(self._current_dialog)

    def _set_trigger(self, trigger_type: str):
        """Set the workflow trigger."""
        if not self.workflow:
            return

        # Get the node definition
        node_def = self.registry.get_definition(trigger_type)

        # Remove existing trigger
        old_trigger = self._get_trigger()
        if old_trigger:
            self.workflow.nodes = [n for n in self.workflow.nodes if n.id != old_trigger.id]
            # Remove connections from old trigger
            self.workflow.connections = [
                c for c in self.workflow.connections if c.source_node_id != old_trigger.id
            ]

        # Add new trigger
        new_trigger = WorkflowNode(
            id=str(uuid4()),
            type=trigger_type,
            name=node_def.name if node_def else trigger_type,
            position={"x": 100, "y": 100},
            config={
                field.name: field.default for field in node_def.inputs if field.default is not None
            }
            if node_def
            else {},
        )
        self.workflow.nodes.insert(0, new_trigger)

        # Connect trigger to first step if exists
        steps = self._get_ordered_steps()
        if steps:
            self.workflow.connections.append(
                WorkflowConnection(
                    source_node_id=new_trigger.id,
                    target_node_id=steps[0].id,
                )
            )

        # Close dialog and refresh
        if hasattr(self, "page") and self.page and self._current_dialog:
            self.page.close(self._current_dialog)
            self._current_dialog = None

        self._notify_change()
        self._refresh()

    def _add_step(self, step_type: str):
        """Add a new step to the workflow."""
        if not self.workflow:
            return

        # Get node definition
        node_def = self.registry.get_definition(step_type)

        # Calculate position
        max_y = 100
        for node in self.workflow.nodes:
            if node.position.get("y", 0) > max_y:
                max_y = node.position.get("y", 0)

        # Get the previous node BEFORE adding the new node
        # BUG FIX (01-03): Must get steps before adding new node to correctly
        # identify the previous step for connection
        existing_steps = self._get_ordered_steps()
        prev_node = existing_steps[-1] if existing_steps else None

        # Create new node
        new_node = WorkflowNode(
            id=str(uuid4()),
            type=step_type,
            name=node_def.name if node_def else step_type,
            position={"x": 100, "y": max_y + 120},
            config={
                field.name: field.default for field in node_def.inputs if field.default is not None
            }
            if node_def
            else {},
        )
        self.workflow.nodes.append(new_node)

        # Connect to previous node (or trigger if no previous steps)
        if prev_node:
            # Connect from previous step to new step
            self.workflow.connections.append(
                WorkflowConnection(
                    source_node_id=prev_node.id,
                    target_node_id=new_node.id,
                )
            )
        else:
            # Connect from trigger (first step after trigger)
            trigger = self._get_trigger()
            if trigger:
                self.workflow.connections.append(
                    WorkflowConnection(
                        source_node_id=trigger.id,
                        target_node_id=new_node.id,
                    )
                )

        # Close dialog and refresh
        if hasattr(self, "page") and self.page and self._current_dialog:
            self.page.close(self._current_dialog)
            self._current_dialog = None

        # Select the new step
        self.selected_step_index = len(self._get_ordered_steps()) - 1
        self._notify_change()
        self._refresh()

    def _select_step(self, index: int):
        """Select a step for editing."""
        self.selected_step_index = index
        self._refresh()

    def _deselect_step(self):
        """Deselect the current step."""
        self.selected_step_index = None
        self._refresh()

    def _delete_step(self, index: int):
        """Delete a step from the workflow."""
        if not self.workflow:
            return

        steps = self._get_ordered_steps()
        if 0 <= index < len(steps):
            node = steps[index]

            # Remove the node
            self.workflow.nodes = [n for n in self.workflow.nodes if n.id != node.id]

            # Reconnect: connect previous to next
            prev_node = steps[index - 1] if index > 0 else self._get_trigger()
            next_node = steps[index + 1] if index < len(steps) - 1 else None

            # Remove connections involving this node
            self.workflow.connections = [
                c
                for c in self.workflow.connections
                if c.source_node_id != node.id and c.target_node_id != node.id
            ]

            # Add new connection if needed
            if prev_node and next_node:
                self.workflow.connections.append(
                    WorkflowConnection(
                        source_node_id=prev_node.id,
                        target_node_id=next_node.id,
                    )
                )

            if self.selected_step_index == index:
                self.selected_step_index = None
            elif self.selected_step_index and self.selected_step_index > index:
                self.selected_step_index -= 1

            self._notify_change()
            self._refresh()

    def _move_step(self, index: int, direction: int):
        """Move a step up (-1) or down (+1)."""
        if not self.workflow:
            return

        steps = self._get_ordered_steps()
        new_index = index + direction

        if 0 <= new_index < len(steps):
            # This is complex for graph-based workflows
            # For now, just swap the positions
            node_a = steps[index]
            node_b = steps[new_index]

            # Swap positions
            pos_a = node_a.position.copy()
            node_a.position = node_b.position.copy()
            node_b.position = pos_a

            # Update selection
            if self.selected_step_index == index:
                self.selected_step_index = new_index

            self._notify_change()
            self._refresh()

    def _update_field(self, node: WorkflowNode, field_name: str, value):
        """Update a field value in a node."""
        node.config[field_name] = value
        self._notify_change()

    def _parse_number(self, value: str):
        """Parse a string to number."""
        try:
            if "." in value:
                return float(value)
            return int(value)
        except (ValueError, TypeError):
            return None

    def _notify_change(self):
        """Notify that the workflow has changed."""
        if self.on_change:
            self.on_change(self.workflow)

    def _refresh(self):
        """Refresh the view."""
        if self._steps_column:
            self._steps_column.controls = self._build_steps_list()
        if self._properties_container:
            self._properties_container.content = self._build_step_properties()
        if hasattr(self, "page") and self.page:
            self.page.update()
