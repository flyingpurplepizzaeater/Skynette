# Phase 4 Sprint 2: AI Hub UI & Model Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Build complete AI Hub interface with provider setup wizard, model library, and AI node integration into the visual workflow editor.

**Architecture:** Enhance existing AIHubView with interactive setup wizard, dynamic provider management, and comprehensive model download UI. Integrate AI nodes into canvas node palette with dedicated "AI" category. Add provider status bar to main app for quick access.

**Tech Stack:** Flet (Python UI), SQLite (via AIStorage), system keyring (API keys), Hugging Face API (model downloads)

**Current State:**
- ✅ AIHubView exists with 3-tab skeleton (My Models, Download, Providers)
- ✅ 5 AI nodes implemented (text_generation, chat, summarize, extract, classify)
- ✅ AI nodes have category="AI", color="#8B5CF6", icon="auto_awesome"
- ✅ ModelHub service exists for downloads
- ✅ AIStorage, API key security, cost tracking (Sprint 1)
- ❌ No setup wizard flow
- ❌ Provider configuration not wired to storage/security
- ❌ AI nodes not visible in node palette
- ❌ No provider status bar
- ❌ No E2E tests for AI Hub

---

## Task 1: Setup Wizard Structure & Navigation

**Files:**
- Modify: `src/ui/views/ai_hub.py:21-48` (_build method and tabs)
- Create: `tests/e2e/test_ai_hub_wizard.py`

**Step 1: Write failing test for wizard tab visibility**

```python
def test_wizard_tab_exists(page: ft.Page):
    """Test that setup wizard tab is visible."""
    ai_hub = AIHubView(page=page)
    view = ai_hub.build()

    # Find tabs
    tabs = _find_tabs_control(view)
    tab_texts = [tab.text for tab in tabs.tabs]

    assert "Setup" in tab_texts
    assert "My Providers" in tab_texts
    assert "Model Library" in tab_texts
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/e2e/test_ai_hub_wizard.py::test_wizard_tab_exists -v`
Expected: FAIL with "Setup" not in tab_texts

**Step 3: Add Setup tab to AIHubView**

In `src/ui/views/ai_hub.py`, modify `build()` method line 21:

```python
def build(self):
    self.wizard_content = self._build_wizard_tab()
    self.providers_management = self._build_providers_tab()

    return ft.Column(
        controls=[
            self._build_header(),
            ft.Tabs(
                tabs=[
                    ft.Tab(
                        text="Setup",
                        icon=ft.Icons.ROCKET_LAUNCH,
                        content=self.wizard_content,
                    ),
                    ft.Tab(
                        text="My Providers",
                        icon=ft.Icons.CLOUD,
                        content=self.providers_management,
                    ),
                    ft.Tab(
                        text="Model Library",
                        icon=ft.Icons.FOLDER,
                        content=self._build_model_library_tab(),
                    ),
                ],
                expand=True,
            ),
        ],
        expand=True,
        spacing=Theme.SPACING_MD,
    )

def _build_wizard_tab(self):
    """Build setup wizard tab (Step 1: Provider Selection)."""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Setup Wizard - Coming Soon", size=18),
            ],
        ),
        padding=Theme.SPACING_MD,
        expand=True,
    )

def _build_model_library_tab(self):
    """Combine installed and download tabs into model library."""
    return ft.Column(
        controls=[
            ft.Tabs(
                tabs=[
                    ft.Tab(text="My Models", content=self._build_installed_tab()),
                    ft.Tab(text="Download", content=self._build_download_tab()),
                ],
            ),
        ],
        expand=True,
    )
```

Also rename existing `_build_providers_tab` to return provider management UI (not wizard):

```python
# Update line 356 method name comment
def _build_providers_tab(self):
    """Build My Providers management tab."""
    # ... existing provider cards code ...
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/e2e/test_ai_hub_wizard.py::test_wizard_tab_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ui/views/ai_hub.py tests/e2e/test_ai_hub_wizard.py
git commit -m "feat(ai-ui): add Setup wizard tab to AI Hub

- Added Setup tab with icon and placeholder
- Reorganized tabs: Setup, My Providers, Model Library
- Model Library now contains My Models + Download subtabs

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Wizard Step 1 - Provider Selection

**Files:**
- Modify: `src/ui/views/ai_hub.py:_build_wizard_tab`
- Modify: `tests/e2e/test_ai_hub_wizard.py`

**Step 1: Write failing test for provider checkboxes**

```python
def test_wizard_shows_provider_checkboxes(page: ft.Page):
    """Test wizard displays provider selection checkboxes."""
    ai_hub = AIHubView(page=page)
    wizard = ai_hub._build_wizard_tab()

    # Find checkboxes
    checkboxes = _find_controls_by_type(wizard, ft.Checkbox)
    checkbox_labels = [cb.label for cb in checkboxes]

    assert "OpenAI" in checkbox_labels
    assert "Anthropic" in checkbox_labels
    assert "Local Models" in checkbox_labels
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/e2e/test_ai_hub_wizard.py::test_wizard_shows_provider_checkboxes -v`
Expected: FAIL with "checkboxes not found"

**Step 3: Implement provider selection UI**

Replace `_build_wizard_tab` in `src/ui/views/ai_hub.py`:

```python
def __init__(self, page: ft.Page = None):
    super().__init__()
    self.page = page
    self.expand = True
    self.hub = get_hub()
    self.download_cards: dict[str, ft.Container] = {}
    self.installed_list = None
    self.recommended_list = None

    # Wizard state
    self.wizard_step = 0
    self.selected_providers = []
    self.provider_configs = {}

