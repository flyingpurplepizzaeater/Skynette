# src/services/diff/diff_service.py
"""Diff generation and application service.

Uses Python's difflib to generate unified diffs and provides
methods to apply changes selectively.
"""

import difflib
import re

from .models import DiffHunk, DiffLine


class DiffService:
    """Generate and apply diffs between code versions.

    Uses difflib.unified_diff for generating diffs and provides
    methods to apply hunks selectively.

    Example:
        service = DiffService()
        hunks = service.generate_diff(original_code, modified_code)
        for hunk in hunks:
            print(f"Changes at line {hunk.source_start}")

        # Apply all changes
        result = service.apply_hunks(original_code, hunks)
    """

    # Regex to parse @@ -X,Y +A,B @@ header
    _HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")

    def generate_diff(
        self,
        original: str,
        modified: str,
        filename: str = "file",
        context_lines: int = 3,
    ) -> list[DiffHunk]:
        """Generate diff hunks between original and modified content.

        Args:
            original: Original content.
            modified: Modified content.
            filename: Filename for diff header.
            context_lines: Number of context lines around changes.

        Returns:
            List of DiffHunk objects representing changes.
        """
        # Split into lines, preserving line endings for accurate diff
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        # Add final newline if missing (for cleaner diff output)
        if original_lines and not original_lines[-1].endswith("\n"):
            original_lines[-1] += "\n"
        if modified_lines and not modified_lines[-1].endswith("\n"):
            modified_lines[-1] += "\n"

        # Generate unified diff
        diff_lines = list(
            difflib.unified_diff(
                original_lines,
                modified_lines,
                fromfile=f"a/{filename}",
                tofile=f"b/{filename}",
                n=context_lines,
            )
        )

        return self._parse_unified_diff(diff_lines)

    def _parse_unified_diff(self, diff_lines: list[str]) -> list[DiffHunk]:
        """Parse unified diff output into DiffHunk objects.

        Args:
            diff_lines: Lines from difflib.unified_diff output.

        Returns:
            List of parsed DiffHunk objects.
        """
        hunks: list[DiffHunk] = []
        current_hunk: DiffHunk | None = None
        old_line = 0
        new_line = 0

        for line in diff_lines:
            # Skip file headers
            if line.startswith("---") or line.startswith("+++"):
                continue

            # Parse hunk header
            match = self._HUNK_HEADER_RE.match(line)
            if match:
                source_start = int(match.group(1))
                source_length = int(match.group(2)) if match.group(2) else 1
                target_start = int(match.group(3))
                target_length = int(match.group(4)) if match.group(4) else 1
                context = match.group(5).strip()

                current_hunk = DiffHunk(
                    source_start=source_start,
                    source_length=source_length,
                    target_start=target_start,
                    target_length=target_length,
                    header=line.strip(),
                )
                hunks.append(current_hunk)
                old_line = source_start
                new_line = target_start
                continue

            if current_hunk is None:
                continue

            # Parse diff lines
            content = line[1:] if len(line) > 1 else ""
            # Remove trailing newline for clean display
            content = content.rstrip("\n\r")

            if line.startswith("-"):
                current_hunk.lines.append(
                    DiffLine(
                        content=content,
                        line_type="remove",
                        old_line_no=old_line,
                        new_line_no=None,
                    )
                )
                old_line += 1
            elif line.startswith("+"):
                current_hunk.lines.append(
                    DiffLine(
                        content=content,
                        line_type="add",
                        old_line_no=None,
                        new_line_no=new_line,
                    )
                )
                new_line += 1
            elif line.startswith(" "):
                current_hunk.lines.append(
                    DiffLine(
                        content=content,
                        line_type="context",
                        old_line_no=old_line,
                        new_line_no=new_line,
                    )
                )
                old_line += 1
                new_line += 1

        return hunks

    def apply_hunks(self, original: str, hunks: list[DiffHunk]) -> str:
        """Apply selected hunks to original content.

        Args:
            original: Original content.
            hunks: Hunks to apply.

        Returns:
            Modified content with hunks applied.
        """
        if not hunks:
            return original

        lines = original.splitlines(keepends=True)
        # Process hunks in reverse order to preserve line numbers
        sorted_hunks = sorted(hunks, key=lambda h: h.source_start, reverse=True)

        for hunk in sorted_hunks:
            lines = self._apply_single_hunk_to_lines(lines, hunk)

        return "".join(lines)

    def _apply_single_hunk_to_lines(
        self, lines: list[str], hunk: DiffHunk
    ) -> list[str]:
        """Apply a single hunk to a list of lines.

        Args:
            lines: Original lines.
            hunk: Hunk to apply.

        Returns:
            Modified lines.
        """
        result = lines.copy()
        # Convert to 0-indexed
        insert_pos = hunk.source_start - 1

        # Count lines to remove and collect new lines
        lines_to_remove = 0
        new_lines: list[str] = []

        for diff_line in hunk.lines:
            if diff_line.line_type == "remove":
                lines_to_remove += 1
            elif diff_line.line_type == "add":
                new_lines.append(diff_line.content + "\n")
            elif diff_line.line_type == "context":
                # Context lines pass through
                new_lines.append(diff_line.content + "\n")

        # Replace the affected range
        # We need to handle this more carefully - context lines are included
        # So we replace from source_start for source_length lines
        end_pos = insert_pos + hunk.source_length
        new_content = []
        for diff_line in hunk.lines:
            if diff_line.line_type in ("add", "context"):
                new_content.append(diff_line.content + "\n")

        result[insert_pos:end_pos] = new_content

        return result

    def apply_single_hunk(self, original: str, hunk: DiffHunk) -> str:
        """Apply a single hunk to original content.

        Args:
            original: Original content.
            hunk: Hunk to apply.

        Returns:
            Modified content with hunk applied.
        """
        return self.apply_hunks(original, [hunk])

    def get_stats(self, hunks: list[DiffHunk]) -> dict:
        """Get statistics about the diff.

        Args:
            hunks: List of hunks to analyze.

        Returns:
            Dict with additions, deletions, and changes counts.
        """
        additions = 0
        deletions = 0

        for hunk in hunks:
            for line in hunk.lines:
                if line.line_type == "add":
                    additions += 1
                elif line.line_type == "remove":
                    deletions += 1

        return {
            "additions": additions,
            "deletions": deletions,
            "hunks": len(hunks),
        }
