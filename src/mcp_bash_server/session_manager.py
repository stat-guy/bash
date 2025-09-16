"""Session management for persistent bash execution."""

import asyncio
import logging
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import threading
import queue
import signal

logger = logging.getLogger(__name__)


@dataclass
class BashSession:
    """Represents a persistent bash session."""
    id: str
    process: subprocess.Popen
    working_directory: str
    environment: Dict[str, str]
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    command_history: List[str] = field(default_factory=list)
    background_jobs: Dict[int, subprocess.Popen] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize session-specific attributes."""
        self.output_queue = queue.Queue()
        self.error_queue = queue.Queue()
        self._setup_readers()
    
    def _setup_readers(self):
        """Set up background threads to read stdout and stderr."""
        def read_stdout():
            """Read from process stdout."""
            for line in iter(self.process.stdout.readline, b''):
                if line:
                    self.output_queue.put(('stdout', line.decode('utf-8', errors='replace')))
        
        def read_stderr():
            """Read from process stderr."""
            for line in iter(self.process.stderr.readline, b''):
                if line:
                    self.error_queue.put(('stderr', line.decode('utf-8', errors='replace')))
        
        # Start reader threads
        threading.Thread(target=read_stdout, daemon=True).start()
        threading.Thread(target=read_stderr, daemon=True).start()
    
    def is_alive(self) -> bool:
        """Check if the session process is still running."""
        return self.process.poll() is None
    
    def update_last_used(self):
        """Update the last used timestamp."""
        self.last_used = time.time()


class SessionManager:
    """Manages multiple persistent bash sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, BashSession] = {}
        self._cleanup_interval = 300  # 5 minutes
        self._max_session_age = 3600  # 1 hour
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup of stale sessions."""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_stale_sessions()
                    time.sleep(self._cleanup_interval)
                except Exception as e:
                    logger.error(f"Error in session cleanup: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_stale_sessions(self):
        """Remove stale or dead sessions."""
        current_time = time.time()
        stale_sessions = []
        
        for session_id, session in self.sessions.items():
            # Check if session is dead or too old
            if not session.is_alive() or (current_time - session.last_used) > self._max_session_age:
                stale_sessions.append(session_id)
        
        for session_id in stale_sessions:
            logger.info(f"Cleaning up stale session: {session_id}")
            self.kill_session(session_id)
    
    async def create_session(
        self, 
        session_id: Optional[str] = None,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a new bash session.
        
        Args:
            session_id: Optional session ID, generated if not provided
            working_directory: Initial working directory
            environment: Environment variables for the session
            
        Returns:
            The session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]
        
        if session_id in self.sessions:
            raise ValueError(f"Session '{session_id}' already exists")
        
        # Set default working directory
        if working_directory is None:
            working_directory = str(Path.cwd())
        else:
            working_directory = str(Path(working_directory).resolve())
        
        # Set up environment
        session_env = os.environ.copy()
        if environment:
            session_env.update(environment)
        
        try:
            # Create bash process with persistent session
            process = subprocess.Popen(
                ['/bin/bash', '--norc', '--noprofile'],  # Non-interactive bash, no config files
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_directory,
                env=session_env,
                text=False,  # Use bytes for better control
                bufsize=0,   # Unbuffered
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Create session object
            session = BashSession(
                id=session_id,
                process=process,
                working_directory=working_directory,
                environment=session_env
            )
            
            self.sessions[session_id] = session
            logger.info(f"Created session '{session_id}' in {working_directory}")
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session '{session_id}': {e}")
            raise
    
    async def execute_command(
        self,
        session_id: str,
        command: str,
        timeout: int = 30,
        background: bool = False
    ) -> Dict[str, Any]:
        """Execute a command in a session.
        
        Args:
            session_id: Target session ID
            command: Command to execute
            timeout: Timeout in seconds
            background: Whether to run in background
            
        Returns:
            Dictionary with execution results
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found")
        
        if not session.is_alive():
            raise RuntimeError(f"Session '{session_id}' is no longer active")
        
        session.update_last_used()
        session.command_history.append(command)
        
        try:
            if background:
                return await self._execute_background_command(session, command)
            else:
                return await self._execute_foreground_command(session, command, timeout)
                
        except Exception as e:
            logger.error(f"Command execution failed in session '{session_id}': {e}")
            raise
    
    async def _execute_foreground_command(
        self, 
        session: BashSession, 
        command: str, 
        timeout: int
    ) -> Dict[str, Any]:
        """Execute a command in the foreground with timeout."""
        # Use a more robust completion detection method
        completion_marker = f"__MCP_CMD_COMPLETE_{int(time.time() * 1000000)}__"
        
        # Send command followed by completion marker on separate line
        full_command = f"{command}\necho '{completion_marker}' >/dev/stderr\n"
        
        # Send command to bash process
        session.process.stdin.write(full_command.encode('utf-8'))
        session.process.stdin.flush()
        
        stdout_lines = []
        stderr_lines = []
        start_time = time.time()
        command_complete = False
        
        # Give a small initial delay for command to start
        await asyncio.sleep(0.02)
        
        # Collect output until timeout or completion
        while time.time() - start_time < timeout and not command_complete:
            try:
                # Process all available stdout
                stdout_found = False
                while True:
                    try:
                        stream, line = session.output_queue.get_nowait()
                        if stream == 'stdout':
                            clean_line = line.rstrip('\n\r')
                            if clean_line:
                                stdout_lines.append(clean_line)
                                stdout_found = True
                    except queue.Empty:
                        break
                
                # Process all available stderr
                stderr_found = False
                while True:
                    try:
                        stream, line = session.error_queue.get_nowait()
                        if stream == 'stderr':
                            clean_line = line.rstrip('\n\r')
                            if completion_marker in clean_line:
                                command_complete = True
                                break
                            elif clean_line and not clean_line.startswith('bash-'):  # Filter bash prompts
                                stderr_lines.append(clean_line)
                                stderr_found = True
                    except queue.Empty:
                        break
                
                # If we found completion marker, break immediately
                if command_complete:
                    break
                
                # If no new output, short sleep to prevent busy waiting
                if not stdout_found and not stderr_found:
                    await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error reading command output: {e}")
                break
        
        # Give a final chance for completion marker if we have output but no completion
        if not command_complete and (stdout_lines or stderr_lines):
            for _ in range(5):  # Try up to 5 more times
                await asyncio.sleep(0.02)
                try:
                    while True:
                        try:
                            stream, line = session.error_queue.get_nowait()
                            if stream == 'stderr' and completion_marker in line:
                                command_complete = True
                                break
                        except queue.Empty:
                            break
                    if command_complete:
                        break
                except Exception:
                    break
        
        # Check if command completed successfully
        if not command_complete:
            logger.warning(f"Command timed out after {timeout} seconds")
        
        return {
            "stdout": '\n'.join(stdout_lines),
            "stderr": '\n'.join(stderr_lines),
            "completed": command_complete,
            "timeout": not command_complete,
            "execution_time": time.time() - start_time
        }
    
    async def _execute_background_command(
        self, 
        session: BashSession, 
        command: str
    ) -> Dict[str, Any]:
        """Execute a command in the background."""
        # TODO: Implement background job management
        # For now, treat as foreground with longer timeout
        return await self._execute_foreground_command(session, f"{command} &", 5)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        session_list = []
        for session in self.sessions.values():
            session_info = {
                "id": session.id,
                "working_directory": session.working_directory,
                "created_at": session.created_at,
                "last_used": session.last_used,
                "is_alive": session.is_alive(),
                "command_count": len(session.command_history),
                "background_jobs": len(session.background_jobs)
            }
            session_list.append(session_info)
        
        return session_list
    
    def kill_session(self, session_id: str) -> bool:
        """Kill a session and clean up resources.
        
        Args:
            session_id: Session to terminate
            
        Returns:
            True if session was killed, False if not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        try:
            # Terminate all background jobs first
            for job_pid, job_process in session.background_jobs.items():
                try:
                    job_process.terminate()
                    job_process.wait(timeout=5)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    try:
                        job_process.kill()
                    except ProcessLookupError:
                        pass
            
            # Terminate the main bash process
            if session.process.poll() is None:
                # Send SIGTERM first
                os.killpg(os.getpgid(session.process.pid), signal.SIGTERM)
                
                # Wait a bit for graceful shutdown
                try:
                    session.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    os.killpg(os.getpgid(session.process.pid), signal.SIGKILL)
                    session.process.wait()
            
            # Remove from sessions
            del self.sessions[session_id]
            logger.info(f"Session '{session_id}' terminated")
            return True
            
        except Exception as e:
            logger.error(f"Error killing session '{session_id}': {e}")
            # Still remove from sessions even if cleanup failed
            if session_id in self.sessions:
                del self.sessions[session_id]
            return False
    
    def get_session(self, session_id: str) -> Optional[BashSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)


# Global session manager instance
session_manager = SessionManager()