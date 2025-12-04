"""SOS Agent CLI - Interactive menu-driven rescue interface."""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

import asyncclick as click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .agent.client import SOSAgentClient
from .agent.config import SOSConfig, load_config
from .tools.log_analyzer import analyze_system_logs

console = Console()
logger = logging.getLogger(__name__)


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
    type=click.Choice(["gemini", "openai", "inception", "claude-agentapi"]),
    default=None,
    help="AI provider (overrides config)",
)
@click.pass_context
async def cli(ctx: click.Context, config: Optional[str], verbose: bool, emergency: bool, provider: Optional[str]) -> None:
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
@click.pass_context
async def diagnose(ctx: click.Context, category: str) -> None:
    """
    🔍 Run comprehensive system diagnostics.

    Analyzes logs, system health, and identifies issues.
    """
    client: SOSAgentClient = ctx.obj["client"]

    console.print(Panel(f"[bold cyan]Running {category} diagnostics...[/bold cyan]"))

    # STEP 1: Collect REAL system data instead of asking AI to hallucinate
    console.print("[dim]Collecting system logs (errors)...[/dim]")
    log_data_errors = await analyze_system_logs(time_range="24h", severity="error")

    console.print("[dim]Collecting system logs (warnings)...[/dim]")
    log_data_warnings = await analyze_system_logs(time_range="24h", severity="warning")

    # Merge data - combine errors and warnings
    log_data = {
        'hardware_errors': log_data_errors['hardware_errors'] + log_data_warnings['hardware_errors'],
        'driver_errors': log_data_errors['driver_errors'] + log_data_warnings['driver_errors'],
        'service_errors': log_data_errors['service_errors'] + log_data_warnings['service_errors'],
        'security_warnings': log_data_errors['security_warnings'] + log_data_warnings['security_warnings'],
        'recommendations': log_data_errors['recommendations'] + log_data_warnings['recommendations']
    }

    # STEP 2: Detect OS/System Info (CRITICAL - must know what we're fixing!)
    console.print("[dim]Detecting system information...[/dim]")
    try:
        os_release_proc = await asyncio.create_subprocess_shell(
            "cat /etc/os-release",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        os_release_out, _ = await os_release_proc.communicate()

        uname_proc = await asyncio.create_subprocess_shell(
            "uname -a",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
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
            "free -h",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        free_out, _ = await free_proc.communicate()

        df_proc = await asyncio.create_subprocess_shell(
            "df -h /",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        df_out, _ = await df_proc.communicate()

        uptime_proc = await asyncio.create_subprocess_shell(
            "uptime",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
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
    gui_keywords = ['x11', 'wayland', 'plasma', 'kde', 'gnome', 'display', 'xorg', 'gdm', 'sddm']
    gui_errors = [e for e in log_data['service_errors']
                  if any(kw in (e['message'].lower() + str(e['unit']).lower())
                        for kw in gui_keywords)]

    other_errors = [e for e in log_data['service_errors']
                    if e not in gui_errors]

    # STEP 5: Build prompt with ACTUAL DATA
    task = f"""
Analyze the following REAL system diagnostic data and provide recommendations.

=== CATEGORY: {category.upper()} ===

=== SYSTEM INFORMATION ===
{system_info}

IMPORTANT: Use the correct package manager for this OS!
- Debian/Ubuntu/MX Linux → apt/apt-get
- Red Hat/Fedora/CentOS → dnf/yum
- Arch Linux → pacman

=== SYSTEM LOGS (Last 24h) ===
Hardware Errors: {len(log_data['hardware_errors'])} found
Driver Errors: {len(log_data['driver_errors'])} found
Service Errors: {len(log_data['service_errors'])} found (including {len(gui_errors)} GUI/Display related)
Security Warnings: {len(log_data['security_warnings'])} found

GUI/Display Errors (HIGH PRIORITY):
{chr(10).join([f"- [{e['timestamp']}] {e['unit']}: {e['message']}" for e in gui_errors[:20]]) if gui_errors else "No GUI/Display errors found"}

Hardware Error Details:
{chr(10).join([f"- [{e['timestamp']}] {e['unit']}: {e['message']}" for e in log_data['hardware_errors'][:20]]) if log_data['hardware_errors'] else "No hardware errors found"}

Driver Error Details:
{chr(10).join([f"- [{e['timestamp']}] {e['unit']}: {e['message']}" for e in log_data['driver_errors'][:20]]) if log_data['driver_errors'] else "No driver errors found"}

Other Service Errors:
{chr(10).join([f"- [{e['timestamp']}] {e['unit']}: {e['message']}" for e in other_errors[:15]]) if other_errors else "No other service errors found"}

=== SYSTEM RESOURCES ===
{resource_data}

=== YOUR TASK ===
Based on the ACTUAL DATA above (not speculation):
1. Identify the root causes of any errors
2. Assess severity (CRITICAL, HIGH, MEDIUM, LOW)
3. Provide specific, actionable fixes with commands
4. Prioritize by risk and impact

IMPORTANT:
- Do NOT repeat this prompt in your response
- Start directly with analysis
- Format as natural flowing text paragraphs, NOT tables
- Use bullet points for recommendations
- Be specific - reference actual errors from the data above
"""

    try:
        buffer = ""
        async for chunk in client.execute_rescue_task(task):
            buffer += chunk
            console.print(chunk, end="")

    except KeyboardInterrupt:
        console.print("\n[yellow]Diagnostics interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error during diagnostics: {e}[/red]")
        logger.error(f"Diagnostics failed: {e}", exc_info=True)


@cli.command()
@click.argument(
    "category",
    type=click.Choice([
        "hardware",
        "services",
        "network",
        "performance",
        "security",
        "all"
    ]),
)
@click.option("--dry-run", is_flag=True, help="Show what would be fixed without making changes")
@click.pass_context
async def fix(ctx: click.Context, category: str, dry_run: bool) -> None:
    """
    🔧 Fix detected issues in specified category.

    CATEGORY: hardware, services, network, performance, security, all
    """
    client: SOSAgentClient = ctx.obj["client"]

    mode = "dry-run (preview only)" if dry_run else "ACTIVE"
    console.print(Panel(f"[bold yellow]Fix mode: {mode} - Category: {category}[/bold yellow]"))

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
        async for message in client.execute_rescue_task(task):
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        console.print(block.text)
            elif isinstance(message, dict) and "content" in message:
                for block in message["content"]:
                    if block.get("type") == "text":
                        console.print(block["text"])

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

    console.print(Panel(
        "[bold red]⚠️  EMERGENCY MODE ACTIVATED ⚠️[/bold red]\n\n"
        "This will perform aggressive recovery operations:\n"
        "- Stop non-critical processes\n"
        "- Clear temporary files and caches\n"
        "- Restart failed critical services\n"
        "- Apply thermal management if needed\n"
        "- Verify system stability",
        style="red"
    ))

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
        async for message in client.execute_rescue_task(task):
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        console.print(block.text)
            elif isinstance(message, dict) and "content" in message:
                for block in message["content"]:
                    if block.get("type") == "text":
                        console.print(block["text"])

        console.print(Panel("[bold green]✅ Emergency recovery completed[/bold green]", style="green"))

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

    console.print(Panel(
        f"[bold cyan]Starting continuous monitoring (interval: {interval}s)[/bold cyan]\n"
        "Press Ctrl+C to stop"
    ))

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

            async for message in client.execute_rescue_task(task):
                if hasattr(message, "content"):
                    for block in message.content:
                        if hasattr(block, "text"):
                            console.print(block.text)
                elif isinstance(message, dict) and "content" in message:
                    for block in message["content"]:
                        if block.get("type") == "text":
                            console.print(block["text"])

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


@cli.command()
@click.pass_context
async def menu(ctx: click.Context) -> None:
    """
    📋 Interactive menu - choose rescue operations.

    Displays available categories and actions.
    """
    console.print(Panel("[bold cyan]🆘 SOS Agent - Main Menu[/bold cyan]"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Description")
    table.add_column("Command")

    table.add_row(
        "System Diagnostics",
        "Analyze logs, check health, identify issues",
        "sos diagnose"
    )
    table.add_row(
        "Fix Issues",
        "Repair detected problems",
        "sos fix <category>"
    )
    table.add_row(
        "Emergency Recovery",
        "Aggressive stabilization and cleanup",
        "sos emergency"
    )
    table.add_row(
        "Monitor",
        "Continuous real-time monitoring",
        "sos monitor"
    )
    table.add_row(
        "Boot/GRUB",
        "Boot system diagnostics and fixes",
        "sos check-boot"
    )
    table.add_row(
        "Applications",
        "Optimize/clean/fix apps (flatpak, snap, docker)",
        "sos optimize-apps"
    )
    table.add_row(
        "Security Audit",
        "System security check",
        "sos security-audit"
    )
    table.add_row(
        "Backup Profile",
        "User profile backup and migration",
        "sos backup-profile"
    )

    console.print(table)

    console.print("\n[dim]Run 'sos <command> --help' for more details[/dim]")


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
        async for message in client.execute_rescue_task(task):
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        console.print(block.text)
            elif isinstance(message, dict) and "content" in message:
                for block in message["content"]:
                    if block.get("type") == "text":
                        console.print(block["text"])

    except Exception as e:
        console.print(f"[red]Error checking boot: {e}[/red]")


@cli.command()
@click.option(
    "--platform",
    type=click.Choice(["all", "flatpak", "snap", "docker", "appimage", "apt"]),
    default="all",
    help="Application platform to optimize",
)
@click.pass_context
async def optimize_apps(ctx: click.Context, platform: str) -> None:
    """
    📦 Optimize, clean, and fix applications.

    Supports: flatpak, snap, docker, appimage, apt
    """
    client: SOSAgentClient = ctx.obj["client"]

    console.print(Panel(f"[bold cyan]Optimizing {platform} applications...[/bold cyan]"))

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
        async for message in client.execute_rescue_task(task):
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        console.print(block.text)
            elif isinstance(message, dict) and "content" in message:
                for block in message["content"]:
                    if block.get("type") == "text":
                        console.print(block["text"])

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
            console.print("Then: [green]gcloud config set project YOUR_PROJECT_ID[/green]")
            return

        console.print(f"[green]✓[/green] Active project: [bold]{current_project}[/bold]")

        # Check if Gemini API is enabled
        api_enabled = manager.is_api_enabled(current_project)
        if api_enabled:
            console.print("[green]✓[/green] Gemini API: [bold green]Enabled[/bold green]")
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
            console.print("2. Use different provider: [green]sos --provider mercury diagnose[/green]")
            console.print("3. Create new project: [green]sos gcloud setup --auto[/green]")

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
            console.print("\nCreate one: [green]sos gcloud setup --auto[/green]")

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
@click.option("--auto", is_flag=True, help="Enable auto-mode (creates project automatically)")
@click.option("--project-id", help="Custom project ID (auto-generated if not provided)")
def setup(auto: bool, project_id: Optional[str]) -> None:
    """Setup Google Cloud project for SOS Agent.

    Level 1 (Safe): Guides you through manual setup
    Level 2 (Auto): Automatically creates and configures project (requires --auto flag)
    """
    from .gcloud.manager import GCloudManager

    try:
        manager = GCloudManager()

        if not auto:
            # Level 1: Safe mode - just guidance
            console.print(Panel(
                "[bold cyan]Google Cloud Setup Guide (Safe Mode)[/bold cyan]\n\n"
                "This mode will guide you through manual setup.\n"
                "For automatic setup, use: [green]sos gcloud setup --auto[/green]"
            ))

            console.print("\n[bold]Step 1:[/bold] Check current status")
            console.print("Run: [green]sos gcloud check[/green]")

            console.print("\n[bold]Step 2:[/bold] If quota exceeded, create new project:")
            console.print("Visit: [blue]https://console.cloud.google.com/projectcreate[/blue]")
            console.print("Or run: [green]sos gcloud setup --auto[/green]")

            console.print("\n[bold]Step 3:[/bold] Enable Gemini API")
            console.print("Run: [green]sos gcloud enable-api[/green]")

            console.print("\n[bold]Step 4:[/bold] Create API key")
            console.print("Visit: [blue]https://aistudio.google.com/app/apikey[/blue]")

            console.print("\n[bold]Step 5:[/bold] Configure SOS Agent")
            console.print("Run: [green]sos setup[/green]")

            return

        # Level 2: Auto mode - automatic project creation
        console.print(Panel(
            "[bold yellow]⚠️  AUTO-MODE WARNING ⚠️[/bold yellow]\n\n"
            "This will automatically:\n"
            "✓ Create new GCP project\n"
            "✓ Enable Gemini API\n"
            "✓ Set as active project\n\n"
            "[bold]Note:[/bold] You still need to create API key manually at:\n"
            "https://aistudio.google.com/app/apikey",
            style="yellow"
        ))

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
        console.print(Panel(
            "[bold green]✓ Setup Complete![/bold green]\n\n"
            f"Project ID: [bold]{project.project_id}[/bold]\n\n"
            "[yellow]⚠️  Important:[/yellow] Create API key manually:\n"
            "1. Visit: [blue]https://aistudio.google.com/app/apikey[/blue]\n"
            f"2. Select project: [bold]{project.project_id}[/bold]\n"
            "3. Create API key\n"
            "4. Run: [green]sos setup[/green] and paste the key",
            style="green"
        ))

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
