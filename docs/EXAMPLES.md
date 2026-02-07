# Skynette Workflow Examples

**Practical automation workflows to get you started**

This guide provides ready-to-use workflow examples for common automation scenarios. Each example includes:
- 📋 Use case description
- 🎯 Required nodes
- ⚙️ Configuration
- 💡 Tips and variations

## Table of Contents

- [Example 1: Daily Weather Email](#example-1-daily-weather-email)
- [Example 2: AI-Powered Email Responder](#example-2-ai-powered-email-responder)
- [Example 3: Document Summarizer](#example-3-document-summarizer)
- [Example 4: Social Media Content Generator](#example-4-social-media-content-generator)
- [Example 5: Data Backup Automation](#example-5-data-backup-automation)
- [Example 6: Knowledge Base Q&A Bot](#example-6-knowledge-base-qa-bot)
- [Example 7: Code Review Assistant](#example-7-code-review-assistant)
- [Example 8: Automated Report Generation](#example-8-automated-report-generation)
- [Example 9: Sentiment Analysis Pipeline](#example-9-sentiment-analysis-pipeline)
- [Example 10: Multi-Provider AI with Fallback](#example-10-multi-provider-ai-with-fallback)

---

## Example 1: Daily Weather Email

**Use Case**: Get a personalized weather report every morning via email.

### Workflow

```
Schedule Trigger (Daily 8 AM)
    ↓
HTTP Request (Fetch weather)
    ↓
AI Text Generation (Format report)
    ↓
Send Email (Deliver report)
```

### Node Configuration

**1. Schedule Trigger**
```yaml
Name: Daily Morning Trigger
Schedule: 0 8 * * *  # 8 AM daily
Timezone: America/New_York
```

**2. HTTP Request**
```yaml
Name: Get Weather Data
Method: GET
URL: https://api.open-meteo.com/v1/forecast
Parameters:
  latitude: 40.7128
  longitude: -74.0060
  daily: temperature_2m_max,temperature_2m_min,precipitation_sum
  timezone: America/New_York
  forecast_days: 1
```

**3. AI Text Generation**
```yaml
Name: Format Weather Report
Provider: openai (or any)
Model: gpt-3.5-turbo
Prompt: |
  Create a friendly, casual weather report from this data:
  {{$prev.data}}
  
  Include:
  - High and low temperature
  - Precipitation chance
  - Clothing recommendation
  - Have a nice day message
Temperature: 0.7
Max Tokens: 200
```

**4. Send Email**
```yaml
Name: Send Report
To: your.email@example.com
Subject: Your Daily Weather Report
Body: {{$prev.text}}
```

### Tips

- **Personalize**: Add location lookup based on IP or user input
- **Multiple locations**: Loop through multiple cities
- **Rich formatting**: Use HTML email with weather icons
- **Variations**: Add UV index, air quality, or pollen count

---

## Example 2: AI-Powered Email Responder

**Use Case**: Auto-respond to customer support emails with AI-generated answers.

### Workflow

```
Webhook Trigger (New email via API)
    ↓
Extract Email Content
    ↓
AI Classify (Determine category)
    ↓
If/Else (Route by category)
    ↓
Query Knowledge Base (Get relevant info)
    ↓
AI Text Generation (Generate response)
    ↓
Send Email Response
```

### Node Configuration

**1. Webhook Trigger**
```yaml
Name: Email Webhook
Path: /api/support-email
Method: POST
Authentication: Bearer token
```

**2. Extract Email Content**
```yaml
Name: Parse Email
Expression: |
  {
    "from": "{{$trigger.body.from}}",
    "subject": "{{$trigger.body.subject}}",
    "body": "{{$trigger.body.body}}"
  }
```

**3. AI Classify**
```yaml
Name: Categorize Email
Text: {{$prev.subject}} - {{$prev.body}}
Categories:
  - billing
  - technical_support
  - feature_request
  - general_inquiry
```

**4. If/Else Node**
```yaml
Name: Route by Category
Conditions:
  - If: {{$prev.category}} == "billing"
    Then: Query billing KB
  - If: {{$prev.category}} == "technical_support"
    Then: Query tech KB
  - Else: Query general KB
```

**5. Query Knowledge Base**
```yaml
Name: Find Relevant Info
Collection: customer_support_docs
Query: {{$node.parse.subject}} {{$node.parse.body}}
Top K: 3
Min Similarity: 0.7
```

**6. AI Text Generation**
```yaml
Name: Generate Response
Provider: anthropic
Model: claude-2
Prompt: |
  You are a helpful customer support agent.
  
  Customer email:
  Subject: {{$node.parse.subject}}
  {{$node.parse.body}}
  
  Relevant documentation:
  {{$prev.results}}
  
  Write a professional, helpful response.
  Be concise but thorough.
Temperature: 0.3
Max Tokens: 500
```

**7. Send Email Response**
```yaml
Name: Reply to Customer
To: {{$node.parse.from}}
Subject: Re: {{$node.parse.subject}}
Body: {{$prev.text}}
```

### Tips

- **Add human review**: Insert approval step for sensitive categories
- **Track metrics**: Log response time and customer category
- **Escalation**: Forward complex issues to humans
- **Feedback loop**: Let customers rate AI responses

---

## Example 3: Document Summarizer

**Use Case**: Automatically summarize long documents into concise overviews.

### Workflow

```
Manual Trigger (Upload file)
    ↓
Read File
    ↓
If (Check length)
    ↓
[Long] Chunk Document → Loop → AI Summarize Each → Combine
[Short] AI Summarize Directly
    ↓
Write Summary File
```

### Node Configuration

**1. Manual Trigger**
```yaml
Name: Start Summarization
Fields:
  - file_path: File to summarize
```

**2. Read File**
```yaml
Name: Load Document
Path: {{$trigger.file_path}}
Encoding: utf-8
```

**3. If Node**
```yaml
Name: Check Document Length
Condition: {{$prev.content.length}} > 10000
```

**4. Chunk Document** (if long)
```yaml
Name: Split into Chunks
Text: {{$node.load.content}}
Chunk Size: 2000
Overlap: 200
```

**5. Loop** (if long)
```yaml
Name: Process Each Chunk
Items: {{$prev.chunks}}
```

**6. AI Summarize**
```yaml
Name: Summarize Text
Provider: openai
Model: gpt-4-turbo
Prompt: |
  Summarize this text concisely:
  {{$loop.item}}
  
  Focus on:
  - Main points
  - Key facts
  - Important conclusions
Temperature: 0.3
Max Tokens: 300
```

**7. Combine Summaries** (if long)
```yaml
Name: Merge Summaries
Expression: |
  {{$prev.map(item => item.text).join('\n\n')}}
```

**8. Final Summary** (if long)
```yaml
Name: Create Final Summary
Provider: openai
Model: gpt-4-turbo
Prompt: |
  Create a cohesive summary from these section summaries:
  {{$prev.combined}}
  
  Make it flow naturally and be comprehensive.
Temperature: 0.3
Max Tokens: 500
```

**9. Write Summary File**
```yaml
Name: Save Summary
Path: {{$trigger.file_path}}.summary.txt
Content: |
  # Summary of {{$trigger.file_path}}
  Generated: {{$now}}
  
  {{$prev.text}}
```

### Tips

- **Support PDF**: Add PDF parser node
- **Custom templates**: Use different prompts for different document types
- **Multi-format output**: Generate markdown, plain text, and HTML versions
- **Key points extraction**: Also extract bullet points separately

---

## Example 4: Social Media Content Generator

**Use Case**: Generate engaging social media posts from blog articles.

### Workflow

```
Manual/Schedule Trigger
    ↓
Read Blog Article (URL or file)
    ↓
AI Extract (Key points)
    ↓
Loop (Multiple platforms)
    ↓
AI Generate (Platform-specific post)
    ↓
Post to Platform (API)
```

### Node Configuration

**1. Schedule Trigger**
```yaml
Name: Weekly Content Push
Schedule: 0 9 * * 1  # Monday 9 AM
```

**2. Read Blog Article**
```yaml
Name: Fetch Article
URL: {{$env.LATEST_BLOG_POST}}
Method: GET
```

**3. AI Extract Key Points**
```yaml
Name: Extract Main Ideas
Provider: openai
Model: gpt-4-turbo
Prompt: |
  Extract 5 key points from this article:
  {{$prev.content}}
  
  Return as JSON array of strings.
Temperature: 0.3
Output Format: JSON
```

**4. Loop Platforms**
```yaml
Name: Generate for Each Platform
Items:
  - platform: twitter
    max_length: 280
    style: concise
  - platform: linkedin
    max_length: 1300
    style: professional
  - platform: instagram
    max_length: 2200
    style: engaging
```

**5. AI Generate Post**
```yaml
Name: Create Platform Post
Provider: anthropic
Model: claude-2
Prompt: |
  Create a {{$loop.item.style}} post for {{$loop.item.platform}}.
  
  Key points:
  {{$node.extract.points}}
  
  Requirements:
  - Max {{$loop.item.max_length}} characters
  - Include relevant hashtags
  - Engaging hook
  - Call to action
  
  Style: {{$loop.item.style}}
Temperature: 0.8
Max Tokens: 300
```

**6. Post to Platform**
```yaml
Name: Publish Post
Platform: {{$loop.item.platform}}
Content: {{$prev.text}}
API Key: {{$env[{{$loop.item.platform}}_API_KEY]}}
```

### Tips

- **Add images**: Use AI image generation (DALL-E, Midjourney)
- **Schedule posts**: Use platform scheduling APIs
- **A/B testing**: Generate multiple variants
- **Analytics**: Track engagement and iterate

---

## Example 5: Data Backup Automation

**Use Case**: Automatically backup important files to cloud storage.

### Workflow

```
Schedule Trigger (Daily)
    ↓
List Files (Watch directory)
    ↓
Filter (Only changed since last backup)
    ↓
Loop Files
    ↓
Read File
    ↓
Upload to Cloud (S3/Drive/Dropbox)
    ↓
Log Backup Status
```

### Node Configuration

**1. Schedule Trigger**
```yaml
Name: Daily Backup
Schedule: 0 2 * * *  # 2 AM daily
```

**2. List Files**
```yaml
Name: Find Files to Backup
Path: ~/Documents/important
Pattern: **/*.{txt,md,json,yaml,pdf}
Recursive: true
```

**3. Filter Files**
```yaml
Name: Only Recent Changes
Expression: |
  {{$prev.files.filter(f => 
    new Date(f.modified) > new Date({{$env.LAST_BACKUP}})
  )}}
```

**4. Loop Files**
```yaml
Name: Process Each File
Items: {{$prev.filtered}}
```

**5. Read File**
```yaml
Name: Load File Content
Path: {{$loop.item.path}}
Encoding: auto
```

**6. Upload to Cloud**
```yaml
Name: Upload to S3
Service: aws_s3
Bucket: my-backup-bucket
Key: backups/{{$now.format('YYYY-MM-DD')}}/{{$loop.item.name}}
Content: {{$prev.content}}
```

**7. Log Backup**
```yaml
Name: Record Backup
Database: backup_log
Query: |
  INSERT INTO backups (file, size, timestamp, cloud_path)
  VALUES (
    '{{$loop.item.name}}',
    {{$loop.item.size}},
    '{{$now}}',
    '{{$prev.cloud_path}}'
  )
```

### Tips

- **Compression**: Add ZIP compression before upload
- **Encryption**: Encrypt sensitive files
- **Retention policy**: Auto-delete old backups
- **Multiple destinations**: Upload to multiple cloud services
- **Notifications**: Send summary email with backup stats

---

## Example 6: Knowledge Base Q&A Bot

**Use Case**: Answer questions using your company documentation.

### Workflow

```
Webhook Trigger (Question endpoint)
    ↓
Query Knowledge Base
    ↓
AI Generate Answer (Using retrieved context)
    ↓
Return Response
```

### Node Configuration

**1. Webhook Trigger**
```yaml
Name: Question Endpoint
Path: /api/ask
Method: POST
Body:
  question: string (required)
```

**2. Query Knowledge Base**
```yaml
Name: Find Relevant Docs
Collection: company_documentation
Query: {{$trigger.body.question}}
Top K: 5
Min Similarity: 0.6
```

**3. AI Generate Answer**
```yaml
Name: Answer Question
Provider: openai
Model: gpt-4
Prompt: |
  Answer this question using ONLY the provided context.
  If the answer isn't in the context, say "I don't have enough information."
  
  Question: {{$trigger.body.question}}
  
  Context:
  {{$prev.results}}
  
  Provide a clear, accurate answer with sources.
Temperature: 0.2
Max Tokens: 500
```

**4. Return Response**
```yaml
Name: Send Answer
Response:
  answer: {{$prev.text}}
  sources: {{$node.find.sources}}
  confidence: {{$node.find.similarity}}
Status: 200
```

### Tips

- **Conversation history**: Include previous Q&A for context
- **Confidence threshold**: Only answer if similarity > 0.7
- **Fallback**: Escalate low-confidence questions to humans
- **Feedback**: Let users rate answers to improve the system
- **Multiple collections**: Search across multiple knowledge bases

---

## Example 7: Code Review Assistant

**Use Case**: Automatically review code changes and suggest improvements.

### Workflow

```
Webhook Trigger (GitHub PR)
    ↓
Fetch PR Diff
    ↓
Split by File
    ↓
Loop Files
    ↓
AI Code Review
    ↓
Post Comment on PR
```

### Node Configuration

**1. Webhook Trigger**
```yaml
Name: GitHub PR Webhook
Path: /api/github/pr
Method: POST
Events:
  - pull_request.opened
  - pull_request.synchronize
```

**2. Fetch PR Diff**
```yaml
Name: Get Code Changes
URL: {{$trigger.body.pull_request.diff_url}}
Method: GET
Headers:
  Authorization: token {{$env.GITHUB_TOKEN}}
```

**3. Split by File**
```yaml
Name: Parse Diff
Expression: |
  {{$prev.diff.split('diff --git').map(parseDiff)}}
```

**4. Loop Files**
```yaml
Name: Review Each File
Items: {{$prev.files}}
```

**5. AI Code Review**
```yaml
Name: Analyze Code
Provider: openai
Model: gpt-4-turbo
Prompt: |
  Review this code change:
  
  File: {{$loop.item.filename}}
  {{$loop.item.diff}}
  
  Check for:
  - Bugs or logic errors
  - Security vulnerabilities
  - Performance issues
  - Code style problems
  - Missing tests
  
  Only report significant issues.
  Format as markdown with line numbers.
Temperature: 0.3
Max Tokens: 800
```

**6. Post Comment**
```yaml
Name: Comment on PR
URL: {{$trigger.body.pull_request.comments_url}}
Method: POST
Headers:
  Authorization: token {{$env.GITHUB_TOKEN}}
Body:
  body: |
    ## 🤖 AI Code Review
    
    {{$prev.text}}
```

### Tips

- **Filter files**: Only review .py, .js, .ts files
- **Rate limiting**: Don't review very large PRs
- **Style checking**: Run linters first
- **Test coverage**: Check if tests were added
- **Human approval**: Require human review for security issues

---

## Example 8: Automated Report Generation

**Use Case**: Generate weekly business reports from database data.

### Workflow

```
Schedule Trigger (Weekly)
    ↓
Query Database (Multiple queries)
    ↓
AI Analyze Data
    ↓
Generate Charts
    ↓
Create Report (Markdown/HTML)
    ↓
Send Report Email
```

### Node Configuration

**1. Schedule Trigger**
```yaml
Name: Weekly Report
Schedule: 0 9 * * 1  # Monday 9 AM
```

**2. Query Sales Data**
```yaml
Name: Get Weekly Sales
Database: postgres
Query: |
  SELECT 
    date,
    SUM(amount) as daily_sales,
    COUNT(*) as num_orders
  FROM orders
  WHERE date >= CURRENT_DATE - INTERVAL '7 days'
  GROUP BY date
  ORDER BY date
```

**3. Query User Growth**
```yaml
Name: Get User Stats
Database: postgres
Query: |
  SELECT 
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - 7) as new_users
  FROM users
```

**4. AI Analyze Data**
```yaml
Name: Generate Insights
Provider: anthropic
Model: claude-2
Prompt: |
  Analyze this business data and provide insights:
  
  Weekly Sales:
  {{$node.sales.data}}
  
  User Growth:
  {{$node.users.data}}
  
  Include:
  - Trends (up/down)
  - Key metrics
  - Recommendations
Temperature: 0.3
Max Tokens: 600
```

**5. Generate Chart**
```yaml
Name: Create Sales Chart
Type: line
Data: {{$node.sales.data}}
X: date
Y: daily_sales
Title: Daily Sales - Last 7 Days
```

**6. Create Report**
```yaml
Name: Build HTML Report
Template: |
  <html>
  <head><title>Weekly Report</title></head>
  <body>
    <h1>Weekly Business Report</h1>
    <p>Week ending {{$now.format('YYYY-MM-DD')}}</p>
    
    <h2>Key Metrics</h2>
    <ul>
      <li>Total Sales: ${{$node.sales.total}}</li>
      <li>New Users: {{$node.users.new_users}}</li>
    </ul>
    
    <h2>AI Insights</h2>
    {{$node.insights.text}}
    
    <h2>Sales Trend</h2>
    <img src="{{$node.chart.url}}" />
  </body>
  </html>
```

**7. Send Report**
```yaml
Name: Email Report
To: management@company.com
Subject: Weekly Business Report - {{$now.format('YYYY-MM-DD')}}
Body: {{$prev.html}}
Content-Type: text/html
```

### Tips

- **Multiple reports**: Create different versions for different audiences
- **Interactive dashboards**: Link to live dashboard
- **Trend comparison**: Compare to previous week/month
- **Anomaly detection**: Highlight unusual patterns
- **PDF export**: Convert HTML to PDF for archiving

---

## Example 9: Sentiment Analysis Pipeline

**Use Case**: Analyze customer feedback sentiment at scale.

### Workflow

```
Schedule Trigger (Hourly)
    ↓
Fetch New Feedback (API/Database)
    ↓
Loop Each Feedback
    ↓
AI Classify Sentiment
    ↓
Extract Key Themes
    ↓
Update Database
    ↓
If (Negative) → Alert Team
```

### Node Configuration

**1. Schedule Trigger**
```yaml
Name: Hourly Feedback Check
Schedule: 0 * * * *  # Every hour
```

**2. Fetch Feedback**
```yaml
Name: Get New Feedback
Database: feedback_db
Query: |
  SELECT id, user_id, text, created_at
  FROM feedback
  WHERE processed = false
  LIMIT 100
```

**3. Loop Feedback**
```yaml
Name: Process Each Item
Items: {{$prev.rows}}
```

**4. AI Classify Sentiment**
```yaml
Name: Analyze Sentiment
Provider: openai
Model: gpt-3.5-turbo
Prompt: |
  Classify the sentiment of this feedback:
  "{{$loop.item.text}}"
  
  Return JSON:
  {
    "sentiment": "positive" | "negative" | "neutral",
    "confidence": 0.0-1.0,
    "emotion": "happy" | "angry" | "confused" | "satisfied"
  }
Temperature: 0.1
Output Format: JSON
```

**5. Extract Themes**
```yaml
Name: Identify Themes
Provider: openai
Model: gpt-3.5-turbo
Prompt: |
  Extract key themes/topics from this feedback:
  "{{$loop.item.text}}"
  
  Categories:
  - product_quality
  - customer_service
  - pricing
  - features
  - bugs
  - other
  
  Return JSON array of relevant categories.
Temperature: 0.2
Output Format: JSON
```

**6. Update Database**
```yaml
Name: Save Analysis
Database: feedback_db
Query: |
  UPDATE feedback
  SET 
    sentiment = '{{$prev.sentiment}}',
    confidence = {{$prev.confidence}},
    themes = '{{$prev.themes}}',
    processed = true
  WHERE id = {{$loop.item.id}}
```

**7. If Negative Alert**
```yaml
Name: Check if Negative
Condition: {{$node.analyze.sentiment}} == "negative" AND {{$node.analyze.confidence}} > 0.8
```

**8. Alert Team**
```yaml
Name: Send Slack Alert
Webhook: {{$env.SLACK_WEBHOOK}}
Message: |
  ⚠️ Negative feedback detected!
  
  User: {{$loop.item.user_id}}
  Confidence: {{$node.analyze.confidence}}
  Text: {{$loop.item.text}}
  
  Themes: {{$node.themes.themes}}
```

### Tips

- **Aggregate reports**: Daily sentiment summary
- **Trend tracking**: Monitor sentiment over time
- **Priority scoring**: Combine sentiment + user importance
- **Auto-response**: Send thank you for positive feedback
- **Topic modeling**: Find emerging issues

---

## Example 10: Multi-Provider AI with Fallback

**Use Case**: Use multiple AI providers with automatic fallback for reliability.

### Workflow

```
Manual Trigger
    ↓
Try Primary AI Provider
    ↓
Error Handler
    ↓
Try Secondary Provider
    ↓
Error Handler
    ↓
Try Tertiary Provider
    ↓
If All Fail → Use Local Model
```

### Node Configuration

**1. Manual Trigger**
```yaml
Name: Start Request
Fields:
  - prompt: Text to generate
```

**2. Try OpenAI**
```yaml
Name: OpenAI (Primary)
Provider: openai
Model: gpt-4-turbo
Prompt: {{$trigger.prompt}}
Temperature: 0.7
Max Tokens: 500
Continue on Error: true
```

**3. Error Handler**
```yaml
Name: Check OpenAI Success
Condition: {{$prev.error}} exists
```

**4. Try Anthropic**
```yaml
Name: Anthropic (Secondary)
Provider: anthropic
Model: claude-2
Prompt: {{$trigger.prompt}}
Temperature: 0.7
Max Tokens: 500
Continue on Error: true
Only Run If: {{$node.check.failed}}
```

**5. Try Google**
```yaml
Name: Google AI (Tertiary)
Provider: google
Model: gemini-pro
Prompt: {{$trigger.prompt}}
Temperature: 0.7
Max Tokens: 500
Continue on Error: true
Only Run If: {{$node.check.failed}} AND {{$node.anthropic.error}}
```

**6. Try Local**
```yaml
Name: Local Fallback
Provider: local
Model: mistral-7b-q4
Prompt: {{$trigger.prompt}}
Temperature: 0.7
Max Tokens: 500
Only Run If: All previous failed
```

**7. Merge Results**
```yaml
Name: Get First Success
Expression: |
  {{$node.openai.text}} || 
  {{$node.anthropic.text}} || 
  {{$node.google.text}} || 
  {{$node.local.text}}
```

**8. Log Provider Used**
```yaml
Name: Record Metrics
Database: metrics
Query: |
  INSERT INTO ai_calls (provider, success, latency)
  VALUES ('{{$prev.provider}}', true, {{$prev.latency}})
```

### Tips

- **Cost optimization**: Try cheaper providers first
- **Performance tracking**: Log response times
- **Rate limiting**: Respect API limits
- **Provider health**: Disable failing providers temporarily
- **Custom routing**: Route by task type (coding → Claude, chat → GPT)

---

## Next Steps

**Learn More:**
- 📖 [User Guide](USER_GUIDE.md) - Complete usage guide
- ❓ [FAQ](FAQ.md) - Common questions
- 🚀 [Quickstart](../QUICKSTART.md) - Get started fast

**Get Help:**
- 💬 [Discussions](https://github.com/flyingpurplepizzaeater/Skynette/discussions)
- 🐛 [Issues](https://github.com/flyingpurplepizzaeater/Skynette/issues)

**Share Your Workflows:**
- Export your workflows
- Share in Discussions
- Help others learn!

---

**Happy Automating! 🚀**
