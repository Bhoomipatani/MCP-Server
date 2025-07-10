# -*- coding: utf-8 -*-
import logging
from kubernetes import client
from .session import get_kube_client, mcp

logger = logging.getLogger("mcpk8")


@mcp.tool()
def kube_list_pods(session_id: str, namespace: str = "default") -> dict:
    """
    List pods in a Kubernetes namespace using the stored session.
    
    Args:
        session_id: Kubernetes session identifier
        namespace: Kubernetes namespace to list pods from
        
    Returns:
        Dictionary with list of pod names or error
    """
    k8s_client = get_kube_client(session_id)
    if not k8s_client:
        return {"error": "Invalid or expired Kubernetes session"}
    
    try:
        pods = k8s_client.list_namespaced_pod(namespace)
        pod_names = [pod.metadata.name for pod in pods.items]
        return {"pods": pod_names}
    except Exception as e:
        logger.error(f"Failed to list pods in namespace {namespace}: {e}")
        return {"error": str(e)}


@mcp.tool()
def kube_get_pod_logs(session_id: str, pod_name: str, namespace: str = "default", container: str = None, tail_lines: int = 100) -> dict:
    """
    Get logs from a specific pod.
    
    Args:
        session_id: Kubernetes session identifier
        pod_name: Name of the pod
        namespace: Kubernetes namespace
        container: Container name (optional)
        tail_lines: Number of lines to tail
        
    Returns:
        Dictionary with pod logs or error
    """
    k8s_client = get_kube_client(session_id)
    if not k8s_client:
        return {"error": "Invalid or expired Kubernetes session"}
    
    try:
        logs = k8s_client.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines
        )
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Failed to get logs for pod {pod_name}: {e}")
        return {"error": str(e)}


@mcp.tool()
def kube_describe_pod(session_id: str, pod_name: str, namespace: str = "default") -> dict:
    """
    Describe a specific pod.
    
    Args:
        session_id: Kubernetes session identifier
        pod_name: Name of the pod
        namespace: Kubernetes namespace
        
    Returns:
        Dictionary with pod description or error
    """
    k8s_client = get_kube_client(session_id)
    if not k8s_client:
        return {"error": "Invalid or expired Kubernetes session"}
    
    try:
        pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=namespace)
        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "node": pod.spec.node_name,
            "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
            "labels": pod.metadata.labels,
            "annotations": pod.metadata.annotations,
            "containers": [
                {
                    "name": container.name,
                    "image": container.image,
                    "ready": next(
                        (status.ready for status in pod.status.container_statuses if status.name == container.name),
                        False
                    )
                }
                for container in pod.spec.containers
            ]
        }
    except Exception as e:
        logger.error(f"Failed to describe pod {pod_name}: {e}")
        return {"error": str(e)}


@mcp.tool()
def kube_list_services(session_id: str, namespace: str = "default") -> dict:
    """
    List services in a Kubernetes namespace.
    
    Args:
        session_id: Kubernetes session identifier
        namespace: Kubernetes namespace
        
    Returns:
        Dictionary with list of services or error
    """
    k8s_client = get_kube_client(session_id)
    if not k8s_client:
        return {"error": "Invalid or expired Kubernetes session"}
    
    try:
        services = k8s_client.list_namespaced_service(namespace)
        service_list = [
            {
                "name": svc.metadata.name,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "ports": [
                    {
                        "port": port.port,
                        "target_port": port.target_port,
                        "protocol": port.protocol
                    }
                    for port in svc.spec.ports
                ] if svc.spec.ports else []
            }
            for svc in services.items
        ]
        return {"services": service_list}
    except Exception as e:
        logger.error(f"Failed to list services in namespace {namespace}: {e}")
        return {"error": str(e)}


@mcp.tool()
def kube_list_deployments(session_id: str, namespace: str = "default") -> dict:
    """
    List deployments in a Kubernetes namespace.
    
    Args:
        session_id: Kubernetes session identifier
        namespace: Kubernetes namespace
        
    Returns:
        Dictionary with list of deployments or error
    """
    k8s_client = get_kube_client(session_id)
    if not k8s_client:
        return {"error": "Invalid or expired Kubernetes session"}
    
    try:
        # We need to use AppsV1Api for deployments
        apps_client = client.AppsV1Api()
        deployments = apps_client.list_namespaced_deployment(namespace)
        deployment_list = [
            {
                "name": dep.metadata.name,
                "replicas": dep.spec.replicas,
                "ready_replicas": dep.status.ready_replicas or 0,
                "available_replicas": dep.status.available_replicas or 0,
                "updated_replicas": dep.status.updated_replicas or 0,
                "image": dep.spec.template.spec.containers[0].image if dep.spec.template.spec.containers else None
            }
            for dep in deployments.items
        ]
        return {"deployments": deployment_list}
    except Exception as e:
        logger.error(f"Failed to list deployments in namespace {namespace}: {e}")
        return {"error": str(e)}


@mcp.tool()
def kube_get_namespaces(session_id: str) -> dict:
    """
    List all namespaces in the cluster.
    
    Args:
        session_id: Kubernetes session identifier
        
    Returns:
        Dictionary with list of namespaces or error
    """
    k8s_client = get_kube_client(session_id)
    if not k8s_client:
        return {"error": "Invalid or expired Kubernetes session"}
    
    try:
        namespaces = k8s_client.list_namespace()
        namespace_list = [
            {
                "name": ns.metadata.name,
                "status": ns.status.phase,
                "created": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None
            }
            for ns in namespaces.items
        ]
        return {"namespaces": namespace_list}
    except Exception as e:
        logger.error(f"Failed to list namespaces: {e}")
        return {"error": str(e)}
