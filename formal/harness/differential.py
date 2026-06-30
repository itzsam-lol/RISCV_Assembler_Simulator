from __future__ import annotations
import json
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from riscv.assembler import Assembler
from riscv.simulator import Simulator


@dataclass
class ArchState:
    registers: list[int]
    memory: dict[int, int]
    pc: int

    def diff(self, other: "ArchState") -> list[str]:
        mismatches = []
        for i in range(32):
            if self.registers[i] != other.registers[i]:
                mismatches.append(
                    f"  x{i:02d}: golden={self.registers[i]:#010x}  dut={other.registers[i]:#010x}"
                )
        for addr in set(self.memory) | set(other.memory):
            a = self.memory.get(addr, 0)
            b = other.memory.get(addr, 0)
            if a != b:
                mismatches.append(
                    f"  mem[{addr:#010x}]: golden={a:#010x}  dut={b:#010x}"
                )
        if self.pc != other.pc:
            mismatches.append(f"  pc: golden={self.pc:#010x}  dut={other.pc:#010x}")
        return mismatches


@dataclass
class DiffResult:
    program_asm: str
    passed: bool
    mismatches: list[str] = field(default_factory=list)
    golden_steps: int = 0
    dut_steps: int = 0


def run_golden(binary: list[str]) -> tuple[ArchState, int]:
    program = {i * 4: enc for i, enc in enumerate(binary)}
    sim = Simulator()
    sim.run(program)
    mem = {addr: val for addr, val in sim.data_memory.items() if val != 0}
    return ArchState(list(sim.registers), mem, sim.pc), len(sim.trace)


def run_verilator_dut(binary: list[str], dut_binary: str) -> ArchState | None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".hex", delete=False) as f:
        for enc in binary:
            f.write(f"{int(enc, 2):08x}\n")
        hex_path = f.name

    try:
        result = subprocess.run(
            [dut_binary, hex_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        regs = data["registers"]
        mem = {int(k, 16): v for k, v in data.get("memory", {}).items()}
        return ArchState(regs, mem, data.get("pc", 0))
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None
    finally:
        os.unlink(hex_path)


class DifferentialHarness:
    def __init__(self, dut_binary: str | None = None) -> None:
        self.dut_binary = dut_binary
        self.results: list[DiffResult] = []

    def run_program(self, source: str) -> DiffResult:
        asm = Assembler()
        binary = asm.assemble(source)
        golden, steps = run_golden(binary)

        if self.dut_binary:
            dut = run_verilator_dut(binary, self.dut_binary)
            if dut is None:
                result = DiffResult(source, False, ["DUT simulation failed"], steps, 0)
            else:
                mismatches = golden.diff(dut)
                result = DiffResult(source, len(mismatches) == 0, mismatches, steps, steps)
        else:
            result = DiffResult(source, True, [], steps, 0)

        self.results.append(result)
        return result

    def run_suite(self, programs: list[str]) -> dict:
        for src in programs:
            self.run_program(src)

        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "failures": [
                {"program": r.program_asm[:80], "mismatches": r.mismatches}
                for r in self.results
                if not r.passed
            ],
        }

    def report(self) -> str:
        lines = []
        for i, r in enumerate(self.results):
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"[{status}] test {i+1}: golden_steps={r.golden_steps}")
            for m in r.mismatches:
                lines.append(m)
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        lines.append(f"\n{passed}/{total} passed")
        return "\n".join(lines)
