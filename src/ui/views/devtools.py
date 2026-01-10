"""
DevTools View - GitHub AutoFixer and other developer utilities.
"""

import flet as ft
import asyncio
from src.ui.theme import Theme
from src.core.coding.fixer import FixGenerator
from src.core.coding.git_ops import GitOperations

class DevToolsView(ft.Column):
    """View for Developer Tools."""

    def __init__(self, page: ft.Page = None):
        super().__init__()
        self.page = page
        self.expand = True
        self.fixer = FixGenerator()
        self.git_ops = GitOperations("temp_repo")

        # UI Components
        self.repo_url = ft.TextField(
            label="Repository URL",
            hint_text="https://github.com/username/repo",
            height=40,
            text_size=13
        )
        self.issue_title = ft.TextField(label="Issue Title")
        self.issue_body = ft.TextField(label="Issue Description", multiline=True, min_lines=3)
        self.log_area = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.code_preview = ft.Markdown("", extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)

    def build(self):
        return ft.Column(
            controls=[
                self._build_header(),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            # Left Panel: Inputs
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text("GitHub AutoFixer", size=16, weight=ft.FontWeight.BOLD),
                                        self.repo_url,
                                        self.issue_title,
                                        self.issue_body,
                                        ft.Button(
                                            "Generate Fix",
                                            icon=ft.Icons.AUTO_FIX_HIGH,
                                            bgcolor=Theme.PRIMARY,
                                            color=Theme.TEXT_PRIMARY,
                                            on_click=self._run_autofixer
                                        ),
                                        ft.Divider(),
                                        ft.Text("Process Log", size=14, weight=ft.FontWeight.BOLD),
                                        ft.Container(
                                            content=self.log_area,
                                            bgcolor=Theme.BG_TERTIARY,
                                            border_radius=Theme.RADIUS_SM,
                                            padding=10,
                                            expand=True
                                        )
                                    ],
                                ),
                                width=400,
                                padding=Theme.SPACING_MD,
                                border=ft.Border.only(right=ft.BorderSide(1, Theme.BORDER)),
                            ),
                            # Right Panel: Preview
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text("Generated Fix Preview", size=16, weight=ft.FontWeight.BOLD),
                                        ft.Container(
                                            content=self.code_preview,
                                            expand=True,
                                            bgcolor=Theme.BG_TERTIARY,
                                            padding=10,
                                            border_radius=Theme.RADIUS_MD,
                                            border=ft.Border.all(1, Theme.BORDER)
                                        )
                                    ],
                                ),
                                expand=True,
                                padding=Theme.SPACING_MD,
                            ),
                        ],
                        expand=True,
                        spacing=0,
                    ),
                    expand=True,
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _build_header(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DEVELOPER_MODE, size=32, color=Theme.PRIMARY),
                    ft.Column(
                        controls=[
                            ft.Text(
                                "DevTools",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=Theme.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Automated coding assistance and repository tools",
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                    ),
                ],
            ),
            padding=Theme.SPACING_MD,
            border=ft.Border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
        )

    def _log(self, message: str, color: str = Theme.TEXT_PRIMARY):
        self.log_area.controls.append(ft.Text(message, color=color, size=12))
        self.page.update()

    def _run_autofixer(self, e):
        if not self.repo_url.value or not self.issue_title.value:
            self._log("Please provide Repo URL and Issue details.", Theme.ERROR)
            return

        self._log("Starting AutoFixer...", Theme.PRIMARY)
        asyncio.create_task(self._process_fix())

    async def _process_fix(self):
        try:
            # 1. Clone
            self._log(f"Cloning {self.repo_url.value}...")
            # Note: synchronous subprocess in git_ops, better to run in executor for GUI apps
            # For prototype, we'll keep it simple but in real app use run_in_executor
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(None, lambda: self.git_ops.clone_repo(self.repo_url.value))

            if not success:
                self._log("Failed to clone repository.", Theme.ERROR)
                return

            # 2. Analyze
            files = self.git_ops.get_file_list()
            self._log(f"Analyzed {len(files)} files.")

            target_file = await self.fixer.analyze_issue(
                self.issue_title.value,
                self.issue_body.value,
                files
            )

            if not target_file:
                self._log("Could not identify target file.", Theme.WARNING)
                return

            self._log(f"Target file identified: {target_file}", Theme.SUCCESS)

            # 3. Read & Fix
            content = self.git_ops.read_file(target_file)
            if not content:
                self._log("Failed to read file.", Theme.ERROR)
                return

            self._log("Generating fix with AI...", Theme.PRIMARY)
            fixed_code = await self.fixer.generate_fix(
                self.issue_title.value,
                self.issue_body.value,
                content,
                target_file
            )

            if fixed_code:
                self._log("Fix generated successfully!", Theme.SUCCESS)
                self.code_preview.value = f"```python\n{fixed_code}\n```"
                self.page.update()
            else:
                self._log("Failed to generate fix.", Theme.ERROR)

        except Exception as e:
            self._log(f"Error: {str(e)}", Theme.ERROR)
        finally:
            # Cleanup
            # self.git_ops.cleanup() # Optional: keep for review
            pass
