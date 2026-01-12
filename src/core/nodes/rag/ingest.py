"""
Ingest Document Node

Workflow node for ingesting documents into RAG collections.
"""

from typing import Any, Dict
from src.core.nodes.base import BaseNode, NodeField, FieldType


class IngestDocumentNode(BaseNode):
    """
    Ingest document into RAG collection.

    Parses document, creates chunks, generates embeddings, and stores in ChromaDB.
    """

    type = "rag-ingest-document"
    name = "Ingest Document"
    category = "RAG"
    description = "Index document for semantic search"
    icon = "upload_file"
    color = "#7C3AED"  # Purple (RAG category color)

    inputs = [
        NodeField(
            name="file_path",
            label="File Path",
            type=FieldType.FILE,
            required=True,
            description="Path to document to ingest (markdown, text)"
        ),
        NodeField(
            name="collection_id",
            label="Collection ID",
            type=FieldType.STRING,
            required=True,
            description="Target collection ID"
        ),
    ]

    outputs = [
        NodeField(
            name="document_id",
            label="Document ID",
            type=FieldType.STRING,
            description="ID of ingested document"
        ),
        NodeField(
            name="chunks_created",
            label="Chunks Created",
            type=FieldType.NUMBER,
            description="Number of chunks created"
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.STRING,
            description="Ingestion status (success/error)"
        ),
        NodeField(
            name="error",
            label="Error",
            type=FieldType.STRING,
            description="Error message if failed"
        ),
    ]

    def __init__(self, rag_service=None, **kwargs):
        """Initialize with RAG service."""
        super().__init__(**kwargs)
        self.rag_service = rag_service

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document ingestion."""
        try:
            file_path = inputs["file_path"]
            collection_id = inputs["collection_id"]

            # Ingest document
            result = await self.rag_service.ingest_document(
                file_path=file_path,
                collection_id=collection_id
            )

            if result["status"] == "success":
                return {
                    "document_id": result["document_id"],
                    "chunks_created": result["chunks_created"],
                    "status": "success",
                    "error": None
                }
            else:
                return {
                    "document_id": None,
                    "chunks_created": 0,
                    "status": "error",
                    "error": result.get("error", "Unknown error")
                }

        except Exception as e:
            return {
                "document_id": None,
                "chunks_created": 0,
                "status": "error",
                "error": str(e)
            }
