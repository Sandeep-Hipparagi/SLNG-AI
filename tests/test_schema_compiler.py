"""Test 1: Unmute Declarative Package Schema & Compilation Verification.

Asserts zero validation errors and validates generated LiveKit and SLNG compilation output.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    print(f"[RUN] {' '.join(cmd)} (in {cwd})")
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[ERROR] Return code: {result.returncode}")
        print(f"Stdout:\n{result.stdout}")
        print(f"Stderr:\n{result.stderr}")
    else:
        print(f"[OK] Stdout: {result.stdout.strip()}")
    return result


def main():
    root_dir = Path(__file__).resolve().parent.parent
    unmute_bin = root_dir / "bin" / "unmute.exe"
    if not unmute_bin.exists():
        unmute_bin = root_dir / "bin" / "unmute"
    if not unmute_bin.exists():
        import shutil
        which_unmute = shutil.which("unmute")
        if which_unmute:
            unmute_bin = Path(which_unmute)

    voice_pkg_dir = root_dir / "voice-package"
    slng_hosted_dir = voice_pkg_dir / "slng-hosted"

    assert unmute_bin.exists(), f"Unmute binary not found at {unmute_bin}"
    assert voice_pkg_dir.exists(), f"voice-package directory not found at {voice_pkg_dir}"

    print("\n=== STEP 1: VALIDATING LIVEKIT VOICE PACKAGE ===")
    res_val = run_cmd([str(unmute_bin), "validate"], cwd=voice_pkg_dir)
    assert res_val.returncode == 0, "unmute validate failed for voice-package"
    assert "livekit" in res_val.stdout, "LiveKit target did not pass validation"

    print("\n=== STEP 2: COMPILING LIVEKIT VOICE PACKAGE ===")
    res_comp = run_cmd([str(unmute_bin), "compile"], cwd=voice_pkg_dir)
    assert res_comp.returncode == 0, "unmute compile failed for voice-package"

    build_livekit = voice_pkg_dir / "build" / "livekit"
    assert (build_livekit / "agent.py").exists(), "Generated agent.py missing in build/livekit"
    assert (build_livekit / "agents.py").exists(), "Generated agents.py missing in build/livekit"
    assert (build_livekit / "compile-report.json").exists(), "compile-report.json missing"
    print(f"[SUCCESS] LiveKit build artifacts verified in {build_livekit}")

    print("\n=== STEP 3: VALIDATING SLNG HOSTED PACKAGE ===")
    res_slng_val = run_cmd([str(unmute_bin), "validate"], cwd=slng_hosted_dir)
    assert res_slng_val.returncode == 0, "unmute validate failed for slng-hosted"
    assert "slng" in res_slng_val.stdout, "SLNG target did not pass validation"

    print("\n=== STEP 4: COMPILING SLNG HOSTED PACKAGE ===")
    res_slng_comp = run_cmd([str(unmute_bin), "compile"], cwd=slng_hosted_dir)
    assert res_slng_comp.returncode == 0, "unmute compile failed for slng-hosted"

    build_slng = slng_hosted_dir / "build" / "slng"
    assert (build_slng / "agent.json").exists(), "Generated agent.json missing in build/slng"
    print(f"[SUCCESS] SLNG hosted build artifacts verified in {build_slng}")

    print("\n[PASSED 100%] ALL UNMUTE SCHEMA & COMPILATION TESTS PASSED 100%!")


if __name__ == "__main__":
    main()
