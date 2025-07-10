# -*- coding: utf-8 -*-
import argparse
import logging
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcpk8")

# Import all modules to register tools
from session import mcp
from . import ssh_operations
from . import get
from . import create
from . import command
from . import describe
from . import auth
from . import logs
from . import events
from . import copyk8
from . import port_forward
from . import rollout
from . import set
from . import top
from . import kubeclient


def server():
    logger.info("Starting K8ProcessMonitor MCP Server")
    logger.info("Available tools: ssh_connect, ssh_run_command, fetch_remote_kubeconfig_and_connect, kube_list_pods, disconnect_session")
    http_app = mcp.http_app()
    uvicorn.run(http_app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    server()
