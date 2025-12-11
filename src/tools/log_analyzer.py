"""System log analysis tool for SOS Agent."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


async def analyze_system_logs(
    log_path: str = "/var/log",
    time_range: str = "1h",
    severity: str = "error",
) -> Dict[str, Any]:
    """
    Analyze system logs for errors and warnings.

    Args:
        log_path: Path to log directory (default: /var/log)
        time_range: Time range to analyze (e.g., "1h", "24h", "7d")
        severity: Minimum severity level ("error", "warning", "info", "all")

    Returns:
        Dictionary with categorized log entries and recommendations
    """
    logger.info(
        f"Analyzing logs: path={log_path}, range={time_range}, severity={severity}"
    )

    results: Dict[str, Any] = {
        "hardware_errors": [],
        "driver_errors": [],
        "service_errors": [],
        "security_warnings": [],
        "recommendations": [],
    }

    # Map severity levels for journalctl
    severity_map = {
        "error": "err",
        "warning": "warning",
        "info": "info",
        "all": "debug",
    }
    journalctl_severity = severity_map.get(severity, "err")

    try:
        # Analyze ALL journalctl logs (system + kernel)
        # CRITICAL: Include kernel logs (-k) for GPU/driver errors!
        cmd_all = (
            f"journalctl --since '{time_range} ago' "
            f"-p {journalctl_severity} --no-pager -o json"
        )

        cmd_kernel = (
            f"journalctl -k --since '{time_range} ago' "
            f"-p {journalctl_severity} --no-pager -o json"
        )

        logger.debug(f"Running commands: {cmd_all} && {cmd_kernel}")

        # Run BOTH system and kernel logs
        process_all = await asyncio.create_subprocess_shell(
            cmd_all, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        process_kernel = await asyncio.create_subprocess_shell(
            cmd_kernel, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout_all, stderr_all = await process_all.communicate()
        stdout_kernel, stderr_kernel = await process_kernel.communicate()

        # Merge outputs
        stdout = stdout_all + b"\n" + stdout_kernel
        stderr = stderr_all

        # Use first process returncode for compatibility
        class FakeProcess:
            returncode = process_all.returncode

        process = FakeProcess()

        # Check kernel logs specifically
        if process_kernel.returncode != 0 and stderr_kernel:
            logger.error(f"journalctl kernel failed: {stderr_kernel.decode()}")
            results["recommendations"].append(
                f"⚠️  Failed to read kernel logs: {stderr_kernel.decode().strip()}"
            )

        if process.returncode == 0 and stdout:
            # Parse JSON output line by line
            for line in stdout.decode().strip().split("\n"):
                if not line:
                    continue

                try:
                    entry = json.loads(line)

                    # Extract relevant fields
                    message = entry.get("MESSAGE", "")
                    unit = entry.get("_SYSTEMD_UNIT", "")
                    priority = entry.get("PRIORITY", "")
                    timestamp = entry.get("__REALTIME_TIMESTAMP", "")

                    # Convert timestamp
                    if timestamp:
                        ts_seconds = int(timestamp) / 1_000_000
                        dt = datetime.fromtimestamp(ts_seconds)
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        formatted_time = "unknown"

                    log_entry = {
                        "timestamp": formatted_time,
                        "unit": unit,
                        "priority": priority,
                        "message": message[:200],  # Truncate long messages
                    }

                    # Categorize by content
                    message_lower = message.lower()

                    # Hardware errors
                    hw_keywords = [
                        "cpu",
                        "memory",
                        "disk",
                        "thermal",
                        "temperature",
                        "overheating",
                        "hardware",
                        "mce",
                        "edac",
                    ]
                    if any(keyword in message_lower for keyword in hw_keywords):
                        results["hardware_errors"].append(log_entry)
                        continue

                    # Driver errors
                    driver_keywords = [
                        "driver",
                        "module",
                        "firmware",
                        "i915",
                        "nvidia",
                        "amdgpu",
                        "radeon",  # AMD legacy GPUs
                        "drm",  # Direct Rendering Manager (GPU subsystem)
                        "usb",
                    ]
                    if any(keyword in message_lower for keyword in driver_keywords):
                        results["driver_errors"].append(log_entry)
                        continue

                    # Security warnings
                    security_keywords = [
                        "authentication failed",
                        "denied",
                        "unauthorized",
                        "permission denied",
                        "security",
                        "firewall",
                    ]
                    if any(keyword in message_lower for keyword in security_keywords):
                        results["security_warnings"].append(log_entry)
                        continue

                    # Service errors
                    if unit or "failed" in message_lower or "error" in message_lower:
                        results["service_errors"].append(log_entry)

                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON line: {line[:100]}")
                    continue

        else:
            logger.error(f"journalctl failed: {stderr.decode()}")
            results["recommendations"].append(
                "⚠️  Failed to read journalctl - check permissions"
            )

        # Generate recommendations based on findings
        if results["hardware_errors"]:
            hw_count = len(results["hardware_errors"])
            results["recommendations"].append(
                f"🔴 CRITICAL: {hw_count} hardware error(s) detected - "
                f"check system health immediately"
            )

        if results["driver_errors"]:
            drv_count = len(results["driver_errors"])
            results["recommendations"].append(
                f"⚠️  {drv_count} driver error(s) detected - "
                f"may need driver updates or module reload"
            )

        if results["service_errors"]:
            svc_count = len(results["service_errors"])
            results["recommendations"].append(
                f"⚠️  {svc_count} service error(s) detected - " f"review failed services"
            )

        if results["security_warnings"]:
            sec_count = len(results["security_warnings"])
            results["recommendations"].append(
                f"🔒 {sec_count} security warning(s) detected - "
                f"review authentication and access logs"
            )

        if not any(
            [
                results["hardware_errors"],
                results["driver_errors"],
                results["service_errors"],
                results["security_warnings"],
            ]
        ):
            results["recommendations"].append(
                f"✅ No {severity} level issues found in the last {time_range}"
            )

    except Exception as e:
        logger.error(f"Error analyzing logs: {e}", exc_info=True)
        results["recommendations"].append(f"❌ Error during log analysis: {str(e)}")

    return results


# MCP tool wrapper format
async def analyze_system_logs_mcp(args: Dict[str, str]) -> Dict[str, Any]:
    """
    MCP-compatible wrapper for analyze_system_logs.

    This function is used when creating an in-process MCP server.
    """
    log_path = args.get("log_path", "/var/log")
    time_range = args.get("time_range", "1h")
    severity = args.get("severity", "error")

    results = await analyze_system_logs(log_path, time_range, severity)

    # Format output for MCP
    output_lines = ["# System Log Analysis Results\n"]

    if results["hardware_errors"]:
        output_lines.append(
            f"\n## 🔴 Hardware Errors ({len(results['hardware_errors'])})\n"
        )
        for entry in results["hardware_errors"][:10]:  # Show top 10
            output_lines.append(
                f"- [{entry['timestamp']}] {entry['unit']}: {entry['message']}\n"
            )

    if results["driver_errors"]:
        output_lines.append(
            f"\n## ⚠️  Driver Errors ({len(results['driver_errors'])})\n"
        )
        for entry in results["driver_errors"][:10]:
            output_lines.append(
                f"- [{entry['timestamp']}] {entry['unit']}: {entry['message']}\n"
            )

    if results["service_errors"]:
        output_lines.append(
            f"\n## ⚠️  Service Errors ({len(results['service_errors'])})\n"
        )
        for entry in results["service_errors"][:10]:
            output_lines.append(
                f"- [{entry['timestamp']}] {entry['unit']}: {entry['message']}\n"
            )

    if results["security_warnings"]:
        output_lines.append(
            f"\n## 🔒 Security Warnings ({len(results['security_warnings'])})\n"
        )
        for entry in results["security_warnings"][:10]:
            output_lines.append(
                f"- [{entry['timestamp']}] {entry['unit']}: {entry['message']}\n"
            )

    if results["recommendations"]:
        output_lines.append("\n## 📋 Recommendations\n")
        for rec in results["recommendations"]:
            output_lines.append(f"- {rec}\n")

    output_text = "".join(output_lines)

    return {"content": [{"type": "text", "text": output_text}]}
