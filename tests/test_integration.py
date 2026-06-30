import os
import pytest
from riscv.assembler import Assembler
from riscv.simulator import Simulator


def assemble_and_run(source: str) -> Simulator:
    binary = Assembler().assemble(source)
    program = {i * 4: enc for i, enc in enumerate(binary)}
    sim = Simulator()
    sim.run(program)
    return sim


def load_program(name: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "programs", name)
    with open(path) as f:
        return f.read()


class TestEndToEnd:
    def test_fibonacci(self):
        sim = assemble_and_run(load_program("fibonacci.asm"))
        assert sim.registers[11] == 55

    def test_mem_rw(self):
        sim = assemble_and_run(load_program("mem_rw.asm"))
        assert sim.registers[6] == 42

    def test_call_ret(self):
        sim = assemble_and_run(load_program("call_ret.asm"))
        assert sim.registers[10] == 8

    def test_countdown_loop(self):
        src = (
            "addi x1, x0, 10\n"
            "loop: addi x1, x1, -1\n"
            "bne x1, x0, loop\n"
            "halt"
        )
        sim = assemble_and_run(src)
        assert sim.registers[1] == 0

    def test_sum_1_to_10(self):
        src = (
            "addi x1, x0, 10\n"
            "addi x2, x0, 0\n"
            "loop: add x2, x2, x1\n"
            "addi x1, x1, -1\n"
            "bne x1, x0, loop\n"
            "halt"
        )
        sim = assemble_and_run(src)
        assert sim.registers[2] == 55

    def test_max_of_two(self):
        src = (
            "addi x1, x0, 7\n"
            "addi x2, x0, 13\n"
            "bge x1, x2, done\n"
            "addi x1, x2, 0\n"
            "done: halt"
        )
        sim = assemble_and_run(src)
        assert sim.registers[1] == 13

    def test_power_of_two(self):
        src = (
            "addi x1, x0, 1\n"
            "addi x2, x0, 8\n"
            "loop: slli x1, x1, 1\n"
            "addi x2, x2, -1\n"
            "bne x2, x0, loop\n"
            "halt"
        )
        sim = assemble_and_run(src)
        assert sim.registers[1] == 256

    def test_stack_push_pop(self):
        src = (
            "addi x1, x0, 100\n"
            "addi x2, x0, 200\n"
            "sw x1, 0(sp)\n"
            "sw x2, 4(sp)\n"
            "lw x3, 0(sp)\n"
            "lw x4, 4(sp)\n"
            "halt"
        )
        sim = assemble_and_run(src)
        assert sim.registers[3] == 100
        assert sim.registers[4] == 200

    def test_text_trace_format(self):
        sim = assemble_and_run("addi x1, x0, 1\nhalt")
        lines = sim.text_trace().strip().split("\n")
        assert len(lines) == 2
        fields = lines[0].split(" ")
        assert fields[0].startswith("0b")
        assert len(fields[0]) == 34

    def test_json_trace_all_steps_present(self):
        sim = assemble_and_run("addi x1, x0, 1\naddi x2, x0, 2\nhalt")
        d = sim.to_json_dict()
        assert len(d["steps"]) == 3

    def test_memory_dump_text_format(self):
        sim = assemble_and_run("addi x1, x0, 5\nsw x1, 0(sp)\nhalt")
        dump = sim.memory_dump_text()
        lines = dump.strip().split("\n")
        assert lines[0].startswith("0x000")
        assert ":0b" in lines[0]

    def test_rst_mid_program(self):
        src = (
            "addi x1, x0, 99\n"
            "rst\n"
            "halt"
        )
        sim = assemble_and_run(src)
        assert sim.registers[1] == 0

    def test_byte_addressing(self):
        src = (
            "addi x1, x0, 0x41\n"
            "sb x1, 0(sp)\n"
            "addi x1, x0, 0x42\n"
            "sb x1, 1(sp)\n"
            "lbu x5, 0(sp)\n"
            "lbu x6, 1(sp)\n"
            "halt"
        )
        sim = assemble_and_run(src)
        assert sim.registers[5] == 0x41
        assert sim.registers[6] == 0x42
