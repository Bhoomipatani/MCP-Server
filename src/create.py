# -*- coding: utf-8 -*-
# pylint: disable=broad-exception-caught
import io
import json
import logging

import yaml
from kubernetes import client
from kubernetes.utils import create_from_yaml

from .get import DateTimeEncoder
from .session import mcp, get_kube_client

logger = logging.getLogger("mcpk8")


def _create(yaml_content, namespace=None, apply=False, session_id=None):
    """Internal function to create Kubernetes resources."""
    try:
        # Parse the YAML content - convert string to stream for safe_load_all
        yaml_objects = list(yaml.safe_load_all(io.StringIO(yaml_content)))
        if not yaml_objects:
            return "Error: No valid YAML/JSON content provided"

        # Use session-specific client if provided, otherwise use default
        if session_id:
            kube_client = get_kube_client(session_id)
            if not kube_client:
                return "Error: Invalid or expired Kubernetes session"
            api_client = client.ApiClient()
        else:
            api_client = client.ApiClient()

        results = []

        for yaml_object in yaml_objects:
            if not yaml_object:
                continue

            # If namespace is provided, override the namespace in the YAML
            if namespace and "metadata" in yaml_object:
                yaml_object["metadata"]["namespace"] = namespace

            # Create the resource
            try:
                resource = create_from_yaml(api_client, yaml_objects=[yaml_object], apply=apply)
                if isinstance(resource, list):
                    for item in resource:
                        if hasattr(item, "to_dict"):
                            results.append(item.to_dict())
                        else:
                            results.append({"status": "created", "object": str(item)})
                elif hasattr(resource, "to_dict"):
                    results.append(resource.to_dict())
                else:
                    results.append({"status": "created", "object": str(resource)})
            except Exception as e:
                results.append(
                    {"status": "error", "message": str(e), "object": yaml_object}
                )

        return json.dumps(results, indent=2, cls=DateTimeEncoder)

    except Exception as exc:
        logger.error(f"Error in _create: {exc}")
        return "Error:\n" + str(exc)


@mcp.tool()
def k8s_create(yaml_content: str, namespace: str = None, session_id: str = None) -> dict:
    """
    Create a Kubernetes resource from YAML/JSON content.

    Args:
        yaml_content: The YAML or JSON content of the resource to create
        namespace: The namespace to create the resource in (optional)
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Dictionary with creation result or error
    """
    try:
        result = _create(yaml_content=yaml_content, namespace=namespace, session_id=session_id)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Failed to create resource: {e}")
        return {"error": str(e)}


@mcp.tool()
def k8s_apply(yaml_content: str, namespace: str = None, session_id: str = None) -> dict:
    """
    Apply a configuration to a resource by file content.

    Args:
        yaml_content: The YAML content to apply
        namespace: The namespace to apply the configuration to (optional)
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Dictionary with apply result or error
    """
    try:
        result = _create(yaml_content=yaml_content, namespace=namespace, apply=True, session_id=session_id)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Failed to apply resource: {e}")
        return {"error": str(e)}
