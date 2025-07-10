# -*- coding: utf-8 -*-
import logging
import os
import uuid
import paramiko
from kubernetes import client, config
from fastmcp import FastMCP

logger = logging.getLogger("mcpk8")

# Global session stores
ssh_connections = {}
kube_connections = {}
kubeconfig_paths = {}

# Create MCP instance
mcp = FastMCP("K8ProcessMonitor")


@mcp.tool()
def ssh_connect(ip: str, username: str, password: str = None, key_filename: str = None) -> dict:
    """
    Establish SSH connection and return session_id.
    
    Args:
        ip: IP address of the remote server
        username: Username for SSH connection
        password: Password for authentication (optional)
        key_filename: Path to SSH private key file (optional)
        
    Returns:
        Dictionary with connection status and session_id
    """
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if key_filename:
            ssh_client.connect(ip, username=username, key_filename=key_filename)
        else:
            ssh_client.connect(ip, username=username, password=password)

        session_id = str(uuid.uuid4())
        ssh_connections[session_id] = ssh_client
        logger.info(f"SSH session established: {session_id}")
        return {"status": "connected", "session_id": session_id}
    except Exception as e:
        logger.error(f"SSH connection failed: {e}")
        return {"error": str(e)}


@mcp.tool()
def ssh_run_command(session_id: str, command: str) -> dict:
    """
    Run command on active SSH session.
    
    Args:
        session_id: SSH session identifier
        command: Command to execute on remote server
        
    Returns:
        Dictionary with command output or error
    """
    ssh_client = ssh_connections.get(session_id)
    if not ssh_client:
        return {"error": "Invalid or expired SSH session"}
    
    try:
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        return {"output": output} if not error else {"error": error}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def fetch_remote_kubeconfig_and_connect(ssh_session_id: str, remote_kubeconfig_path: str = "/home/dev/.kube/config") -> dict:
    """
    Pulls kubeconfig from remote machine via SSH and connects to the Kubernetes cluster.
    Stores a session-specific Kubernetes client for multi-user support.
    
    Args:
        ssh_session_id: SSH session identifier
        remote_kubeconfig_path: Path to kubeconfig on remote server
        
    Returns:
        Dictionary with connection status and kubernetes session_id
    """
    ssh_client = ssh_connections.get(ssh_session_id)
    if not ssh_client:
        return {"error": "Invalid or expired SSH session"}

    try:
        stdin, stdout, stderr = ssh_client.exec_command(f"cat {remote_kubeconfig_path}")
        content = stdout.read().decode()
        err = stderr.read().decode()

        if err:
            return {"error": f"SSH error while reading kubeconfig: {err.strip()}"}

        session_id = str(uuid.uuid4())
        local_path = f"/tmp/kubeconfig_{session_id}.yaml"
        with open(local_path, "w") as f:
            f.write(content)

        config.load_kube_config(config_file=local_path)
        kube_client = client.CoreV1Api()
        kube_connections[session_id] = kube_client
        kubeconfig_paths[session_id] = local_path

        logger.info(f"Kubernetes session established: {session_id}")
        return {"status": "connected", "session_id": session_id}
    except Exception as e:
        logger.error(f"Kubernetes connection failed: {e}")
        return {"error": str(e)}


@mcp.tool()
def disconnect_session(session_id: str) -> dict:
    """
    Disconnect and clean up SSH or Kubernetes session.
    
    Args:
        session_id: Session identifier to disconnect
        
    Returns:
        Dictionary with disconnection status
    """
    # Try to disconnect SSH session
    ssh_client = ssh_connections.pop(session_id, None)
    if ssh_client:
        try:
            ssh_client.close()
            logger.info(f"SSH session {session_id} disconnected")
            return {"status": "disconnected", "session_type": "ssh"}
        except Exception as e:
            logger.warning(f"Failed to close SSH session {session_id}: {e}")
            return {"error": str(e)}

    # Try to disconnect Kubernetes session
    k8s_client = kube_connections.pop(session_id, None)
    if k8s_client:
        kubeconfig_path = kubeconfig_paths.pop(session_id, None)
        if kubeconfig_path:
            try:
                os.remove(kubeconfig_path)
                logger.info(f"Removed temporary kubeconfig file: {kubeconfig_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary kubeconfig: {e}")
                return {"error": str(e)}
        logger.info(f"Kubernetes session {session_id} disconnected")
        return {"status": "disconnected", "session_type": "kubernetes"}

    return {"error": "Invalid or expired session"}


def get_kube_client(session_id: str) -> client.CoreV1Api:
    """
    Get Kubernetes client for a session.
    
    Args:
        session_id: Kubernetes session identifier
        
    Returns:
        Kubernetes CoreV1Api client or None if session doesn't exist
    """
    return kube_connections.get(session_id)
