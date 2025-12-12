"""
DocuMind Document Upload Handler
Demonstrates Skills, Subagents, and Hooks integration
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path

# Configure security logger
logger = logging.getLogger(__name__)

# Security constants
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Base directory for allowed file access
# Priority: 1) UPLOAD_DIR env var, 2) Project root (fixed path relative to this module)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_UPLOAD_DIR = Path(os.getenv("DOCUMIND_UPLOAD_DIR", _PROJECT_ROOT)).resolve()

# Validate BASE_UPLOAD_DIR exists at module load
if not BASE_UPLOAD_DIR.is_dir():
    logger.warning(f"BASE_UPLOAD_DIR does not exist: {BASE_UPLOAD_DIR}")
    raise RuntimeError(f"Upload directory not found: {BASE_UPLOAD_DIR}")


def validate_file_path(file_path):
    """
    Validates that file path is safe and exists.

    Security checks:
    - Base directory containment (prevents path traversal)
    - Validate file extension
    - Check file size limits

    Returns:
        dict with 'valid' (bool) and 'error' (str or None)
    """
    path = Path(file_path)

    # Resolve to absolute path first (handles ../, symlinks, etc.)
    try:
        resolved = path.resolve()
    except (OSError, ValueError, RuntimeError) as e:
        logger.warning(f"Path resolution failed for '{file_path}': {e}")
        return {"valid": False, "error": "Invalid file path"}

    # CRITICAL: Check resolved path is within allowed base directory
    # This catches ALL path traversal variants (../, encoded, unicode, etc.)
    try:
        resolved.relative_to(BASE_UPLOAD_DIR)
    except ValueError:
        logger.warning(
            f"Path traversal attempt blocked: '{file_path}' resolved to '{resolved}' "
            f"which is outside BASE_UPLOAD_DIR '{BASE_UPLOAD_DIR}'"
        )
        return {"valid": False, "error": "Access denied: path outside allowed directory"}

    # Check file exists
    if not resolved.exists():
        return {"valid": False, "error": "File does not exist"}

    if not resolved.is_file():
        return {"valid": False, "error": "Path is not a file"}

    # Validate extension
    ext = resolved.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {
            "valid": False,
            "error": f"Invalid extension. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        }

    # Check file size
    try:
        file_size = resolved.stat().st_size
    except OSError as e:
        logger.error(f"Failed to stat file '{resolved}': {e}")
        return {"valid": False, "error": "Unable to read file information"}

    if file_size > MAX_FILE_SIZE:
        return {
            "valid": False,
            "error": f"File too large. Maximum allowed: {MAX_FILE_SIZE // (1024*1024)}MB",
        }

    return {"valid": True, "error": None, "resolved_path": str(resolved)}


def read_document(file_path):
    """
    Reads document contents safely.

    Handles:
    - UTF-8 encoding with fallback to latin-1
    - Binary files (PDF) return placeholder message

    Returns:
        dict with 'success' (bool), 'content' (str or None), 'error' (str or None)
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    # PDF files are binary - return indicator for further processing
    if ext == ".pdf":
        return {
            "success": True,
            "content": "[PDF binary content - requires specialized parser]",
            "error": None,
            "is_binary": True,
        }

    # Text-based files (.txt, .md)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "content": content, "error": None, "is_binary": False}
    except UnicodeDecodeError:
        # Fallback to latin-1 which can decode any byte sequence
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()
            return {
                "success": True,
                "content": content,
                "error": None,
                "is_binary": False,
            }
        except Exception as e:
            # Log detailed error internally, return generic message
            logger.error(f"Failed to read file '{file_path}' with latin-1: {e}")
            return {"success": False, "content": None, "error": "Unable to read file"}
    except Exception as e:
        # Log detailed error internally, return generic message
        logger.error(f"Failed to read file '{file_path}': {e}")
        return {"success": False, "content": None, "error": "Unable to read file"}


def extract_metadata(file_path, contents):
    """
    Extracts metadata from document.

    Extracts:
    - File name and extension
    - File size (bytes and human-readable)
    - Created and modified dates
    - Line count, word count, character count

    Returns:
        dict with metadata fields
    """
    path = Path(file_path)
    stat = path.stat()

    # File system metadata
    file_size = stat.st_size
    created_time = datetime.fromtimestamp(stat.st_ctime)
    modified_time = datetime.fromtimestamp(stat.st_mtime)

    # Content analysis (only for text content)
    if contents and not contents.startswith("[PDF binary"):
        lines = contents.split("\n")
        line_count = len(lines)
        word_count = len(contents.split())
        char_count = len(contents)
    else:
        line_count = None
        word_count = None
        char_count = None

    # Human-readable file size
    def format_size(size_bytes):
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    return {
        "file_name": path.name,
        "file_extension": path.suffix.lower(),
        "file_size_bytes": file_size,
        "file_size_human": format_size(file_size),
        "created_at": created_time.isoformat(),
        "modified_at": modified_time.isoformat(),
        "line_count": line_count,
        "word_count": word_count,
        "char_count": char_count,
    }


def analyze_document(file_path):
    """
    Main function: orchestrates document analysis.

    Pipeline:
    1. Validate the file path (security)
    2. Read the document contents
    3. Extract metadata
    4. Return structured JSON analysis

    Returns:
        dict with status, metadata, content preview, and any errors
    """
    result = {
        "status": "success",
        "file_path": file_path,
        "validation": None,
        "metadata": None,
        "content_preview": None,
        "error": None,
    }

    # Step 1: Validate file path
    validation = validate_file_path(file_path)
    result["validation"] = validation

    if not validation["valid"]:
        result["status"] = "error"
        result["error"] = validation["error"]
        return result

    # Step 2: Read document contents
    read_result = read_document(file_path)

    if not read_result["success"]:
        result["status"] = "error"
        result["error"] = read_result["error"]
        return result

    content = read_result["content"]

    # Step 3: Extract metadata
    metadata = extract_metadata(file_path, content)
    result["metadata"] = metadata

    # Step 4: Create content preview (first 500 chars)
    if content and not read_result.get("is_binary"):
        preview_length = min(500, len(content))
        result["content_preview"] = content[:preview_length]
        if len(content) > preview_length:
            result["content_preview"] += "..."
    else:
        result["content_preview"] = content

    return result


# Test the function
if __name__ == "__main__":
    # Create a sample document for testing
    test_doc = "test_document.txt"
    with open(test_doc, 'w') as f:
        f.write("Sample document for DocuMind testing.\nThis is line 2.")

    # Analyze it
    result = analyze_document(test_doc)
    print(json.dumps(result, indent=2))
