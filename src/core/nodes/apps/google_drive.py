"""
Google Drive Integration Nodes - Upload, download, and manage files.
"""

import base64

from src.core.nodes.base import BaseNode, FieldType, NodeField


def _get_credential(credential_id: str | None) -> dict | None:
    """Load credential from vault if ID is provided."""
    if not credential_id:
        return None
    try:
        from src.data.credentials import CredentialVault

        vault = CredentialVault()
        cred = vault.get_credential(credential_id)
        if cred:
            return cred.get("data", {})
    except Exception:
        pass
    return None


def _get_drive_service(config: dict):
    """Build Google Drive service from config."""
    import json

    try:
        from google.oauth2 import service_account
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError(
            "Google API libraries not installed. Install with: "
            "pip install google-auth google-auth-oauthlib google-api-python-client"
        )

    # Check for saved credential first
    credential_id = config.get("credential")
    cred_data = _get_credential(credential_id) if credential_id else None

    if cred_data:
        # OAuth2 credential from vault
        if "access_token" in cred_data:
            credentials = Credentials(
                token=cred_data.get("access_token"),
                refresh_token=cred_data.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=cred_data.get("client_id"),
                client_secret=cred_data.get("client_secret"),
            )
        # Service account credential from vault
        elif "private_key" in cred_data or "type" in cred_data:
            credentials = service_account.Credentials.from_service_account_info(
                cred_data,
                scopes=["https://www.googleapis.com/auth/drive"],
            )
        else:
            raise ValueError("Invalid credential format in vault")
    else:
        # Direct service account JSON
        credentials_json = config.get("credentials_json", "")
        if not credentials_json:
            raise ValueError("Credentials required (select saved credential or provide JSON)")

        if isinstance(credentials_json, str):
            creds_dict = json.loads(credentials_json)
        else:
            creds_dict = credentials_json

        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/drive"],
        )

    return build("drive", "v3", credentials=credentials)


