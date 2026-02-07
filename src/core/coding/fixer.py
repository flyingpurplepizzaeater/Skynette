"""
GitHub AutoFixer Integration.
Analyzes code and generates fixes using the AI Gateway.
"""

from src.ai.gateway import get_gateway


class FixGenerator:
    """Generates fixes for code issues using AI."""

    def __init__(self):
        self.gateway = get_gateway()

    async def analyze_issue(self, title: str, body: str, file_list: list[str]) -> str | None:
        """Determine which file needs fixing."""
        prompt = f"""
        You are a senior developer. Analyze this GitHub issue and identify the single most likely file that needs modification from the provided list.

        Issue Title: {title}
        Issue Body: {body}

        File List:
        {", ".join(file_list[:100])}

        Return ONLY the filename. If uncertain or the file isn't listed, return 'None'.
        """

        try:
            response = await self.gateway.generate(prompt)
            filename = response.content.strip()
            # Clean up potential markdown code blocks
            filename = filename.replace("`", "").strip()

            if filename == "None" or filename not in file_list:
                return None
            return filename
        except Exception as e:
            print(f"Analysis failed: {e}")
            return None

    async def generate_fix(
        self, title: str, body: str, file_content: str, filename: str
    ) -> str | None:
        """Generate the fixed code."""
        prompt = f"""
        You are an expert developer. Fix the bug described in the issue for the provided file.

        Issue: {title}
        Context: {body}
        File: {filename}

        Current Code:
        ```
        {file_content}
        ```

        Return ONLY the full, corrected code for the file. Do not include markdown formatting or explanations.
        """

        try:
            response = await self.gateway.generate(prompt)
            code = response.content.strip()

            # Strip markdown code blocks if present
            if code.startswith("```"):
                lines = code.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                code = "\n".join(lines)

            return code
        except Exception as e:
            print(f"Fix generation failed: {e}")
            return None
