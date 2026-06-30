import pytest
from riscv.assembler import Assembler, AssemblerError


def asm(source: str) -> list[str]:
    return Assembler().assemble(source)


def single(source: str) -> str:
    return asm(source)[0]


class TestRType:
    def test_add(self):
        assert single("add x1, x2, x3") == "0000000" + "00011" + "00010" + "000" + "00001" + "0110011"

    def test_sub(self):
        assert single("sub x1, x2, x3") == "0100000" + "00011" + "00010" + "000" + "00001" + "0110011"

    def test_sll(self):
        assert single("sll x4, x5, x6") == "0000000" + "00110" + "00101" + "001" + "00100" + "0110011"

    def test_slt(self):
        assert single("slt x1, x2, x3") == "0000000" + "00011" + "00010" + "010" + "00001" + "0110011"

    def test_sltu(self):
        assert single("sltu x1, x2, x3") == "0000000" + "00011" + "00010" + "011" + "00001" + "0110011"

    def test_xor(self):
        assert single("xor x1, x2, x3") == "0000000" + "00011" + "00010" + "100" + "00001" + "0110011"

    def test_srl(self):
        assert single("srl x1, x2, x3") == "0000000" + "00011" + "00010" + "101" + "00001" + "0110011"

    def test_sra(self):
        assert single("sra x1, x2, x3") == "0100000" + "00011" + "00010" + "101" + "00001" + "0110011"

    def test_or(self):
        assert single("or x1, x2, x3") == "0000000" + "00011" + "00010" + "110" + "00001" + "0110011"

    def test_and(self):
        assert single("and x1, x2, x3") == "0000000" + "00011" + "00010" + "111" + "00001" + "0110011"

    def test_abi_names(self):
        assert single("add a0, a1, a2") == single("add x10, x11, x12")


class TestIType:
    def test_addi_positive(self):
        enc = single("addi x1, x2, 5")
        assert enc[0:12] == "000000000101"
        assert enc[25:32] == "0010011"
        assert enc[17:20] == "000"

    def test_addi_negative(self):
        enc = single("addi x1, x2, -1")
        assert enc[0:12] == "111111111111"

    def test_slti(self):
        enc = single("slti x1, x2, 1")
        assert enc[17:20] == "010"
        assert enc[25:32] == "0010011"

    def test_sltiu(self):
        enc = single("sltiu x1, x2, 1")
        assert enc[17:20] == "011"

    def test_xori(self):
        enc = single("xori x1, x2, 15")
        assert enc[17:20] == "100"

    def test_ori(self):
        enc = single("ori x1, x2, 15")
        assert enc[17:20] == "110"

    def test_andi(self):
        enc = single("andi x1, x2, 15")
        assert enc[17:20] == "111"

    def test_slli(self):
        enc = single("slli x1, x2, 3")
        assert enc[17:20] == "001"
        assert enc[25:32] == "0010011"
        assert enc[0:7] == "0000000"
        assert enc[7:12] == "00011"

    def test_srli(self):
        enc = single("srli x1, x2, 3")
        assert enc[17:20] == "101"
        assert enc[0:7] == "0000000"

    def test_srai(self):
        enc = single("srai x1, x2, 3")
        assert enc[17:20] == "101"
        assert enc[0:7] == "0100000"

    def test_lw(self):
        enc = single("lw x1, 4(x2)")
        assert enc[17:20] == "010"
        assert enc[25:32] == "0000011"
        assert enc[0:12] == "000000000100"

    def test_lb(self):
        enc = single("lb x1, 0(x2)")
        assert enc[17:20] == "000"
        assert enc[25:32] == "0000011"

    def test_lh(self):
        enc = single("lh x1, 0(x2)")
        assert enc[17:20] == "001"

    def test_lbu(self):
        enc = single("lbu x1, 0(x2)")
        assert enc[17:20] == "100"

    def test_lhu(self):
        enc = single("lhu x1, 0(x2)")
        assert enc[17:20] == "101"

    def test_jalr(self):
        enc = single("jalr x1, x2, 0")
        assert enc[25:32] == "1100111"
        assert enc[17:20] == "000"


