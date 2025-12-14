import pytest
from src.tools.fixers import get_all_fixers


@pytest.mark.asyncio
async def test_all_fixers_dry_run_safety(mocker):
    """Ensure dry_run never calls subprocess (executes commands)."""
    # Mock subprocess to fail if called (or just spy)
    # create_subprocess_shell is the dangerous one
    mock_sub = mocker.patch("asyncio.create_subprocess_shell")

    fixers = get_all_fixers()
    for fixer in fixers:
        print(f"Testing dry_run for {fixer.name}")
        actions = await fixer.apply(dry_run=True)
        assert len(actions) > 0  # Should propose something

    # Assert subprocess was NEVER called
    mock_sub.assert_not_called()


@pytest.mark.asyncio
async def test_fixer_root_enforcement(mocker):
    """Ensure fixers requiring root fail if not root."""
    # Simulate non-root user
    mocker.patch("src.tools.fixers.network.is_root", return_value=False)
    mocker.patch("src.tools.fixers.services.is_root", return_value=False)
    mocker.patch("src.tools.fixers.disk.is_root", return_value=False)

    fixers = get_all_fixers()
    for fixer in fixers:
        if fixer.requires_root:
            print(f"Testing root enforcement for {fixer.name}")
            with pytest.raises(PermissionError):
                await fixer.apply(dry_run=False)


@pytest.mark.asyncio
async def test_services_fixer_logic(mocker):
    """Test ServicesFixer restarts critical services safely."""
    # Simulate root
    mocker.patch("src.tools.fixers.services.is_root", return_value=True)

    # Mock subprocess
    mock_sub = mocker.patch(
        "asyncio.create_subprocess_shell", new_callable=mocker.AsyncMock
    )
    mock_sub.return_value.returncode = 0
    mock_sub.return_value.communicate.return_value = (b"", b"")

    from src.tools.fixers.services import ServicesFixer

    fixer = ServicesFixer()

    actions = await fixer.apply(dry_run=False)

    assert "Restarted NetworkManager" in str(actions)
    assert "Restarted sshd" in str(actions)

    # Verify commands
    calls = [c[0][0] for c in mock_sub.call_args_list]
    assert any("systemctl restart NetworkManager" in cmd for cmd in calls)
    assert any("systemctl restart sshd" in cmd for cmd in calls)

    # Ensure NO "stop" commands were issued
    for cmd in calls:
        assert "stop" not in cmd, f"Dangerous command detected: {cmd}"


@pytest.mark.asyncio
async def test_disk_fixer_logic(mocker):
    """Test DiskCleanupFixer commands."""
    mocker.patch("src.tools.fixers.disk.is_root", return_value=True)
    mock_sub = mocker.patch(
        "asyncio.create_subprocess_shell", new_callable=mocker.AsyncMock
    )
    mock_sub.return_value.returncode = 0
    mock_sub.return_value.communicate.return_value = (b"", b"")

    from src.tools.fixers.disk import DiskCleanupFixer

    fixer = DiskCleanupFixer()

    await fixer.apply(dry_run=False)

    calls = [c[0][0] for c in mock_sub.call_args_list]
    assert any("apt-get clean" in cmd for cmd in calls)
    assert any("apt-get autoremove" in cmd for cmd in calls)

    # Verify safety: no rm -rf /
    for cmd in calls:
        assert "rm -rf /" not in cmd


@pytest.mark.asyncio
async def test_dns_fixer_safety(mocker):
    """Ensure DNS fixer backs up configuration."""
    mocker.patch("src.tools.fixers.network.is_root", return_value=True)
    mock_sub = mocker.patch(
        "asyncio.create_subprocess_shell", new_callable=mocker.AsyncMock
    )
    mock_sub.return_value.returncode = 0
    mock_sub.return_value.communicate.return_value = (b"", b"")
    # Mock open() to avoid writing to real file
    mocker.patch("builtins.open", mocker.mock_open())

    from src.tools.fixers.network import DNSFixer

    fixer = DNSFixer()

    await fixer.apply(dry_run=False)

    calls = [c[0][0] for c in mock_sub.call_args_list]
    # Ensure backup is made via CP (copy)
    assert any("cp /etc/resolv.conf" in cmd for cmd in calls)
    # Ensure no MV (destructive move)
    assert not any("mv /etc/resolv.conf" in cmd for cmd in calls)