def _build_wizard_tab(self):
    """Build setup wizard tab."""
    if self.wizard_step == 0:
        return self._build_wizard_step1_provider_selection()
    else:
        return ft.Container(content=ft.Text("Other steps TBD"))

def _build_wizard_step1_provider_selection(self):
    """Step 1: Select AI providers to configure."""
    providers = [
        {
            "id": "openai",
            "name": "OpenAI",
            "description": "GPT-4, GPT-3.5 Turbo",
            "cost": "$$$",
            "type": "Cloud • Requires API key",
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "description": "Claude 3 Opus, Sonnet, Haiku",
            "cost": "$$",
            "type": "Cloud • Requires API key",
        },
        {
            "id": "local",
            "name": "Local Models",
            "description": "llama.cpp - Run models on your computer",
            "cost": "Free",
            "type": "Private • No API key needed",
        },
    ]

    def on_provider_checked(e, provider_id):
        if e.control.value:
            if provider_id not in self.selected_providers:
                self.selected_providers.append(provider_id)
        else:
            if provider_id in self.selected_providers:
                self.selected_providers.remove(provider_id)

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "Welcome to Skynette AI Setup",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=Theme.TEXT_PRIMARY,
                ),
                ft.Text(
                    "Select which AI providers you want to use:",
                    size=14,
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Container(height=Theme.SPACING_LG),
                *[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Checkbox(
                                    label=p["name"],
                                    value=p["id"] in self.selected_providers,
                                    on_change=lambda e, pid=p["id"]: on_provider_checked(e, pid),
                                ),
                                ft.Container(expand=True),
                                ft.Column(
                                    controls=[
                                        ft.Text(p["description"], size=12, color=Theme.TEXT_SECONDARY),
                                        ft.Text(
                                            f"{p['type']} • {p['cost']}",
                                            size=11,
                                            color=Theme.TEXT_MUTED,
                                        ),
                                    ],
                                    spacing=2,
                                ),
                            ],
                        ),
                        bgcolor=Theme.SURFACE,
                        padding=Theme.SPACING_MD,
                        border_radius=Theme.RADIUS_MD,
                        border=ft.border.all(1, Theme.BORDER),
                    )
                    for p in providers
                ],
                ft.Container(expand=True),
                ft.Row(
                    controls=[
                        ft.TextButton("Skip Setup", on_click=lambda e: self._skip_wizard()),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Next: Configure →",
                            bgcolor=Theme.PRIMARY,
                            on_click=lambda e: self._wizard_next_step(),
                            disabled=len(self.selected_providers) == 0,
                        ),
                    ],
                ),
            ],
            spacing=Theme.SPACING_SM,
        ),
        padding=Theme.SPACING_LG,
        expand=True,
    )

def _wizard_next_step(self):
    """Advance wizard to next step."""
    self.wizard_step += 1
    if self.page:
        self.page.update()

def _skip_wizard(self):
    """Skip wizard and go to providers tab."""
    # Switch to My Providers tab (index 1)
    if self.page:
        # TODO: Implement tab switching
        pass
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/e2e/test_ai_hub_wizard.py::test_wizard_shows_provider_checkboxes -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ui/views/ai_hub.py tests/e2e/test_ai_hub_wizard.py
git commit -m "feat(ai-ui): implement wizard step 1 - provider selection

- Provider checkboxes for OpenAI, Anthropic, Local Models
- Dynamic selection tracking
- Skip/Next navigation buttons
- Provider descriptions with cost indicators

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Wizard Step 2 - Provider Configuration

**Files:**
- Modify: `src/ui/views/ai_hub.py:_build_wizard_tab`
- Modify: `tests/e2e/test_ai_hub_wizard.py`

**Step 1: Write failing test for API key input**

