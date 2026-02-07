"""App integration nodes."""

from src.core.nodes.apps.airtable import (
    AirtableCreateRecordNode,
    AirtableDeleteRecordNode,
    AirtableGetRecordNode,
    AirtableListBasesNode,
    AirtableListRecordsNode,
    AirtableUpdateRecordNode,
)
from src.core.nodes.apps.aws_s3 import S3DownloadNode, S3ListObjectsNode, S3UploadNode
from src.core.nodes.apps.database import (
    MongoDBQueryNode,
    MongoDBWriteNode,
    MySQLQueryNode,
    PostgreSQLQueryNode,
    SQLiteQueryNode,
)
from src.core.nodes.apps.discord import DiscordBotMessageNode, DiscordWebhookNode
from src.core.nodes.apps.dropbox import (
    DropboxCreateFolderNode,
    DropboxDeleteNode,
    DropboxDownloadNode,
    DropboxGetLinkNode,
    DropboxListNode,
    DropboxUploadNode,
)
from src.core.nodes.apps.email import EmailReadNode, EmailSendNode
from src.core.nodes.apps.github import (
    GitHubCreateIssueNode,
    GitHubCreatePRNode,
    GitHubListReposNode,
)
from src.core.nodes.apps.google_drive import (
    GoogleDriveCreateFolderNode,
    GoogleDriveDeleteNode,
    GoogleDriveDownloadNode,
    GoogleDriveListNode,
    GoogleDriveUploadNode,
)
from src.core.nodes.apps.google_sheets import GoogleSheetsReadNode, GoogleSheetsWriteNode
from src.core.nodes.apps.hubspot import (
    HubSpotCreateContactNode,
    HubSpotCreateDealNode,
    HubSpotGetContactNode,
    HubSpotGetDealNode,
    HubSpotListDealsNode,
    HubSpotSearchContactsNode,
    HubSpotUpdateContactNode,
)
from src.core.nodes.apps.jira import (
    JiraAddCommentNode,
    JiraCreateIssueNode,
    JiraGetIssueNode,
    JiraGetTransitionsNode,
    JiraListProjectsNode,
    JiraSearchIssuesNode,
    JiraTransitionIssueNode,
    JiraUpdateIssueNode,
)
from src.core.nodes.apps.mailchimp import (
    MailchimpAddSubscriberNode,
    MailchimpCreateCampaignNode,
    MailchimpGetAudienceNode,
    MailchimpGetSubscriberNode,
    MailchimpListAudiencesNode,
    MailchimpListCampaignsNode,
    MailchimpSendCampaignNode,
    MailchimpUpdateSubscriberNode,
)
from src.core.nodes.apps.notion import (
    NotionCreatePageNode,
    NotionQueryDatabaseNode,
    NotionUpdatePageNode,
)
from src.core.nodes.apps.sendgrid import (
    SendGridAddContactNode,
    SendGridGetStatsNode,
    SendGridListTemplatesNode,
    SendGridSearchContactsNode,
    SendGridSendEmailNode,
    SendGridSendTemplateNode,
)
from src.core.nodes.apps.shopify import (
    ShopifyCreateCustomerNode,
    ShopifyGetOrderNode,
    ShopifyGetProductNode,
    ShopifyListCustomersNode,
    ShopifyListOrdersNode,
    ShopifyListProductsNode,
    ShopifyUpdateInventoryNode,
)
from src.core.nodes.apps.slack import SlackReactionNode, SlackSendMessageNode
from src.core.nodes.apps.stripe import (
    StripeCreateCustomerNode,
    StripeCreateInvoiceNode,
    StripeCreatePaymentIntentNode,
    StripeCreateProductNode,
    StripeCreateRefundNode,
    StripeGetCustomerNode,
    StripeListChargesNode,
)
from src.core.nodes.apps.teams import (
    TeamsCreateMeetingNode,
    TeamsGetMessagesNode,
    TeamsListChannelsNode,
    TeamsListTeamsNode,
    TeamsSendMessageNode,
)
from src.core.nodes.apps.telegram import (
    TelegramGetUpdatesNode,
    TelegramSendMessageNode,
    TelegramSendPhotoNode,
)
from src.core.nodes.apps.trello import (
    TrelloAddCommentNode,
    TrelloCreateCardNode,
    TrelloDeleteCardNode,
    TrelloListBoardsNode,
    TrelloListCardsNode,
    TrelloListListsNode,
    TrelloUpdateCardNode,
)
from src.core.nodes.apps.twilio import (
    TwilioGetMessageNode,
    TwilioListMessagesNode,
    TwilioLookupNode,
    TwilioMakeCallNode,
    TwilioSendSMSNode,
    TwilioSendWhatsAppNode,
)
from src.core.nodes.apps.twitter import (
    TwitterGetUserNode,
    TwitterPostTweetNode,
    TwitterSearchTweetsNode,
)
from src.core.nodes.apps.webhook import WebhookCallNode, WebhookResponseNode, WebhookTriggerNode
from src.core.nodes.apps.zendesk import (
    ZendeskAddCommentNode,
    ZendeskCreateTicketNode,
    ZendeskCreateUserNode,
    ZendeskGetTicketNode,
    ZendeskGetUserNode,
    ZendeskListTicketsNode,
    ZendeskSearchTicketsNode,
    ZendeskUpdateTicketNode,
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
    # SendGrid
    "SendGridSendEmailNode",
    "SendGridSendTemplateNode",
    "SendGridGetStatsNode",
    "SendGridListTemplatesNode",
    "SendGridAddContactNode",
    "SendGridSearchContactsNode",
    # Stripe
    "StripeCreateCustomerNode",
    "StripeGetCustomerNode",
    "StripeCreatePaymentIntentNode",
    "StripeListChargesNode",
    "StripeCreateInvoiceNode",
    "StripeCreateProductNode",
    "StripeCreateRefundNode",
    # Shopify
    "ShopifyListProductsNode",
    "ShopifyGetProductNode",
    "ShopifyListOrdersNode",
    "ShopifyGetOrderNode",
    "ShopifyListCustomersNode",
    "ShopifyCreateCustomerNode",
    "ShopifyUpdateInventoryNode",
    # HubSpot
    "HubSpotGetContactNode",
    "HubSpotSearchContactsNode",
    "HubSpotCreateContactNode",
    "HubSpotUpdateContactNode",
    "HubSpotGetDealNode",
    "HubSpotListDealsNode",
    "HubSpotCreateDealNode",
    # Zendesk
    "ZendeskCreateTicketNode",
    "ZendeskGetTicketNode",
    "ZendeskUpdateTicketNode",
    "ZendeskListTicketsNode",
    "ZendeskSearchTicketsNode",
    "ZendeskAddCommentNode",
    "ZendeskGetUserNode",
    "ZendeskCreateUserNode",
    # Mailchimp
    "MailchimpListAudiencesNode",
    "MailchimpGetAudienceNode",
    "MailchimpAddSubscriberNode",
    "MailchimpUpdateSubscriberNode",
    "MailchimpGetSubscriberNode",
    "MailchimpListCampaignsNode",
    "MailchimpCreateCampaignNode",
    "MailchimpSendCampaignNode",
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
    # SendGrid
    SendGridSendEmailNode,
    SendGridSendTemplateNode,
    SendGridGetStatsNode,
    SendGridListTemplatesNode,
    SendGridAddContactNode,
    SendGridSearchContactsNode,
    # Stripe
    StripeCreateCustomerNode,
    StripeGetCustomerNode,
    StripeCreatePaymentIntentNode,
    StripeListChargesNode,
    StripeCreateInvoiceNode,
    StripeCreateProductNode,
    StripeCreateRefundNode,
    # Shopify
    ShopifyListProductsNode,
    ShopifyGetProductNode,
    ShopifyListOrdersNode,
    ShopifyGetOrderNode,
    ShopifyListCustomersNode,
    ShopifyCreateCustomerNode,
    ShopifyUpdateInventoryNode,
    # HubSpot
    HubSpotGetContactNode,
    HubSpotSearchContactsNode,
    HubSpotCreateContactNode,
    HubSpotUpdateContactNode,
    HubSpotGetDealNode,
    HubSpotListDealsNode,
    HubSpotCreateDealNode,
    # Zendesk
    ZendeskCreateTicketNode,
    ZendeskGetTicketNode,
    ZendeskUpdateTicketNode,
    ZendeskListTicketsNode,
    ZendeskSearchTicketsNode,
    ZendeskAddCommentNode,
    ZendeskGetUserNode,
    ZendeskCreateUserNode,
    # Mailchimp
    MailchimpListAudiencesNode,
    MailchimpGetAudienceNode,
    MailchimpAddSubscriberNode,
    MailchimpUpdateSubscriberNode,
    MailchimpGetSubscriberNode,
    MailchimpListCampaignsNode,
    MailchimpCreateCampaignNode,
    MailchimpSendCampaignNode,
]
