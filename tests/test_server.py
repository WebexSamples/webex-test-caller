import json
from dataclasses import replace
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from webex_test_caller.models import AudioAsset, RunConfig
from webex_test_caller.server import LocalRunServer


def _config(tmp_path: Path) -> RunConfig:
    audio_path = tmp_path / "caller.wav"
    audio_path.write_bytes(b"RIFF")
    return RunConfig(
        destination="9999",
        access_token="test-token",
        audio_path=audio_path,
        audio_sha256="0" * 64,
        audio_duration_seconds=1,
        remote_silence_seconds=0.75,
        initial_silence_fallback_seconds=10,
        prompt_timeout_seconds=60,
        call_timeout_seconds=120,
        post_audio_grace_seconds=5,
    )


def test_browser_event_receives_utc_correlation_timestamp(tmp_path) -> None:
    static_root = tmp_path / "static"
    static_root.mkdir()
    server = LocalRunServer(static_root, _config(tmp_path))
    server.start()
    try:
        request = Request(
            f"{server.url}api/events",
            data=json.dumps(
                {
                    "name": "injection_finished",
                    "timestamp": 12.5,
                    "details": {},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            assert response.status == 204

        event = server.next_event(1)
    finally:
        server.close()

    assert event is not None
    assert event.name == "injection_finished"
    assert event.timestamp == 12.5
    assert event.received_at_utc is not None
    assert event.received_at_utc.endswith("+00:00")


def test_server_exposes_each_prepared_audio_asset(tmp_path) -> None:
    first = tmp_path / "first.wav"
    second = tmp_path / "second.wav"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    config = replace(
        _config(tmp_path),
        audio_assets=(
            AudioAsset(first, "1" * 64, 1),
            AudioAsset(second, "2" * 64, 1),
        ),
    )
    static_root = tmp_path / "static"
    static_root.mkdir()
    server = LocalRunServer(static_root, config)
    server.start()
    try:
        with urlopen(f"{server.url}api/config") as response:
            assert response.headers["Cache-Control"] == "no-store"
            browser_config = json.load(response)
        with urlopen(f"{server.url}run/caller.wav") as response:
            legacy_audio = response.read()
        with urlopen(f"{server.url}run/caller-1.wav") as response:
            second_audio = response.read()
    finally:
        server.close()

    assert browser_config["audioUrls"] == [
        "/run/caller-0.wav",
        "/run/caller-1.wav",
    ]
    assert browser_config["audioUrl"] == "/run/caller.wav"
    assert legacy_audio == b"first"
    assert second_audio == b"second"


@pytest.mark.parametrize("method,path", [("GET", "api/config"), ("POST", "api/events")])
@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "attacker.example"},
        {"Origin": "https://attacker.example"},
        {"Origin": "null"},
        {"Sec-Fetch-Site": "cross-site"},
        {"Sec-Fetch-Site": "same-site"},
    ],
)
def test_server_rejects_foreign_hosts_and_browser_origins(
    tmp_path, method, path, headers
) -> None:
    server = LocalRunServer(tmp_path, _config(tmp_path))
    server.start()
    try:
        request = Request(
            server.url + path,
            method=method,
            data=b'{"name":"injection_finished"}' if method == "POST" else None,
            headers=headers,
        )
        with pytest.raises(HTTPError) as rejected:
            urlopen(request)
        assert rejected.value.code == 403
        assert b"test-token" not in rejected.value.read()
        assert server.next_event(0.01) is None
    finally:
        server.close()


def test_server_accepts_its_own_browser_origin(tmp_path) -> None:
    server = LocalRunServer(tmp_path, _config(tmp_path))
    server.start()
    try:
        request = Request(
            server.url + "api/events",
            method="POST",
            data=b'{"name":"frontend_ready"}',
            headers={
                "Origin": server.url.rstrip("/"),
                "Sec-Fetch-Site": "same-origin",
                "Content-Type": "application/json",
            },
        )
        with urlopen(request) as response:
            assert response.status == 204
        assert server.next_event(0.1).name == "frontend_ready"
    finally:
        server.close()


@pytest.mark.parametrize("length", ["-1", "65537", "invalid"])
def test_server_rejects_invalid_or_unbounded_event_lengths(tmp_path, length) -> None:
    server = LocalRunServer(tmp_path, _config(tmp_path))
    server.start()
    try:
        request = Request(
            server.url + "api/events",
            method="POST",
            data=b"{}",
            headers={"Content-Length": length},
        )
        with pytest.raises(HTTPError) as rejected:
            urlopen(request)
        assert rejected.value.code in {400, 413}
        assert server.next_event(0.01) is None
    finally:
        server.close()
