# Knowledge Bases User Guide

## Overview

The Knowledge Bases feature allows you to create searchable collections of documents using Retrieval Augmented Generation (RAG) technology.

## Creating a Collection

1. Navigate to **AI Hub** → **Knowledge Bases**
2. Click **New Collection**
3. Fill in the form:
   - **Name**: Alphanumeric name (e.g., "ProjectDocs")
   - **Description**: Optional description
   - **Embedding Model**: Choose Local (free), OpenAI, or Cohere
   - **Chunking Settings**: Leave defaults unless you know what you're doing
4. Click **Save**

## Uploading Documents

### Supported Formats
- Markdown (.md)
- Text (.txt)

### Upload Methods

1. **File Picker**: Click "Select Files" and choose files
2. **Drag & Drop**: Drag files directly into the drop area
3. **Folder**: Select an entire folder to index recursively

### Upload Process

- Files are processed in parallel (up to 5 at a time)
- Progress bar shows overall status
- Failed files are reported with specific error messages
- You can continue using the app while upload is in progress

## Querying a Collection

1. Click **Query** on a collection card
2. Enter your question in natural language
3. Adjust options:
   - **Top K**: Number of results to return (1-10)
   - **Min Similarity**: Threshold for relevance (0.0-1.0)
4. Click **Search**

### Understanding Results

- Results are ranked by similarity score
- Higher scores = more relevant
- Click **Copy** to copy chunk text to clipboard
- Query time is displayed for performance monitoring

## Managing Collections

Click **Manage** on a collection card to:
- Edit settings
- Add more documents
- View collection statistics
- Delete collection (⚠️ cannot be undone)

## Tips

- Use descriptive collection names
- Start with default chunking settings
- Lower min similarity if you get no results
- Use specific queries for better results
- Delete unused collections to save space