```python
def test_wizard_step2_shows_api_key_input(page: ft.Page):
    """Test step 2 shows API key configuration for selected providers."""
    ai_hub = AIHubView(page=page)
    ai_hub.selected_providers = ["openai"]
    ai_hub.wizard_step = 1

    wizard = ai_hub._build_wizard_tab()

    # Find API key field
    textfields = _find_controls_by_type(wizard, ft.TextField)
    assert any("API Key" in str(tf.label) for tf in textfields)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/e2e/test_ai_hub_wizard.py::test_wizard_step2_shows_api_key_input -v`
Expected: FAIL

**Step 3: Implement provider configuration UI**

Update `_build_wizard_tab` in `src/ui/views/ai_hub.py`:

```python
def _build_wizard_tab(self):
    """Build setup wizard tab."""
    if self.wizard_step == 0:
        return self._build_wizard_step1_provider_selection()
    elif self.wizard_step == 1:
        return self._build_wizard_step2_configure_providers()
    else:
        return ft.Container(content=ft.Text("Other steps TBD"))

def _build_wizard_step2_configure_providers(self):
    """Step 2: Configure selected providers."""
    if not self.selected_providers:
        # No providers selected, skip to step 3
        self.wizard_step = 2
        return self._build_wizard_tab()

    # Configure first provider in list
    provider_id = self.selected_providers[0]
    provider_names = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "local": "Local Models",
    }

    provider_name = provider_names.get(provider_id, provider_id)

    # For local provider, no API key needed
    if provider_id == "local":
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Configure {provider_name}",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "Local models run on your computer. No API key required!",
                        size=14,
                        color=Theme.SUCCESS,
                    ),
                    ft.Container(height=Theme.SPACING_LG),
                    ft.Text("Local models will be available after downloading them in the Model Library."),
                    ft.Container(expand=True),
                    ft.Row(
                        controls=[
                            ft.TextButton("← Back", on_click=lambda e: self._wizard_prev_step()),
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                "Next →",
                                bgcolor=Theme.PRIMARY,
                                on_click=lambda e: self._wizard_next_step(),
                            ),
                        ],
                    ),
                ],
            ),
            padding=Theme.SPACING_LG,
            expand=True,
        )

    # Cloud providers need API key
    api_key_field = ft.TextField(
        label="API Key",
        password=True,
        can_reveal_password=True,
        hint_text=f"Enter your {provider_name} API key",
        on_change=lambda e: self._update_provider_config(provider_id, "api_key", e.control.value),
    )

    test_button = ft.ElevatedButton(
        "Test Connection",
        icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
        on_click=lambda e: self._test_provider_connection(provider_id),
    )

    status_text = ft.Text("", size=12)

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    f"Configure {provider_name}",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(height=Theme.SPACING_MD),
                api_key_field,
                ft.Container(height=Theme.SPACING_SM),
                test_button,
                status_text,
                ft.Container(expand=True),
                ft.Row(
                    controls=[
                        ft.TextButton("← Back", on_click=lambda e: self._wizard_prev_step()),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Next →",
                            bgcolor=Theme.PRIMARY,
                            on_click=lambda e: self._wizard_next_step(),
                        ),
                    ],
                ),
            ],
        ),
        padding=Theme.SPACING_LG,
        expand=True,
    )

def _wizard_prev_step(self):
    """Go back to previous wizard step."""
    if self.wizard_step > 0:
        self.wizard_step -= 1
    if self.page:
        self.page.update()

def _update_provider_config(self, provider_id: str, key: str, value: str):
    """Update provider configuration."""
    if provider_id not in self.provider_configs:
        self.provider_configs[provider_id] = {}
    self.provider_configs[provider_id][key] = value

def _test_provider_connection(self, provider_id: str):
    """Test provider connection (mock for now)."""
    # TODO: Implement actual API test
    print(f"Testing {provider_id} connection...")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/e2e/test_ai_hub_wizard.py::test_wizard_step2_shows_api_key_input -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ui/views/ai_hub.py tests/e2e/test_ai_hub_wizard.py
git commit -m "feat(ai-ui): implement wizard step 2 - provider configuration

- API key input with show/hide toggle
- Test connection button
- Back/Next navigation
- Special handling for local provider (no API key)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Wizard Step 3 - Recommended Model & Completion

**Files:**
- Modify: `src/ui/views/ai_hub.py:_build_wizard_tab`
- Modify: `tests/e2e/test_ai_hub_wizard.py`

**Step 1: Write failing test for completion**

```python
def test_wizard_step3_shows_completion(page: ft.Page):
    """Test step 3 shows completion summary."""
    ai_hub = AIHubView(page=page)
    ai_hub.selected_providers = ["openai"]
    ai_hub.wizard_step = 2

    wizard = ai_hub._build_wizard_tab()

    # Find completion text
    assert "Setup Complete" in str(wizard.content)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/e2e/test_ai_hub_wizard.py::test_wizard_step3_shows_completion -v`
Expected: FAIL

**Step 3: Implement completion screen**

Update `_build_wizard_tab` in `src/ui/views/ai_hub.py`:

```python
def _build_wizard_tab(self):
    """Build setup wizard tab."""
    if self.wizard_step == 0:
        return self._build_wizard_step1_provider_selection()
    elif self.wizard_step == 1:
        return self._build_wizard_step2_configure_providers()
    elif self.wizard_step == 2:
        return self._build_wizard_step3_completion()
    else:
        return ft.Container(content=ft.Text("Setup complete!"))

