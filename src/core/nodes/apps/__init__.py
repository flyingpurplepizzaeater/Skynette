"""App integration nodes."""

from src.core.nodes.apps.slack import SlackSendMessageNode, SlackReactionNode
from src.core.nodes.apps.email import EmailSendNode, EmailReadNode
from src.core.nodes.apps.discord import DiscordWebhookNode, DiscordBotMessageNode
from src.core.nodes.apps.database import (
    SQLiteQueryNode,
    PostgreSQLQueryNode,
    MySQLQueryNode,
    MongoDBQueryNode,
    MongoDBWriteNode,
)
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
from src.core.nodes.apps.dropbox import (
    DropboxListNode,
    DropboxDownloadNode,
    DropboxUploadNode,
    DropboxCreateFolderNode,
    DropboxDeleteNode,
    DropboxGetLinkNode,
)
from src.core.nodes.apps.trello import (
    TrelloListBoardsNode,
    TrelloListListsNode,
    TrelloListCardsNode,
    TrelloCreateCardNode,
    TrelloUpdateCardNode,
    TrelloDeleteCardNode,
    TrelloAddCommentNode,
)
from src.core.nodes.apps.airtable import (
    AirtableListBasesNode,
    AirtableListRecordsNode,
    AirtableGetRecordNode,
    AirtableCreateRecordNode,
    AirtableUpdateRecordNode,
    AirtableDeleteRecordNode,
)
from src.core.nodes.apps.jira import (
    JiraListProjectsNode,
    JiraSearchIssuesNode,
    JiraGetIssueNode,
    JiraCreateIssueNode,
    JiraUpdateIssueNode,
    JiraAddCommentNode,
    JiraTransitionIssueNode,
    JiraGetTransitionsNode,
)
from src.core.nodes.apps.twilio import (
    TwilioSendSMSNode,
    TwilioSendWhatsAppNode,
    TwilioGetMessageNode,
    TwilioListMessagesNode,
    TwilioMakeCallNode,
    TwilioLookupNode,
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
    "MySQLQueryNode",
    "MongoDBQueryNode",
    "MongoDBWriteNode",
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
    # Dropbox
    "DropboxListNode",
    "DropboxDownloadNode",
    "DropboxUploadNode",
    "DropboxCreateFolderNode",
    "DropboxDeleteNode",
    "DropboxGetLinkNode",
    # Trello
    "TrelloListBoardsNode",
    "TrelloListListsNode",
    "TrelloListCardsNode",
    "TrelloCreateCardNode",
    "TrelloUpdateCardNode",
    "TrelloDeleteCardNode",
    "TrelloAddCommentNode",
    # Airtable
    "AirtableListBasesNode",
    "AirtableListRecordsNode",
    "AirtableGetRecordNode",
    "AirtableCreateRecordNode",
    "AirtableUpdateRecordNode",
    "AirtableDeleteRecordNode",
    # Jira
    "JiraListProjectsNode",
    "JiraSearchIssuesNode",
    "JiraGetIssueNode",
    "JiraCreateIssueNode",
    "JiraUpdateIssueNode",
    "JiraAddCommentNode",
    "JiraTransitionIssueNode",
    "JiraGetTransitionsNode",
    # Twilio
    "TwilioSendSMSNode",
    "TwilioSendWhatsAppNode",
    "TwilioGetMessageNode",
    "TwilioListMessagesNode",
    "TwilioMakeCallNode",
    "TwilioLookupNode",
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
    MySQLQueryNode,
    MongoDBQueryNode,
    MongoDBWriteNode,
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
    # Dropbox
    DropboxListNode,
    DropboxDownloadNode,
    DropboxUploadNode,
    DropboxCreateFolderNode,
    DropboxDeleteNode,
    DropboxGetLinkNode,
    # Trello
    TrelloListBoardsNode,
    TrelloListListsNode,
    TrelloListCardsNode,
    TrelloCreateCardNode,
    TrelloUpdateCardNode,
    TrelloDeleteCardNode,
    TrelloAddCommentNode,
    # Airtable
    AirtableListBasesNode,
    AirtableListRecordsNode,
    AirtableGetRecordNode,
    AirtableCreateRecordNode,
    AirtableUpdateRecordNode,
    AirtableDeleteRecordNode,
    # Jira
    JiraListProjectsNode,
    JiraSearchIssuesNode,
    JiraGetIssueNode,
    JiraCreateIssueNode,
    JiraUpdateIssueNode,
    JiraAddCommentNode,
    JiraTransitionIssueNode,
    JiraGetTransitionsNode,
    # Twilio
    TwilioSendSMSNode,
    TwilioSendWhatsAppNode,
    TwilioGetMessageNode,
    TwilioListMessagesNode,
    TwilioMakeCallNode,
    TwilioLookupNode,
]
