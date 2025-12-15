"""SOS Agent CLI - Interactive menu-driven rescue interface."""

import asyncio
import logging
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import asyncclick as click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .agent.client import SOSAgentClient
from .agent.config import SOSConfig, load_config
from .agent.permissions import safe_permission_handler, CRITICAL_SERVICES
from .tools.log_analyzer import analyze_system_logs
from .session.store import FileSessionStore
from .tools.fixers import get_all_fixers
from .agent.privilege import is_root

console = Console()
logger = logging.getLogger(__name__)

# Ensure environment variables are loaded
load_dotenv()

MAX_LOG_SAMPLES = 10


def _has_provider_key(config: SOSConfig) -> bool:
    """Check if a usable API key is present for the configured provider."""
    provider = config.ai_provider
    if provider in ("auto", "gemini"):
        if config.gemini_api_key:
            return True
    if provider in ("auto", "openai"):
        if config.openai_api_key:
            return True
    if provider in ("auto", "inception"):
        if config.inception_api_key:
            return True
    if provider in ("auto", "claude-agentapi"):
        if config.anthropic_api_key:
            return True
    return False


async def _run_shell(command: str) -> tuple[int, str, str]:
    """Run a shell command and capture output."""
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return (
        proc.returncode or 0,
        stdout.decode(errors="replace"),
        stderr.decode(errors="replace"),
    )


def _t(config: SOSConfig, cs: str, en: str) -> str:
    return cs if (config.ai_language or "en").lower().startswith("cs") else en


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for SOS Agent."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/sos-agent.log"),
        ],
    )


async def _safe_print_stream(stream):
    """Print stream chunks with safety guardrails."""
    async for message in stream:
        text_chunk = ""
        # Handle various response formats
        if hasattr(message, "content"):
            for block in message.content:
                if hasattr(block, "text"):
                    text_chunk += block.text
        elif isinstance(message, dict) and "content" in message:
            for block in message["content"]:
                if block.get("type") == "text":
                    text_chunk += block["text"]
        elif isinstance(message, str):
            text_chunk = message

        if not text_chunk:
            continue

        # Guardrail logic: Check for critical service stop/disable
        for service in CRITICAL_SERVICES:
            # We check for the dangerous pattern in the chunk.
            # Note: This is a best-effort check for streaming text.
            patterns = [f"stop {service}", f"disable {service}"]
            for pattern in patterns:
                if pattern in text_chunk:
                    # Simulate a Bash command check
                    full_cmd = f"systemctl {pattern}"
                    # Call handler (assuming empty context is safe for now, or we could pass emergency_mode if available)
                    # For now passing {} context.
                    res = await safe_permission_handler(
                        "Bash", {"command": full_cmd}, {}
                    )
                    if res["behavior"] == "deny":
                        console.print(
                            f"\n[bold red]🚫 SAFETY INTERCEPT: {res['reason']}[/bold red]"
                        )
                        text_chunk = text_chunk.replace(pattern, "[BLOCKED]")

        console.print(text_chunk, end="")


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Configuration file path",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--emergency", is_flag=True, help="Enable emergency mode")
@click.option(
    "--provider",
    type=click.Choice(["gemini", "openai", "inception", "claude-agentapi", "claude-sdk"]),
    default=None,
    help="AI provider (overrides config)",
)
@click.pass_context
async def cli(
    ctx: click.Context,
    config: Optional[str],
    verbose: bool,
    emergency: bool,
    provider: Optional[str],
) -> None:
    """
    🆘 SOS Agent - System Rescue & Optimization Agent

    Powered by Claude for intelligent system diagnostics and recovery.
    """
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    setup_logging(verbose)

    ctx.ensure_object(dict)

    # Load configuration
    sos_config = await load_config(config)

    # Override emergency mode if flag is set
    if emergency:
        sos_config.emergency_mode = True
        console.print(Panel("⚠️  EMERGENCY MODE ACTIVATED", style="bold red"))

    # Override provider if flag is set
    if provider:
        sos_config.ai_provider = provider
        console.print(f"[yellow]Using provider: {provider}[/yellow]")

    ctx.obj["config"] = sos_config
    ctx.obj["client"] = SOSAgentClient(sos_config)

    logger.info("SOS Agent initialized")