def _build_wizard_step3_completion(self):
    """Step 3: Setup completion and summary."""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE,
                    size=64,
                    color=Theme.SUCCESS,
                ),
                ft.Text(
                    "Setup Complete!",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=Theme.TEXT_PRIMARY,
                ),
                ft.Text(
                    f"Configured {len(self.selected_providers)} AI provider(s)",
                    size=14,
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Container(height=Theme.SPACING_LG),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "What's Next:",
                                size=16,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text("• Download local models in Model Library tab"),
                            ft.Text("• Add AI nodes to your workflows"),
                            ft.Text("• Monitor usage and costs in Dashboard"),
                        ],
                        spacing=8,
                    ),
                    bgcolor=Theme.SURFACE,
                    padding=Theme.SPACING_MD,
                    border_radius=Theme.RADIUS_MD,
                ),
                ft.Container(expand=True),
                ft.Row(
                    controls=[
                        ft.TextButton("← Back", on_click=lambda e: self._wizard_prev_step()),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Get Started",
                            bgcolor=Theme.SUCCESS,
                            on_click=lambda e: self._complete_wizard(),
                        ),
                    ],
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Theme.SPACING_SM,
        ),
        padding=Theme.SPACING_LG,
        expand=True,
    )

def _complete_wizard(self):
    """Complete wizard and save configurations."""
    from src.ai.security import store_api_key
    from src.ai.storage import AIStorage
    from src.data.storage import get_storage

    # Save API keys to system keyring
    for provider_id, config in self.provider_configs.items():
        if "api_key" in config:
            try:
                store_api_key(provider_id, config["api_key"])
            except Exception as e:
                print(f"Failed to store API key for {provider_id}: {e}")

    # Save provider configurations to database
    storage = get_storage()
    ai_storage = AIStorage(db_path=storage.db_path)

    # Mark wizard as completed
    storage.set_setting("ai_wizard_completed", "true")

    # Reset wizard state
    self.wizard_step = 0
    self.selected_providers = []
    self.provider_configs = {}

    # Navigate to My Providers tab
    if self.page:
        # TODO: Switch to tab 1 (My Providers)
        self.page.update()
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/e2e/test_ai_hub_wizard.py::test_wizard_step3_shows_completion -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ui/views/ai_hub.py tests/e2e/test_ai_hub_wizard.py
git commit -m "feat(ai-ui): implement wizard step 3 - completion

- Completion screen with success icon
- Summary of configured providers
- What's next guidance
- Save API keys to system keyring
- Mark wizard as completed in settings

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Provider Management - Dynamic Status Display

**Files:**
- Modify: `src/ui/views/ai_hub.py:_build_providers_tab`
- Create: `tests/e2e/test_ai_providers.py`

**Step 1: Write failing test for provider status**

```python
async def test_providers_show_configured_status(page: ft.Page):
    """Test providers display correct status based on stored config."""
    from src.ai.security import store_api_key

    # Set up - store API key for OpenAI
    store_api_key("openai", "sk-test123")

    ai_hub = AIHubView(page=page)
    providers_tab = ai_hub._build_providers_tab()

    # Find OpenAI provider card
    # Should show "Configured" status
    assert "Configured" in str(providers_tab.content)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/e2e/test_ai_providers.py::test_providers_show_configured_status -v`
Expected: FAIL (hardcoded "Not configured")

**Step 3: Wire providers tab to read from storage**

Replace `_build_providers_tab` in `src/ui/views/ai_hub.py`:

