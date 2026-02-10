#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Noterang (노트랑) - NotebookLM Control Agent
A powerful agent for controlling Google NotebookLM
"""
import json
import sys
import asyncio
from pathlib import Path
from typing import Optional, List, Dict

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

class NoterangAgent:
    """NotebookLM Control Agent"""

    def __init__(self):
        self.auth_path = Path.home() / ".notebooklm-mcp-cli" / "auth.json"
        self.work_dir = Path("G:/내 드라이브/notebooklm")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.client = None

    def load_auth(self) -> Dict:
        """Load authentication data"""
        if not self.auth_path.exists():
            raise FileNotFoundError(
                "NotebookLM auth not found. Run 'notebooklm-mcp-auth' first."
            )

        with open(self.auth_path) as f:
            return json.load(f)

    def get_client(self):
        """Get NotebookLM client"""
        if self.client is None:
            from notebooklm_tools import NotebookLMClient

            auth_data = self.load_auth()
            self.client = NotebookLMClient(
                cookies=auth_data['cookies'],
                csrf_token=auth_data['csrf_token'],
                session_id=auth_data['session_id']
            )
        return self.client

    def list_notebooks(self, limit: Optional[int] = None) -> List:
        """List all notebooks"""
        client = self.get_client()
        notebooks = client.list_notebooks()

        if limit:
            notebooks = notebooks[:limit]

        result = []
        for nb in notebooks:
            result.append({
                'id': getattr(nb, 'id', 'N/A'),
                'title': getattr(nb, 'title', 'Untitled'),
                'created_at': str(getattr(nb, 'created_at', 'N/A')),
                'modified_at': str(getattr(nb, 'modified_at', 'N/A')),
                'source_count': getattr(nb, 'source_count', 0),
            })

        return result

    def get_latest_notebook(self):
        """Get the most recently modified notebook"""
        client = self.get_client()
        notebooks = client.list_notebooks()

        if not notebooks:
            return None

        # Sort by modified_at
        latest = max(notebooks, key=lambda nb: getattr(nb, 'modified_at', ''))

        return {
            'id': getattr(latest, 'id', 'N/A'),
            'title': getattr(latest, 'title', 'Untitled'),
            'created_at': str(getattr(latest, 'created_at', 'N/A')),
            'modified_at': str(getattr(latest, 'modified_at', 'N/A')),
            'source_count': getattr(latest, 'source_count', 0),
        }

    async def create_infographic(self, notebook_id: str) -> Dict:
        """Create infographic from notebook"""
        client = self.get_client()

        result = client.create_infographic(notebook_id)

        # Save info
        info_file = self.work_dir / f"infographic_{result['artifact_id']}.json"
        with open(info_file, 'w') as f:
            json.dump(result, f, indent=2)

        return result

    async def create_audio(self, notebook_id: str) -> Dict:
        """Create audio overview from notebook"""
        client = self.get_client()
        result = await client.create_audio_overview(notebook_id)

        # Save info
        info_file = self.work_dir / f"audio_{result.get('artifact_id', 'unknown')}.json"
        with open(info_file, 'w') as f:
            json.dump(result if isinstance(result, dict) else {'result': str(result)}, f, indent=2)

        return result

    async def create_slides(self, notebook_id: str) -> Dict:
        """Create slide deck from notebook"""
        client = self.get_client()
        result = await client.create_slide_deck(notebook_id)

        # Save info
        info_file = self.work_dir / f"slides_{result.get('artifact_id', 'unknown')}.json"
        with open(info_file, 'w') as f:
            json.dump(result if isinstance(result, dict) else {'result': str(result)}, f, indent=2)

        return result

    async def create_quiz(self, notebook_id: str) -> Dict:
        """Create quiz from notebook"""
        client = self.get_client()
        result = await client.create_quiz(notebook_id)

        # Save info
        info_file = self.work_dir / f"quiz_{result.get('artifact_id', 'unknown')}.json"
        with open(info_file, 'w') as f:
            json.dump(result if isinstance(result, dict) else {'result': str(result)}, f, indent=2)

        return result

    def create_notebook(self, title: str) -> Dict:
        """Create a new notebook"""
        client = self.get_client()
        result = client.create_notebook(title)

        return {
            'id': getattr(result, 'id', 'N/A'),
            'title': getattr(result, 'title', title),
        }

    async def add_url_source(self, notebook_id: str, url: str) -> Dict:
        """Add URL source to notebook"""
        client = self.get_client()
        result = await client.add_url_source(notebook_id, url)

        return result if isinstance(result, dict) else {'result': str(result)}

    async def add_file_source(self, notebook_id: str, file_path: str) -> Dict:
        """Add file source to notebook"""
        client = self.get_client()
        result = await client.add_file(notebook_id, file_path)

        return result if isinstance(result, dict) else {'result': str(result)}

    async def query_notebook(self, notebook_id: str, question: str) -> str:
        """Query the notebook with a question"""
        client = self.get_client()
        result = await client.query(notebook_id, question)

        # Save Q&A
        qa_file = self.work_dir / f"qa_{notebook_id}.jsonl"
        with open(qa_file, 'a', encoding='utf-8') as f:
            json.dump({
                'question': question,
                'answer': result,
                'timestamp': str(Path.ctime(qa_file)) if qa_file.exists() else None
            }, f)
            f.write('\n')

        return result

    def save_notebook_list(self, filename: str = "notebooks_list.json"):
        """Save all notebooks to file"""
        notebooks = self.list_notebooks()

        output_file = self.work_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(notebooks, f, indent=2, ensure_ascii=False)

        return str(output_file)


# CLI Interface
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Noterang - NotebookLM Control Agent')
    parser.add_argument('command', choices=[
        'list', 'latest', 'create', 'infographic', 'audio', 'slides', 'quiz',
        'add-url', 'add-file', 'query'
    ])
    parser.add_argument('--notebook-id', help='Notebook ID')
    parser.add_argument('--title', help='Notebook title')
    parser.add_argument('--url', help='URL to add')
    parser.add_argument('--file', help='File path to add')
    parser.add_argument('--question', help='Question to ask')
    parser.add_argument('--limit', type=int, help='Limit number of results')

    args = parser.parse_args()

    agent = NoterangAgent()

    try:
        if args.command == 'list':
            notebooks = agent.list_notebooks(limit=args.limit)
            print(json.dumps(notebooks, indent=2, ensure_ascii=False))

        elif args.command == 'latest':
            notebook = agent.get_latest_notebook()
            print(json.dumps(notebook, indent=2, ensure_ascii=False))

        elif args.command == 'create':
            if not args.title:
                print("Error: --title required")
                sys.exit(1)
            result = agent.create_notebook(args.title)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == 'infographic':
            if not args.notebook_id:
                print("Error: --notebook-id required")
                sys.exit(1)
            result = asyncio.run(agent.create_infographic(args.notebook_id))
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == 'audio':
            if not args.notebook_id:
                print("Error: --notebook-id required")
                sys.exit(1)
            result = asyncio.run(agent.create_audio(args.notebook_id))
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == 'slides':
            if not args.notebook_id:
                print("Error: --notebook-id required")
                sys.exit(1)
            result = asyncio.run(agent.create_slides(args.notebook_id))
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == 'quiz':
            if not args.notebook_id:
                print("Error: --notebook-id required")
                sys.exit(1)
            result = asyncio.run(agent.create_quiz(args.notebook_id))
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == 'add-url':
            if not args.notebook_id or not args.url:
                print("Error: --notebook-id and --url required")
                sys.exit(1)
            result = asyncio.run(agent.add_url_source(args.notebook_id, args.url))
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == 'add-file':
            if not args.notebook_id or not args.file:
                print("Error: --notebook-id and --file required")
                sys.exit(1)
            result = asyncio.run(agent.add_file_source(args.notebook_id, args.file))
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == 'query':
            if not args.notebook_id or not args.question:
                print("Error: --notebook-id and --question required")
                sys.exit(1)
            result = asyncio.run(agent.query_notebook(args.notebook_id, args.question))
            print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
