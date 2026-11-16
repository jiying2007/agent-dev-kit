"""Controlled host-only CMake cache-identity evidence; no repository edits."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
cmake = Path("/workspace/scratch/771b38332ec2/domain-audit-tools/cmake-wheel/cmake/data/bin/cmake")
ninja = Path("/workspace/scratch/fe5385ca063a/verification-tools/ninja")
rows = []

def run(label, args):
    p = subprocess.run([str(a) for a in args], capture_output=True, text=True, timeout=30)
    row = {"label": label, "argv": [str(a) for a in args], "exit_code": p.returncode,
           "stdout": p.stdout, "stderr": p.stderr}
    rows.append(row)
    if p.returncode:
        raise RuntimeError(row)
    return p.stdout

def configure(label, build, toolchain):
    return run(label, [cmake, "-S", root / "src", "-B", root / build,
                      "-G", "Ninja", f"-DCMAKE_MAKE_PROGRAM={ninja}",
                      f"-DCMAKE_TOOLCHAIN_FILE={root / toolchain}",
                      "-DCMAKE_BUILD_TYPE=Debug", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"])

def observe(label, build):
    run(label + "-build", [cmake, "--build", root / build, "--config", "Debug", "--parallel", "1", "--verbose"])
    actual = run(label + "-execute", [root / build / "probe"]).strip()
    commands = json.loads((root / build / "compile_commands.json").read_text())
    cache = (root / build / "CMakeCache.txt").read_text()
    system = next((root / build / "CMakeFiles").glob("*/CMakeSystem.cmake")).read_text()
    rows.append({"label": label + "-identity", "actual": actual,
                 "compile_commands": commands,
                 "cache_toolchain": [line for line in cache.splitlines() if line.startswith("CMAKE_TOOLCHAIN_FILE:")],
                 "system_toolchain_includes": [line for line in system.splitlines() if "toolchain" in line]})
    return actual, commands, cache, system

run("tool-version", [cmake, "--version"])
configure("fresh-a-configure", "build-reused", "toolchain-a.cmake")
a = observe("fresh-a", "build-reused")
configure("same-a-configure", "build-reused", "toolchain-a.cmake")
aa = observe("same-a", "build-reused")
configure("reused-to-b-configure", "build-reused", "toolchain-b.cmake")
ab = observe("reused-to-b", "build-reused")
configure("fresh-b-configure", "build-fresh-b", "toolchain-b.cmake")
b = observe("fresh-b", "build-fresh-b")
checks = {"initial_a": a[0] == "toolchain_id=101",
          "same_a_control": aa[0] == "toolchain_id=101",
          "changed_toolchain_cache_says_b": "toolchain-b.cmake" in "\n".join(line for line in ab[2].splitlines() if line.startswith("CMAKE_TOOLCHAIN_FILE:")),
          "changed_toolchain_still_a": ab[0] == "toolchain_id=101",
          "fresh_b_control": b[0] == "toolchain_id=202"}
out = {"kind": "real-host-cmake-cache-probe", "checks": checks, "runs": rows,
       "limits": "Host compiler/toolchain configuration only; no cross-target, device, HIL, or model A/B claim."}
(root / "evidence.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps({"checks": checks, "evidence": str(root / "evidence.json")}, indent=2))
if not all(checks.values()):
    raise SystemExit("Candidate falsified or environment differs; inspect raw evidence")
