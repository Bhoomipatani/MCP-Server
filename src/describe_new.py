# -*- coding: utf-8 -*-
# pylint: disable=broad-exception-caught
import logging
import json
from kubernetes import client, dynamic
from .get import _get_group_versions, DateTimeEncoder
from .session import mcp, get_kube_client

logger = logging.getLogger("mcpk8")


@mcp.tool()
def k8s_describe(
    resource_type: str, 
    name: str = None, 
    namespace: str = "default", 
    selector: str = None, 
    all_namespaces: bool = False,
    session_id: str = None
) -> dict:
    """
    Show detailed information about a specific resource or group of resources.

    Args:
        resource_type: The type of resource to describe (e.g., pods, deployments)
        name: The name of the resource to describe (optional)
        namespace: The namespace of the resource (default: default)
        selector: Label selector to filter resources (e.g., "app=nginx") (optional)
        all_namespaces: Whether to describe resources in all namespaces (default: False)
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Dictionary with resource description or error
    """
    try:
        # Use session-specific client if provided
        if session_id:
            kube_client = get_kube_client(session_id)
            if not kube_client:
                return {"error": "Invalid or expired Kubernetes session"}

        # Get the API client
        api_client = client.ApiClient()
        dyn = dynamic.DynamicClient(api_client)

        # Find the resource
        rc = None
        for group, version in _get_group_versions(api_client):
            path = f"/api/{version}" if group == "" else f"/apis/{group}/{version}"
            try:
                reslist = api_client.call_api(
                    path, "GET", response_type="object", _return_http_data_only=True
                )
            except client.exceptions.ApiException:
                continue

            for r in reslist["resources"]:
                if (resource_type == r.get("name") or 
                    resource_type == r.get("singularName") or 
                    resource_type in (r.get("shortNames") or [])):
                    gv = version if group == "" else f"{group}/{version}"
                    rc = dyn.resources.get(api_version=gv, kind=r["kind"])
                    break
            if rc:
                break

        if rc is None:
            return {"error": f"resource '{resource_type}' not found in cluster"}

        # Get the resource(s)
        if rc.namespaced:
            if name:
                if all_namespaces:
                    resources = rc.get(name=name, all_namespaces=True)
                else:
                    resources = rc.get(name=name, namespace=namespace)
            else:
                if all_namespaces:
                    resources = rc.get(all_namespaces=True, label_selector=selector)
                else:
                    resources = rc.get(namespace=namespace, label_selector=selector)
        else:
            if name:
                resources = rc.get(name=name)
            else:
                resources = rc.get(label_selector=selector)

        # Convert to JSON
        if hasattr(resources, 'items'):
            result = [item.to_dict() for item in resources.items]
        else:
            result = resources.to_dict()

        return {"status": "success", "resources": result}

    except Exception as exc:
        logger.error(f"Error in k8s_describe: {exc}")
        return {"error": str(exc)}
