from __future__ import annotations
import random
from riscv.isa import ABI_NAMES

_GPR = [ABI_NAMES[i] for i in range(1, 32) if i not in (2,)]

_ARITH_TEMPLATES = [
    "addi {rd}, x0, {imm12}",
    "add {rd}, {rs1}, {rs2}",
    "sub {rd}, {rs1}, {rs2}",
    "sll {rd}, {rs1}, {rs2}",
    "srl {rd}, {rs1}, {rs2}",
    "sra {rd}, {rs1}, {rs2}",
    "and {rd}, {rs1}, {rs2}",
    "or  {rd}, {rs1}, {rs2}",
    "xor {rd}, {rs1}, {rs2}",
    "slt {rd}, {rs1}, {rs2}",
    "sltu {rd}, {rs1}, {rs2}",
    "xori {rd}, {rs1}, {imm12}",
    "ori  {rd}, {rs1}, {imm12}",
    "andi {rd}, {rs1}, {imm12}",
    "slli {rd}, {rs1}, {shamt}",
    "srli {rd}, {rs1}, {shamt}",
    "srai {rd}, {rs1}, {shamt}",
]


def _imm12(rng: random.Random) -> int:
    return rng.randint(-2048, 2047)


def _shamt(rng: random.Random) -> int:
    return rng.randint(0, 31)


def _reg(rng: random.Random) -> str:
    return rng.choice(_GPR)


def random_program(n_instructions: int = 20, seed: int | None = None) -> str:
    rng = random.Random(seed)
    lines: list[str] = []

    for _ in range(n_instructions):
        template = rng.choice(_ARITH_TEMPLATES)
        inst = template.format(
            rd=_reg(rng),
            rs1=_reg(rng),
            rs2=_reg(rng),
            imm12=_imm12(rng),
            shamt=_shamt(rng),
        )
        lines.append(inst)

    lines.append("halt")
    return "\n".join(lines)


def corner_case_programs() -> list[str]:
    return [
        "addi x1, x0, -1\naddi x2, x0, 1\nadd x3, x1, x2\nhalt",
        "addi x1, x0, -2048\nhalt",
        "addi x1, x0, 2047\nhalt",
        "addi x1, x0, 1\nslli x2, x1, 31\nhalt",
        "addi x1, x0, -1\nsrli x2, x1, 31\nhalt",
        "addi x1, x0, -1\nsrai x2, x1, 31\nhalt",
        "addi x1, x0, 1\nrvrs x2, x1\nhalt",
        "lui x1, 524288\naddi x1, x1, -1\nhalt",
        "addi x1, x0, 0\nslt x2, x1, x0\nhalt",
        "addi x1, x0, -1\nsltu x2, x0, x1\nhalt",
        "addi x1, x0, 5\nsw x1, 0(sp)\nlw x2, 0(sp)\nhalt",
        "addi x1, x0, 255\nsb x1, 0(sp)\nlb x2, 0(sp)\nhalt",
        "addi x1, x0, 0\naddi x2, x0, 0\nbeq x1, x2, done\naddi x3, x0, 1\ndone: halt",
        "addi x1, x0, -1\naddi x2, x0, 0\nblt x1, x2, done\naddi x3, x0, 1\ndone: halt",
        "addi x1, x0, -1\naddi x2, x0, 0\nbltu x1, x2, done\naddi x3, x0, 1\ndone: halt",
    ]
