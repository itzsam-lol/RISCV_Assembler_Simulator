from __future__ import annotations
from .isa import REGISTERS, INSTRUCTIONS


def _to_bin(val: int, bits: int) -> str:
    if val < 0:
        val = (1 << bits) + val
    return bin(val & ((1 << bits) - 1))[2:].zfill(bits)


class AssemblerError(Exception):
    pass


class Assembler:
    def __init__(self) -> None:
        self.labels: dict[str, int] = {}
        self._address: int = 0

    def _parse_register(self, reg: str) -> str:
        reg = reg.strip()
        if reg not in REGISTERS:
            raise AssemblerError(f"unknown register '{reg}'")
        return _to_bin(REGISTERS[reg], 5)

    def _parse_imm_reg(self, token: str) -> tuple[int, str]:
        if "(" in token and token.endswith(")"):
            imm_str, reg_str = token[:-1].split("(", 1)
            return int(imm_str.strip(), 0), reg_str.strip()
        raise AssemblerError(f"expected imm(reg), got '{token}'")

    def _resolve_target(self, target: str, current_addr: int) -> int:
        if target in self.labels:
            return self.labels[target] - current_addr
        return int(target, 0)

    def pass_one(self, lines: list[str]) -> list[tuple[int, int, str]]:
        self._address = 0
        cleaned: list[tuple[int, int, str]] = []
        for line_num, raw in enumerate(lines, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line[: line.index("#")].strip()
            if ":" in line:
                label, rest = line.split(":", 1)
                self.labels[label.strip()] = self._address
                line = rest.strip()
                if not line:
                    continue
            cleaned.append((line_num, self._address, line))
            self._address += 4
        return cleaned

    def pass_two(self, cleaned: list[tuple[int, int, str]]) -> list[str]:
        output: list[str] = []
        for line_num, addr, line in cleaned:
            try:
                parts = line.replace(",", " ").split()
                name = parts[0].lower()
                if name not in INSTRUCTIONS:
                    raise AssemblerError(f"unknown instruction '{name}'")
                itype, opcode, funct3, funct7 = INSTRUCTIONS[name]
                args = parts[1:]
                encoded = self._encode(name, itype, opcode, funct3, funct7, args, addr)
                output.append(encoded)
            except AssemblerError:
                raise
            except Exception as exc:
                raise AssemblerError(f"line {line_num}: {exc}") from exc
        return output

    def _encode(
        self,
        name: str,
        itype: str,
        opcode: str,
        funct3: str | None,
        funct7: str | None,
        args: list[str],
        addr: int,
    ) -> str:
        if itype == "R":
            if name == "rvrs":
                if len(args) != 2:
                    raise AssemblerError("rvrs expects rd, rs1")
                rd  = self._parse_register(args[0])
                rs1 = self._parse_register(args[1])
                rs2 = "00000"
            else:
                if len(args) != 3:
                    raise AssemblerError(f"{name} expects rd, rs1, rs2")
                rd  = self._parse_register(args[0])
                rs1 = self._parse_register(args[1])
                rs2 = self._parse_register(args[2])
            return funct7 + rs2 + rs1 + funct3 + rd + opcode

        if itype == "I":
            if name in ("lb", "lh", "lw", "lbu", "lhu"):
                if len(args) != 2:
                    raise AssemblerError(f"{name} expects rd, imm(rs1)")
                rd = self._parse_register(args[0])
                imm_val, rs1_str = self._parse_imm_reg(args[1])
                rs1 = self._parse_register(rs1_str)
                imm = _to_bin(imm_val, 12)
            elif name == "jalr":
                if len(args) == 3:
                    rd  = self._parse_register(args[0])
                    rs1 = self._parse_register(args[1])
                    imm = _to_bin(int(args[2], 0), 12)
                elif len(args) == 2:
                    imm_val, rs1_str = self._parse_imm_reg(args[1])
                    rd  = self._parse_register(args[0])
                    rs1 = self._parse_register(rs1_str)
                    imm = _to_bin(imm_val, 12)
                else:
                    raise AssemblerError("jalr expects rd, rs1, imm or rd, imm(rs1)")
            else:
                if len(args) != 3:
                    raise AssemblerError(f"{name} expects rd, rs1, imm")
                rd  = self._parse_register(args[0])
                rs1 = self._parse_register(args[1])
                imm = _to_bin(int(args[2], 0), 12)
            return imm + rs1 + funct3 + rd + opcode

        if itype == "IS":
            if len(args) != 3:
                raise AssemblerError(f"{name} expects rd, rs1, shamt")
            rd     = self._parse_register(args[0])
            rs1    = self._parse_register(args[1])
            shamt  = _to_bin(int(args[2], 0), 5)
            return funct7 + shamt + rs1 + funct3 + rd + opcode

        if itype == "S":
            if len(args) != 2:
                raise AssemblerError(f"{name} expects rs2, imm(rs1)")
            rs2 = self._parse_register(args[0])
            imm_val, rs1_str = self._parse_imm_reg(args[1])
            rs1 = self._parse_register(rs1_str)
            imm = _to_bin(imm_val, 12)
            return imm[:7] + rs2 + rs1 + funct3 + imm[7:] + opcode

        if itype == "B":
            if len(args) != 3:
                raise AssemblerError(f"{name} expects rs1, rs2, label/offset")
            rs1    = self._parse_register(args[0])
            rs2    = self._parse_register(args[1])
            offset = self._resolve_target(args[2], addr)
            imm    = _to_bin(offset, 13)
            return imm[0] + imm[2:8] + rs2 + rs1 + funct3 + imm[8:12] + imm[1] + opcode

        if itype == "U":
            if len(args) != 2:
                raise AssemblerError(f"{name} expects rd, imm")
            rd  = self._parse_register(args[0])
            imm = _to_bin(int(args[1], 0) & 0xFFFFF, 20)
            return imm + rd + opcode

        if itype == "J":
            if len(args) != 2:
                raise AssemblerError(f"{name} expects rd, label/offset")
            rd     = self._parse_register(args[0])
            offset = self._resolve_target(args[1], addr)
            imm    = _to_bin(offset, 21)
            return imm[0] + imm[10:20] + imm[9] + imm[1:9] + rd + opcode

        if itype == "Z":
            if name == "rst":
                return "0" * 32
            if name == "halt":
                return "00000000000000000000000001100011"

        raise AssemblerError(f"unhandled instruction type '{itype}'")

    def assemble(self, source: str) -> list[str]:
        lines = source.splitlines()
        cleaned = self.pass_one(lines)
        return self.pass_two(cleaned)
