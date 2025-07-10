# -*- coding: utf-8 -*-
# pylint: disable=broad-exception-caught
import json
import logging
from kubernetes import client
from .get import DateTimeEncoder
from .session import mcp, get_kube_client

logger = logging.getLogger("mcpk8")


@mcp.tool()
def k8s_events(
    namespace: str = "default",
    all_namespaces: bool = False,
    field_selector: str = None,
    resource_type: str = None,
    resource_name: str = None,
    sort_by: str = None,
    session_id: str = None,
) -> dict:
    """
    List events in the cluster.

    Args:
        namespace: The namespace to get events from (default: default)
        all_namespaces: Whether to get events from all namespaces (default: False)
        field_selector: Field selector to filter events (optional)
        resource_type: The type of resource to get events for (optional)
        resource_name: The name of the resource to get events for (optional)
        sort_by: Field to sort by (e.g., "lastTimestamp") (optional)
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Dictionary with events or error
    """
    try:
        # Use session-specific client if provided
        if session_id:
            kube_client = get_kube_client(session_id)
            if not kube_client:
                return {"error": "Invalid or expired Kubernetes session"}

        # Get the API client
        core_v1 = client.CoreV1Api()

        # Build field selector
        selectors = []
        if field_selector:
            selectors.append(field_selector)
        if resource_type and resource_name:
            selectors.append(f"involvedObject.kind={resource_type}")
            selectors.append(f"involvedObject.name={resource_name}")

        field_selector_str = ",".join(selectors) if selectors else None

        # Get events
        if all_namespaces:
            events = core_v1.list_event_for_all_namespaces(
                field_selector=field_selector_str
            )
        else:
            events = core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=field_selector_str
            )

        # Sort if requested
        if sort_by and events.items:
            if sort_by == "lastTimestamp":
                events.items.sort(key=lambda x: x.last_timestamp or x.first_timestamp, reverse=True)

        result = json.dumps(events.to_dict(), indent=2, cls=DateTimeEncoder)
        return {"status": "success", "events": result}

    except Exception as exc:
        logger.error(f"Error in k8s_events: {exc}")
        return {"error": str(exc)}
