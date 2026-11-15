#!/usr/bin/env python3
"""Offline host-only counterexamples for Skill command examples, not HIL evidence."""
from pathlib import Path
import hashlib
import json
import os
import struct
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT.parent / "domain-audit-tools"
ROWS = []


def run(label, argv, cwd=None, env=None):
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=20)
    row = {"label": label, "argv": [str(a) for a in argv], "exit": p.returncode,
           "stdout": p.stdout, "stderr": p.stderr}
    ROWS.append(row)
    return row


wheel = next(TOOLS.glob("cmake-3.31.6-*.whl"))
unpack = TOOLS / "cmake-wheel"
if not unpack.exists():
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(unpack)
cmake = unpack / "cmake/data/bin/cmake"
ctest = unpack / "cmake/data/bin/ctest"
for binary in [cmake, ctest]:
    binary.chmod(binary.stat().st_mode | 0o111)
run("ctest-version", [ctest, "--version"])

for name, content in {
    "empty": "# intentionally no tests\n",
    "pass": f'add_test(pass "{cmake}" "-E" "true")\n',
    "fail": f'add_test(fail "{cmake}" "-E" "false")\n',
    "disabled": f'add_test(disabled "{cmake}" "-E" "true")\nset_tests_properties(disabled PROPERTIES DISABLED TRUE)\n',
}.items():
    case = ROOT / "ctest" / name
    case.mkdir(parents=True, exist_ok=True)
    (case / "CTestTestfile.cmake").write_text(content)
    original = run(f"ctest-{name}-original", [ctest, "--test-dir", case, "--output-on-failure"])
    strict = run(f"ctest-{name}-strict", [ctest, "--test-dir", case, "--output-on-failure", "--no-tests=error"])
    if name == "empty":
        assert original["exit"] == 0 and strict["exit"] != 0
    if name == "pass":
        assert original["exit"] == strict["exit"] == 0
    if name == "fail":
        assert original["exit"] != 0 and strict["exit"] != 0

case = ROOT / "ctest" / "pass"
original = run("ctest-filtered-empty-original", [ctest, "--test-dir", case, "--output-on-failure", "-R", "not-a-test"])
strict = run("ctest-filtered-empty-strict", [ctest, "--test-dir", case, "--output-on-failure", "-R", "not-a-test", "--no-tests=error"])
assert original["exit"] == 0 and strict["exit"] != 0

source = ROOT / "relocation.c"
binary = ROOT / "relocation"
build = run("relocation-build", ["gcc", "-g", "-O0", "-fPIE", "-pie", str(source), "-ldl", "-o", str(binary)])
assert build["exit"] == 0
execution = run("relocation-addresses", [binary])
assert execution["exit"] == 0
runtime_pc, load_base = [int(x, 16) for x in execution["stdout"].split()]
raw = run("addr2line-raw-runtime-pc", ["addr2line", "-e", binary, hex(runtime_pc)])
correct = run("addr2line-corrected-pc", ["addr2line", "-e", binary, hex(runtime_pc - load_base)])
assert "??" in raw["stdout"] and "relocation.c:" in correct["stdout"]

wireshark_root = TOOLS / "wireshark-root"
tshark = wireshark_root / "usr/bin/tshark"
env = os.environ.copy()
env["LD_LIBRARY_PATH"] = str(wireshark_root / "usr/lib/x86_64-linux-gnu")
env["WIRESHARK_DATA_DIR"] = str(wireshark_root / "usr/share/wireshark")
env["WIRESHARK_CONFIG_DIR"] = str(ROOT / "wireshark-config")
run("tshark-version", [tshark, "--version"], env=env)

# Self-authored IPv4/UDP pcap. No live capture and -n prevents name resolution.
payload = b"fixture"
udp = struct.pack("!HHHH", 49152, 49153, 8 + len(payload), 0) + payload
ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(udp), 1, 0, 64, 17, 0,
                 bytes([198, 51, 100, 1]), bytes([198, 51, 100, 2]))
words = struct.unpack("!10H", ip)
checksum = sum(words)
while checksum >> 16:
    checksum = (checksum & 0xffff) + (checksum >> 16)
checksum = (~checksum) & 0xffff
ip = ip[:10] + struct.pack("!H", checksum) + ip[12:]
packet = ip + udp
header = struct.pack("<IHHIIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, 101)
pcap = ROOT / "one-packet.pcap"
pcap.write_bytes(header + struct.pack("<IIII", 1, 0, len(packet), len(packet)) + packet)
quiet = run("tshark-quiet-original", [tshark, "-n", "-r", pcap, "-q"], env=env)
visible = run("tshark-visible-fixed", [tshark, "-n", "-r", pcap], env=env)
fields = run("tshark-fields-control", [tshark, "-n", "-r", pcap, "-T", "fields",
             "-e", "frame.number", "-e", "ip.src", "-e", "ip.dst", "-e", "udp.length"], env=env)
assert quiet["exit"] == 0 and quiet["stdout"] == ""
assert visible["exit"] == 0 and "198.51.100.1" in visible["stdout"]
assert fields["stdout"] == "1\t198.51.100.1\t198.51.100.2\t15\n"
bad_pcap = ROOT / "malformed.pcap"
bad_pcap.write_bytes(b"not a pcap\n")
malformed = run("tshark-malformed-control", [tshark, "-n", "-r", bad_pcap], env=env)
assert malformed["exit"] != 0

report = {"scope": "host-only deterministic fixtures; no live kernel/MCU/network evidence",
          "cmake_wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
          "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "rows": ROWS}
(ROOT / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
for row in ROWS:
    print(f'{row["label"]}: exit={row["exit"]}; stdout={row["stdout"][:180]!r}; stderr={row["stderr"][:140]!r}')
print("report:", ROOT / "results.json")
