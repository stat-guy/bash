"""MCP Bash Server - FastMCP-based server providing bash execution capabilities."""

import asyncio
import base64
import logging
import sys
import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ImageContent, EmbeddedResource

try:
    from .session_manager import session_manager
except ImportError:
    # Handle direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from session_manager import session_manager

# Configure logging to stderr only (STDIO transport requirement)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("bash-server")


@mcp.tool()
async def execute_command(
    command: str,
    session_id: str = "default",
    timeout: int = 30,
    background: bool = False
) -> str:
    """Execute a bash command in a persistent session.
    
    Args:
        command: The bash command to execute
        session_id: Session identifier (default: "default")
        timeout: Command timeout in seconds (default: 30)
        background: Whether to run command in background (default: False)
    
    Returns:
        Command output and execution details
    """
    logger.info(f"Executing command in session {session_id}: {command}")
    
    try:
        # Ensure session exists
        if not session_manager.get_session(session_id):
            # Create default session if it doesn't exist
            await session_manager.create_session(session_id)
        
        # Execute command
        result = await session_manager.execute_command(
            session_id=session_id,
            command=command,
            timeout=timeout,
            background=background
        )
        
        # Format response
        output_parts = []
        if result.get("stdout"):
            output_parts.append(f"STDOUT:\n{result['stdout']}")
        if result.get("stderr"):
            output_parts.append(f"STDERR:\n{result['stderr']}")
        
        status_info = []
        if result.get("timeout"):
            status_info.append("⚠️ Command timed out")
        if result.get("completed"):
            status_info.append("✅ Command completed")
        
        execution_time = result.get("execution_time", 0)
        status_info.append(f"Execution time: {execution_time:.2f}s")
        
        response = []
        if output_parts:
            response.extend(output_parts)
        response.append(f"Status: {' | '.join(status_info)}")
        
        return "\n\n".join(response)
        
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return f"Error executing command: {str(e)}"