```python
def _build_providers_tab(self):
    """Build My Providers management tab."""
    from src.ai.security import has_api_key
    from src.data.storage import get_storage

    storage = get_storage()

    # Check which providers are configured
    providers_data = [
        {
            "id": "openai",
            "name": "OpenAI",
            "icon": ft.Icons.CLOUD,
            "color": "#10a37f",
            "requires_key": True,
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "icon": ft.Icons.CLOUD,
            "color": "#d4a574",
            "requires_key": True,
        },
        {
            "id": "local",
            "name": "Local (llama.cpp)",
            "icon": ft.Icons.COMPUTER,
            "color": Theme.SUCCESS,
            "requires_key": False,
        },
    ]

    provider_cards = []
    for p in providers_data:
        # Check if configured
        if p["requires_key"]:
            configured = has_api_key(p["id"])
            status = "Configured ✓" if configured else "Not configured"
            status_color = Theme.SUCCESS if configured else Theme.TEXT_SECONDARY
            button_text = "Edit" if configured else "Configure"
            button_color = Theme.SURFACE if configured else Theme.PRIMARY
        else:
            configured = True
            status = "Ready (no key required)"
            status_color = Theme.SUCCESS
            button_text = "Settings"
            button_color = Theme.SURFACE

        provider_cards.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(p["icon"], size=24, color=p["color"]),
                        ft.Column(
                            controls=[
                                ft.Text(p["name"], size=14, weight=ft.FontWeight.W_500),
                                ft.Text(status, size=12, color=status_color),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.ElevatedButton(
                            button_text,
                            bgcolor=button_color,
                            on_click=lambda e, provider=p: self._open_provider_config_dialog(provider),
                        ),
                    ],
                    spacing=Theme.SPACING_MD,
                ),
                bgcolor=Theme.SURFACE,
                padding=Theme.SPACING_MD,
                border_radius=Theme.RADIUS_MD,
                border=ft.border.all(1, Theme.BORDER),
            )
        )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "My AI Providers",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=Theme.TEXT_PRIMARY,
                ),
                ft.Text(
                    "Manage API keys and provider settings",
                    size=12,
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Container(height=Theme.SPACING_MD),
                *provider_cards,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=Theme.SPACING_SM,
        ),
        padding=Theme.SPACING_MD,
        expand=True,
    )

def _open_provider_config_dialog(self, provider: dict):
    """Open provider configuration dialog."""
    # TODO: Implement modal dialog
    print(f"Opening config for: {provider['name']}")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/e2e/test_ai_providers.py::test_providers_show_configured_status -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ui/views/ai_hub.py tests/e2e/test_ai_providers.py
git commit -m "feat(ai-ui): dynamic provider status in My Providers tab

- Read API key status from system keyring
- Show Configured/Not configured status
- Different button text for configured vs unconfigured
- Visual status colors

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Provider Configuration Dialog

**Files:**
- Modify: `src/ui/views/ai_hub.py:_open_provider_config_dialog`
- Modify: `tests/e2e/test_ai_providers.py`

**Step 1: Write failing test for config dialog**

```python
def test_provider_config_dialog_opens(page: ft.Page):
    """Test provider configuration dialog can open."""
    ai_hub = AIHubView(page=page)
    provider = {"id": "openai", "name": "OpenAI", "requires_key": True}

    dialog = ai_hub._build_provider_config_dialog(provider)

    assert dialog is not None
    assert "OpenAI" in str(dialog.title)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/e2e/test_ai_providers.py::test_provider_config_dialog_opens -v`
Expected: FAIL (method not defined)

**Step 3: Implement provider configuration dialog**

Add to `src/ui/views/ai_hub.py`:

```python
def _open_provider_config_dialog(self, provider: dict):
    """Open provider configuration dialog."""
    dialog = self._build_provider_config_dialog(provider)
    if self.page:
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

def _build_provider_config_dialog(self, provider: dict):
    """Build provider configuration dialog."""
    from src.ai.security import get_api_key, store_api_key, delete_api_key

    # Get existing API key if configured
    existing_key = get_api_key(provider["id"]) if provider.get("requires_key") else None
    masked_key = f"{existing_key[:8]}...{existing_key[-4:]}" if existing_key else ""

    api_key_field = ft.TextField(
        label="API Key",
        password=True,
        can_reveal_password=True,
        value=existing_key or "",
        hint_text="Enter your API key",
    )

    status_text = ft.Text("", size=12)

    def save_config(e):
        """Save provider configuration."""
        try:
            api_key = api_key_field.value
            if api_key:
                store_api_key(provider["id"], api_key)
                status_text.value = "✓ API key saved successfully"
                status_text.color = Theme.SUCCESS
            else:
                delete_api_key(provider["id"])
                status_text.value = "API key removed"
                status_text.color = Theme.TEXT_SECONDARY

            if self.page:
                self.page.update()
                # Refresh providers tab
                # Close dialog after 1 second
                import time
                time.sleep(1)
                close_dialog(e)
        except Exception as ex:
            status_text.value = f"Error: {ex}"
            status_text.color = Theme.ERROR
            if self.page:
                self.page.update()

    def close_dialog(e):
        """Close the dialog."""
        if self.page:
            dialog.open = False
            self.page.update()
            # Rebuild providers tab to show updated status
            # (Parent will handle this)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(f"Configure {provider['name']}"),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "API Key Configuration",
                        size=14,
                        weight=ft.FontWeight.W_600,
                    ),
                    api_key_field,
                    ft.Container(height=4),
                    ft.Text(
                        "Your API key is stored securely in your system keyring.",
                        size=11,
                        color=Theme.TEXT_MUTED,
                        italic=True,
                    ),
                    ft.Container(height=8),
                    status_text,
                ],
                tight=True,
            ),
            width=400,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.ElevatedButton("Save", bgcolor=Theme.PRIMARY, on_click=save_config),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    return dialog
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/e2e/test_ai_providers.py::test_provider_config_dialog_opens -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ui/views/ai_hub.py tests/e2e/test_ai_providers.py
git commit -m "feat(ai-ui): provider configuration dialog

