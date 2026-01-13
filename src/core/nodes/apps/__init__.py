"""App integration nodes."""

from src.core.nodes.apps.slack import SlackSendMessageNode, SlackReactionNode
from src.core.nodes.apps.email import EmailSendNode, EmailReadNode
from src.core.nodes.apps.discord import DiscordWebhookNode, DiscordBotMessageNode
from src.core.nodes.apps.database import SQLiteQueryNode, PostgreSQLQueryNode
from src.core.nodes.apps.google_sheets import GoogleSheetsReadNode, GoogleSheetsWriteNode
from src.core.nodes.apps.google_drive import (
    GoogleDriveListNode,
    GoogleDriveDownloadNode,
    GoogleDriveUploadNode,
    GoogleDriveCreateFolderNode,
    GoogleDriveDeleteNode,
)
from src.core.nodes.apps.webhook import WebhookTriggerNode, WebhookResponseNode, WebhookCallNode
from src.core.nodes.apps.telegram import TelegramSendMessageNode, TelegramSendPhotoNode, TelegramGetUpdatesNode
from src.core.nodes.apps.github import GitHubCreateIssueNode, GitHubCreatePRNode, GitHubListReposNode
from src.core.nodes.apps.notion import NotionQueryDatabaseNode, NotionCreatePageNode, NotionUpdatePageNode
from src.core.nodes.apps.aws_s3 import S3UploadNode, S3DownloadNode, S3ListObjectsNode
from src.core.nodes.apps.twitter import TwitterPostTweetNode, TwitterSearchTweetsNode, TwitterGetUserNode
from src.core.nodes.apps.teams import (
    TeamsSendMessageNode,
    TeamsListChannelsNode,
    TeamsListTeamsNode,
    TeamsGetMessagesNode,
    TeamsCreateMeetingNode,
)

__all__ = [
    # Slack
    "SlackSendMessageNode",
    "SlackReactionNode",
    # Email
    "EmailSendNode",
    "EmailReadNode",
    # Discord
    "DiscordWebhookNode",
    "DiscordBotMessageNode",
    # Database
    "SQLiteQueryNode",
    "PostgreSQLQueryNode",
    # Google Sheets
    "GoogleSheetsReadNode",
    "GoogleSheetsWriteNode",
    # Google Drive
    "GoogleDriveListNode",
    "GoogleDriveDownloadNode",
    "GoogleDriveUploadNode",
    "GoogleDriveCreateFolderNode",
    "GoogleDriveDeleteNode",
    # Webhook
    "WebhookTriggerNode",
    "WebhookResponseNode",
    "WebhookCallNode",
    # Telegram
    "TelegramSendMessageNode",
    "TelegramSendPhotoNode",
    "TelegramGetUpdatesNode",
    # GitHub
    "GitHubCreateIssueNode",
    "GitHubCreatePRNode",
    "GitHubListReposNode",
    # Notion
    "NotionQueryDatabaseNode",
    "NotionCreatePageNode",
    "NotionUpdatePageNode",
    # AWS S3
    "S3UploadNode",
    "S3DownloadNode",
    "S3ListObjectsNode",
    # Twitter
    "TwitterPostTweetNode",
    "TwitterSearchTweetsNode",
    "TwitterGetUserNode",
    # Microsoft Teams
    "TeamsSendMessageNode",
    "TeamsListChannelsNode",
    "TeamsListTeamsNode",
    "TeamsGetMessagesNode",
    "TeamsCreateMeetingNode",
]

# All app nodes for registry
APP_NODES = [
    # Slack
    SlackSendMessageNode,
    SlackReactionNode,
    # Email
    EmailSendNode,
    EmailReadNode,
    # Discord
    DiscordWebhookNode,
    DiscordBotMessageNode,
    # Database
    SQLiteQueryNode,
    PostgreSQLQueryNode,
    # Google Sheets
    GoogleSheetsReadNode,
    GoogleSheetsWriteNode,
    # Google Drive
    GoogleDriveListNode,
    GoogleDriveDownloadNode,
    GoogleDriveUploadNode,
    GoogleDriveCreateFolderNode,
    GoogleDriveDeleteNode,
    # Webhook
    WebhookTriggerNode,
    WebhookResponseNode,
    WebhookCallNode,
    # Telegram
    TelegramSendMessageNode,
    TelegramSendPhotoNode,
    TelegramGetUpdatesNode,
    # GitHub
    GitHubCreateIssueNode,
    GitHubCreatePRNode,
    GitHubListReposNode,
    # Notion
    NotionQueryDatabaseNode,
    NotionCreatePageNode,
    NotionUpdatePageNode,
    # AWS S3
    S3UploadNode,
    S3DownloadNode,
    S3ListObjectsNode,
    # Twitter
    TwitterPostTweetNode,
    TwitterSearchTweetsNode,
    TwitterGetUserNode,
    # Microsoft Teams
    TeamsSendMessageNode,
    TeamsListChannelsNode,
    TeamsListTeamsNode,
    TeamsGetMessagesNode,
    TeamsCreateMeetingNode,
]
