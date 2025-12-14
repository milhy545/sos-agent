import pytest
from src.tools.fixers.network import DNSFixer


@pytest.mark.asyncio
async def test_dns_fixer_dry_run():
    fixer = DNSFixer()
    actions = await fixer.apply(dry_run=True)
    assert len(actions) > 0
    assert any("Backup" in a for a in actions)
    assert any("8.8.8.8" in a for a in actions)


@pytest.mark.asyncio
async def test_dns_fixer_check(mocker):
    # Mock subprocess for check
    mock_proc = mocker.AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.returncode = 0  # Success

    mocker.patch("asyncio.create_subprocess_shell", return_value=mock_proc)

    fixer = DNSFixer()
    needs_fix, reason = await fixer.check()
    assert needs_fix is False
    assert "normal" in reason


@pytest.mark.asyncio
async def test_dns_fixer_check_fail(mocker):
    # Mock subprocess for check failure
    mock_proc = mocker.AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.returncode = 1  # Failure

    mocker.patch("asyncio.create_subprocess_shell", return_value=mock_proc)

    fixer = DNSFixer()
    needs_fix, reason = await fixer.check()
    assert needs_fix is True
    assert "Cannot reach" in reason
