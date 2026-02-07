"""
Twitter/X Integration Nodes - Post tweets and interact with Twitter API v2.
"""

from src.core.nodes.base import BaseNode, FieldType, NodeField


class TwitterPostTweetNode(BaseNode):
    """
    Post a tweet to Twitter/X.

    Uses Twitter API v2 with OAuth 2.0.
    """

    type = "twitter-post-tweet"
    name = "Twitter: Post Tweet"
    category = "Apps"
    description = "Post a tweet to Twitter/X"
    icon = "edit"
    color = "#1DA1F2"  # Twitter blue

    inputs = [
        NodeField(
            name="bearer_token",
            label="Bearer Token",
            type=FieldType.SECRET,
            required=True,
            description="Twitter API Bearer Token.",
        ),
        NodeField(
            name="text",
            label="Tweet Text",
            type=FieldType.TEXT,
            required=True,
            description="Tweet content (max 280 characters).",
        ),
        NodeField(
            name="reply_to",
            label="Reply To Tweet ID",
            type=FieldType.STRING,
            required=False,
            description="Tweet ID to reply to.",
        ),
        NodeField(
            name="quote_tweet_id",
            label="Quote Tweet ID",
            type=FieldType.STRING,
            required=False,
            description="Tweet ID to quote.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
        ),
        NodeField(
            name="tweet_id",
            label="Tweet ID",
            type=FieldType.STRING,
        ),
        NodeField(
            name="tweet_url",
            label="Tweet URL",
            type=FieldType.STRING,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Post tweet to Twitter."""
        import httpx

        bearer_token = config.get("bearer_token", "")
        text = config.get("text", "")
        reply_to = config.get("reply_to")
        quote_tweet_id = config.get("quote_tweet_id")

        url = "https://api.twitter.com/2/tweets"

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        }

        payload = {"text": text}

        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}
        if quote_tweet_id:
            payload["quote_tweet_id"] = quote_tweet_id

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        if response.status_code == 201:
            tweet_id = data.get("data", {}).get("id", "")
            return {
                "success": True,
                "tweet_id": tweet_id,
                "tweet_url": f"https://twitter.com/i/status/{tweet_id}",
            }

        return {
            "success": False,
            "tweet_id": "",
            "tweet_url": "",
        }


class TwitterSearchTweetsNode(BaseNode):
    """
    Search for tweets.
    """

    type = "twitter-search-tweets"
    name = "Twitter: Search Tweets"
    category = "Apps"
    description = "Search for recent tweets"
    icon = "search"
    color = "#1DA1F2"

    inputs = [
        NodeField(
            name="bearer_token",
            label="Bearer Token",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="query",
            label="Search Query",
            type=FieldType.STRING,
            required=True,
            description="Twitter search query.",
        ),
        NodeField(
            name="max_results",
            label="Max Results",
            type=FieldType.NUMBER,
            required=False,
            default=10,
            description="Number of tweets to return (10-100).",
        ),
    ]

    outputs = [
        NodeField(
            name="tweets",
            label="Tweets",
            type=FieldType.JSON,
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Search tweets."""
        import httpx

        bearer_token = config.get("bearer_token", "")
        query = config.get("query", "")
        max_results = min(100, max(10, int(config.get("max_results", 10))))

        url = "https://api.twitter.com/2/tweets/search/recent"

        headers = {
            "Authorization": f"Bearer {bearer_token}",
        }

        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,author_id,public_metrics",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            data = response.json()

        tweets = data.get("data", [])

        return {
            "tweets": [
                {
                    "id": t.get("id"),
                    "text": t.get("text"),
                    "created_at": t.get("created_at"),
                    "author_id": t.get("author_id"),
                    "metrics": t.get("public_metrics", {}),
                }
                for t in tweets
            ],
            "count": len(tweets),
        }


class TwitterGetUserNode(BaseNode):
    """
    Get Twitter user information.
    """

    type = "twitter-get-user"
    name = "Twitter: Get User"
    category = "Apps"
    description = "Get Twitter user information"
    icon = "person"
    color = "#1DA1F2"

    inputs = [
        NodeField(
            name="bearer_token",
            label="Bearer Token",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="username",
            label="Username",
            type=FieldType.STRING,
            required=True,
            description="Twitter username (without @).",
        ),
    ]

    outputs = [
        NodeField(
            name="user",
            label="User Data",
            type=FieldType.JSON,
        ),
        NodeField(
            name="found",
            label="User Found",
            type=FieldType.BOOLEAN,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Get Twitter user."""
        import httpx

        bearer_token = config.get("bearer_token", "")
        username = config.get("username", "").lstrip("@")

        url = f"https://api.twitter.com/2/users/by/username/{username}"

        headers = {
            "Authorization": f"Bearer {bearer_token}",
        }

        params = {
            "user.fields": "description,public_metrics,profile_image_url,created_at,verified",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            data = response.json()

        user = data.get("data")

        if user:
            return {
                "user": {
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "username": user.get("username"),
                    "description": user.get("description"),
                    "profile_image": user.get("profile_image_url"),
                    "verified": user.get("verified", False),
                    "metrics": user.get("public_metrics", {}),
                    "created_at": user.get("created_at"),
                },
                "found": True,
            }

        return {
            "user": {},
            "found": False,
        }
