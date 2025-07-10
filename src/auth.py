# -*- coding: utf-8 -*-
# pylint: disable=broad-exception-caught
import json
import logging

from kubernetes import client
from kubernetes.config import kube_config
from .session import mcp, get_kube_client

logger = logging.getLogger("mcpk8")


@mcp.tool()
def k8s_auth_whoami(session_id: str = None) -> dict:
    """
    Show the subject that you are currently authenticated as.

    Args:
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Dictionary with user information or error
    """
    try:
        # Use session-specific client if provided
        if session_id:
            kube_client = get_kube_client(session_id)
            if not kube_client:
                return {"error": "Invalid or expired Kubernetes session"}
        
        # Get the user info using the Kubernetes Python SDK
        user_info = {}

        # Get the configuration
        config = client.Configuration.get_default_copy()

        # Get the user info from the configuration
        if hasattr(config, "username") and config.username:
            user_info["username"] = config.username

        if hasattr(config, "client_certificate") and config.client_certificate:
            user_info["client_certificate"] = config.client_certificate

        # Get the token if available
        if hasattr(config, "api_key") and config.api_key:
            user_info["token"] = "present"

        # Get the current context
        try:
            current_context = kube_config.list_kube_config_contexts()[1]
            # Add the context info
            user_info["context"] = {
                "name": current_context["name"],
                "cluster": current_context["context"]["cluster"],
                "user": current_context["context"]["user"],
            }
        except Exception:
            user_info["context"] = "unknown"

        return {"status": "success", "user_info": user_info}

    except Exception as exc:
        logger.error(f"Error in k8s_auth_whoami: {exc}")
        return {"error": str(exc)}


@mcp.tool()
def k8s_auth_can_i(verb: str, resource: str, subresource: str = None, namespace: str = "default", name: str = None, session_id: str = None) -> dict:
    """
    Check whether an action is allowed.

    Args:
        verb: The verb to check (e.g., get, list, create, update, delete)
        resource: The resource to check (e.g., pods, deployments)
        subresource: The subresource to check (e.g., log, status) (optional)
        namespace: The namespace to check in (default: default)
        name: The name of the resource to check (optional)
        session_id: Kubernetes session ID for remote cluster (optional)
        
    Returns:
        Dictionary with permission result or error
    """
    try:
        # Use session-specific client if provided
        if session_id:
            kube_client = get_kube_client(session_id)
            if not kube_client:
                return {"error": "Invalid or expired Kubernetes session"}

        # Check using the Kubernetes Python SDK
        # Get the API client
        auth_v1 = client.AuthorizationV1Api()

        # Create the self subject access review
        sar = client.V1SelfSubjectAccessReview(
            spec=client.V1SelfSubjectAccessReviewSpec(
                resource_attributes=client.V1ResourceAttributes(
                    namespace=namespace,
                    verb=verb,
                    resource=resource,
                    subresource=subresource,
                    name=name,
                )
            )
        )

        # Check the access
        response = auth_v1.create_self_subject_access_review(sar)

        return {"status": "success", "allowed": response.status.allowed}

    except Exception as exc:
        logger.error(f"Error in k8s_auth_can_i: {exc}")
        return {"error": str(exc)}