- Modal dialog for API key management
- Masked display of existing keys
- Save to system keyring
- Delete API key option
- Success/error feedback

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: AI Nodes in Node Palette

**Files:**
- Modify: `src/ui/app.py` (node palette section around line 1560)
- Create: `tests/e2e/test_ai_node_palette.py`

**Step 1: Write failing test for AI category**

```python
def test_node_palette_has_ai_category(page: ft.Page):
    """Test node palette displays AI category."""
    from src.ui.app import WorkflowApp

    app = WorkflowApp(page)
    # Navigate to workflow editor
    # Check node palette for "AI" category

    palette = app._get_node_palette()
    categories = [cat for cat in palette if "AI" in str(cat)]

    assert len(categories) > 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/e2e/test_ai_node_palette.py::test_node_palette_has_ai_category -v`
Expected: FAIL (AI category not visible)

**Step 3: Ensure AI nodes appear in palette**

In `src/ui/app.py`, find the node palette building section (around line 1560). The code should already register AI nodes via NodeRegistry. Verify AI category appears:

```python
# Around line 1560 in _build_advanced_editor
# Build node palette
node_categories = {}
for node_type, node_class in registry.get_all_nodes().items():
    node_def = node_class.get_definition()
    cat = node_def.category or "other"
    if cat not in node_categories:
        node_categories[cat] = []
    node_categories[cat].append((node_type, node_def))

# Ensure AI category is present and styled
category_order = ["Triggers", "AI", "Actions", "Flow", "Data", "Other"]
```

Add AI category styling to color map (around line 2142):

```python
# Determine color by category
color_map = {
    "trigger": Theme.WARNING,
    "action": Theme.PRIMARY,
    "ai": "#8B5CF6",  # Violet for AI nodes
    "flow": Theme.INFO,
}
color = color_map.get(node_def.category.lower() if node_def and node_def.category else "action", Theme.PRIMARY)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/e2e/test_ai_node_palette.py::test_node_palette_has_ai_category -v`
Expected: PASS

**Step 5: Write test for AI nodes visibility**

```python
def test_ai_nodes_visible_in_palette(page: ft.Page):
    """Test all 5 AI nodes appear in AI category."""
    from src.ui.app import WorkflowApp

    app = WorkflowApp(page)
    palette = app._get_node_palette()

    ai_nodes = _find_nodes_in_category(palette, "AI")
    node_names = [n.name for n in ai_nodes]

    assert "AI Text Generation" in node_names
    assert "AI Chat" in node_names
    assert "AI Summarize" in node_names
    assert "AI Extract" in node_names
    assert "AI Classify" in node_names
```

**Step 6: Run test to verify it passes**

