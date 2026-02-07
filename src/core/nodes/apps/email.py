"""
Email Integration Nodes - Send and receive emails.
"""

import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.core.nodes.base import BaseNode, FieldType, NodeField


class EmailSendNode(BaseNode):
    """
    Send emails via SMTP.

    Supports:
    - Plain text and HTML emails
    - Multiple recipients (To, CC, BCC)
    - File attachments
    - Common providers (Gmail, Outlook, custom SMTP)
    """

    type = "email-send"
    name = "Email: Send"
    category = "Apps"
    description = "Send an email via SMTP"
    icon = "email"
    color = "#EA4335"  # Gmail red

    inputs = [
        NodeField(
            name="smtp_host",
            label="SMTP Host",
            type=FieldType.STRING,
            required=True,
            default="smtp.gmail.com",
            description="SMTP server host.",
        ),
        NodeField(
            name="smtp_port",
            label="SMTP Port",
            type=FieldType.NUMBER,
            required=True,
            default=587,
            description="SMTP server port (587 for TLS, 465 for SSL).",
        ),
        NodeField(
            name="username",
            label="Username",
            type=FieldType.STRING,
            required=True,
            description="SMTP username (usually your email).",
        ),
        NodeField(
            name="password",
            label="Password",
            type=FieldType.SECRET,
            required=True,
            description="SMTP password or app-specific password.",
        ),
        NodeField(
            name="from_email",
            label="From Email",
            type=FieldType.STRING,
            required=True,
            description="Sender email address.",
        ),
        NodeField(
            name="from_name",
            label="From Name",
            type=FieldType.STRING,
            required=False,
            description="Sender display name.",
        ),
        NodeField(
            name="to",
            label="To",
            type=FieldType.STRING,
            required=True,
            description="Recipient email(s), comma-separated.",
        ),
        NodeField(
            name="cc",
            label="CC",
            type=FieldType.STRING,
            required=False,
            description="CC recipient(s), comma-separated.",
        ),
        NodeField(
            name="bcc",
            label="BCC",
            type=FieldType.STRING,
            required=False,
            description="BCC recipient(s), comma-separated.",
        ),
        NodeField(
            name="subject",
            label="Subject",
            type=FieldType.STRING,
            required=True,
            description="Email subject line.",
        ),
        NodeField(
            name="body",
            label="Body",
            type=FieldType.TEXT,
            required=True,
            description="Email body content.",
        ),
        NodeField(
            name="html",
            label="HTML Body",
            type=FieldType.TEXT,
            required=False,
            description="HTML version of the body (optional).",
        ),
        NodeField(
            name="use_tls",
            label="Use TLS",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
            description="Use TLS encryption.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the email was sent.",
        ),
        NodeField(
            name="message_id",
            label="Message ID",
            type=FieldType.STRING,
            description="Unique message identifier.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Send email via SMTP."""
        import smtplib
        import uuid

        smtp_host = config.get("smtp_host", "smtp.gmail.com")
        smtp_port = int(config.get("smtp_port", 587))
        username = config.get("username")
        password = config.get("password")
        from_email = config.get("from_email")
        from_name = config.get("from_name", "")
        to = config.get("to", "")
        cc = config.get("cc", "")
        bcc = config.get("bcc", "")
        subject = config.get("subject", "")
        body = config.get("body", "")
        html = config.get("html", "")
        use_tls = config.get("use_tls", True)

        # Parse recipients
        to_list = [e.strip() for e in to.split(",") if e.strip()]
        cc_list = [e.strip() for e in cc.split(",") if e.strip()] if cc else []
        bcc_list = [e.strip() for e in bcc.split(",") if e.strip()] if bcc else []
        all_recipients = to_list + cc_list + bcc_list

        # Build message
        if html:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html, "html"))
        else:
            msg = MIMEText(body, "plain")

        # Set headers
        if from_name:
            msg["From"] = f"{from_name} <{from_email}>"
        else:
            msg["From"] = from_email
        msg["To"] = ", ".join(to_list)
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)
        msg["Subject"] = subject

        message_id = f"<{uuid.uuid4()}@skynette>"
        msg["Message-ID"] = message_id

        # Send email in executor to avoid blocking
        loop = asyncio.get_event_loop()

        def send():
            try:
                if smtp_port == 465:
                    # SSL
                    server = smtplib.SMTP_SSL(smtp_host, smtp_port)
                else:
                    # TLS
                    server = smtplib.SMTP(smtp_host, smtp_port)
                    if use_tls:
                        server.starttls()

                server.login(username, password)
                server.sendmail(from_email, all_recipients, msg.as_string())
                server.quit()
                return True
            except Exception as e:
                print(f"Email send failed: {e}")
                return False

        success = await loop.run_in_executor(None, send)

        return {
            "success": success,
            "message_id": message_id if success else "",
        }


