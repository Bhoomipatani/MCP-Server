# -*- coding: utf-8 -*-
# pylint: disable=broad-exception-caught
import datetime
import re
import logging

from kubernetes import client
from .session import mcp, get_kube_client

logger = logging.getLogger("mcpk8")


@mcp.tool()
def k8s_logs(
    pod_name: str,
    container: str = None,
    namespace: str = "default",
    tail: int = None,
    previous: bool = False,
    since: str = None,
    timestamps: bool = False,
    session_id: str = None
) -> dict:
    """
    Print the logs for a container in a pod.

    Args:
        pod_name: The name of the pod
        container: The name of the container (optional, uses first container if not specified)
        namespace: The namespace of the pod (default: default)
        tail: Number of lines from the end to show (optional)
        previous: Whether to show logs for previous instance (default: False)
        since: Only return logs newer than duration like 5s, 2m, 3h (optional)
        timestamps: Whether to include timestamps (default: False)
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Dictionary with logs or error
    """
    try:
        # Use session-specific client if provided
        if session_id:
            kube_client = get_kube_client(session_id)
            if not kube_client:
                return {"error": "Invalid or expired Kubernetes session"}

        # Get the API client
        core_v1 = client.CoreV1Api()

        # Get the pod
        pod = core_v1.read_namespaced_pod(pod_name, namespace)

        # If container is not specified, use the first container
        if not container:
            if pod.spec.containers:
                container = pod.spec.containers[0].name
            else:
                return {"error": "No containers found in pod"}

        # Get the logs
        logs = core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            previous=previous,
            tail_lines=int(tail) if tail else None,
            timestamps=timestamps,
            since_seconds=_parse_since(since) if since else None,
        )

        return {"status": "success", "logs": logs}

    except client.exceptions.ApiException as e:
        logger.error(f"Kubernetes API error in k8s_logs: {e}")
        return {"error": str(e)}
    except Exception as exc:
        logger.error(f"Error in k8s_logs: {exc}")
        return {"error": str(exc)}


def _parse_since(since):
    """
    Parse a since string into seconds.

    Args:
        since: A string like 5s, 2m, 3h, or an absolute timestamp
        
    Returns:
        The number of seconds
    """
    if not since:
        return None

    # Check if it's a relative duration
    match = re.match(r"^(\d+)([smhd])$", since)
    if match:
        value, unit = match.groups()
        value = int(value)

        # Convert to seconds
        if unit == "s":
            return value
        elif unit == "m":
            return value * 60
        elif unit == "h":
            return value * 60 * 60
        elif unit == "d":
            return value * 60 * 60 * 24

    # Check if it's an absolute timestamp
    try:
        # Try to parse as ISO 8601
        dt = datetime.datetime.fromisoformat(since.replace("Z", "+00:00"))

        # Calculate seconds since then
        now = datetime.datetime.now(datetime.timezone.utc)
        return int((now - dt).total_seconds())
    except ValueError:
        # Not a valid timestamp
        return None