Run: `python -m pytest tests/e2e/test_ai_node_palette.py::test_ai_nodes_visible_in_palette -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/ui/app.py tests/e2e/test_ai_node_palette.py
git commit -m "feat(ai-ui): add AI nodes to node palette

- AI category in node palette
- Violet color (#8B5CF6) for AI nodes
- All 5 AI nodes visible and draggable
- Category ordering: Triggers, AI, Actions, Flow, Data

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Provider Status Bar in Main App

**Files:**
- Modify: `src/ui/app.py` (main layout, top bar area)
- Create: `tests/e2e/test_provider_status_bar.py`

**Step 1: Write failing test for status bar**

```python
def test_provider_status_bar_visible(page: ft.Page):
    """Test provider status bar appears in main app."""
    from src.ui.app import WorkflowApp

    app = WorkflowApp(page)

    # Find status bar
    status_bar = _find_provider_status_bar(app)
    assert status_bar is not None
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/e2e/test_provider_status_bar.py::test_provider_status_bar_visible -v`
Expected: FAIL (not found)

**Step 3: Add provider status bar to main app**

In `src/ui/app.py`, add status bar to top bar (around line 266 `_build_top_bar`):

```python
def _build_top_bar(self):
    """Build the top bar with title and actions."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    "Skynette",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=Theme.TEXT_PRIMARY,
                ),
                ft.Container(expand=True),
                self._build_provider_status_bar(),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    icon_color=Theme.TEXT_SECONDARY,
                    tooltip="Settings",
                    on_click=lambda e: self._navigate_to_page("settings"),
                ),
            ],
        ),
        padding=ft.padding.only(left=16, right=16, top=8, bottom=8),
        bgcolor=Theme.SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
    )

def _build_provider_status_bar(self):
    """Build provider status indicator."""
    from src.ai.security import has_api_key

    # Count configured providers
    providers = ["openai", "anthropic"]
    configured_count = sum(1 for p in providers if has_api_key(p))

    # Always count local as available
    total_available = configured_count + 1

    if total_available == 0:
        icon_color = Theme.TEXT_MUTED
        tooltip = "No AI providers configured"
    elif configured_count == 0:
        icon_color = Theme.WARNING
        tooltip = f"{total_available} provider available (Local only)"
    else:
        icon_color = Theme.SUCCESS
        tooltip = f"{total_available} providers available"

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.CLOUD_DONE if total_available > 1 else ft.Icons.COMPUTER,
                    size=16,
                    color=icon_color,
                ),
                ft.Text(
                    f"{total_available} AI",
                    size=12,
                    color=icon_color,
                ),
            ],
            spacing=4,
        ),
        tooltip=tooltip,
        on_click=lambda e: self._navigate_to_page("ai_hub"),
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=12,
        bgcolor=Theme.SURFACE_VARIANT,
    )
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/e2e/test_provider_status_bar.py::test_provider_status_bar_visible -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ui/app.py tests/e2e/test_provider_status_bar.py
git commit -m "feat(ai-ui): add provider status bar to main app

- Shows count of available AI providers
- Click to open AI Hub
- Visual indicator (green=configured, yellow=local only, gray=none)
- Tooltip with details

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Model Library - System Requirements Detection

**Files:**
- Create: `src/ai/system_info.py`
- Create: `tests/unit/test_system_info.py`
- Modify: `src/ui/views/ai_hub.py:_build_recommended_model_card`

**Step 1: Write failing test for RAM detection**

```python
def test_detect_available_ram():
    """Test RAM detection returns value in GB."""
    from src.ai.system_info import get_available_ram_gb

    ram_gb = get_available_ram_gb()

    assert ram_gb > 0
    assert isinstance(ram_gb, (int, float))
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_system_info.py::test_detect_available_ram -v`
Expected: FAIL (module not found)

**Step 3: Implement system info detection**

Create `src/ai/system_info.py`:

```python
"""System information detection for AI model requirements."""

import platform
import psutil


def get_available_ram_gb() -> float:
    """Get available RAM in gigabytes."""
    try:
        mem = psutil.virtual_memory()
        return mem.total / (1024 ** 3)
    except Exception:
        return 0.0


def has_cuda() -> bool:
    """Check if CUDA GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def get_system_info() -> dict:
    """Get comprehensive system information."""
    return {
        "ram_gb": get_available_ram_gb(),
        "has_cuda": has_cuda(),
        "platform": platform.system(),
        "architecture": platform.machine(),
    }


def can_run_model(model_size_gb: float) -> bool:
    """Check if system can run a model of given size."""
    ram_gb = get_available_ram_gb()
    # Rule of thumb: need 1.5x model size in RAM
    required_ram = model_size_gb * 1.5
    return ram_gb >= required_ram
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_system_info.py::test_detect_available_ram -v`
Expected: PASS

**Step 5: Add psutil to dependencies**

In `pyproject.toml`, add to dependencies:

```toml
dependencies = [
    # ... existing deps ...
    "psutil>=5.9.0",
]
```

**Step 6: Commit**

```bash
git add src/ai/system_info.py tests/unit/test_system_info.py pyproject.toml
git commit -m "feat(ai): add system requirements detection

- Detect available RAM
- Check for CUDA GPU
- Model size compatibility check
- Add psutil dependency

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: E2E Tests for AI Hub Complete Flow

**Files:**
- Create: `tests/e2e/test_ai_hub_full_flow.py`

**Step 1: Write E2E test for full wizard flow**

