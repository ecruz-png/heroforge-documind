#!/usr/bin/env python3
"""
DocuMind Upload CLI - Fast batch document upload with processing.

Usage:
    python -m src.documind.cli.upload_cli file1.pdf file2.docx file3.csv
    python -m src.documind.cli.upload_cli docs/workshops/S7-sample-docs/*.pdf
    python -m src.documind.cli.upload_cli --dir docs/workshops/S7-sample-docs/
"""

import argparse
import sys
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.documind.processor import DocumentProcessor


# ANSI colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def upload_to_documind(processed_doc) -> dict:
    """Upload document to DocuMind via direct Supabase connection."""
    try:
        import os
        from dotenv import load_dotenv
        from supabase import create_client

        load_dotenv()

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            return {"success": False, "error": "Supabase credentials not configured", "title": processed_doc.file_name}

        client = create_client(supabase_url, supabase_key)

        # Prepare metadata
        metadata = {
            "fingerprint": processed_doc.metadata.fingerprint,
            "word_count": processed_doc.metadata.basic.word_count,
            "chunks": len(processed_doc.chunks),
            "source": "upload-cli",
            "processor": "documind-processor-v1"
        }

        # Insert document into documents table
        result = client.table("documents").insert({
            "title": processed_doc.file_name,
            "content": processed_doc.content,
            "file_type": processed_doc.extractor_used,
            "metadata": metadata
        }).execute()

        if result.data:
            doc_id = result.data[0].get("id")
            return {
                "success": True,
                "document_id": doc_id,
                "title": processed_doc.file_name
            }
        else:
            return {"success": False, "error": "No data returned from insert", "title": processed_doc.file_name}

    except Exception as e:
        return {"success": False, "error": str(e), "title": getattr(processed_doc, 'file_name', 'unknown')}


def process_and_upload(file_path: str, processor: DocumentProcessor) -> Dict[str, Any]:
    """Process a single document and upload to DocuMind."""
    start = time.time()
    path = Path(file_path)

    try:
        # Process document
        result = processor.process_document(str(path))

        # Upload to DocuMind
        upload_result = upload_to_documind(result)

        elapsed = time.time() - start

        return {
            "file": path.name,
            "success": upload_result.get("success", False),
            "document_id": upload_result.get("document_id"),
            "format": result.extractor_used,
            "words": result.metadata.basic.word_count,
            "chunks": len(result.chunks),
            "time": elapsed,
            "error": upload_result.get("error")
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "file": path.name,
            "success": False,
            "error": str(e),
            "time": elapsed
        }


def collect_files(paths: List[str], directory: str = None, recursive: bool = False) -> List[str]:
    """Collect all files to process."""
    files = []

    # Supported extensions
    supported = {'.pdf', '.docx', '.csv', '.xlsx', '.txt', '.md', '.markdown'}

    # Add files from directory
    if directory:
        dir_path = Path(directory)
        if dir_path.is_dir():
            pattern = '**/*' if recursive else '*'
            for ext in supported:
                files.extend([str(f) for f in dir_path.glob(f'{pattern}{ext}')])

    # Add individual files
    for path in paths:
        p = Path(path)
        if p.is_file() and p.suffix.lower() in supported:
            files.append(str(p))
        elif p.is_dir():
            for ext in supported:
                files.extend([str(f) for f in p.glob(f'*{ext}')])

    return list(set(files))  # Remove duplicates


def main():
    parser = argparse.ArgumentParser(
        description='Fast batch document upload to DocuMind',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s file1.pdf file2.docx
  %(prog)s --dir docs/workshops/S7-sample-docs/
  %(prog)s --dir docs/ --recursive
  %(prog)s *.pdf *.docx --workers 8
        """
    )

    parser.add_argument('files', nargs='*', help='Files to upload')
    parser.add_argument('--dir', '-d', help='Directory to scan for documents')
    parser.add_argument('--recursive', '-r', action='store_true', help='Scan directory recursively')
    parser.add_argument('--workers', '-w', type=int, default=4, help='Parallel workers (default: 4)')
    parser.add_argument('--dry-run', action='store_true', help='Process without uploading')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output')

    args = parser.parse_args()

    # Collect files
    files = collect_files(args.files, args.dir, args.recursive)

    if not files:
        print(f"{Colors.RED}No supported files found.{Colors.END}")
        print(f"Supported formats: PDF, DOCX, CSV, XLSX, TXT, MD")
        sys.exit(1)

    if not args.quiet:
        print(f"\n{Colors.BOLD}📤 DocuMind Upload CLI{Colors.END}")
        print(f"{'=' * 50}")
        print(f"Files to process: {len(files)}")
        print(f"Workers: {args.workers}")
        if args.dry_run:
            print(f"{Colors.YELLOW}DRY RUN - No uploads will be performed{Colors.END}")
        print()

    # Initialize processor
    processor = DocumentProcessor(auto_upload=False)

    # Process files in parallel
    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        if args.dry_run:
            # Just process without upload
            futures = {
                executor.submit(processor.process_document, f): f
                for f in files
            }
        else:
            futures = {
                executor.submit(process_and_upload, f, processor): f
                for f in files
            }

        for i, future in enumerate(as_completed(futures), 1):
            file_path = futures[future]

            try:
                if args.dry_run:
                    doc = future.result()
                    result = {
                        "file": Path(file_path).name,
                        "success": True,
                        "format": doc.extractor_used,
                        "words": doc.metadata.basic.word_count,
                        "chunks": len(doc.chunks),
                        "fingerprint": doc.metadata.fingerprint[:16]
                    }
                else:
                    result = future.result()
            except Exception as e:
                result = {"file": Path(file_path).name, "success": False, "error": str(e)}

            results.append(result)

            if not args.quiet and not args.json:
                status = f"{Colors.GREEN}✓{Colors.END}" if result.get("success") else f"{Colors.RED}✗{Colors.END}"
                name = result["file"][:40]
                if result.get("success"):
                    words = result.get("words", 0)
                    fmt = result.get("format", "?")
                    print(f"  {status} [{i}/{len(files)}] {name:<40} {fmt:<5} {words:>5} words")
                else:
                    error = result.get("error", "Unknown error")[:50]
                    print(f"  {status} [{i}/{len(files)}] {name:<40} {Colors.RED}{error}{Colors.END}")

    total_time = time.time() - start_time

    # Summary
    success_count = sum(1 for r in results if r.get("success"))
    fail_count = len(results) - success_count

    if args.json:
        output = {
            "total": len(results),
            "success": success_count,
            "failed": fail_count,
            "time_seconds": round(total_time, 2),
            "results": results
        }
        print(json.dumps(output, indent=2))
    elif not args.quiet:
        print()
        print(f"{'=' * 50}")
        print(f"{Colors.BOLD}Summary:{Colors.END}")
        print(f"  {Colors.GREEN}✓ Success: {success_count}{Colors.END}")
        if fail_count:
            print(f"  {Colors.RED}✗ Failed:  {fail_count}{Colors.END}")
        print(f"  ⏱ Time:    {total_time:.2f}s ({len(files)/total_time:.1f} docs/sec)")
        print()

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
