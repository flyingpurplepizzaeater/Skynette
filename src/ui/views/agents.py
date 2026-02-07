"""
Agents View - Agent Orchestrator Interface.
Visualizes and manages autonomous agent tasks.
"""

import flet as ft
import asyncio
import json
from src.ui.theme import Theme
from src.core.agents.supervisor import Supervisor, SupervisorPlan

class AgentsView(ft.Column):
    """View for running complex agentic tasks."""

    def __init__(self, page: ft.Page = None):
        super().__init__()
        self._page = page
        self.expand = True
        self.supervisor = Supervisor()
        self.is_running = False

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

    def build(self):
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
                                alignment=ft.Alignment.CENTER,
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
                alignment=ft.Alignment.CENTER_right,
            )
        )
        if self._page:
            self._page.update()

        asyncio.create_task(self._run_supervisor(prompt))

    async def _run_supervisor(self, prompt: str):
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
                    alignment=ft.Alignment.CENTER
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
