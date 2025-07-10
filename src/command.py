# -*- coding: utf-8 -*-
import subprocess
import logging
from typing import List, Union
from .session import mcp, ssh_connections

logger = logging.getLogger("mcpk8")


class ShellProcess:
    """Wrapper for shell command."""

    def __init__(
        self,
        command: str = "/bin/bash",
        strip_newlines: bool = False,
        return_err_output: bool = True,
    ):
        """Initialize with stripping newlines."""
        self.strip_newlines = strip_newlines
        self.return_err_output = return_err_output
        self.command = command

    def run(self, args: Union[str, List[str]], input=None) -> str:
        """Run the command."""
        if isinstance(args, str):
            args = [args]
        commands = ";".join(args)
        if not commands.startswith(self.command):
            commands = f"{self.command} {commands}"

        return self.exec(commands, input=input)

    def exec(self, commands: Union[str, List[str]], input=None) -> str:
        """Run commands and return final output."""
        if isinstance(commands, str):
            commands = [commands]
        commands = ";".join(commands)
        try:
            output = subprocess.run(
                commands,
                shell=True,
                check=True,
                input=input,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            ).stdout.decode()
        except subprocess.CalledProcessError as error:
            if self.return_err_output:
                return error.stdout.decode()
            return str(error)
        if self.strip_newlines:
            output = output.strip()
        return output


@mcp.tool()
def shell_execute_local(command: str, session_id: str = None) -> dict:
    """
    Execute a shell command locally or on a remote session.
    
    Args:
        command: The command to execute
        session_id: Optional SSH session ID for remote execution
        
    Returns:
        Dictionary with command output or error
    """
    try:
        if session_id:
            # Execute on remote session
            ssh_client = ssh_connections.get(session_id)
            if not ssh_client:
                return {"error": "Invalid or expired SSH session"}
            
            stdin, stdout, stderr = ssh_client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if error:
                return {"error": error, "output": output}
            return {"output": output}
        else:
            # Execute locally
            process = ShellProcess()
            output = process.exec(command)
            return {"output": output}
    except Exception as e:
        logger.error(f"Failed to execute command '{command}': {e}")
        return {"error": str(e)}


@mcp.tool()
def shell_execute_kubectl(command: str, session_id: str = None) -> dict:
    """
    Execute a kubectl command locally or on a remote session.
    
    Args:
        command: The kubectl command to execute
        session_id: Optional SSH session ID for remote execution
        
    Returns:
        Dictionary with command output or error
    """
    try:
        if not command.startswith("kubectl"):
            command = f"kubectl {command}"
            
        if session_id:
            # Execute on remote session
            ssh_client = ssh_connections.get(session_id)
            if not ssh_client:
                return {"error": "Invalid or expired SSH session"}
            
            stdin, stdout, stderr = ssh_client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if error:
                return {"error": error, "output": output}
            return {"output": output}
        else:
            # Execute locally
            process = ShellProcess(command="kubectl")
            output = process.run(command)
            return {"output": output}
    except Exception as e:
        logger.error(f"Failed to execute kubectl command '{command}': {e}")
        return {"error": str(e)}
