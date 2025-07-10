# -*- coding: utf-8 -*-
# pylint: disable=broad-exception-caught
import json
import logging
from datetime import datetime
from kubernetes import client, dynamic
from .session import mcp, get_kube_client

logger = logging.getLogger("mcpk8")


def _match(res, target):
    return (
        target == res.get("name")
        or target == res.get("singularName")
        or target in (res.get("shortNames") or [])
    )


def _get_group_versions(api_client):
    """
    Generator yielding ('', 'v1') for core, then ('apps', 'v1'), …
    Works no matter which SDK version you have.
    """
    # core
    yield "", "v1"

    # /apis – list API groups
    resp = api_client.call_api(
        "/apis", "GET", response_type="object", _return_http_data_only=True
    )
    for g in resp["groups"]:
        for v in g["versions"]:
            yield g["name"], v["version"]


class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle datetime objects.
    """

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


@mcp.tool()
def k8s_get(resource: str, name: str = "", namespace: str = "default", session_id: str = None) -> dict:
    """
    Fetch any Kubernetes object (or list) as JSON string.
    
    Args:
        resource: The resource type (e.g., pods, deployments)
        name: The name of the resource (empty string to list all)
        namespace: The namespace of the resource
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Dictionary with resource data or error
    """
    try:
        # Use session-specific client if provided
        if session_id:
            kube_client = get_kube_client(session_id)
            if not kube_client:
                return {"error": "Invalid or expired Kubernetes session"}
            api_client = client.ApiClient()
        else:
            api_client = client.ApiClient()

        dyn = dynamic.DynamicClient(api_client)

        rc = None  # dynamic.Resource we will eventually find

        # 2. iterate every group/version, read its /…/resources list
        for group, version in _get_group_versions(api_client):
            # discover resources for that gv
            path = f"/api/{version}" if group == "" else f"/apis/{group}/{version}"
            try:
                reslist = api_client.call_api(
                    path, "GET", response_type="object", _return_http_data_only=True
                )
            except client.exceptions.ApiException:
                continue  # disabled / no permission → skip

            for r in reslist["resources"]:
                if _match(r, resource):
                    gv = version if group == "" else f"{group}/{version}"
                    rc = dyn.resources.get(api_version=gv, kind=r["kind"])
                    break
            if rc:
                break

        if rc is None:
            return {"error": f"resource '{resource}' not found in cluster"}

        # 3. GET the object or list
        if rc.namespaced:
            if name:
                fetched = rc.get(name=name, namespace=namespace or "default")
            else:
                if namespace == "" or namespace is None:
                    fetched = rc.get(all_namespaces=True)
                else:
                    fetched = rc.get(namespace=namespace)
        else:
            fetched = rc.get(name=name) if name else rc.get()

        result = json.dumps(fetched.to_dict(), indent=2, cls=DateTimeEncoder)
        return {"status": "success", "result": result}

    except Exception as exc:
        logger.error(f"Error in k8s_get: {exc}")
        return {"error": str(exc)}


@mcp.tool()
def k8s_apis(session_id: str = None) -> dict:
    """
    List all available APIs in the Kubernetes cluster.
    
    Args:
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Dictionary with APIs data or error
    """
    try:
        # Use session-specific client if provided  
        if session_id:
            kube_client = get_kube_client(session_id)
            if not kube_client:
                return {"error": "Invalid or expired Kubernetes session"}
        
        result = client.ApisApi().get_api_versions()
        return {"status": "success", "result": json.dumps(result.to_dict(), indent=2)}
    except Exception as e:
        logger.error(f"Error listing APIs: {e}")
        return {"error": str(e)}


@mcp.tool()
def k8s_crds(session_id: str = None) -> dict:
    """
    List all Custom Resource Definitions (CRDs) in the Kubernetes cluster.
    
    Args:
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Dictionary with CRDs data or error
    """
    try:
        # Use session-specific client if provided
        if session_id:
            kube_client = get_kube_client(session_id)
            if not kube_client:
                return {"error": "Invalid or expired Kubernetes session"}
        
        result = client.ApiextensionsV1Api().list_custom_resource_definition()
        return {"status": "success", "result": json.dumps(result.to_dict(), indent=2, cls=DateTimeEncoder)}
    except Exception as e:
        logger.error(f"Error listing CRDs: {e}")
        return {"error": str(e)}
