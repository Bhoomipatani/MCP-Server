import logging
import uuid
import paramiko
from fastmcp import FastMCP
from kubernetes import client, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcpk8")

mcp = FastMCP("K8ProcessMonitor")

ssh_connections = {}
kube_connections = {}
kubeconfig_paths = {}

@mcp.tool()
def ssh_connect(ip: str, username: str, password: str = None, key_filename: str = None) -> dict:
    """
    Establish SSH connection and return session_id.
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
        logger.error(f"SSH failed: {e}")
        return {"error": str(e)}

@mcp.tool()
def ssh_run_command(session_id: str, command: str) -> dict:
    """
    Run command on active SSH session.
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
def fetch_remote_kubeconfig_and_connect(ssh_session_id: str, remote_kubeconfig_path: str = "/home/dev/.kube/config" ) -> dict:
    """
    Pulls kubeconfig from remote machine via SSH and connects to the Kubernetes cluster.
    Stores a session-specific Kubernetes client for multi-user support.
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

        return {"status": "connected", "session_id": session_id}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def kube_list_pods(session_id: str, namespace: str = "default") -> dict:
    """
    List pods in a Kubernetes namespace using the stored session.
    """
    k8s_client = kube_connections.get(session_id)
    if not k8s_client:
        return {"error": "Invalid or expired Kubernetes session"}
    try:
        pods = k8s_client.list_namespaced_pod(namespace)
        pod_names = [pod.metadata.name for pod in pods.items]
        return {"pods": pod_names}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def disconnect_session(session_id: str) -> dict:
    """
    Disconnect and clean up SSH or Kubernetes session.
    """
    ssh_client = ssh_connections.pop(session_id, None)
    if ssh_client:
        try:
            ssh_client.close()
        except Exception as e:
            logger.warning(f"Failed to close SSH session {session_id}: {e}")
            return {"error": str(e)}
        logger.info(f"SSH session {session_id} disconnected")
        return {"status": "disconnected", "session_type": "ssh"}

    k8s_client = kube_connections.pop(session_id, None)
    if k8s_client:
        kubeconfig_path = kubeconfig_paths.pop(session_id, None)
        if kubeconfig_path:
            try:
                import os
                os.remove(kubeconfig_path)
                logger.info(f"Removed temporary kubeconfig file: {kubeconfig_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary kubeconfig: {e}")
                return {"error": str(e)}
        logger.info(f"Kubernetes session {session_id} disconnected")
        return {"status": "disconnected", "session_type": "kubernetes"}

    return {"error": "Invalid or expired session"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting K8ProcessMonitor MCP Server")
    logger.info("Available tools: ssh_connect, ssh_run_command, fetch_remote_kubeconfig_and_connect, kube_list_pods, disconnect_session")
    http_app = mcp.http_app()
    uvicorn.run(http_app, host="0.0.0.0", port=8001)
