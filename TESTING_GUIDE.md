# Skynette v0.5.0 Testing Guide

This guide will walk you through testing all major features of Skynette to ensure everything works correctly.

## Prerequisites

- Skynette.exe built successfully (✓ Done - 260.3 MB)
- Windows 10+ system
- Internet connection (for cloud AI providers - optional)

## Quick Start

**Launch the application:**
1. Double-click `Skynette.lnk` in the project root
   - OR navigate to `dist/` and run `Skynette.exe`
2. Wait for the Flet window to open (may take 10-20 seconds on first launch)
3. The main dashboard should appear

## Test Checklist

### ✅ Test 1: Application Launch
**Expected**: Application starts without errors
- [ ] Skynette.exe launches successfully
- [ ] No console errors appear
- [ ] Main window opens within 30 seconds
- [ ] UI renders correctly (no blank screen)

**If it fails**: Check Windows Defender, antivirus, or run as Administrator

---

### ✅ Test 2: AI Hub - All 5 Tabs Load
**Navigation**: Click "AI Hub" in the main navigation
**Expected**: 5 tabs visible: Setup, My Providers, Model Library, Usage, Knowledge Bases

**Test each tab:**
- [ ] **Setup Tab**: Wizard with provider checkboxes (OpenAI, Anthropic, Google AI, Groq, Local Models)
- [ ] **My Providers Tab**: List of 5 providers with "Configure" buttons
- [ ] **Model Library Tab**: Two subtabs: "My Models" and "Download"
- [ ] **Usage Tab**: Analytics dashboard (may be empty if no usage yet)
- [ ] **Knowledge Bases Tab**: "Create Collection" button visible

---

### ✅ Test 3: AI Hub Setup Wizard
**Location**: AI Hub → Setup Tab

**Steps:**
1. [ ] Select "Local Models" checkbox
2. [ ] Click "Next: Configure →"
3. [ ] See message: "Local models run on your computer. No API key required!"
4. [ ] Click "Next →"
5. [ ] See "Setup Complete!" with green checkmark
6. [ ] Click "Get Started"

**Expected**: Wizard completes without errors, local models configured

---

### ✅ Test 4: Knowledge Bases - Create Collection
**Location**: AI Hub → Knowledge Bases Tab

**Steps:**
1. [ ] Click "Create Collection" button
2. [ ] Dialog appears with form fields
3. [ ] Enter Name: "Test Collection"
4. [ ] Enter Description: "Testing RAG functionality"
5. [ ] Embedding Model shows: "all-MiniLM-L6-v2 (384 dimensions)"
6. [ ] Click "Create"
7. [ ] Collection card appears with:
   - Name and description
   - "0 documents" counter
   - "0 chunks" counter
   - Last updated timestamp

**Expected**: Collection created successfully, card displays correct info

---

### ✅ Test 5: Knowledge Bases - Upload Documents
**Location**: AI Hub → Knowledge Bases → Click on "Test Collection"

**Prerequisites**: Create a test markdown file:
```bash
# Create test file in project root
echo "# Test Document

This is a test document for RAG functionality.

## Section 1
Some content about AI and machine learning.

## Section 2
More information about retrieval augmented generation.
" > test_document.md
```

**Steps:**
1. [ ] Click on "Test Collection" card
2. [ ] Click "Upload Documents" button
3. [ ] Upload dialog appears
4. [ ] Click "Choose Files" and select `test_document.md`
5. [ ] File appears in upload list
6. [ ] Click "Start Upload"
7. [ ] Progress bar shows:
   - "Processing: test_document.md"
   - Progress: 0% → 100%
   - Status: "Completed successfully"
8. [ ] Close dialog
9. [ ] Collection card updates:
   - "1 document" counter
   - Chunk count increases (should be 2-3 chunks)

**Expected**: Document uploads, processes, and chunks successfully

---

### ✅ Test 6: Knowledge Bases - Semantic Search
**Location**: AI Hub → Knowledge Bases → Test Collection