@mcp.tool()
async def list_sessions() -> str:
    """List all active bash sessions.
    
    Returns:
        JSON string containing session information
    """
    logger.info("Listing active sessions")
    
    try:
        session_list = session_manager.list_sessions()
        
        if not session_list:
            return "No active sessions"
        
        # Format session information for display
        formatted_sessions = []
        for session_info in session_list:
            formatted_session = {
                "id": session_info["id"],
                "working_directory": session_info["working_directory"],
                "status": "active" if session_info["is_alive"] else "dead",
                "created_at": session_info["created_at"],
                "last_used": session_info["last_used"],
                "commands_executed": session_info["command_count"],
                "background_jobs": session_info["background_jobs"]
            }
            formatted_sessions.append(formatted_session)
        
        return json.dumps(formatted_sessions, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return f"Error listing sessions: {str(e)}"


@mcp.tool()
async def create_session(session_id: str, working_directory: str = None) -> str:
    """Create a new bash session.
    
    Args:
        session_id: Unique identifier for the new session
        working_directory: Initial working directory (optional)
    
    Returns:
        Session creation confirmation
    """
    logger.info(f"Creating session: {session_id}")
    
    try:
        # Check if session already exists
        if session_manager.get_session(session_id):
            return f"Session '{session_id}' already exists"
        
        # Create the session
        actual_session_id = await session_manager.create_session(
            session_id=session_id,
            working_directory=working_directory
        )
        
        return f"Session '{actual_session_id}' created successfully in {working_directory or 'current directory'}"
        
    except Exception as e:
        logger.error(f"Failed to create session '{session_id}': {e}")
        return f"Error creating session: {str(e)}"


@mcp.tool()
async def kill_session(session_id: str) -> str:
    """Terminate a bash session.
    
    Args:
        session_id: Session identifier to terminate
    
    Returns:
        Session termination confirmation
    """
    logger.info(f"Killing session: {session_id}")
    
    try:
        success = session_manager.kill_session(session_id)
        
        if success:
            return f"Session '{session_id}' terminated successfully"
        else:
            return f"Session '{session_id}' not found or already terminated"
            
    except Exception as e:
        logger.error(f"Failed to kill session '{session_id}': {e}")
        return f"Error terminating session: {str(e)}"


@mcp.tool()
async def upload_file(
    file_path: str,
    content: str,
    encoding: str = "base64",
    session_id: str = "default",
    mode: str = "w"
) -> str:
    """Upload file content to the server filesystem.
    
    Args:
        file_path: Target file path on the server
        content: File content (base64 encoded by default)
        encoding: Content encoding (base64 or text)
        session_id: Session context for the upload
        mode: File write mode (w=write, a=append, wb=write binary)
    
    Returns:
        Upload confirmation and file details
    """
    logger.info(f"Uploading file to {file_path} in session {session_id}")
    
    try:
        # Resolve file path (handle relative paths from session working directory)
        target_path = Path(file_path)
        if not target_path.is_absolute():
            # Get session working directory if available
            session = session_manager.get_session(session_id)
            if session:
                base_dir = Path(session.working_directory)
            else:
                base_dir = Path.cwd()
            target_path = base_dir / target_path
        
        # Create parent directories if they don't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Decode content based on encoding
        if encoding == "base64":
            try:
                decoded_content = base64.b64decode(content)
                # For base64, always use binary mode
                write_mode = "wb"
                file_content = decoded_content
            except Exception as e:
                return f"Failed to decode base64 content: {str(e)}"
        elif encoding == "text":
            file_content = content
            write_mode = mode
        else:
            return f"Unsupported encoding: {encoding}. Use 'base64' or 'text'"
        
        # Write file content
        if write_mode == "wb":
            with open(target_path, write_mode) as f:
                f.write(file_content)
        else:
            with open(target_path, write_mode, encoding='utf-8') as f:
                f.write(file_content)
        
        # Get file info
        file_size = target_path.stat().st_size
        
        return f"File uploaded successfully to '{target_path}' ({file_size} bytes, mode: {write_mode})"
        
    except PermissionError:
        return f"Permission denied: Cannot write to '{file_path}'"
    except OSError as e:
        return f"File system error: {str(e)}"
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        return f"Upload failed: {str(e)}"


@mcp.tool()
async def download_file(
    file_path: str,
    encoding: str = "base64",
    session_id: str = "default",
    max_size: int = 10485760  # 10MB default limit
) -> str:
    """Download file content from the server filesystem.
    
    Args:
        file_path: Source file path on the server
        encoding: Content encoding for response (base64 or text)
        session_id: Session context for the download
        max_size: Maximum file size in bytes (default: 10MB)
    
    Returns:
        File content encoded as specified
    """
    logger.info(f"Downloading file from {file_path} in session {session_id}")
    
    try:
        # Resolve file path (handle relative paths from session working directory)
        source_path = Path(file_path)
        if not source_path.is_absolute():
            # Get session working directory if available
            session = session_manager.get_session(session_id)
            if session:
                base_dir = Path(session.working_directory)
            else:
                base_dir = Path.cwd()
            source_path = base_dir / source_path
        
        # Check if file exists
        if not source_path.exists():
            return f"File not found: '{source_path}'"
        
        if not source_path.is_file():
            return f"Path is not a file: '{source_path}'"
        
        # Check file size
        file_size = source_path.stat().st_size
        if file_size > max_size:
            return f"File too large: {file_size} bytes (max: {max_size} bytes)"
        
        # Read file content
        if encoding == "base64":
            # Read as binary and encode to base64
            with open(source_path, 'rb') as f:
                file_content = f.read()
            encoded_content = base64.b64encode(file_content).decode('ascii')
            return json.dumps({
                "file_path": str(source_path),
                "encoding": "base64",
                "size": file_size,
                "content": encoded_content
            }, indent=2)
            
        elif encoding == "text":
            # Read as text
            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                return json.dumps({
                    "file_path": str(source_path),
                    "encoding": "text",
                    "size": file_size,
                    "content": file_content
                }, indent=2)
            except UnicodeDecodeError:
                return f"File contains binary data, use encoding='base64'"
                
        else:
            return f"Unsupported encoding: {encoding}. Use 'base64' or 'text'"
            
    except PermissionError:
        return f"Permission denied: Cannot read '{file_path}'"
    except OSError as e:
        return f"File system error: {str(e)}"
    except Exception as e:
        logger.error(f"File download failed: {e}")
        return f"Download failed: {str(e)}"


@mcp.tool()
async def get_server_info() -> str:
    """Get server information and capabilities.
    
    Returns:
        Server information including version and features
    """
    info = {
        "server": "MCP Bash Server",
        "version": "1.0.0",
        "capabilities": {
            "bash_execution": True,
            "multi_session": True,
            "file_operations": True,
            "background_processes": True
        },
        "active_sessions": len(session_manager.sessions),
        "transport": "stdio"
    }
    
    import json
    return json.dumps(info, indent=2)


def main() -> None:
    """Main entry point for the MCP bash server."""
    logger.info("Starting MCP Bash Server")
    
    try:
        # Run the FastMCP server with STDIO transport
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()