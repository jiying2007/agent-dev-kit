"""Real host controls for CMake build identity; prose compliance needs a consumer task.

These controls also pass against the old published command block. They preserve
the physical counterexample and the safe directory choice, not a model RED/GREEN.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import tempfile
import unittest

from tests.test_skill_command_examples import CMAKE, bash_example, run_example


class CmakeBuildIdentityMethodsTests(unittest.TestCase):
    def setUp(self):
        missing = [name for name in ("cmake", "ninja", "cc", "bash")
                   if shutil.which(name) is None]
        if missing:
            reason = "real CMake identity controls require: " + ", ".join(missing)
            if os.environ.get("GITHUB_ACTIONS") == "true":
                self.fail(reason)
            self.skipTest(reason)
        temporary = tempfile.TemporaryDirectory(prefix="adk cmake identity ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.evidence = self.root / "evidence"
        self.evidence.mkdir()
        self.records = []
        self.compiler = shutil.which("cc")
        self.old = self.root / "build a"
        self.fresh = self.root / "build b"
        (self.source / "CMakeLists.txt").write_text(
            'cmake_minimum_required(VERSION 3.21)\n'
            'project(adk_build_identity C)\n'
            'set(CMAKE_EXPORT_COMPILE_COMMANDS ON)\n'
            'add_executable(probe main.c)\n')
        (self.source / "main.c").write_text(
            '#include <stdio.h>\n'
            'int main(void) { printf("toolchain_id=%d\\n", TOOLCHAIN_ID); return 0; }\n')
        self.toolchains = {}
        for name, identity in (("a", 101), ("b", 202)):
            path = self.root / f"toolchain-{name}.cmake"
            path.write_text(f'set(CMAKE_C_COMPILER "{self.compiler}")\n'
                            f'set(CMAKE_C_FLAGS_INIT "-DTOOLCHAIN_ID={identity}")\n')
            self.toolchains[name] = path
        self.environment = dict(os.environ)
        for name in ("CFLAGS", "CPPFLAGS", "LDFLAGS", "CMAKE_TOOLCHAIN_FILE",
                     "CMAKE_GENERATOR", "CMAKE_GENERATOR_PLATFORM", "CMAKE_GENERATOR_TOOLSET"):
            self.environment.pop(name, None)
        self.environment.update(
            CC=self.compiler, VERBOSE="1", ADK_SOURCE_DIR=str(self.source),
            ADK_BUILD_MODE="manual", ADK_BINARY_DIR=str(self.old),
            ADK_GENERATOR="Ninja", ADK_TOOLCHAIN_FILE=str(self.toolchains["a"]),
            ADK_CONFIG="Debug", ADK_BUILD_JOBS="1", ADK_TEST_BACKEND="compile-only")

    def published(self, label, directory, toolchain, **overrides):
        environment = dict(self.environment, ADK_BINARY_DIR=str(directory),
                           ADK_TOOLCHAIN_FILE=str(toolchain), **overrides)
        code = bash_example(CMAKE, "# cmake-build:")
        result = run_example(code, self.source, environment=environment, label=label)
        record = {"label": label, "binary_dir": str(directory),
                  "requested_toolchain": str(toolchain), "mode": environment["ADK_BUILD_MODE"],
                  "published_code_sha256": hashlib.sha256(code.encode()).hexdigest(),
                  "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        self.records.append(record)
        (self.evidence / f"{label}.json").write_text(json.dumps(record, indent=2) + "\n")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("target tests: not-run", result.stdout)
        return result

    def command(self, label, *arguments):
        argv = [str(argument) for argument in arguments]
        result = run_example(shlex.join(argv), self.source, environment=self.environment, label=label)
        self.records.append({"label": label, "argv": argv, "exit_code": result.returncode,
                             "stdout": result.stdout, "stderr": result.stderr})
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result

    def assert_identity(self, directory, value, loaded, *, requested=None):
        executed = self.command(f"execute-{directory.name}", directory / "probe")
        self.assertEqual(f"toolchain_id={value}\n", executed.stdout)
        cache = (directory / "CMakeCache.txt").read_text()
        entries = {line.split(":", 1)[0]: line.split("=", 1)[1]
                   for line in cache.splitlines() if ":" in line and "=" in line
                   and not line.startswith(("//", "#"))}
        self.assertEqual(str(requested or loaded), entries["CMAKE_TOOLCHAIN_FILE"])
        self.assertEqual("Ninja", entries["CMAKE_GENERATOR"])
        self.assertEqual("Debug", entries["CMAKE_BUILD_TYPE"])
        system_path, = (directory / "CMakeFiles").glob("*/CMakeSystem.cmake")
        compiler_path, = (directory / "CMakeFiles").glob("*/CMakeCCompiler.cmake")
        system, compiler = system_path.read_text(), compiler_path.read_text()
        self.assertIn(f'include("{loaded}")', system)
        self.assertIn(f'set(CMAKE_C_COMPILER "{self.compiler}")', compiler)
        commands = json.loads((directory / "compile_commands.json").read_text())
        self.assertEqual(1, len(commands))
        self.assertEqual(str(self.source / "main.c"), commands[0]["file"])
        self.assertIn(f"-DTOOLCHAIN_ID={value}", commands[0]["command"])
        self.records.append({"label": "observed-identity", "binary_dir": str(directory),
                             "program_stdout": executed.stdout, "cache": entries,
                             "system": system, "compiler": compiler, "compile_commands": commands})

    @staticmethod
    def snapshot(directory):
        return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in directory.rglob("*") if path.is_file()}

    def test_same_identity_keeps_incremental_build(self):
        first = self.published("initial-a", self.old, self.toolchains["a"])
        self.assertIn("-DTOOLCHAIN_ID=101", first.stdout)
        self.assert_identity(self.old, 101, self.toolchains["a"])
        object_path = self.old / "CMakeFiles/probe.dir/main.c.o"
        original = (object_path.stat().st_mtime_ns, object_path.read_bytes())
        self.published("same-a", self.old, self.toolchains["a"])
        self.assert_identity(self.old, 101, self.toolchains["a"])
        self.assertEqual(original, (object_path.stat().st_mtime_ns, object_path.read_bytes()))

    def test_old_directory_can_report_b_but_build_a_even_after_clean_first(self):
        self.published("initial-a", self.old, self.toolchains["a"])
        # Deliberately violate the workflow's pre-configure identity decision.
        # Exit 0 and a changed cache entry do not demonstrate toolchain replacement.
        self.published("unsafe-in-place-b", self.old, self.toolchains["b"])
        self.assert_identity(self.old, 101, self.toolchains["a"], requested=self.toolchains["b"])
        rebuilt = self.command("forced-rebuild", "cmake", "--build", self.old,
                               "--config", "Debug", "--parallel", "1", "--clean-first", "--verbose")
        self.assertIn("-DTOOLCHAIN_ID=101", rebuilt.stdout)
        self.assertNotIn("-DTOOLCHAIN_ID=202", rebuilt.stdout)
        self.assert_identity(self.old, 101, self.toolchains["a"], requested=self.toolchains["b"])

    def check_fresh_b(self, **overrides):
        self.published("initial-a", self.old, self.toolchains["a"])
        self.assert_identity(self.old, 101, self.toolchains["a"])
        retained = self.snapshot(self.old)
        old_log = (self.evidence / "initial-a.json").read_bytes()
        built = self.published("fresh-b", self.fresh, self.toolchains["b"], **overrides)
        self.assertIn("-DTOOLCHAIN_ID=202", built.stdout)
        self.assert_identity(self.fresh, 202, self.toolchains["b"])
        self.assertEqual(retained, self.snapshot(self.old))
        self.assertEqual(old_log, (self.evidence / "initial-a.json").read_bytes())

    def test_new_manual_directory_builds_b_and_preserves_old_cache_and_logs(self):
        self.check_fresh_b()

    def test_matching_preset_selects_fresh_b_and_preserves_old_directory(self):
        (self.source / "CMakePresets.json").write_text(json.dumps({
            "version": 3,
            "configurePresets": [{"name": "configure-b", "generator": "Ninja",
                                  "binaryDir": str(self.fresh),
                                  "toolchainFile": str(self.toolchains["b"]),
                                  "cacheVariables": {"CMAKE_BUILD_TYPE": "Debug"}}],
            "buildPresets": [{"name": "build-b", "configurePreset": "configure-b",
                              "configuration": "Debug"}],
        }))
        self.check_fresh_b(ADK_BUILD_MODE="preset", ADK_CONFIGURE_PRESET="configure-b",
                           ADK_BUILD_PRESET="build-b")


if __name__ == "__main__":
    unittest.main()