class GoogleDriveListNode(BaseNode):
    """
    List files and folders in Google Drive.

    Supports:
    - Listing all files or specific folders
    - Filtering by file type
    - Sorting options
    """

    type = "google-drive-list"
    name = "Google Drive: List Files"
    category = "Apps"
    description = "List files and folders in Google Drive"
    icon = "folder"
    color = "#4285F4"  # Google blue

    inputs = [
        NodeField(
            name="credential",
            label="Google Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Google credential.",
            credential_service="google_oauth",
        ),
        NodeField(
            name="credentials_json",
            label="Service Account JSON",
            type=FieldType.SECRET,
            required=False,
            description="Google Service Account credentials JSON (or use saved credential).",
        ),
        NodeField(
            name="folder_id",
            label="Folder ID",
            type=FieldType.STRING,
            required=False,
            default="root",
            description="Folder ID to list files from ('root' for My Drive).",
        ),
        NodeField(
            name="file_type",
            label="File Type Filter",
            type=FieldType.SELECT,
            required=False,
            default="all",
            options=[
                {"value": "all", "label": "All Files"},
                {"value": "folder", "label": "Folders Only"},
                {"value": "document", "label": "Google Docs"},
                {"value": "spreadsheet", "label": "Google Sheets"},
                {"value": "presentation", "label": "Google Slides"},
                {"value": "pdf", "label": "PDFs"},
                {"value": "image", "label": "Images"},
            ],
            description="Filter by file type.",
        ),
        NodeField(
            name="max_results",
            label="Max Results",
            type=FieldType.NUMBER,
            required=False,
            default=100,
            description="Maximum number of files to return.",
        ),
        NodeField(
            name="order_by",
            label="Order By",
            type=FieldType.SELECT,
            required=False,
            default="modifiedTime desc",
            options=[
                {"value": "modifiedTime desc", "label": "Modified (Newest First)"},
                {"value": "modifiedTime asc", "label": "Modified (Oldest First)"},
                {"value": "name asc", "label": "Name (A-Z)"},
                {"value": "name desc", "label": "Name (Z-A)"},
                {"value": "createdTime desc", "label": "Created (Newest First)"},
            ],
            description="Sort order for results.",
        ),
    ]

    outputs = [
        NodeField(
            name="files",
            label="Files",
            type=FieldType.JSON,
            description="List of files with metadata.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of files returned.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List files in Google Drive."""
        service = _get_drive_service(config)

        folder_id = config.get("folder_id", "root")
        file_type = config.get("file_type", "all")
        max_results = config.get("max_results", 100)
        order_by = config.get("order_by", "modifiedTime desc")

        # Build query
        query_parts = [f"'{folder_id}' in parents", "trashed = false"]

        mime_type_map = {
            "folder": "application/vnd.google-apps.folder",
            "document": "application/vnd.google-apps.document",
            "spreadsheet": "application/vnd.google-apps.spreadsheet",
            "presentation": "application/vnd.google-apps.presentation",
            "pdf": "application/pdf",
        }

        if file_type == "image":
            query_parts.append("mimeType contains 'image/'")
        elif file_type in mime_type_map:
            query_parts.append(f"mimeType = '{mime_type_map[file_type]}'")

        query = " and ".join(query_parts)

        # Fetch files
        results = (
            service.files()
            .list(
                q=query,
                pageSize=min(max_results, 1000),
                orderBy=order_by,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)",
            )
            .execute()
        )

        files = results.get("files", [])

        return {
            "files": files,
            "count": len(files),
        }


class GoogleDriveDownloadNode(BaseNode):
    """
    Download files from Google Drive.

    Supports:
    - Direct downloads
    - Export Google Docs/Sheets/Slides to various formats
    """

    type = "google-drive-download"
    name = "Google Drive: Download"
    category = "Apps"
    description = "Download a file from Google Drive"
    icon = "cloud_download"
    color = "#4285F4"

    inputs = [
        NodeField(
            name="credential",
            label="Google Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Google credential.",
            credential_service="google_oauth",
        ),
        NodeField(
            name="credentials_json",
            label="Service Account JSON",
            type=FieldType.SECRET,
            required=False,
            description="Google Service Account credentials JSON (or use saved credential).",
        ),
        NodeField(
            name="file_id",
            label="File ID",
            type=FieldType.STRING,
            required=True,
            description="Google Drive file ID to download.",
        ),
        NodeField(
            name="export_format",
            label="Export Format",
            type=FieldType.SELECT,
            required=False,
            default="auto",
            options=[
                {"value": "auto", "label": "Auto (Native Format)"},
                {"value": "pdf", "label": "PDF"},
                {"value": "docx", "label": "Word Document"},
                {"value": "xlsx", "label": "Excel Spreadsheet"},
                {"value": "pptx", "label": "PowerPoint"},
                {"value": "txt", "label": "Plain Text"},
                {"value": "csv", "label": "CSV"},
            ],
            description="Export format for Google Docs/Sheets/Slides.",
        ),
    ]

    outputs = [
        NodeField(
            name="content",
            label="Content",
            type=FieldType.STRING,
            description="File content (base64 encoded for binary files).",
        ),
        NodeField(
            name="filename",
            label="Filename",
            type=FieldType.STRING,
            description="Original filename.",
        ),
        NodeField(
            name="mime_type",
            label="MIME Type",
            type=FieldType.STRING,
            description="File MIME type.",
        ),
        NodeField(
            name="size",
            label="Size",
            type=FieldType.NUMBER,
            description="File size in bytes.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Download file from Google Drive."""

        service = _get_drive_service(config)

        file_id = config.get("file_id", "")
        export_format = config.get("export_format", "auto")

        # Get file metadata
        file_meta = (
            service.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, size",
            )
            .execute()
        )

        mime_type = file_meta.get("mimeType", "")
        filename = file_meta.get("name", "")

        # Google Workspace files need export
        google_mime_types = {
            "application/vnd.google-apps.document": {
                "auto": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "txt": "text/plain",
            },
            "application/vnd.google-apps.spreadsheet": {
                "auto": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "pdf": "application/pdf",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "csv": "text/csv",
            },
            "application/vnd.google-apps.presentation": {
                "auto": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "pdf": "application/pdf",
                "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            },
        }

        if mime_type in google_mime_types:
            # Export Google Workspace file
            export_mime = google_mime_types[mime_type].get(
                export_format, google_mime_types[mime_type]["auto"]
            )

            request = service.files().export_media(
                fileId=file_id,
                mimeType=export_mime,
            )
            content = request.execute()

            # Update filename with export extension
            ext_map = {
                "application/pdf": ".pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
                "text/plain": ".txt",
                "text/csv": ".csv",
            }
            if export_mime in ext_map:
                base_name = filename.rsplit(".", 1)[0] if "." in filename else filename
                filename = base_name + ext_map[export_mime]

            return {
                "content": base64.b64encode(content).decode("utf-8"),
                "filename": filename,
                "mime_type": export_mime,
                "size": len(content),
            }
        else:
            # Direct download
            request = service.files().get_media(fileId=file_id)
            content = request.execute()

            return {
                "content": base64.b64encode(content).decode("utf-8"),
                "filename": filename,
                "mime_type": mime_type,
                "size": len(content),
            }


class GoogleDriveUploadNode(BaseNode):
    """
    Upload files to Google Drive.

    Supports:
    - Creating new files
    - Uploading to specific folders
    - Setting file metadata
    """

    type = "google-drive-upload"
    name = "Google Drive: Upload"
    category = "Apps"
    description = "Upload a file to Google Drive"
    icon = "cloud_upload"
    color = "#4285F4"

    inputs = [
        NodeField(
            name="credential",
            label="Google Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Google credential.",
            credential_service="google_oauth",
        ),
        NodeField(
            name="credentials_json",
            label="Service Account JSON",
            type=FieldType.SECRET,
            required=False,
            description="Google Service Account credentials JSON (or use saved credential).",
        ),
        NodeField(
            name="filename",
            label="Filename",
            type=FieldType.STRING,
            required=True,
            description="Name for the uploaded file.",
        ),
        NodeField(
            name="content",
            label="Content",
            type=FieldType.TEXT,
            required=True,
            description="File content (text or base64 encoded binary).",
        ),
        NodeField(
            name="mime_type",
            label="MIME Type",
            type=FieldType.STRING,
            required=False,
            default="text/plain",
            description="MIME type of the file.",
        ),
        NodeField(
            name="folder_id",
            label="Folder ID",
            type=FieldType.STRING,
            required=False,
            description="Folder ID to upload to (leave empty for root).",
        ),
        NodeField(
            name="is_base64",
            label="Content is Base64",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Set to true if content is base64 encoded.",
        ),
    ]

    outputs = [
        NodeField(
            name="file_id",
            label="File ID",
            type=FieldType.STRING,
            description="ID of the uploaded file.",
        ),
        NodeField(
            name="web_link",
            label="Web Link",
            type=FieldType.STRING,
            description="Link to view the file.",
        ),
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether upload was successful.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Upload file to Google Drive."""
        from io import BytesIO

        try:
            from googleapiclient.http import MediaIoBaseUpload
        except ImportError:
            raise RuntimeError(
                "Google API libraries not installed. Install with: "
                "pip install google-auth google-auth-oauthlib google-api-python-client"
            )

        service = _get_drive_service(config)

        filename = config.get("filename", "untitled")
        content = config.get("content", "")
        mime_type = config.get("mime_type", "text/plain")
        folder_id = config.get("folder_id")
        is_base64 = config.get("is_base64", False)

        # Prepare content
        if is_base64:
            file_content = base64.b64decode(content)
        else:
            file_content = content.encode("utf-8")

        # Prepare metadata
        file_metadata = {"name": filename}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        # Create media upload
        media = MediaIoBaseUpload(
            BytesIO(file_content),
            mimetype=mime_type,
            resumable=True,
        )

        # Upload file
        file = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink",
            )
            .execute()
        )

        return {
            "file_id": file.get("id", ""),
            "web_link": file.get("webViewLink", ""),
            "success": True,
        }


class GoogleDriveCreateFolderNode(BaseNode):
    """
    Create folders in Google Drive.
    """

    type = "google-drive-create-folder"
    name = "Google Drive: Create Folder"
    category = "Apps"
    description = "Create a new folder in Google Drive"
    icon = "create_new_folder"
    color = "#4285F4"

    inputs = [
        NodeField(
            name="credential",
            label="Google Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Google credential.",
            credential_service="google_oauth",
        ),
        NodeField(
            name="credentials_json",
            label="Service Account JSON",
            type=FieldType.SECRET,
            required=False,
            description="Google Service Account credentials JSON (or use saved credential).",
        ),
        NodeField(
            name="folder_name",
            label="Folder Name",
            type=FieldType.STRING,
            required=True,
            description="Name for the new folder.",
        ),
        NodeField(
            name="parent_id",
            label="Parent Folder ID",
            type=FieldType.STRING,
            required=False,
            description="Parent folder ID (leave empty for root).",
        ),
    ]

    outputs = [
        NodeField(
            name="folder_id",
            label="Folder ID",
            type=FieldType.STRING,
            description="ID of the created folder.",
        ),
        NodeField(
            name="web_link",
            label="Web Link",
            type=FieldType.STRING,
            description="Link to the folder.",
        ),
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether creation was successful.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Create folder in Google Drive."""
        service = _get_drive_service(config)

        folder_name = config.get("folder_name", "New Folder")
        parent_id = config.get("parent_id")

        # Prepare metadata
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]

        # Create folder
        folder = (
            service.files()
            .create(
                body=file_metadata,
                fields="id, webViewLink",
            )
            .execute()
        )

        return {
            "folder_id": folder.get("id", ""),
            "web_link": folder.get("webViewLink", ""),
            "success": True,
        }


class GoogleDriveDeleteNode(BaseNode):
    """
    Delete files or folders from Google Drive.
    """

    type = "google-drive-delete"
    name = "Google Drive: Delete"
    category = "Apps"
    description = "Delete a file or folder from Google Drive"
    icon = "delete"
    color = "#4285F4"

    inputs = [
        NodeField(
            name="credential",
            label="Google Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Google credential.",
            credential_service="google_oauth",
        ),
        NodeField(
            name="credentials_json",
            label="Service Account JSON",
            type=FieldType.SECRET,
            required=False,
            description="Google Service Account credentials JSON (or use saved credential).",
        ),
        NodeField(
            name="file_id",
            label="File/Folder ID",
            type=FieldType.STRING,
            required=True,
            description="ID of the file or folder to delete.",
        ),
        NodeField(
            name="trash",
            label="Move to Trash",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
            description="Move to trash instead of permanent delete.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether deletion was successful.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Delete file or folder from Google Drive."""
        service = _get_drive_service(config)

        file_id = config.get("file_id", "")
        trash = config.get("trash", True)

        if trash:
            # Move to trash
            service.files().update(
                fileId=file_id,
                body={"trashed": True},
            ).execute()
        else:
            # Permanent delete
            service.files().delete(fileId=file_id).execute()

        return {"success": True}
