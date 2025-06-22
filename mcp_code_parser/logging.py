"""Logging configuration for mcp-code-parser."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
    log_to_stderr: bool = True
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Specific log file path (overrides log_dir)
        log_dir: Directory for log files (defaults to ./logs)
        log_to_stderr: Whether to log to stderr (required for MCP)
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("mcp_code_parser")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Format for log messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add stderr handler (required for MCP - must use stderr not stdout)
    if log_to_stderr:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)
        stderr_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        logger.addHandler(stderr_handler)
    
    # Add file handler if specified
    if log_file or log_dir:
        if log_file:
            file_path = Path(log_file)
        else:
            # Use log_dir with timestamp
            log_dir_path = Path(log_dir) if log_dir else Path("logs")
            log_dir_path.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = log_dir_path / f"mcp_code_parser_{timestamp}.log"
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # File gets all levels
        logger.addHandler(file_handler)
        
        # Log the log file location (to stderr only)
        if log_to_stderr:
            logger.info(f"Logging to file: {file_path}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"mcp_code_parser.{name}")