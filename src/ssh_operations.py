# -*- coding: utf-8 -*-
import logging
from .session import ssh_connections, mcp

logger = logging.getLogger("mcpk8")

# Note: ssh_execute_command is removed as it's duplicate of ssh_run_command in session.py

@mcp.tool()
def ssh_transfer_file(session_id: str, local_path: str, remote_path: str, direction: str = "upload") -> dict:
    """
    Transfer files between local and remote systems via SSH.
    
    Args:
        session_id: SSH session identifier
        local_path: Path to local file
        remote_path: Path to remote file
        direction: 'upload' or 'download'
        
    Returns:
        Dictionary with transfer status or error
    """
    ssh_client = ssh_connections.get(session_id)
    if not ssh_client:
        return {"error": "Invalid or expired SSH session"}
    
    try:
        sftp = ssh_client.open_sftp()
        
        if direction == "upload":
            sftp.put(local_path, remote_path)
            logger.info(f"Uploaded {local_path} to {remote_path}")
            return {"status": "success", "message": f"File uploaded from {local_path} to {remote_path}"}
        elif direction == "download":
            sftp.get(remote_path, local_path)
            logger.info(f"Downloaded {remote_path} to {local_path}")
            return {"status": "success", "message": f"File downloaded from {remote_path} to {local_path}"}
        else:
            return {"error": "Invalid direction. Use 'upload' or 'download'"}
            
    except Exception as e:
        logger.error(f"File transfer failed: {e}")
        return {"error": str(e)}
    finally:
        try:
            sftp.close()
        except:
            pass


@mcp.tool()
def ssh_get_system_info(session_id: str) -> dict:
    """
    Get system information from remote server.
    
    Args:
        session_id: SSH session identifier
        
    Returns:
        Dictionary with system information or error
    """
    ssh_client = ssh_connections.get(session_id)
    if not ssh_client:
        return {"error": "Invalid or expired SSH session"}
    
    try:
        # Get various system information
        commands = {
            "hostname": "hostname",
            "os": "cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"'",
            "kernel": "uname -r",
            "uptime": "uptime",
            "memory": "free -h",
            "disk": "df -h",
            "cpu": "lscpu | grep 'Model name' | cut -d':' -f2 | xargs"
        }
        
        result = {}
        for key, cmd in commands.items():
            try:
                stdin, stdout, stderr = ssh_client.exec_command(cmd)
                output = stdout.read().decode().strip()
                if output:
                    result[key] = output
            except Exception as e:
                result[key] = f"Error: {str(e)}"
        
        return {"system_info": result}
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return {"error": str(e)}


@mcp.tool()
def ssh_list_processes(session_id: str) -> dict:
    """
    List running processes on remote server.
    
    Args:
        session_id: SSH session identifier
        
    Returns:
        Dictionary with process list or error
    """
    ssh_client = ssh_connections.get(session_id)
    if not ssh_client:
        return {"error": "Invalid or expired SSH session"}
    
    try:
        stdin, stdout, stderr = ssh_client.exec_command("ps aux --sort=-%cpu | head -20")
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if error:
            return {"error": error}
        return {"processes": output}
    except Exception as e:
        logger.error(f"Failed to list processes: {e}")
        return {"error": str(e)}


@mcp.tool()
def ssh_check_port(session_id: str, port: int, host: str = "localhost") -> dict:
    """
    Check if a port is open on the remote server.
    
    Args:
        session_id: SSH session identifier
        port: Port number to check
        host: Host to check (default: localhost)
        
    Returns:
        Dictionary with port status or error
    """
    ssh_client = ssh_connections.get(session_id)
    if not ssh_client:
        return {"error": "Invalid or expired SSH session"}
    
    try:
        command = f"nc -zv {host} {port} 2>&1"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        # netcat output goes to stderr for some reason
        result = output + error
        
        if "succeeded" in result or "open" in result:
            return {"port": port, "host": host, "status": "open"}
        else:
            return {"port": port, "host": host, "status": "closed", "details": result}
    except Exception as e:
        logger.error(f"Failed to check port {port}: {e}")
        return {"error": str(e)}