class TestSType:
    def test_sw(self):
        enc = single("sw x3, 8(x2)")
        assert enc[25:32] == "0100011"
        assert enc[17:20] == "010"
        imm = enc[0:7] + enc[20:25]
        assert int(imm, 2) == 8

    def test_sb(self):
        enc = single("sb x3, 0(x2)")
        assert enc[17:20] == "000"
        assert enc[25:32] == "0100011"

    def test_sh(self):
        enc = single("sh x3, 0(x2)")
        assert enc[17:20] == "001"

    def test_sw_negative_offset(self):
        enc = single("sw x3, -4(x2)")
        imm = enc[0:7] + enc[20:25]
        val = int(imm, 2)
        if val & (1 << 11):
            val -= 1 << 12
        assert val == -4


class TestBType:
    def test_beq_forward(self):
        lines = asm("beq x1, x2, target\nnop: addi x0, x0, 0\ntarget: halt")
        enc = lines[0]
        assert enc[25:32] == "1100011"
        assert enc[17:20] == "000"
        imm = enc[0] + enc[24] + enc[1:7] + enc[20:24] + "0"
        offset = int(imm, 2)
        assert offset == 8

    def test_bne(self):
        enc = single("bne x1, x2, 0")
        assert enc[17:20] == "001"

    def test_blt(self):
        enc = single("blt x1, x2, 0")
        assert enc[17:20] == "100"

    def test_bge(self):
        enc = single("bge x1, x2, 0")
        assert enc[17:20] == "101"

    def test_bltu(self):
        enc = single("bltu x1, x2, 0")
        assert enc[17:20] == "110"

    def test_bgeu(self):
        enc = single("bgeu x1, x2, 0")
        assert enc[17:20] == "111"

    def test_branch_backward(self):
        lines = asm("start: addi x0, x0, 0\nbeq x0, x0, start")
        enc = lines[1]
        imm = enc[0] + enc[24] + enc[1:7] + enc[20:24] + "0"
        raw = int(imm, 2)
        if raw & (1 << 12):
            raw -= 1 << 13
        assert raw == -4


class TestUType:
    def test_lui(self):
        enc = single("lui x1, 1")
        assert enc[25:32] == "0110111"
        assert enc[0:20] == "00000000000000000001"

    def test_auipc(self):
        enc = single("auipc x1, 1")
        assert enc[25:32] == "0010111"


class TestJType:
    def test_jal_forward(self):
        lines = asm("jal x1, target\nnop: addi x0, x0, 0\ntarget: halt")
        enc = lines[0]
        assert enc[25:32] == "1101111"
        imm = enc[0] + enc[12:20] + enc[11] + enc[1:11] + "0"
        offset = int(imm, 2)
        assert offset == 8

    def test_jal_rd(self):
        enc = single("jal ra, 0")
        assert enc[20:25] == "00001"


class TestCustom:
    def test_rvrs(self):
        enc = single("rvrs x1, x2")
        assert enc[25:32] == "0000000"
        assert enc[17:20] == "001"
        assert enc[7:12] == "00000"

    def test_mul(self):
        enc = single("mul x1, x2, x3")
        assert enc[25:32] == "0000000"
        assert enc[17:20] == "011"

    def test_halt(self):
        enc = single("halt")
        assert enc == "00000000000000000000000001100011"

    def test_rst(self):
        enc = single("rst")
        assert enc == "0" * 32


class TestErrors:
    def test_unknown_instruction(self):
        with pytest.raises(AssemblerError):
            asm("foobar x1, x2, x3")

    def test_unknown_register(self):
        with pytest.raises(AssemblerError):
            asm("add x99, x1, x2")

    def test_wrong_arg_count(self):
        with pytest.raises(AssemblerError):
            asm("add x1, x2")


class TestLabelResolution:
    def test_forward_label(self):
        result = asm("jal zero, end\naddi x1, x0, 1\nend: halt")
        assert len(result) == 3

    def test_label_on_own_line(self):
        result = asm("start:\n  addi x1, x0, 1\n  halt")
        assert len(result) == 2

    def test_inline_label(self):
        result = asm("start: addi x1, x0, 1\nhalt")
        assert len(result) == 2
