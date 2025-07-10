# -*- coding: utf-8 -*-
# pylint: disable=broad-exception-caught
import logging
from .session import mcp, get_kube_client

logger = logging.getLogger("mcpk8")


@mcp.tool()
async def k8s_port_forward(resource_type: str, name: str, ports, namespace: str = "default", address: str = None, session_id: str = None):
    """
    Forward one or more local ports to a pod.

    Args:
        resource_type: The type of resource to port-forward to (e.g., pod, service, deployment).
        name: The name of the resource.
        ports: The ports to forward (e.g., ["8080:80"] to forward local port 8080 to port 80 in the pod).
        namespace: The namespace of the resource (default: default).
        address: The IP address to listen on (default: 127.0.0.1).
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Information about the port-forward process.
    """
    try:
        # Use session-specific client if provided
        if session_id:
            kube_client = get_kube_client(session_id)
            if not kube_client:
                return {"error": "Invalid or expired Kubernetes session"}

        # Set default namespace if not provided
        if not namespace:
            namespace = "default"

        # Use kubectl port-forward as it provides the best port-forward functionality
        cmd = ["kubectl", "port-forward", f"{resource_type}/{name}", "-n", namespace]

        # Add address if specified
        if address:
            cmd.extend(["--address", address])

        # Add ports
        if isinstance(ports, list):
            cmd.extend(ports)
        else:
            cmd.append(ports)

        # Run the command
        import subprocess
        import threading
        import time

        # Start the process
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )

        # Store the process ID
        pid = process.pid

        # Function to read output
        def read_output():
            output = ""
            error = ""

            # Read stdout
            for line in process.stdout:
                output += line

            # Read stderr
            for line in process.stderr:
                error += line

            return output, error

        # Start a thread to read output
        thread = threading.Thread(target=read_output)
        thread.daemon = True
        thread.start()

        # Wait for the port-forward to start
        time.sleep(1)

        # Check if the process is still running
        if process.poll() is not None:
            # Process has exited
            _, error = read_output()
            return f"Error: Port-forward failed to start: {error}"

        # Return information about the port-forward
        port_info = []
        for port in ports if isinstance(ports, list) else [ports]:
            parts = port.split(":")
            if len(parts) == 1:
                local_port = remote_port = parts[0]
            else:
                local_port, remote_port = parts

            port_info.append(
                {
                    "local_port": local_port,
                    "remote_port": remote_port,
                    "address": address or "127.0.0.1",
                    "url": f"http://{address or '127.0.0.1'}:{local_port}",
                }
            )

        return {
            "status": "running",
            "pid": pid,
            "resource_type": resource_type,
            "resource_name": name,
            "namespace": namespace,
            "ports": port_info,
            "message": f"Port-forward to {resource_type}/{name} started. Use Ctrl+C to stop.",
        }

    except Exception as exc:
        logger.error(f"Error in k8s_port_forward: {exc}")
        return {"error": str(exc)}