@cli.command()
@click.option(
    "--category",
    type=click.Choice(["hardware", "services", "network", "all"]),
    default="all",
    help="Diagnostic category",
)
@click.option("--issue", help="Describe the specific issue you are facing")
@click.pass_context
async def diagnose(ctx: click.Context, category: str, issue: Optional[str]) -> None:
    """
    🔍 Run comprehensive system diagnostics.

    Analyzes logs, system health, and identifies issues.
    """
    client: SOSAgentClient = ctx.obj["client"]
    store = FileSessionStore()

    if issue:
        await store.save_issue(issue)
        console.print(f"[green]Issue saved to session: {issue}[/green]")
    else:
        # Load previously saved issue to keep context across runs
        issue = await store.get_issue()

    console.print(Panel(f"[bold cyan]Running {category} diagnostics...[/bold cyan]"))

    # STEP 1: Collect REAL system data instead of asking AI to hallucinate
    console.print("[dim]Collecting system logs (errors)...[/dim]")
    log_data_errors = await analyze_system_logs(time_range="24h", severity="error")

    console.print("[dim]Collecting system logs (warnings)...[/dim]")
    log_data_warnings = await analyze_system_logs(time_range="24h", severity="warning")

    # Merge data - combine errors and warnings, dedupe by (unit, message)
    def _dedupe(entries):
        seen = set()
        unique = []
        for entry in entries:
            key = (entry.get("unit", ""), entry.get("message", ""))
            if key in seen:
                continue
            seen.add(key)
            unique.append(entry)
        return unique

    log_data = {
        "hardware_errors": _dedupe(
            log_data_errors["hardware_errors"] + log_data_warnings["hardware_errors"]
        ),
        "driver_errors": _dedupe(
            log_data_errors["driver_errors"] + log_data_warnings["driver_errors"]
        ),
        "service_errors": _dedupe(
            log_data_errors["service_errors"] + log_data_warnings["service_errors"]
        ),
        "security_warnings": _dedupe(
            log_data_errors["security_warnings"]
            + log_data_warnings["security_warnings"]
        ),
        "recommendations": log_data_errors["recommendations"]
        + log_data_warnings["recommendations"],
    }

    # STEP 2: Detect OS/System Info (CRITICAL - must know what we're fixing!)
    console.print("[dim]Detecting system information...[/dim]")
    try:
        os_release_proc = await asyncio.create_subprocess_shell(
            "cat /etc/os-release",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        os_release_out, _ = await os_release_proc.communicate()

        uname_proc = await asyncio.create_subprocess_shell(
            "uname -a", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        uname_out, _ = await uname_proc.communicate()

        system_info = f"""
OS Information:
{os_release_out.decode()}

Kernel:
{uname_out.decode()}
"""
    except Exception as e:
        logger.warning(f"Failed to detect system info: {e}")
        system_info = "⚠️  Could not detect system information"

    # STEP 3: Collect resource usage
    console.print("[dim]Checking system resources...[/dim]")
    try:
        # Get actual system metrics
        free_proc = await asyncio.create_subprocess_shell(
            "free -h", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        free_out, _ = await free_proc.communicate()

        df_proc = await asyncio.create_subprocess_shell(
            "df -h /", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        df_out, _ = await df_proc.communicate()

        uptime_proc = await asyncio.create_subprocess_shell(
            "uptime", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        uptime_out, _ = await uptime_proc.communicate()

        resource_data = f"""
Memory Usage:
{free_out.decode()}

Disk Usage:
{df_out.decode()}

System Load:
{uptime_out.decode()}
"""
    except Exception as e:
        logger.warning(f"Failed to collect resource data: {e}")
        resource_data = "⚠️  Could not collect resource data"

    # STEP 4: Prioritize GUI/Display errors (critical for user experience)
    gui_keywords = [
        "x11",
        "wayland",
        "plasma",
        "kde",
        "gnome",
        "display",
        "xorg",
        "gdm",
        "sddm",
    ]
    gui_errors = [
        e
        for e in log_data["service_errors"]
        if any(
            kw in (e["message"].lower() + str(e["unit"]).lower()) for kw in gui_keywords
        )
    ]

    other_errors = [e for e in log_data["service_errors"] if e not in gui_errors]

    def _format_entries(entries, limit=MAX_LOG_SAMPLES):
        if not entries:
            return "No entries"
        lines = [
            f"- [{e['timestamp']}] {e.get('unit','unknown')}: {e.get('message','')}"
            for e in entries[:limit]
        ]
        return "\n".join(lines)

    # STEP 5: Build prompt with ACTUAL DATA
    task = f"""
Analyze the REAL collected data and return a concise one-page summary (max ~25 lines).

User Issue Description:
{issue if issue else "No specific issue provided."}

System: 
{system_info.strip()}

Resources:
{resource_data.strip()}

Log summary (last 24h, deduped):
- Hardware errors: {len(log_data['hardware_errors'])}
- Driver errors: {len(log_data['driver_errors'])}
- Service errors: {len(log_data['service_errors'])} (GUI/display: {len(gui_errors)})
- Security warnings: {len(log_data['security_warnings'])}

Analyzer Recommendations (automated pre-analysis):
{chr(10).join(f"- {r}" for r in log_data['recommendations'])}

Sample logs (showed to you):
GUI/Display (up to {MAX_LOG_SAMPLES}):
{_format_entries(gui_errors)}

Hardware (up to {MAX_LOG_SAMPLES}):
{_format_entries(log_data['hardware_errors'])}

Driver (up to {MAX_LOG_SAMPLES}):
{_format_entries(log_data['driver_errors'])}

Other service (up to {MAX_LOG_SAMPLES}):
{_format_entries(other_errors)}

Security (up to {MAX_LOG_SAMPLES}):
{_format_entries(log_data['security_warnings'])}

Your response must be a single-page summary with these sections (no tables):
1) Top findings (3-5 bullets) with severity labels AND embed the referenced log line (timestamp, unit, message) for each.
2) Quick actions (max 5 commands), each tied to a Top finding. Must include: one GUI log/repair step, one disk check/cleanup step, and one auth/winbind verification step. Prefer diagnostics/restarts; avoid reinstall/disable unless explicitly justified. Reject generic maintenance commands like "apt update/upgrade/clean" unless explicitly tied to a finding.
3) Resources: one line with load, RAM/swap, and top disk hot spots (mount + used% from provided data).
4) Security notes: include at least one log line if any; otherwise say "none seen".
5) Next steps: 2-3 follow-up checks (log commands over destructive steps).

Rules:
- Reference the sample logs by unit/message; do not invent data.
- Keep it compact; no ASCII art, no long paragraphs, no repetition of this prompt.
- Use package manager appropriate to the detected OS (Debian/Ubuntu → apt, RedHat → dnf, Arch → pacman).
"""

    try:
        await _safe_print_stream(client.execute_rescue_task(task))

    except KeyboardInterrupt:
        console.print("\n[yellow]Diagnostics interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error during diagnostics: {e}[/red]")
        logger.error(f"Diagnostics failed: {e}", exc_info=True)


@cli.command()
@click.argument(
    "category",
    type=click.Choice(
        ["hardware", "services", "network", "performance", "security", "all"]
    ),
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be fixed without making changes"
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Apply fixes without interactive confirmation (only for local fixers).",
)
@click.option(
    "--ai",
    "use_ai",
    is_flag=True,
    help="Force AI-driven fix plan instead of built-in fixers.",
)
@click.pass_context
async def fix(
    ctx: click.Context, category: str, dry_run: bool, yes: bool, use_ai: bool
) -> None:
    """
    🔧 Fix detected issues in specified category.

    CATEGORY: hardware, services, network, performance, security, all
    """
    client: SOSAgentClient = ctx.obj["client"]

    mode = "dry-run (preview only)" if dry_run else "ACTIVE"
    console.print(
        Panel(f"[bold yellow]Fix mode: {mode} - Category: {category}[/bold yellow]")
    )

    # Prefer built-in fixers for safety; fall back to AI if requested or missing
    fixers = [f for f in get_all_fixers() if category in (f.category, "all")]

    if fixers and not use_ai:
        console.print("[cyan]Using built-in safe fixers.[/cyan]")
        for fixer in fixers:
            console.print(
                f"\n[bold cyan]{fixer.name}[/bold cyan] (category: {fixer.category})"
            )

            needs_fix, reason = await fixer.check()
            if not needs_fix:
                console.print(f"[green]Status OK:[/green] {reason}")
                continue

            console.print(f"[yellow]Issue detected:[/yellow] {reason}")
            plan = await fixer.apply(dry_run=True)
            console.print("[bold]Planned actions:[/bold]")
            for step in plan:
                console.print(f"- {step}")

            if dry_run:
                console.print("[dim]Dry-run only; no changes executed.[/dim]")
                continue

            if fixer.requires_root and not is_root():
                console.print(
                    "[red]Skipping: root privileges required. Run with sudo.[/red]"
                )
                continue

            if not yes:
                proceed = click.confirm("Apply this fix now?", default=False)
                if not proceed:
                    console.print("[dim]Skipped by user.[/dim]")
                    continue

            try:
                results = await fixer.apply(dry_run=False)
                for res in results:
                    console.print(f"[green]✓ {res}[/green]")
            except Exception as e:
                console.print(f"[red]Fixer failed: {e}[/red]")

        return

    task = f"""
Fix all {category} issues detected in recent diagnostics.

Mode: {"dry-run (show actions only, don't execute)" if dry_run else "execute fixes"}

Steps:
1. Review latest diagnostic findings for {category} issues
2. Propose fix actions
3. {"Show what would be done" if dry_run else "Execute approved fixes"}
4. Verify fixes were successful

Remember:
- NEVER stop or disable critical services: sshd, NetworkManager, ollama, tailscaled
- Always explain what you're doing before making changes
- Verify changes don't break system stability
"""

    try:
        await _safe_print_stream(client.execute_rescue_task(task))

    except KeyboardInterrupt:
        console.print("\n[yellow]Fix operation interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error during fix: {e}[/red]")
        logger.error(f"Fix failed: {e}", exc_info=True)


@cli.command()
@click.pass_context
async def emergency(ctx: click.Context) -> None:
    """
    🚨 Emergency recovery mode - automated stabilization.

    Performs aggressive cleanup and recovery operations.
    """
    client: SOSAgentClient = ctx.obj["client"]
    config: SOSConfig = ctx.obj["config"]

    # Force emergency mode
    config.emergency_mode = True

    console.print(
        Panel(
            "[bold red]⚠️  EMERGENCY MODE ACTIVATED ⚠️[/bold red]\n\n"
            "This will perform aggressive recovery operations:\n"
            "- Stop non-critical processes\n"
            "- Clear temporary files and caches\n"
            "- Restart failed critical services\n"
            "- Apply thermal management if needed\n"
            "- Verify system stability",
            style="red",
        )
    )

    if not click.confirm("Continue with emergency recovery?"):
        console.print("[yellow]Emergency recovery cancelled[/yellow]")
        return

    task = """
Execute emergency recovery protocol:

1. **Immediate stabilization**:
   - Check system load and thermal status
   - Kill high-resource non-critical processes if needed
   - Clear /tmp and cache directories

2. **Service recovery**:
   - Check status of critical services
   - Restart any failed critical services (sshd, NetworkManager, ollama)
   - Verify services are running correctly

3. **Resource cleanup**:
   - Clear old logs if disk space critical
   - Clean package manager caches
   - Remove orphaned processes

4. **Verification**:
   - Verify system is stable
   - Check resource levels are normal
   - Confirm critical services operational

5. **Report**:
   - Summary of actions taken
   - Current system status
   - Any remaining issues requiring manual intervention

CRITICAL: Never stop sshd, NetworkManager, ollama, or tailscaled.
"""

    try:
        await _safe_print_stream(client.execute_rescue_task(task))

        console.print(
            Panel(
                "[bold green]✅ Emergency recovery completed[/bold green]",
                style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Emergency recovery interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error during emergency recovery: {e}[/red]")
        logger.error(f"Emergency recovery failed: {e}", exc_info=True)


@cli.command()
@click.option("--interval", "-i", default=60, help="Monitoring interval in seconds")
@click.pass_context
async def monitor(ctx: click.Context, interval: int) -> None:
    """
    📊 Continuous system monitoring.

    Watch system health in real-time.
    """
    client: SOSAgentClient = ctx.obj["client"]

    console.print(
        Panel(
            f"[bold cyan]Starting continuous monitoring (interval: {interval}s)[/bold cyan]\n"
            "Press Ctrl+C to stop"
        )
    )

    try:
        while True:
            task = """
Quick system health check:
- CPU and memory usage
- Disk space
- Critical service status
- Recent error count in logs

Provide a brief status summary.
"""

            console.print(f"\n[dim]--- {asyncio.get_event_loop().time()} ---[/dim]")

            await _safe_print_stream(client.execute_rescue_task(task))

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


@cli.command()
@click.option("--message", "-m", help="Send a single message and exit")
@click.pass_context
async def chat(ctx: click.Context, message: Optional[str]) -> None:
    """
    💬 Chat with SOS Agent (stores session history).
    """
    client: SOSAgentClient = ctx.obj["client"]
    config: SOSConfig = ctx.obj["config"]

    if not _has_provider_key(config):
        console.print(
            "[red]No API key configured. Run 'sos setup' or set environment variables.[/red]"
        )
        return

    store = FileSessionStore()
    issue = await store.get_issue()
    history = await store.get_chat_history()

    if history:
        console.print("[dim]Loaded previous chat history.[/dim]")

    async def _send_message(user_message: str) -> None:
        if not user_message.strip():
            console.print("[yellow]Empty message ignored.[/yellow]")
            return

        context_prefix = f"Context (User Issue): {issue}\n\n" if issue else ""
        full_prompt = f"{context_prefix}{user_message}"

        await store.save_chat_message("user", user_message)
        console.print(f"[cyan]You:[/cyan] {user_message}")
        console.print("[magenta]Agent:[/magenta] ", end="")

        response_text = ""
        try:
            async for chunk in client.execute_rescue_task(full_prompt):
                text_chunk = ""
                if hasattr(chunk, "content"):
                    for block in chunk.content:
                        if hasattr(block, "text"):
                            text_chunk += block.text
                elif isinstance(chunk, dict) and "content" in chunk:
                    for block in chunk["content"]:
                        if block.get("type") == "text":
                            text_chunk += block["text"]
                elif isinstance(chunk, str):
                    text_chunk = chunk

                if text_chunk:
                    response_text += text_chunk
                    console.print(text_chunk, end="")
            console.print()  # Newline after streaming
        except Exception as e:
            console.print(f"[red]Error during chat: {e}[/red]")
            return

        if response_text:
            await store.save_chat_message("assistant", response_text)

    if message:
        await _send_message(message)
        return

    # Interactive loop
    console.print("[dim]Type 'exit' or 'quit' to leave chat.[/dim]")
    while True:
        user_message = await click.prompt("You", default="", show_default=False)
        if user_message.lower() in {"exit", "quit"}:
            break
        await _send_message(user_message)


@cli.command()
@click.pass_context
async def menu(ctx: click.Context) -> None:
    """
    📋 Launch Interactive TUI (Text User Interface).
    """
    from .tui.app import start_tui_async

    await start_tui_async()


@cli.command("tui-screenshot")
@click.option(
    "--out",
    type=click.Path(dir_okay=False),
    default=None,
    help="Output SVG path (default: ./SOS_Agent_<timestamp>.svg)",
)
@click.option(
    "--png",
    "as_png",
    is_flag=True,
    help="Also export PNG (uses headless Chrome if available).",
)
@click.pass_context
async def tui_screenshot(ctx: click.Context, out: Optional[str], as_png: bool) -> None:
    """Save a TUI screenshot without manual Ctrl+P."""
    from datetime import datetime
    from .tui.app import SOSApp

    ts = datetime.now().strftime("%Y-%m-%dT%H_%M_%S")
    svg_path = Path(out) if out else Path.cwd() / f"SOS_Agent_{ts}.svg"

    app = SOSApp(init_client=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        saved = app.save_screenshot(filename=svg_path.name, path=str(svg_path.parent))

    console.print(f"[green]Saved:[/green] {saved}")

    if not as_png:
        return

    png_path = svg_path.with_suffix(".png")
    if shutil.which("google-chrome"):
        cmd = (
            f"google-chrome --headless --disable-gpu --no-sandbox "
            f'--window-size=2200,1200 --screenshot="{png_path}" "file://{svg_path}"'
        )
        rc, _, err = await _run_shell(cmd)
        if rc == 0 and png_path.exists():
            console.print(f"[green]Saved:[/green] {png_path}")
            return
        console.print(f"[yellow]PNG export failed:[/yellow] {err.strip()}")

    console.print(
        "[yellow]PNG export not available (install Chrome or use another SVG viewer).[/yellow]"
    )


@cli.command()
@click.pass_context
async def check_boot(ctx: click.Context) -> None:
    """
    🥾 Boot and GRUB diagnostics.

    Check bootloader configuration and boot issues.
    """
    client: SOSAgentClient = ctx.obj["client"]

    console.print(Panel("[bold cyan]Checking boot configuration...[/bold cyan]"))

    task = """
Analyze boot and GRUB configuration:

1. Check GRUB configuration (/boot/grub/grub.cfg or /etc/default/grub)
2. Verify kernel parameters
3. Check for boot errors in logs
4. Verify bootloader installation
5. Check for initramfs issues

Provide recommendations for any issues found.
"""

    try:
        await _safe_print_stream(client.execute_rescue_task(task))

    except Exception as e:
        console.print(f"[red]Error checking boot: {e}[/red]")


@cli.command()
@click.option(
    "--platform",
    type=click.Choice(["all", "flatpak", "snap", "docker", "appimage", "apt"]),
    default="all",
    help="Application platform to optimize",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Execute suggested steps without per-step confirmation (still shows preview).",
)
@click.option(
    "--ai",
    "use_ai",
    is_flag=True,
    help="Use AI-only optimization plan instead of interactive local steps.",
)
@click.pass_context
async def optimize_apps(
    ctx: click.Context, platform: str, yes: bool, use_ai: bool
) -> None:
    """
    📦 Optimize, clean, and fix applications.

    Supports: flatpak, snap, docker, appimage, apt
    """
    client: SOSAgentClient = ctx.obj["client"]
    config: SOSConfig = ctx.obj["config"]

    console.print(
        Panel(f"[bold cyan]Optimizing {platform} applications...[/bold cyan]")
    )

    if not use_ai:
        console.print(
            Panel(
                _t(
                    config,
                    "Interaktivní režim: nejdřív preview (dry-run), pak nabídka provedení kroků.",
                    "Interactive mode: preview first (dry-run), then offer to execute steps.",
                ),
                style="cyan",
            )
        )

        steps: list[tuple[str, str, Optional[str]]] = []
        # (label, preview_cmd, exec_cmd)

        if platform in {"all", "apt"}:
            if shutil.which("apt-get"):
                steps.extend(
                    [
                        (
                            "APT autoremove (preview)",
                            "sudo -n true >/dev/null 2>&1 && sudo apt-get -s autoremove || apt-get -s autoremove",
                            "sudo apt-get autoremove -y",
                        ),
                        (
                            "APT upgrade (preview)",
                            "sudo -n true >/dev/null 2>&1 && sudo apt-get -s upgrade || apt-get -s upgrade",
                            "sudo apt-get upgrade -y",
                        ),
                    ]
                )
            else:
                console.print(
                    _t(
                        config,
                        "[yellow]APT není k dispozici (apt-get nenalezen).[/yellow]",
                        "[yellow]APT not available (apt-get not found).[/yellow]",
                    )
                )

            if shutil.which("deborphan"):
                steps.append(
                    (
                        "Deborphan (orphan packages)",
                        "deborphan",
                        None,
                    )
                )

        if platform in {"all", "flatpak"}:
            if shutil.which("flatpak"):
                steps.append(
                    (
                        "Flatpak unused (preview)",
                        "flatpak uninstall --unused --dry-run",
                        "flatpak uninstall --unused -y",
                    )
                )
            else:
                console.print(
                    _t(
                        config,
                        "[yellow]Flatpak není k dispozici.[/yellow]",
                        "[yellow]Flatpak not available.[/yellow]",
                    )
                )

        if platform in {"all", "snap"}:
            if shutil.which("snap"):
                steps.append(("Snap list (all)", "snap list --all", None))
                steps.append(
                    (
                        "Snap disabled revisions (preview)",
                        "snap list --all | awk '/disabled/{print $1, $3}'",
                        'snap list --all | awk \'/disabled/{print $1, $3}\' | while read snap rev; do sudo snap remove "$snap" --revision="$rev"; done',
                    )
                )
            else:
                console.print(
                    _t(
                        config,
                        "[yellow]Snap není k dispozici.[/yellow]",
                        "[yellow]Snap not available.[/yellow]",
                    )
                )

        if platform in {"all", "docker"}:
            if shutil.which("docker"):
                steps.append(("Docker disk usage", "docker system df", None))
                steps.append(
                    (
                        "Docker prune (preview)",
                        "docker system prune --dry-run 2>/dev/null || echo 'docker system prune does not support --dry-run; will ask before running.'",
                        "docker system prune -f",
                    )
                )
            else:
                console.print(
                    _t(
                        config,
                        "[yellow]Docker není k dispozici.[/yellow]",
                        "[yellow]Docker not available.[/yellow]",
                    )
                )

        if platform in {"all", "appimage"}:
            console.print(
                _t(
                    config,
                    "[dim]AppImage optimalizace zatím jen informativní (TODO).[/dim]",
                    "[dim]AppImage optimization is informational only (TODO).[/dim]",
                )
            )

        if not steps:
            console.print(
                _t(
                    config,
                    "[yellow]Žádné kroky k provedení (nebo chybí nástroje).[/yellow]",
                    "[yellow]No actionable steps (or required tools missing).[/yellow]",
                )
            )
            return

        for label, preview_cmd, exec_cmd in steps:
            console.print(Panel(label, style="bold magenta"))
            rc, out, err = await _run_shell(preview_cmd)
            if out.strip():
                console.print(out.rstrip())
            if err.strip():
                console.print(f"[dim]{err.rstrip()}[/dim]")
            if rc != 0:
                console.print(
                    _t(
                        config,
                        f"[yellow]Pozn.: preview příkaz skončil kódem {rc}.[/yellow]",
                        f"[yellow]Note: preview command exited with {rc}.[/yellow]",
                    )
                )

            if not exec_cmd:
                continue

            if yes:
                proceed = True
            elif not sys.stdin.isatty():
                console.print(
                    _t(
                        config,
                        "[dim]Bez TTY: přeskočeno. Pro provedení použij `--yes` nebo spusť interaktivně.[/dim]",
                        "[dim]No TTY detected: skipped. Use `--yes` or run interactively to execute.[/dim]",
                    )
                )
                proceed = False
            else:
                proceed = click.confirm(
                    _t(
                        config,
                        f"Chceš provést tento krok teď? ({label})",
                        f"Execute this step now? ({label})",
                    ),
                    default=False,
                )
            if not proceed:
                continue

            # Safety gate
            perm = await safe_permission_handler(
                "Bash", {"command": exec_cmd}, {"emergency_mode": config.emergency_mode}
            )
            if perm.get("behavior") == "deny":
                console.print(f"[red]Blocked:[/red] {perm.get('reason')}")
                continue

            console.print(
                _t(config, "[cyan]Spouštím...[/cyan]", "[cyan]Running...[/cyan]")
            )
            rc2, out2, err2 = await _run_shell(exec_cmd)
            if out2.strip():
                console.print(out2.rstrip())
            if err2.strip():
                console.print(f"[dim]{err2.rstrip()}[/dim]")
            if rc2 != 0:
                console.print(
                    _t(
                        config,
                        f"[red]Krok selhal (exit {rc2}).[/red]",
                        f"[red]Step failed (exit {rc2}).[/red]",
                    )
                )
        return

    task = f"""
Optimize and clean {platform} applications:

1. List installed applications for {platform}
2. Check for:
   - Unused packages
   - Old versions/cache
   - Broken dependencies
   - Disk space usage
3. Recommend cleanup actions
4. Optimize package databases

Platforms to check: {platform}
"""

    try:
        await _safe_print_stream(client.execute_rescue_task(task))

    except Exception as e:
        console.print(f"[red]Error optimizing apps: {e}[/red]")


@cli.command()
def setup() -> None:
    """🛠️  Run interactive setup wizard to configure API keys."""
    console.print(Panel("[bold green]Starting SOS Agent Setup Wizard...[/bold green]"))

    # Run setup wizard
    try:
        result = subprocess.run(
            [sys.executable, "-m", "src.setup_wizard"],
            check=True,
        )
        if result.returncode == 0:
            console.print("\n[green]✅ Setup completed successfully![/green]")
        else:
            console.print("\n[yellow]⚠️  Setup exited with warnings.[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]❌ Setup failed: {e}[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled by user.[/yellow]")
        sys.exit(0)


@cli.group()
def gcloud() -> None:
    """🌐 Google Cloud Platform management commands."""
    pass


@gcloud.command()
def check() -> None:
    """Check current GCloud project and quota status."""
    from .gcloud.manager import GCloudManager

    try:
        manager = GCloudManager()

        console.print(Panel("[bold cyan]Google Cloud Status Check[/bold cyan]"))

        # Get current project
        current_project = manager.get_current_project()

        if not current_project:
            console.print("[yellow]⚠️  No active GCloud project found[/yellow]")
            console.print("\nRun: [green]gcloud auth login[/green]")
            console.print(
                "Then: [green]gcloud config set project YOUR_PROJECT_ID[/green]"
            )
            return

        console.print(
            f"[green]✓[/green] Active project: [bold]{current_project}[/bold]"
        )

        # Check if Gemini API is enabled
        api_enabled = manager.is_api_enabled(current_project)
        if api_enabled:
            console.print(
                "[green]✓[/green] Gemini API: [bold green]Enabled[/bold green]"
            )
        else:
            console.print("[red]✗[/red] Gemini API: [bold red]Not Enabled[/bold red]")
            console.print("\nEnable with: [green]sos gcloud enable-api[/green]")

        # Check quota status
        quota = manager.check_quota_status(current_project)

        table = Table(title="Gemini API Quota Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Project ID", quota.project_id)
        table.add_row("Region", quota.region)
        table.add_row("Limit", str(quota.limit_value))
        table.add_row("Current Usage", str(quota.current_usage))

        status_style = "red" if quota.is_exceeded else "green"
        status_text = "EXCEEDED ❌" if quota.is_exceeded else "OK ✓"
        table.add_row("Status", f"[{status_style}]{status_text}[/{status_style}]")

        console.print(table)

        if quota.is_exceeded or quota.limit_value == 0:
            console.print("\n[bold red]⚠️  Quota Exceeded or Banned![/bold red]")
            console.print("\n[yellow]Recommendations:[/yellow]")
            console.print("1. Wait for quota reset (usually hourly)")
            console.print(
                "2. Use different provider: [green]sos --provider mercury diagnose[/green]"
            )
            console.print(
                "3. Create new project: [green]sos gcloud init --auto[/green]"
            )

    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@gcloud.command()
def list_projects() -> None:
    """List all Google Cloud projects."""
    from .gcloud.manager import GCloudManager

    try:
        manager = GCloudManager()
        projects = manager.list_projects()

        table = Table(title="Google Cloud Projects")
        table.add_column("Project ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Number", style="blue")
        table.add_column("State", style="green")

        for project in projects:
            table.add_row(
                project.project_id,
                project.name,
                project.project_number,
                project.lifecycle_state,
            )

        console.print(table)

        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            console.print("\nCreate one: [green]sos gcloud init --auto[/green]")

    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@gcloud.command()
@click.option("--project", help="Project ID to enable API for")
def enable_api(project: Optional[str]) -> None:
    """Enable Gemini API for a project."""
    from .gcloud.manager import GCloudManager

    try:
        manager = GCloudManager()

        if not project:
            project = manager.get_current_project()
            if not project:
                console.print("[red]No active project. Specify with --project[/red]")
                return

        console.print(f"Enabling Gemini API for project: [bold]{project}[/bold]")

        manager.enable_api(project)

        console.print("[green]✓ Gemini API enabled successfully![/green]")

    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@gcloud.command()
@click.option(
    "--auto", is_flag=True, help="Enable auto-mode (creates project automatically)"
)
@click.option("--project-id", help="Custom project ID (auto-generated if not provided)")
def init(auto: bool, project_id: Optional[str]) -> None:
    """Initialize Google Cloud project for SOS Agent.

    Level 1 (Safe): Guides you through manual setup
    Level 2 (Auto): Automatically creates and configures project (requires --auto flag)
    """
    from .gcloud.manager import GCloudManager

    try:
        manager = GCloudManager()

        if not auto:
            # Level 1: Safe mode - just guidance
            console.print(
                Panel(
                    "[bold cyan]Google Cloud Setup Guide (Safe Mode)[/bold cyan]\n\n"
                    "This mode will guide you through manual setup.\n"
                    "For automatic setup, use: [green]sos gcloud init --auto[/green]"
                )
            )

            console.print("\n[bold]Step 1:[/bold] Check current status")
            console.print("Run: [green]sos gcloud check[/green]")

            console.print(
                "\n[bold]Step 2:[/bold] If quota exceeded, create new project:"
            )
            console.print(
                "Visit: [blue]https://console.cloud.google.com/projectcreate[/blue]"
            )
            console.print("Or run: [green]sos gcloud init --auto[/green]")

            console.print("\n[bold]Step 3:[/bold] Enable Gemini API")
            console.print("Run: [green]sos gcloud enable-api[/green]")

            console.print("\n[bold]Step 4:[/bold] Create API key")
            console.print("Visit: [blue]https://aistudio.google.com/app/apikey[/blue]")

            console.print("\n[bold]Step 5:[/bold] Configure SOS Agent")
            console.print("Run: [green]sos setup[/green]")

            return

        # Level 2: Auto mode - automatic project creation
        console.print(
            Panel(
                "[bold yellow]⚠️  AUTO-MODE WARNING ⚠️[/bold yellow]\n\n"
                "This will automatically:\n"
                "✓ Create new GCP project\n"
                "✓ Enable Gemini API\n"
                "✓ Set as active project\n\n"
                "[bold]Note:[/bold] You still need to create API key manually at:\n"
                "https://aistudio.google.com/app/apikey",
                style="yellow",
            )
        )

        if not click.confirm("\nType 'yes' to continue with auto-setup", default=False):
            console.print("[yellow]Setup cancelled[/yellow]")
            return

        # Create project
        console.print("\n[cyan]Creating new GCP project...[/cyan]")
        project = manager.create_project(project_id=project_id, auto_confirm=True)

        console.print(f"[green]✓ Project created: {project.project_id}[/green]")

        # Enable API
        console.print("\n[cyan]Enabling Gemini API...[/cyan]")
        manager.enable_api(project.project_id)

        console.print("[green]✓ Gemini API enabled[/green]")

        # Final instructions
        console.print(
            Panel(
                "[bold green]✓ Setup Complete![/bold green]\n\n"
                f"Project ID: [bold]{project.project_id}[/bold]\n\n"
                "[yellow]⚠️  Important:[/yellow] Create API key manually:\n"
                "1. Visit: [blue]https://aistudio.google.com/app/apikey[/blue]\n"
                f"2. Select project: [bold]{project.project_id}[/bold]\n"
                "3. Create API key\n"
                "4. Run: [green]sos setup[/green] and paste the key",
                style="green",
            )
        )

    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    try:
        cli(_anyio_backend="asyncio")
    except KeyboardInterrupt:
        console.print("\n[yellow]SOS Agent interrupted[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
