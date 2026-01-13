# Phase 6: App Integrations - Implementation Plan

**Version**: 0.6.0
**Status**: In Progress
**Created**: 2026-01-13

## Overview

Phase 6 focuses on completing and hardening app integrations. While 28 nodes already exist across 11 services, they lack tests, OAuth flows, and some key integrations are missing.

## Current State

### Existing Integrations (28 nodes)

| Service | Nodes | Has Tests |
|---------|-------|-----------|
| Slack | Send Message, Add Reaction | No |
| Email (SMTP/IMAP) | Send, Read | No |
| Discord | Webhook, Bot Message | No |
| Database | SQLite, PostgreSQL | No |
| Google Sheets | Read, Write | No |
| Webhook | Trigger, Response, Call | No |
| Telegram | Send Message, Send Photo, Get Updates | No |
| GitHub | Create Issue, Create PR, List Repos | No |
| Notion | Query Database, Create Page, Update Page | No |
| AWS S3 | Upload, Download, List Objects | No |
| Twitter | Post Tweet, Search, Get User | No |

### Missing Integrations (Priority)

**High Priority:**
- Microsoft Teams (Send Message, Read Messages)
- Microsoft Outlook (via Graph API - modern approach)
- Google Drive (Upload, Download, List)
- Dropbox (Upload, Download, List)
- MySQL Database
- MongoDB

**Medium Priority:**
- Airtable (CRUD operations)
- Trello (Cards, Lists, Boards)
- Jira (Issues, Projects)
- Linear (Issues)
- Stripe (Customers, Payments)

**Lower Priority:**
- Twilio (SMS, WhatsApp)
- SendGrid (Transactional email)
- Mailchimp (Campaigns)
- HubSpot (Contacts, Deals)

## Sprint Plan

### Sprint 1: Testing & Hardening (Week 1-2)

**Goal**: Add comprehensive tests for all existing app nodes.

#### Tasks

1. **Create test fixtures for app nodes** (`tests/unit/test_app_nodes.py`)
   - Mock HTTP responses for each service
   - Test success and error cases
   - Test input validation

2. **Test each service category:**
   - [ ] Slack nodes (webhook + bot API)
   - [ ] Email nodes (SMTP/IMAP mocking)
   - [ ] Discord nodes
   - [ ] Database nodes (SQLite real, PostgreSQL mocked)
   - [ ] Google Sheets nodes
   - [ ] Webhook nodes
   - [ ] Telegram nodes
   - [ ] GitHub nodes
   - [ ] Notion nodes
   - [ ] AWS S3 nodes
   - [ ] Twitter nodes

3. **Fix any bugs discovered during testing**

4. **Add error handling improvements:**
   - Better error messages with troubleshooting hints
   - Rate limit handling
   - Retry logic for transient failures

**Success Criteria:**
- 100+ new tests for app nodes
- All existing nodes have test coverage
- CI passes with app node tests

### Sprint 2: OAuth & Credentials UI (Week 3-4)

**Goal**: Build credential management system with OAuth support.

#### Tasks

1. **Create Credentials Manager** (`src/core/credentials/`)
   ```python
   # credential_types.py
   class CredentialType(Enum):
       API_KEY = "api_key"
       OAUTH2 = "oauth2"
       BASIC_AUTH = "basic_auth"
       CUSTOM = "custom"

   # manager.py
   class CredentialsManager:
       def save_credential(name, type, data)
       def get_credential(name)
       def list_credentials()
       def delete_credential(name)
       def test_credential(name)
   ```

2. **OAuth2 Flow Implementation:**
   - Authorization code flow
   - Refresh token handling
   - Secure token storage (keyring)
   - Supported providers: Google, Microsoft, GitHub, Slack, Notion

3. **Credentials UI** (`src/ui/views/credentials.py`)
   - List saved credentials
   - Add new credential (form or OAuth)
   - Test connection button
   - Delete credential
   - Use in node configuration (dropdown selection)

4. **Update existing nodes** to use credential manager:
   - Replace inline secrets with credential references
   - Add "Select Credential" dropdown to node inputs

**Success Criteria:**
- OAuth flow works for Google, Microsoft, GitHub
- Credentials stored securely in system keyring
- Nodes can reference saved credentials

### Sprint 3: High-Priority Integrations (Week 5-6)

**Goal**: Add Microsoft and cloud storage integrations.

#### Tasks

1. **Microsoft Teams** (`src/core/nodes/apps/teams.py`)
   - TeamsSendMessageNode (channels, chats)
   - TeamsCreateMeetingNode
   - OAuth via Microsoft Graph API