**Steps:**
1. [ ] Click on "Test Collection" card
2. [ ] Click "Query" button
3. [ ] Query dialog appears
4. [ ] Enter query: "What is retrieval augmented generation?"
5. [ ] Click "Search" or press Enter
6. [ ] Results appear with:
   - Relevant chunk from test_document.md
   - Similarity score (e.g., "85% match")
   - Source file: "test_document.md"
   - Copy button for each result
7. [ ] Click copy button
8. [ ] Snackbar shows: "Copied to clipboard"

**Expected**: Query returns relevant results with correct metadata

---

### ✅ Test 7: Knowledge Bases - Multiple File Upload
**Steps:**
1. [ ] Create 3 more test files (test2.md, test3.md, test4.md)
2. [ ] Click "Upload Documents"
3. [ ] Select all 3 files
4. [ ] Click "Start Upload"
5. [ ] Observe parallel processing (multiple "Processing" messages)
6. [ ] All files complete within reasonable time
7. [ ] Collection updates to show 4 total documents

**Expected**: Parallel processing works, all files upload successfully

---

### ✅ Test 8: Usage Dashboard
**Location**: AI Hub → Usage Tab

**What to check:**
- [ ] Dashboard loads without errors
- [ ] If no usage data: Shows empty state with helpful message
- [ ] If usage data exists:
  - Token usage charts
  - Cost estimates
  - Provider breakdown

**Expected**: Dashboard displays correctly (empty or with data)

---

### ✅ Test 9: Model Library - View Downloaded Models
**Location**: AI Hub → Model Library → My Models

**Expected**:
- [ ] If no models: Shows "No Models Downloaded" with icon
- [ ] If models exist: Shows list with model cards
- [ ] Each card has: Name, quantization, size, "Ready" status

---

### ✅ Test 10: Theme Toggle
**Location**: Settings (if available)

**Steps:**
1. [ ] Navigate to Settings
2. [ ] Find theme toggle
3. [ ] Switch between Light/Dark mode
4. [ ] UI colors update immediately
5. [ ] Theme persists after restart

**Expected**: Theme switches smoothly, setting persists

---

## Critical Issues to Report

If you encounter any of these, **stop testing and report**:
- Application crashes on startup
- White screen / frozen UI
- Cannot click any buttons
- Errors when creating collections
- Upload fails for all files
- Search returns no results for valid queries

## Performance Benchmarks

**Expected performance:**
- Launch time: 10-30 seconds
- Collection creation: < 1 second
- Single file upload (1KB): < 2 seconds
- Query response: < 1 second
- Switching tabs: Instant

**If slower**: May indicate issues with ChromaDB or embedding model

---

## Next Steps After Testing

**If all tests pass ✅:**
- Application is stable and ready for Phase 6 (integrations)
- Consider publishing to PyPI or creating installers

**If issues found 🐛:**
- Document each issue with:
  - Steps to reproduce
  - Expected vs actual behavior
  - Error messages or screenshots
- Prioritize fixes before proceeding

---

## Advanced Testing (Optional)

### Test API Key Configuration
1. Add OpenAI or Anthropic API key
2. Verify key stored in system keyring
3. Test AI provider connection

### Test Large File Upload
1. Create a 100KB markdown file
2. Upload and verify chunking
3. Check memory usage

### Test Error Handling
1. Try uploading unsupported file type (.pdf, .docx)
2. Try uploading file with invalid characters
3. Try creating collection with duplicate name
4. Verify error messages are helpful

---

## Cleanup After Testing

```bash
# Remove test files
rm test_document.md test2.md test3.md test4.md

# Optional: Clear RAG data
# rm -rf ~/.skynette/rag
```

---

**Questions or Issues?**
- Check logs in: `~/.skynette/logs/`
- Review error messages in console (if running from terminal)
- File GitHub issue: https://github.com/flyingpurplepizzaeater/Skynette/issues
