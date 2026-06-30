from __future__ import annotations
from .isa import (
    ABI_NAMES,
    DATA_MEM_BASE,
    DATA_MEM_WORDS,
    HALT_ENCODING,
    RST_ENCODING,
    INITIAL_SP,
)


def _sign_extend(val: int, bits: int) -> int:
    if val & (1 << (bits - 1)):
        return val - (1 << bits)
    return val


def _u32(val: int) -> int:
    return val & 0xFFFFFFFF


def _s32(val: int) -> int:
    return _sign_extend(_u32(val), 32)


class SimulatorError(Exception):
    pass


class StepTrace:
    __slots__ = ("step", "pc", "instruction", "register_delta", "memory_writes")

    def __init__(
        self,
        step: int,
        pc: int,
        instruction: str,
        register_delta: dict[str, tuple[int, int]],
        memory_writes: list[dict[str, int]],
    ) -> None:
        self.step = step
        self.pc = pc
        self.instruction = instruction
        self.register_delta = register_delta
        self.memory_writes = memory_writes

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "pc": self.pc,
            "instruction": self.instruction,
            "register_delta": {k: list(v) for k, v in self.register_delta.items()},
            "memory_writes": self.memory_writes,
        }


class Simulator:
    def __init__(self) -> None:
        self.registers: list[int] = [0] * 32
        self.registers[2] = INITIAL_SP
        self.pc: int = 0
        self.data_memory: dict[int, int] = {}
        for i in range(DATA_MEM_WORDS):
            self.data_memory[DATA_MEM_BASE + i * 4] = 0
        self.halted: bool = False
        self._step_count: int = 0
        self.trace: list[StepTrace] = []
        self._text_trace: list[str] = []

    def _to_bin32(self, val: int) -> str:
        return "0b" + bin(_u32(val))[2:].zfill(32)

    def _load_byte(self, addr: int) -> int:
        word_addr = addr & ~3
        shift = (addr & 3) * 8
        word = self.data_memory.get(word_addr, 0)
        return (word >> shift) & 0xFF

    def _load_half(self, addr: int) -> int:
        word_addr = addr & ~3
        shift = (addr & 3) * 8
        word = self.data_memory.get(word_addr, 0)
        return (word >> shift) & 0xFFFF

    def _store_byte(self, addr: int, val: int) -> None:
        word_addr = addr & ~3
        shift = (addr & 3) * 8
        old = self.data_memory.get(word_addr, 0)
        mask = ~(0xFF << shift) & 0xFFFFFFFF
        self.data_memory[word_addr] = (old & mask) | ((_u32(val) & 0xFF) << shift)

    def _store_half(self, addr: int, val: int) -> None:
        word_addr = addr & ~3
        shift = (addr & 3) * 8
        old = self.data_memory.get(word_addr, 0)
        mask = ~(0xFFFF << shift) & 0xFFFFFFFF
        self.data_memory[word_addr] = (old & mask) | ((_u32(val) & 0xFFFF) << shift)

    def step(self, inst_bin: str) -> StepTrace:
        pre_regs = list(self.registers)
        pre_mem = dict(self.data_memory)

        self._execute(inst_bin)

        reg_delta: dict[str, tuple[int, int]] = {}
        for i in range(32):
            if self.registers[i] != pre_regs[i]:
                reg_delta[ABI_NAMES[i]] = (pre_regs[i], self.registers[i])

        mem_writes: list[dict[str, int]] = []
        for addr, val in self.data_memory.items():
            if val != pre_mem.get(addr, 0):
                mem_writes.append({"address": addr, "value": val})

        t = StepTrace(self._step_count, self.pc if self.halted else self.pc,
                      inst_bin, reg_delta, mem_writes)
        self._step_count += 1
        self.trace.append(t)

        regs_str = " ".join(self._to_bin32(r) for r in self.registers) + " "
        self._text_trace.append(self._to_bin32(self.pc) + " " + regs_str)

        return t

    def _execute(self, inst_bin: str) -> None:
        self.registers[0] = 0

        if inst_bin == HALT_ENCODING:
            self.halted = True
            return

        if inst_bin == RST_ENCODING:
            self.registers = [0] * 32
            self.registers[2] = INITIAL_SP
            self.pc += 4
            return

        opcode = inst_bin[25:32]
        rd     = int(inst_bin[20:25], 2)
        funct3 = inst_bin[17:20]
        rs1    = int(inst_bin[12:17], 2)
        rs2    = int(inst_bin[7:12], 2)
        funct7 = inst_bin[0:7]

        next_pc = self.pc + 4

        if opcode == "0110011":
            a = _s32(self.registers[rs1])
            b = _s32(self.registers[rs2])
            au = _u32(self.registers[rs1])
            bu = _u32(self.registers[rs2])
            if funct3 == "000":
                self.registers[rd] = _u32(au + bu) if funct7 == "0000000" else _u32(au - bu)
            elif funct3 == "001":
                self.registers[rd] = _u32(au << (bu & 0x1F))
            elif funct3 == "010":
                self.registers[rd] = 1 if a < b else 0
            elif funct3 == "011":
                self.registers[rd] = 1 if au < bu else 0
            elif funct3 == "100":
                self.registers[rd] = _u32(au ^ bu)
            elif funct3 == "101":
                if funct7 == "0000000":
                    self.registers[rd] = au >> (bu & 0x1F)
                else:
                    self.registers[rd] = _u32(a >> (bu & 0x1F))
            elif funct3 == "110":
                self.registers[rd] = _u32(au | bu)
            elif funct3 == "111":
                self.registers[rd] = _u32(au & bu)

        elif opcode == "0000000":
            rs1v = self.registers[rs1]
            rs2v = self.registers[rs2]
            if funct3 == "001":
                val_bin = bin(_u32(rs1v))[2:].zfill(32)
                self.registers[rd] = int(val_bin[::-1], 2)
            elif funct3 == "011":
                self.registers[rd] = _u32(rs1v * rs2v)

        elif opcode in ("0000011",):
            imm  = _sign_extend(int(inst_bin[0:12], 2), 12)
            addr = _u32(self.registers[rs1] + imm)
            if funct3 == "000":
                self.registers[rd] = _u32(_sign_extend(self._load_byte(addr), 8))
            elif funct3 == "001":
                self.registers[rd] = _u32(_sign_extend(self._load_half(addr), 16))
            elif funct3 == "010":
                self.registers[rd] = self.data_memory.get(addr, 0)
            elif funct3 == "100":
                self.registers[rd] = self._load_byte(addr)
            elif funct3 == "101":
                self.registers[rd] = self._load_half(addr)

        elif opcode == "0010011":
            imm = _sign_extend(int(inst_bin[0:12], 2), 12)
            au  = _u32(self.registers[rs1])
            a   = _s32(self.registers[rs1])
            shamt = int(inst_bin[7:12], 2)
            f7    = inst_bin[0:7]
            if funct3 == "000":
                self.registers[rd] = _u32(au + imm)
            elif funct3 == "010":
                self.registers[rd] = 1 if a < imm else 0
            elif funct3 == "011":
                self.registers[rd] = 1 if au < _u32(imm) else 0
            elif funct3 == "100":
                self.registers[rd] = _u32(au ^ _u32(imm))
            elif funct3 == "110":
                self.registers[rd] = _u32(au | _u32(imm))
            elif funct3 == "111":
                self.registers[rd] = _u32(au & _u32(imm))
            elif funct3 == "001":
                self.registers[rd] = _u32(au << shamt)
            elif funct3 == "101":
                if f7 == "0000000":
                    self.registers[rd] = au >> shamt
                else:
                    self.registers[rd] = _u32(a >> shamt)

        elif opcode == "1100111":
            if funct3 == "000":
                imm = _sign_extend(int(inst_bin[0:12], 2), 12)
                self.registers[rd] = next_pc
                next_pc = _u32(self.registers[rs1] + imm) & ~1

        elif opcode == "0100011":
            imm  = _sign_extend(int(inst_bin[0:7] + inst_bin[20:25], 2), 12)
            addr = _u32(self.registers[rs1] + imm)
            val  = self.registers[rs2]
            if funct3 == "000":
                self._store_byte(addr, val)
            elif funct3 == "001":
                self._store_half(addr, val)
            elif funct3 == "010":
                self.data_memory[addr] = _u32(val)

        elif opcode == "1100011":
            imm_str = inst_bin[0] + inst_bin[24] + inst_bin[1:7] + inst_bin[20:24] + "0"
            imm = _sign_extend(int(imm_str, 2), 13)
            a   = _s32(self.registers[rs1])
            b   = _s32(self.registers[rs2])
            au  = _u32(self.registers[rs1])
            bu  = _u32(self.registers[rs2])
            taken = False
            if   funct3 == "000": taken = au == bu
            elif funct3 == "001": taken = au != bu
            elif funct3 == "100": taken = a < b
            elif funct3 == "101": taken = a >= b
            elif funct3 == "110": taken = au < bu
            elif funct3 == "111": taken = au >= bu
            if taken:
                next_pc = self.pc + imm

        elif opcode == "0110111":
            imm = _sign_extend(int(inst_bin[0:20] + "0" * 12, 2), 32)
            self.registers[rd] = _u32(imm)

        elif opcode == "0010111":
            imm = _sign_extend(int(inst_bin[0:20] + "0" * 12, 2), 32)
            self.registers[rd] = _u32(self.pc + imm)

        elif opcode == "1101111":
            imm_str = inst_bin[0] + inst_bin[12:20] + inst_bin[11] + inst_bin[1:11] + "0"
            imm = _sign_extend(int(imm_str, 2), 21)
            self.registers[rd] = next_pc
            next_pc = self.pc + imm

        self.registers[0] = 0
        self.pc = next_pc

    def run(self, program: dict[int, str]) -> None:
        while not self.halted and self.pc in program:
            self.step(program[self.pc])

    def text_trace(self) -> str:
        return "\n".join(self._text_trace)

    def memory_dump_text(self) -> str:
        lines = []
        for i in range(DATA_MEM_WORDS):
            addr = DATA_MEM_BASE + i * 4
            val  = self.data_memory.get(addr, 0)
            lines.append(f"0x000{addr:x}:0b{bin(val)[2:].zfill(32)}")
        return "\n".join(lines)

    def to_json_dict(self) -> dict:
        return {
            "steps": [t.to_dict() for t in self.trace],
            "final_registers": list(self.registers),
            "final_memory": {
                hex(DATA_MEM_BASE + i * 4): self.data_memory.get(DATA_MEM_BASE + i * 4, 0)
                for i in range(DATA_MEM_WORDS)
            },
        }