2. **Google Drive** (`src/core/nodes/apps/google_drive.py`)
   - GoogleDriveUploadNode
   - GoogleDriveDownloadNode
   - GoogleDriveListNode
   - GoogleDriveCreateFolderNode

3. **Dropbox** (`src/core/nodes/apps/dropbox.py`)
   - DropboxUploadNode
   - DropboxDownloadNode
   - DropboxListNode

4. **MySQL** (`src/core/nodes/apps/database.py` - extend)
   - MySQLQueryNode
   - Connection pooling

5. **MongoDB** (`src/core/nodes/apps/mongodb.py`)
   - MongoDBFindNode
   - MongoDBInsertNode
   - MongoDBUpdateNode
   - MongoDBDeleteNode

**Success Criteria:**
- 15+ new nodes added
- Tests for all new nodes
- Documentation for each integration

### Sprint 4: Polish & Documentation (Week 7-8)

**Goal**: Production-ready integrations with full documentation.

#### Tasks

1. **Integration documentation** (`docs/integrations/`)
   - Setup guides for each service
   - OAuth configuration instructions
   - Example workflows
   - Troubleshooting guides

2. **Integration browser UI:**
   - Browse available integrations
   - Quick setup for popular services
   - Connection status indicators

3. **Workflow templates:**
   - "Slack notification on GitHub PR"
   - "Email daily report from Google Sheets"
   - "Sync files from Dropbox to S3"
   - "Auto-respond to Telegram messages with AI"

4. **Performance optimization:**
   - Connection pooling for databases
   - Rate limit awareness per service
   - Batch operations where supported

**Success Criteria:**
- All integrations documented
- 5+ workflow templates
- Production-ready error handling

## Technical Details

### Credential Storage Schema

```sql
CREATE TABLE credentials (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,  -- api_key, oauth2, basic_auth
    service TEXT NOT NULL,  -- slack, google, etc.
    encrypted_data BLOB NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_used_at TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE
);

CREATE TABLE oauth_tokens (
    credential_id TEXT PRIMARY KEY REFERENCES credentials(id),
    access_token_encrypted BLOB,
    refresh_token_encrypted BLOB,
    expires_at TIMESTAMP,
    scopes TEXT
);
```

### OAuth2 Provider Configuration

```python
OAUTH_PROVIDERS = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": {
            "drive": ["https://www.googleapis.com/auth/drive"],
            "sheets": ["https://www.googleapis.com/auth/spreadsheets"],
            "gmail": ["https://www.googleapis.com/auth/gmail.modify"],
        }
    },
    "microsoft": {
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "scopes": {
            "teams": ["Chat.ReadWrite", "Channel.ReadBasic.All"],
            "onedrive": ["Files.ReadWrite.All"],
        }
    },
    # ... more providers
}
```

### Node Credential Reference

```python
class SlackSendMessageNode(BaseNode):
    inputs = [
        NodeField(
            name="credential",
            label="Slack Credential",
            type=FieldType.CREDENTIAL,  # New field type
            credential_type="slack",  # Filter to Slack credentials
            required=True,
        ),
        # ... other fields
    ]
```

## Dependencies

**New packages:**
```toml
[project.optional-dependencies]
integrations = [
    "google-api-python-client>=2.0",
    "google-auth-oauthlib>=1.0",
    "msal>=1.20",  # Microsoft Auth Library
    "dropbox>=11.0",
    "pymongo>=4.0",
    "mysql-connector-python>=8.0",
    "aiomysql>=0.2",  # Async MySQL
    "motor>=3.0",  # Async MongoDB
]
```

## Success Metrics

| Metric | Target |
|--------|--------|
| App node tests | 100+ new tests |
| Test coverage for apps | >80% |
| New integrations | 15+ nodes |
| OAuth providers | 5+ |
| Documentation pages | 10+ |
| Workflow templates | 5+ |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| OAuth complexity | Start with simpler API key integrations, add OAuth incrementally |
| Rate limits | Add rate limit tracking per service, implement backoff |
| API changes | Pin API versions, add version detection |
| Credential security | Use system keyring, never log secrets, encrypt at rest |

## Version Bump

After Phase 6 completion:
- Version: 0.5.0 → 0.6.0
- Update CHANGELOG.md
- Tag release

## Next Phase Preview

**Phase 7: Cloud Sync & Sharing**
- User accounts and authentication
- Workflow sync across devices
- Workflow marketplace
- Cloud execution for scheduled workflows