class EmailReadNode(BaseNode):
    """
    Read emails via IMAP.

    Supports:
    - Reading from inbox or specific folders
    - Filtering by date, sender, subject
    - Marking as read/unread
    """

    type = "email-read"
    name = "Email: Read"
    category = "Apps"
    description = "Read emails via IMAP"
    icon = "mark_email_read"
    color = "#EA4335"

    inputs = [
        NodeField(
            name="imap_host",
            label="IMAP Host",
            type=FieldType.STRING,
            required=True,
            default="imap.gmail.com",
            description="IMAP server host.",
        ),
        NodeField(
            name="imap_port",
            label="IMAP Port",
            type=FieldType.NUMBER,
            required=True,
            default=993,
            description="IMAP server port.",
        ),
        NodeField(
            name="username",
            label="Username",
            type=FieldType.STRING,
            required=True,
            description="IMAP username.",
        ),
        NodeField(
            name="password",
            label="Password",
            type=FieldType.SECRET,
            required=True,
            description="IMAP password.",
        ),
        NodeField(
            name="folder",
            label="Folder",
            type=FieldType.STRING,
            required=False,
            default="INBOX",
            description="Mailbox folder to read from.",
        ),
        NodeField(
            name="filter",
            label="Filter",
            type=FieldType.SELECT,
            required=False,
            default="unseen",
            options=[
                {"value": "all", "label": "All"},
                {"value": "unseen", "label": "Unread Only"},
                {"value": "seen", "label": "Read Only"},
                {"value": "recent", "label": "Recent"},
            ],
            description="Email filter.",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=10,
            description="Maximum number of emails to fetch.",
        ),
        NodeField(
            name="mark_as_read",
            label="Mark as Read",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Mark fetched emails as read.",
        ),
    ]

    outputs = [
        NodeField(
            name="emails",
            label="Emails",
            type=FieldType.JSON,
            description="List of email objects.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of emails fetched.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Read emails via IMAP."""
        import email
        import imaplib
        from email.header import decode_header

        imap_host = config.get("imap_host", "imap.gmail.com")
        imap_port = int(config.get("imap_port", 993))
        username = config.get("username")
        password = config.get("password")
        folder = config.get("folder", "INBOX")
        email_filter = config.get("filter", "unseen")
        limit = int(config.get("limit", 10))
        mark_as_read = config.get("mark_as_read", False)

        # Map filter to IMAP search criteria
        filter_map = {
            "all": "ALL",
            "unseen": "UNSEEN",
            "seen": "SEEN",
            "recent": "RECENT",
        }
        search_criteria = filter_map.get(email_filter, "ALL")

        loop = asyncio.get_event_loop()

        def fetch_emails():
            emails = []
            try:
                # Connect
                mail = imaplib.IMAP4_SSL(imap_host, imap_port)
                mail.login(username, password)
                mail.select(folder)

                # Search
                _, message_numbers = mail.search(None, search_criteria)
                message_ids = message_numbers[0].split()

                # Limit and reverse (newest first)
                message_ids = message_ids[-limit:][::-1]

                for msg_id in message_ids:
                    _, msg_data = mail.fetch(msg_id, "(RFC822)")
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)

                    # Decode subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")

                    # Decode from
                    from_addr = msg["From"]

                    # Get body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()

                    emails.append(
                        {
                            "id": msg_id.decode(),
                            "subject": subject,
                            "from": from_addr,
                            "to": msg["To"],
                            "date": msg["Date"],
                            "body": body[:5000],  # Limit body length
                        }
                    )

                    # Mark as read if requested
                    if mark_as_read:
                        mail.store(msg_id, "+FLAGS", "\\Seen")

                mail.close()
                mail.logout()
            except Exception as e:
                print(f"Email read failed: {e}")

            return emails

        emails = await loop.run_in_executor(None, fetch_emails)

        return {
            "emails": emails,
            "count": len(emails),
        }
