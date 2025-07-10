# -*- coding: utf-8 -*-
import os
from typing import Optional


class Config:
    """Configuration class for K8ProcessMonitor MCP Server."""
    
    def __init__(self):
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.default_host = os.getenv("MCP_HOST", "127.0.0.1")
        self.default_port = int(os.getenv("MCP_PORT", "8001"))
        self.max_sessions = int(os.getenv("MAX_SESSIONS", "10"))
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
        self.temp_dir = os.getenv("TEMP_DIR", "/tmp")
        
    def get_kubeconfig_path(self, session_id: str) -> str:
        """Get the temporary kubeconfig path for a session."""
        return os.path.join(self.temp_dir, f"kubeconfig_{session_id}.yaml")
    
    def validate_ssh_params(self, ip: str, username: str, password: Optional[str] = None, key_filename: Optional[str] = None) -> bool:
        """Validate SSH connection parameters."""
        if not ip or not username:
            return False
        if not password and not key_filename:
            return False
        if key_filename and not os.path.exists(key_filename):
            return False
        return True


# Global configuration instance
config = Config()