```python
async def test_complete_wizard_flow(page: ft.Page):
    """Test complete wizard flow from start to finish."""
    from src.ui.views.ai_hub import AIHubView

    ai_hub = AIHubView(page=page)
    page.add(ai_hub.build())
    await page.update_async()

    # Step 1: Select provider
    checkbox = _find_checkbox(page, "OpenAI")
    checkbox.value = True
    await page.update_async()

    # Click Next
    next_button = _find_button(page, "Next")
    next_button.on_click(None)
    await page.update_async()

    # Step 2: Enter API key
    api_key_field = _find_textfield(page, "API Key")
    api_key_field.value = "sk-test123"
    await page.update_async()

    # Click Next
    next_button = _find_button(page, "Next")
    next_button.on_click(None)
    await page.update_async()

    # Step 3: Verify completion screen
    assert "Setup Complete" in str(page.controls)

    # Click Get Started
    get_started = _find_button(page, "Get Started")
    get_started.on_click(None)
    await page.update_async()

    # Verify API key was saved
    from src.ai.security import has_api_key
    assert has_api_key("openai")
```

**Step 2: Run test to verify flow works**

Run: `python -m pytest tests/e2e/test_ai_hub_full_flow.py::test_complete_wizard_flow -v`
Expected: PASS

**Step 3: Write more E2E tests**

Add 10+ more tests covering:
- Provider configuration dialog
- Model download UI
- AI nodes drag and drop
- Provider status bar click
- Error cases

```python
async def test_provider_configuration_roundtrip(page: ft.Page):
    """Test configuring provider via dialog."""
    # ... implementation ...

async def test_model_download_progress(page: ft.Page):
    """Test model download shows progress."""
    # ... implementation ...

async def test_ai_node_drag_to_canvas(page: ft.Page):
    """Test AI node can be dragged to canvas."""
    # ... implementation ...

# ... 7 more tests ...
```

**Step 4: Run all E2E tests**

Run: `python -m pytest tests/e2e/test_ai_hub*.py tests/e2e/test_ai_providers.py tests/e2e/test_ai_node_palette.py tests/e2e/test_provider_status_bar.py -v`
Expected: 32+ tests passing

**Step 5: Commit**

```bash
git add tests/e2e/
git commit -m "test(ai-ui): comprehensive E2E tests for AI Hub

- Full wizard flow test
- Provider configuration tests
- Model download UI tests
- AI node palette tests
- Provider status bar tests
- 32 total E2E tests

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 11: Final Integration & Bug Fixes

**Files:**
- Modify: Various files as needed for integration issues

**Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: Identify any integration issues

**Step 2: Fix wizard tab switching**

Implement tab switching in `_skip_wizard` and `_complete_wizard` methods. The parent Tabs control needs to be accessible.

**Step 3: Fix provider tab refresh after dialog**

Ensure provider status updates after saving API key in dialog.

**Step 4: Test AI node execution**

Verify AI nodes can actually execute (may need to mock AI Gateway for tests).

**Step 5: Polish UI spacing and colors**

Ensure consistent spacing, colors matching SkynetteTheme.

**Step 6: Run full test suite again**

Run: `python -m pytest tests/ -v`
Expected: All tests passing (unit + e2e)

**Step 7: Commit**

```bash
git add src/ tests/
git commit -m "fix(ai-ui): final integration and polish

- Fixed tab switching in wizard
- Provider tab refreshes after config changes
- Consistent UI spacing and colors
- All 185+ tests passing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Sprint 2 Success Criteria Verification

After all tasks complete, verify:

```bash
# 1. Run all tests
python -m pytest tests/ -v

# Expected: 185+ tests passing (153 unit + 32+ e2e)

# 2. Start app and manually test
python -m src.main

# Verify:
# ✅ Setup wizard completable end-to-end
# ✅ All providers configurable via UI
# ✅ Model download UI functional
# ✅ AI nodes visible in palette
# ✅ Provider status bar shows in top bar
# ✅ 32 E2E tests passing

# 3. Check code coverage
python -m pytest tests/ --cov=src --cov-report=html

# Expected: >85% coverage on new AI UI code
```

---

## Notes for Implementation

- **TDD Approach**: Every feature starts with a failing test
- **Frequent Commits**: Commit after each completed step
- **No Mocking in E2E**: E2E tests use real components, unit tests use mocks
- **System Keyring**: Use existing `src/ai/security.py` for API key storage
- **AIStorage**: Use existing `src/ai/storage.py` for provider configs
- **Theme Consistency**: All colors from `src/ui/theme.py` (Theme class)
- **Async Handling**: Flet UI updates must use `page.update()` or `await page.update_async()`

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-01-10-phase4-sprint2-ai-hub-ui.md`.

Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
