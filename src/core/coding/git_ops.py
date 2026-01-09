"""
Git Operations Module.
Handles cloning, reading, and committing code.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

class GitOperations:
    """Handles git operations for the AutoFixer."""

    def __init__(self, work_dir: str = "temp_repo"):
        self.work_dir = Path(work_dir)

    def clone_repo(self, repo_url: str) -> bool:
        """Clone a repository."""
        self.cleanup()
        try:
            subprocess.run(["git", "clone", repo_url, str(self.work_dir)], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Clone failed: {e}")
            return False

    def get_file_list(self) -> list[str]:
        """Get list of files in repo."""
        file_list = []
        for root, dirs, files in os.walk(self.work_dir):
            if '.git' in dirs:
                dirs.remove('.git')
            for file in files:
                try:
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.work_dir)
                    file_list.append(str(rel_path).replace("\\", "/"))
                except Exception:
                    pass
        return file_list

    def read_file(self, filename: str) -> Optional[str]:
        """Read content of a file."""
        try:
            path = self.work_dir / filename
            return path.read_text(encoding='utf-8')
        except Exception:
            return None

    def write_file(self, filename: str, content: str) -> bool:
        """Write content to a file."""
        try:
            path = self.work_dir / filename
            path.write_text(content, encoding='utf-8')
            return True
        except Exception:
            return False

    def cleanup(self):
        """Remove the temporary directory."""
        if self.work_dir.exists():
            try:
                # On Windows, we might need shell=True or specialized removal for .git folders
                # Using rmtree with ignore_errors usually works for simple cleanup
                shutil.rmtree(self.work_dir, ignore_errors=True)
            except Exception as e:
                print(f"Cleanup warning: {e}")
