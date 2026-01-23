"""
Agents View - Agent Orchestrator Interface.
Visualizes and manages autonomous agent tasks.
"""

import flet as ft
import asyncio
import json
from typing import Optional

from src.ui.theme import Theme
from src.core.agents.supervisor import Supervisor, SupervisorPlan
from src.agent.loop.executor import AgentExecutor
from src.agent.models.state import AgentSession
from src.agent.models.event import AgentEvent
from src.agent.ui import AgentPanel, ApprovalSheet, AgentStatusIndicator
from src.agent.safety import get_approval_manager


class AgentsView(ft.Column):
    """View for running complex agentic tasks."""

    def __init__(self, page: ft.Page = None, app=None):
        """
        Initialize agents view.

        Args:
            page: Flet page reference
            app: Optional SkynetteApp reference for accessing agent panel
        """
        super().__init__()
        self._page = page
        self._app = app
        self.expand = True
        self.supervisor = Supervisor()
        self.is_running = False

        # Agent execution state
        self._current_executor: Optional[AgentExecutor] = None
        self._current_session: Optional[AgentSession] = None

        # UI Components
        self.input_field = ft.TextField(
            hint_text="Describe a complex task (e.g., 'Research the history of AI and summarize key milestones')",
            expand=True,
            multiline=True,
            min_lines=1,
            max_lines=4,
            border_radius=Theme.RADIUS_MD,
            on_submit=self._start_task,
        )
        self.run_btn = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            icon_color=Theme.PRIMARY,
            tooltip="Start Task",
            on_click=self._start_task,
        )
        self.results_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=Theme.SPACING_MD,
            auto_scroll=True,
        )

        # Status indicator for execution state
        self._status_indicator: Optional[AgentStatusIndicator] = None

    def build(self):
        # Create status indicator
        self._status_indicator = AgentStatusIndicator(initial_status="idle")

        return ft.Column(
            controls=[
                self._build_header(),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.results_column,
                            self._build_input_area(),
                        ],
                        expand=True,
                    ),
                    expand=True,
                    padding=Theme.SPACING_MD,
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _build_header(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.AUTO_AWESOME, size=32, color=Theme.PRIMARY),
                    ft.Column(
                        controls=[
                            ft.Text(
                                "Agent Orchestrator",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=Theme.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Autonomous multi-agent task execution",
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Container(expand=True),
                    # Add status indicator to header
                    self._status_indicator if self._status_indicator else ft.Container(),
                ],
            ),
            padding=Theme.SPACING_MD,
            border=ft.border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
        )

    def _build_input_area(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    self.input_field,
                    self.run_btn,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(top=10),
        )

    def _build_plan_card(self, plan: SupervisorPlan) -> ft.Container:
        """Build a visual representation of the agent plan."""
        steps = []
        for i, task in enumerate(plan.subtasks, 1):
            steps.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(str(i), size=12, weight=ft.FontWeight.BOLD),
                                width=24, height=24,
                                bgcolor=Theme.PRIMARY + "20",
                                border_radius=12,
                                alignment=ft.alignment.center,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(f"{task.agent_name} ({task.agent_role})", weight=ft.FontWeight.BOLD, size=13),
                                    ft.Text(task.task_description, size=12, color=Theme.TEXT_SECONDARY),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.PENDING_OUTLINED, size=16, color=Theme.TEXT_SECONDARY),
                        ],
                    ),
                    padding=8,
                    bgcolor=Theme.BG_TERTIARY,
                    border_radius=Theme.RADIUS_SM,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.MAP, size=16, color=Theme.PRIMARY),
                            ft.Text("Execution Plan", weight=ft.FontWeight.BOLD),
                        ],
                    ),
                    ft.Text(plan.plan_overview, italic=True, size=13, color=Theme.TEXT_SECONDARY),
                    ft.Divider(height=10, color="transparent"),
                    ft.Column(controls=steps, spacing=4),
                ],
                spacing=4,
            ),
            padding=16,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.border.all(1, Theme.BORDER),
        )

    def _build_result_card(self, agent_name: str, result: str, status: str) -> ft.Container:
        """Build a card for an agent's result."""
        color = Theme.SUCCESS if status == "success" else Theme.ERROR
        icon = ft.Icons.CHECK_CIRCLE if status == "success" else ft.Icons.ERROR

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SMART_TOY, size=16, color=color),
                            ft.Text(agent_name, weight=ft.FontWeight.BOLD, color=color),
                            ft.Container(expand=True),
                            ft.Icon(icon, size=16, color=color),
                        ],
                    ),
                    ft.Divider(),
                    ft.Markdown(
                        result,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    ),
                ],
            ),
            padding=16,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.border.all(1, color if status == "error" else Theme.BORDER),
        )

    def _start_task(self, e):
        if self.is_running:
            return

        prompt = self.input_field.value
        if not prompt:
            return

        self.input_field.value = ""
        self.is_running = True
        self.run_btn.disabled = True
        self.input_field.disabled = True

        # Add user message
        self.results_column.controls.append(
            ft.Container(
                content=ft.Text(prompt, size=16, weight=ft.FontWeight.W_500),
                padding=16,
                bgcolor=Theme.BG_TERTIARY,
                border_radius=Theme.RADIUS_MD,
                alignment=ft.alignment.center_right,
            )
        )
        if self._page:
            self._page.update()

        # Run with AgentExecutor (new agent loop)
        asyncio.create_task(self._run_agent_task(prompt))

    async def _run_agent_task(self, prompt: str):
        """Run task using the new AgentExecutor with panel integration."""
        try:
            # Create session and executor
            self._current_session = AgentSession(task=prompt)
            self._current_executor = AgentExecutor(self._current_session)

            # Start panel listening if app has agent panel
            panel = self._get_agent_panel()
            if panel:
                panel.start_listening(self._current_executor.emitter)

            # Add status
            loading_idx = len(self.results_column.controls)
            self.results_column.controls.append(
                ft.Row([ft.ProgressRing(width=16, height=16), ft.Text("Agent is planning...")])
            )
            if self._page:
                self._page.update()

            # Process events from executor
            async for event in self._current_executor.run(prompt):
                # Update status indicator
                if self._status_indicator:
                    self._status_indicator.update_from_event(event)

                # Remove loading indicator if present
                if len(self.results_column.controls) > loading_idx:
                    last = self.results_column.controls[-1]
                    if isinstance(last, ft.Row) and len(last.controls) > 0:
                        if isinstance(last.controls[0], ft.ProgressRing):
                            self.results_column.controls.pop()

                # Handle events
                await self._handle_agent_event(event)

                if self._page:
                    self._page.update()

            # Completion message
            self.results_column.controls.append(
                ft.Container(
                    content=ft.Text("Task completed.", color=Theme.SUCCESS, weight=ft.FontWeight.BOLD),
                    padding=10,
                    alignment=ft.alignment.center
                )
            )

        except Exception as e:
            self.results_column.controls.append(
                ft.Container(
                    content=ft.Text(f"Error: {str(e)}", color=Theme.ERROR),
                    padding=10
                )
            )

        finally:
            # Stop panel listening
            panel = self._get_agent_panel()
            if panel:
                panel.stop_listening()

            self._current_executor = None
            self._current_session = None
            self.is_running = False
            self.run_btn.disabled = False
            self.input_field.disabled = False

            # Reset status indicator
            if self._status_indicator:
                self._status_indicator.set_status("idle")

            if self._page:
                self._page.update()

    async def _handle_agent_event(self, event: AgentEvent):
        """Handle events from the agent executor."""
        if event.type == "plan_created":
            plan_data = event.data.get("plan", {})
            self.results_column.controls.append(
                self._build_agent_plan_card(plan_data)
            )
            # Add loading for execution
            self.results_column.controls.append(
                ft.Row([ft.ProgressRing(width=16, height=16), ft.Text("Agent executing steps...")])
            )

        elif event.type == "step_completed":
            step_id = event.data.get("step_id", "")
            result = event.data.get("result", {})
            self.results_column.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=Theme.SUCCESS),
                        ft.Text(f"Step completed: {step_id}", size=12),
                    ]),
                    padding=8,
                    bgcolor=Theme.BG_TERTIARY,
                    border_radius=Theme.RADIUS_SM,
                )
            )

        elif event.type == "approval_requested":
            # Show approval sheet via the approval manager
            await self._handle_approval_request(event)

        elif event.type == "error":
            error_msg = event.data.get("message", event.data.get("error", "Unknown error"))
            self.results_column.controls.append(
                ft.Container(
                    content=ft.Text(f"Error: {error_msg}", color=Theme.ERROR),
                    padding=10
                )
            )

    async def _handle_approval_request(self, event: AgentEvent):
        """Handle approval request by showing ApprovalSheet."""
        approval_manager = get_approval_manager()

        # Get pending request
        pending = approval_manager.get_pending()
        if not pending:
            return

        request = pending[0]

        # Create event for completion signaling
        approval_complete = asyncio.Event()
        approval_result = {"approved": False, "approve_similar": False}

        def on_approve(approve_similar: bool, modified_params=None, remember_scope=None):
            approval_result["approved"] = True
            approval_result["approve_similar"] = approve_similar
            approval_manager.resolve(
                request.id,
                decision="approved",
                approve_similar=approve_similar,
            )
            approval_complete.set()

        def on_reject():
            approval_result["approved"] = False
            approval_manager.resolve(
                request.id,
                decision="rejected",
            )
            approval_complete.set()

        # Show approval sheet
        sheet = ApprovalSheet(
            request=request,
            on_approve=on_approve,
            on_reject=on_reject,
            detail_level="detailed",
            approval_manager=approval_manager,
        )

        if self._page:
            sheet.show(self._page)

        # Wait for user decision (with timeout handling by ApprovalManager)
        try:
            await asyncio.wait_for(approval_complete.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            # Close sheet on timeout
            sheet.hide()
            approval_manager.resolve(request.id, decision="timeout")

    def _build_agent_plan_card(self, plan_data: dict) -> ft.Container:
        """Build a card for the agent plan."""
        overview = plan_data.get("overview", "")
        steps = plan_data.get("steps", [])

        step_controls = []
        for i, step in enumerate(steps, 1):
            description = step.get("description", "")
            tool_name = step.get("tool_name", "")
            status = step.get("status", "pending")

            step_controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(str(i), size=12, weight=ft.FontWeight.BOLD),
                                width=24, height=24,
                                bgcolor=Theme.PRIMARY + "20",
                                border_radius=12,
                                alignment=ft.alignment.center,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(description, weight=ft.FontWeight.W_500, size=13),
                                    ft.Text(
                                        f"Tool: {tool_name}" if tool_name else "Reasoning step",
                                        size=11,
                                        color=Theme.TEXT_SECONDARY,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(
                                ft.Icons.PENDING_OUTLINED if status == "pending"
                                else ft.Icons.CHECK_CIRCLE if status == "completed"
                                else ft.Icons.ERROR,
                                size=16,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                    ),
                    padding=8,
                    bgcolor=Theme.BG_TERTIARY,
                    border_radius=Theme.RADIUS_SM,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.MAP, size=16, color=Theme.PRIMARY),
                            ft.Text("Execution Plan", weight=ft.FontWeight.BOLD),
                        ],
                    ),
                    ft.Text(overview, italic=True, size=13, color=Theme.TEXT_SECONDARY) if overview else ft.Container(),
                    ft.Divider(height=10, color="transparent"),
                    ft.Column(controls=step_controls, spacing=4),
                ],
                spacing=4,
            ),
            padding=16,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.border.all(1, Theme.BORDER),
        )

    def _get_agent_panel(self) -> Optional[AgentPanel]:
        """Get agent panel from app if available."""
        if self._app and hasattr(self._app, 'get_agent_panel'):
            return self._app.get_agent_panel()
        return None

    async def _run_supervisor(self, prompt: str):
        """Legacy: Run task using Supervisor (kept for compatibility)."""
        try:
            # Add status
            loading_idx = len(self.results_column.controls)
            self.results_column.controls.append(
                ft.Row([ft.ProgressRing(width=16, height=16), ft.Text("Supervisor is planning...")])
            )
            if self._page:
                self._page.update()

            # Execute
            async for event in self.supervisor.execute(prompt):
                # Remove loading if present
                if len(self.results_column.controls) > loading_idx:
                    if isinstance(self.results_column.controls[-1], ft.Row):
                        self.results_column.controls.pop()

                if event["type"] == "plan":
                    plan = event["data"]
                    self.results_column.controls.append(self._build_plan_card(plan))
                    self.results_column.controls.append(
                        ft.Row([ft.ProgressRing(width=16, height=16), ft.Text("Agents executing tasks...")])
                    )

                elif event["type"] == "result":
                    # Check if loading indicator is last, remove it temporarily to append result
                    has_loading = False
                    if self.results_column.controls and isinstance(self.results_column.controls[-1], ft.Row):
                        self.results_column.controls.pop()
                        has_loading = True

                    result_data = event["data"]
                    self.results_column.controls.append(
                        self._build_result_card(
                            result_data.agent_name,
                            result_data.result,
                            result_data.status
                        )
                    )

                    if has_loading:
                        self.results_column.controls.append(
                            ft.Row([ft.ProgressRing(width=16, height=16), ft.Text("Agents executing tasks...")])
                        )

                if self._page:
                    self._page.update()

            # Final cleanup of loading
            if self.results_column.controls and isinstance(self.results_column.controls[-1], ft.Row):
                self.results_column.controls.pop()

            self.results_column.controls.append(
                ft.Container(
                    content=ft.Text("All tasks completed.", color=Theme.SUCCESS, weight=ft.FontWeight.BOLD),
                    padding=10,
                    alignment=ft.alignment.center
                )
            )

        except Exception as e:
            self.results_column.controls.append(
                ft.Container(
                    content=ft.Text(f"Error: {str(e)}", color=Theme.ERROR),
                    padding=10
                )
            )

        finally:
            self.is_running = False
            self.run_btn.disabled = False
            self.input_field.disabled = False
            if self._page:
                self._page.update()
