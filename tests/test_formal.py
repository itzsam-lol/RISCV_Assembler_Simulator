import pytest
from formal.harness.differential import DifferentialHarness, run_golden, ArchState
from formal.harness.program_gen import random_program, corner_case_programs
from riscv.assembler import Assembler
from riscv.simulator import Simulator


def _run(source: str) -> Simulator:
    binary = Assembler().assemble(source)
    program = {i * 4: enc for i, enc in enumerate(binary)}
    sim = Simulator()
    sim.run(program)
    return sim


class TestGoldenModel:
    def test_all_corner_cases_assemble_and_run(self):
        for src in corner_case_programs():
            sim = _run(src)
            assert sim.halted

    def test_random_programs_complete(self):
        for seed in range(30):
            src = random_program(n_instructions=15, seed=seed)
            sim = _run(src)
            assert sim.halted

    def test_diff_harness_golden_only_passes(self):
        harness = DifferentialHarness(dut_binary=None)
        programs = corner_case_programs() + [random_program(seed=i) for i in range(10)]
        summary = harness.run_suite(programs)
        assert summary["failed"] == 0

    def test_arch_state_diff_identical(self):
        sim = _run("addi x1, x0, 42\nhalt")
        regs = list(sim.registers)
        mem = {addr: val for addr, val in sim.data_memory.items() if val != 0}
        a = ArchState(regs, mem, sim.pc)
        b = ArchState(list(regs), dict(mem), sim.pc)
        assert a.diff(b) == []

    def test_arch_state_diff_detects_register_mismatch(self):
        sim = _run("addi x1, x0, 42\nhalt")
        regs = list(sim.registers)
        mem = {}
        a = ArchState(regs, mem, sim.pc)
        bad_regs = list(regs)
        bad_regs[1] = 0
        b = ArchState(bad_regs, mem, sim.pc)
        diffs = a.diff(b)
        assert any("x01" in d for d in diffs)

    def test_arch_state_diff_detects_memory_mismatch(self):
        a = ArchState([0] * 32, {0x100: 1}, 0)
        b = ArchState([0] * 32, {0x100: 2}, 0)
        diffs = a.diff(b)
        assert len(diffs) == 1
        assert "0x00000100" in diffs[0]

    def test_lb_sign_extension(self):
        src = "addi x1, x0, -1\nsb x1, 0(sp)\nlb x2, 0(sp)\nhalt"
        sim = _run(src)
        assert sim.registers[2] == 0xFFFFFFFF

    def test_lh_sign_extension(self):
        src = "addi x1, x0, -1\nsh x1, 0(sp)\nlh x2, 0(sp)\nhalt"
        sim = _run(src)
        assert sim.registers[2] == 0xFFFFFFFF

    def test_branch_offset_encoding_roundtrip(self):
        src = (
            "addi x1, x0, 0\n"
            "loop: addi x1, x1, 1\n"
            "addi x2, x0, 5\n"
            "bne x1, x2, loop\n"
            "halt"
        )
        sim = _run(src)
        assert sim.registers[1] == 5

    def test_jalr_lsb_always_cleared(self):
        src = (
            "addi x1, x0, 13\n"
            "jalr x2, x1, 0\n"
            "addi x3, x0, 99\n"
            "halt"
        )
        sim = _run(src)
        assert sim.registers[3] == 0

    def test_sra_negative_preserves_sign(self):
        src = "addi x1, x0, -128\nsrai x2, x1, 3\nhalt"
        sim = _run(src)
        assert sim.registers[2] == 0xFFFFFFF0

    def test_add_overflow_no_trap(self):
        src = "lui x1, 524288\naddi x2, x0, 1\nadd x3, x1, x2\nhalt"
        sim = _run(src)
        assert sim.registers[3] == 0x80000001

    def test_random_seed_determinism(self):
        p1 = random_program(seed=7)
        p2 = random_program(seed=7)
        assert p1 == p2

    def test_different_seeds_different_programs(self):
        p1 = random_program(seed=0)
        p2 = random_program(seed=1)
        assert p1 != p2
