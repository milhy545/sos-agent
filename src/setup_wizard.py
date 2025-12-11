#!/usr/bin/env python3
"""SOS Agent Setup Wizard - Interactive API key configuration."""

import sys
from pathlib import Path


def print_banner():
    """Print SOS Agent banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🆘  SOS AGENT - System Rescue & Optimization  🆘      ║
║                                                           ║
║          Interactive Setup Wizard v1.0                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def get_api_key(
    service_name: str, env_var: str, url: str, optional: bool = False
) -> str:
    """
    Prompt user for API key.

    Args:
        service_name: Service name (e.g., "Gemini")
        env_var: Environment variable name
        url: URL to get API key
        optional: Whether this key is optional

    Returns:
        API key or empty string
    """
    print(f"\n{'─' * 60}")
    print(f"📌 {service_name} API Key")
    print(f"{'─' * 60}")

    if optional:
        print("⚠️  This API key is OPTIONAL.")

    print(f"🔗 Get your key at: {url}")
    print()

    while True:
        key = input(f"Enter {service_name} API key (or press Enter to skip): ").strip()

        if not key:
            if optional:
                print(f"ℹ️  Skipping {service_name} configuration.")
                return ""
            else:
                print(f"❌ {service_name} API key is required!")
                continue

        # Basic validation
        if len(key) < 10:
            print("❌ API key seems too short. Please check and try again.")
            continue

        return key


def setup_wizard():
    """Run interactive setup wizard."""
    print_banner()

    print("\n👋 Welcome to SOS Agent Setup!")
    print()
    print("This wizard will help you configure API keys for AI providers.")
    print("You need at least ONE API key to use SOS Agent.")
    print()
    print("Supported providers:")
    print("  🟢 Gemini (Google) - Recommended, fast and free tier available")
    print("  🔵 OpenAI (GPT-4o) - Powerful but requires paid subscription")
    print("  🟣 Inception Labs Mercury - Fast coding model")
    print("  🟡 Claude (via AgentAPI) - OAuth, no key needed (has auth issues)")
    print()

    proceed = input("Ready to start? (y/n): ").strip().lower()
    if proceed != "y":
        print("\n👋 Setup cancelled. Run 'sos setup' when ready!")
        sys.exit(0)

    # Language selection
    print("\n" + "=" * 60)
    print("  🌍 Language Selection / Výběr Jazyka")
    print("=" * 60)
    print("Choose AI response language / Vyberte jazyk odpovědí AI:")
    print("  1️⃣  English (default)")
    print("  2️⃣  Čeština (Czech)")
    print()

    language_choice = input("Enter choice (1 or 2) [1]: ").strip() or "1"

    if language_choice == "2":
        ai_language = "cs"
        language_name = "Čeština"
        print(f"✅ Jazyk nastaven: {language_name}")
    else:
        ai_language = "en"
        language_name = "English"
        print(f"✅ Language set: {language_name}")

    # Collect API keys
    api_keys = {"SOS_AI_LANGUAGE": ai_language}

    # Gemini (recommended)
    print("\n" + "=" * 60)
    print("  RECOMMENDED: Gemini API")
    print("=" * 60)
    print("🌟 Gemini is fast, reliable, and has a generous free tier.")
    gemini_key = get_api_key(
        "Gemini",
        "GEMINI_API_KEY",
        "https://aistudio.google.com/app/apikey",
        optional=False,
    )
    if gemini_key:
        api_keys["GEMINI_API_KEY"] = gemini_key

    # OpenAI (optional)
    openai_key = get_api_key(
        "OpenAI",
        "OPENAI_API_KEY",
        "https://platform.openai.com/api-keys",
        optional=True,
    )
    if openai_key:
        api_keys["OPENAI_API_KEY"] = openai_key

    # Inception Labs (optional)
    inception_key = get_api_key(
        "Inception Labs Mercury",
        "INCEPTION_API_KEY",
        "https://inceptionlabs.ai",
        optional=True,
    )
    if inception_key:
        api_keys["INCEPTION_API_KEY"] = inception_key

    # Save to .env
    print("\n" + "=" * 60)
    print("  💾 Saving Configuration")
    print("=" * 60)

    env_path = Path.cwd() / ".env"

    # Read existing .env or create new one
    existing_lines = []
    if env_path.exists():
        with open(env_path, "r") as f:
            existing_lines = f.readlines()

    # Update or add API keys
    updated_lines = []
    keys_updated = set()

    for line in existing_lines:
        key_found = False
        for env_var, value in api_keys.items():
            if line.strip().startswith(f"{env_var}="):
                updated_lines.append(f"{env_var}={value}\n")
                keys_updated.add(env_var)
                key_found = True
                break

        if not key_found:
            updated_lines.append(line)

    # Add new keys that weren't in existing file
    for env_var, value in api_keys.items():
        if env_var not in keys_updated:
            updated_lines.append(f"{env_var}={value}\n")

    # Write back
    with open(env_path, "w") as f:
        f.writelines(updated_lines)

    print(f"✅ Configuration saved to: {env_path}")

    # Summary
    print("\n" + "=" * 60)
    print("  🎉 Setup Complete!")
    print("=" * 60)
    print()
    print("Configured providers:")
    for key in api_keys.keys():
        provider = key.replace("_API_KEY", "").replace("_", " ").title()
        print(f"  ✅ {provider}")

    print()
    print("🚀 You can now use SOS Agent!")
    print()
    print("Quick start:")
    print("  sos diagnose --category hardware    # Run hardware diagnostics")
    print("  sos menu                             # Interactive menu")
    print("  sos --help                           # See all commands")
    print()


if __name__ == "__main__":
    try:
        setup_wizard()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during setup: {e}")
        sys.exit(1)
