"""UI view components."""

from src.ui.views.ai_hub import AIHubView
from src.ui.views.credentials import CredentialsView
from src.ui.views.plugins import PluginsView
from src.ui.views.runs import RunsView
from src.ui.views.settings import SettingsView
from src.ui.views.simple_mode import SimpleModeView
from src.ui.views.workflow_editor import WorkflowEditorView
from src.ui.views.workflows import WorkflowsView

__all__ = [
    "WorkflowsView",
    "WorkflowEditorView",
    "AIHubView",
    "PluginsView",
    "RunsView",
    "SettingsView",
    "SimpleModeView",
    "CredentialsView",
]
