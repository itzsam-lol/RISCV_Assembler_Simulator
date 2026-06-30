import pytest
from riscv.assembler import Assembler
from riscv.simulator import Simulator
from riscv.isa import INITIAL_SP, DATA_MEM_BASE


def run(source: str) -> Simulator:
    binary = Assembler().assemble(source)
    program = {i * 4: enc for i, enc in enumerate(binary)}
    sim = Simulator()
    sim.run(program)
    return sim


def reg(sim: Simulator, name: str) -> int:
    from riscv.isa import REGISTERS
    return sim.registers[REGISTERS[name]]


class TestX0Hardwired:
    def test_write_to_x0_ignored(self):
        sim = run("addi x0, x0, 99\nhalt")
        assert sim.registers[0] == 0

    def test_x0_always_zero_after_add(self):
        sim = run("add x0, x0, x0\nhalt")
        assert sim.registers[0] == 0


class TestArithmeticR:
    def test_add(self):
        sim = run("addi x1, x0, 10\naddi x2, x0, 20\nadd x3, x1, x2\nhalt")
        assert sim.registers[3] == 30

    def test_add_overflow_wraps(self):
        sim = run("addi x1, x0, -1\naddi x2, x0, 1\nadd x3, x1, x2\nhalt")
        assert sim.registers[3] == 0

    def test_add_max_plus_one_wraps(self):
        sim = run("lui x1, 524288\naddi x1, x1, -1\naddi x2, x0, 1\nadd x3, x1, x2\nhalt")
        assert sim.registers[3] == 0x80000000

    def test_sub(self):
        sim = run("addi x1, x0, 30\naddi x2, x0, 10\nsub x3, x1, x2\nhalt")
        assert sim.registers[3] == 20

    def test_sub_underflow_wraps(self):
        sim = run("addi x1, x0, 0\naddi x2, x0, 1\nsub x3, x1, x2\nhalt")
        assert sim.registers[3] == 0xFFFFFFFF

    def test_sll(self):
        sim = run("addi x1, x0, 1\naddi x2, x0, 4\nsll x3, x1, x2\nhalt")
        assert sim.registers[3] == 16

    def test_sll_uses_low5_bits(self):
        sim = run("addi x1, x0, 1\naddi x2, x0, 32\nsll x3, x1, x2\nhalt")
        assert sim.registers[3] == 1

    def test_srl(self):
        sim = run("addi x1, x0, 16\naddi x2, x0, 2\nsrl x3, x1, x2\nhalt")
        assert sim.registers[3] == 4

    def test_srl_logical(self):
        sim = run("addi x1, x0, -1\naddi x2, x0, 1\nsrl x3, x1, x2\nhalt")
        assert sim.registers[3] == 0x7FFFFFFF

    def test_sra_positive(self):
        sim = run("addi x1, x0, 16\naddi x2, x0, 2\nsra x3, x1, x2\nhalt")
        assert sim.registers[3] == 4

    def test_sra_arithmetic(self):
        sim = run("addi x1, x0, -8\naddi x2, x0, 1\nsra x3, x1, x2\nhalt")
        assert sim.registers[3] == 0xFFFFFFFC

    def test_slt_true(self):
        sim = run("addi x1, x0, -1\naddi x2, x0, 0\nslt x3, x1, x2\nhalt")
        assert sim.registers[3] == 1

    def test_slt_false(self):
        sim = run("addi x1, x0, 1\naddi x2, x0, 0\nslt x3, x1, x2\nhalt")
        assert sim.registers[3] == 0

    def test_sltu(self):
        sim = run("addi x1, x0, -1\naddi x2, x0, 0\nsltu x3, x1, x2\nhalt")
        assert sim.registers[3] == 0

    def test_xor(self):
        sim = run("addi x1, x0, 0b1010\naddi x2, x0, 0b1100\nxor x3, x1, x2\nhalt")
        assert sim.registers[3] == 0b0110

    def test_or(self):
        sim = run("addi x1, x0, 0b1010\naddi x2, x0, 0b0101\nor x3, x1, x2\nhalt")
        assert sim.registers[3] == 0b1111

    def test_and(self):
        sim = run("addi x1, x0, 0b1111\naddi x2, x0, 0b1010\nand x3, x1, x2\nhalt")
        assert sim.registers[3] == 0b1010


class TestArithmeticI:
    def test_addi(self):
        sim = run("addi x1, x0, 42\nhalt")
        assert sim.registers[1] == 42

    def test_addi_negative(self):
        sim = run("addi x1, x0, -1\nhalt")
        assert sim.registers[1] == 0xFFFFFFFF

    def test_addi_min_imm(self):
        sim = run("addi x1, x0, -2048\nhalt")
        assert sim.registers[1] == 0xFFFFF800

    def test_addi_max_imm(self):
        sim = run("addi x1, x0, 2047\nhalt")
        assert sim.registers[1] == 2047

    def test_slti_true(self):
        sim = run("addi x1, x0, -1\nslti x2, x1, 0\nhalt")
        assert sim.registers[2] == 1

    def test_slti_false(self):
        sim = run("addi x1, x0, 5\nslti x2, x1, 5\nhalt")
        assert sim.registers[2] == 0

    def test_sltiu(self):
        sim = run("addi x1, x0, -1\nsltiu x2, x1, 1\nhalt")
        assert sim.registers[2] == 0

    def test_xori(self):
        sim = run("addi x1, x0, 0b1010\nxori x2, x1, 0b1100\nhalt")
        assert sim.registers[2] == 0b0110

    def test_ori(self):
        sim = run("addi x1, x0, 0b1010\nori x2, x1, 0b0101\nhalt")
        assert sim.registers[2] == 0b1111

    def test_andi(self):
        sim = run("addi x1, x0, 0b1111\nandi x2, x1, 0b1010\nhalt")
        assert sim.registers[2] == 0b1010

    def test_slli(self):
        sim = run("addi x1, x0, 1\nslli x2, x1, 3\nhalt")
        assert sim.registers[2] == 8

    def test_srli(self):
        sim = run("addi x1, x0, -1\nsrli x2, x1, 1\nhalt")
        assert sim.registers[2] == 0x7FFFFFFF

    def test_srai(self):
        sim = run("addi x1, x0, -8\nsrai x2, x1, 2\nhalt")
        assert sim.registers[2] == 0xFFFFFFFE


class TestLoadStore:
    def test_sw_lw_roundtrip(self):
        sim = run("addi x1, x0, 99\nsw x1, 0(sp)\nlw x2, 0(sp)\nhalt")
        assert sim.registers[2] == 99

    def test_sw_negative_value(self):
        sim = run("addi x1, x0, -1\nsw x1, 0(sp)\nlw x2, 0(sp)\nhalt")
        assert sim.registers[2] == 0xFFFFFFFF

    def test_sb_lbu(self):
        sim = run("addi x1, x0, 255\nsb x1, 4(sp)\nlbu x2, 4(sp)\nhalt")
        assert sim.registers[2] == 255

    def test_sb_lb_sign_extends(self):
        sim = run("addi x1, x0, -1\nsb x1, 4(sp)\nlb x2, 4(sp)\nhalt")
        assert sim.registers[2] == 0xFFFFFFFF

    def test_sh_lhu(self):
        sim = run("addi x1, x0, 1000\nsh x1, 4(sp)\nlhu x2, 4(sp)\nhalt")
        assert sim.registers[2] == 1000

    def test_sh_lh_sign_extends(self):
        sim = run("addi x1, x0, -1\nsh x1, 4(sp)\nlh x2, 4(sp)\nhalt")
        assert sim.registers[2] == 0xFFFFFFFF

    def test_lw_uninitialized_zero(self):
        sim = run("addi x1, x0, 100\nlw x2, 100(x1)\nhalt")
        assert sim.registers[2] == 0

    def test_memory_dump_has_written_value(self):
        sim = run("addi x1, x0, 77\nsw x1, 0(sp)\nhalt")
        assert sim.data_memory[INITIAL_SP] == 77


class TestBranches:
    def test_beq_taken(self):
        sim = run("addi x1, x0, 5\naddi x2, x0, 5\nbeq x1, x2, done\naddi x3, x0, 1\ndone: halt")
        assert sim.registers[3] == 0

    def test_beq_not_taken(self):
        sim = run("addi x1, x0, 5\naddi x2, x0, 6\nbeq x1, x2, done\naddi x3, x0, 1\ndone: halt")
        assert sim.registers[3] == 1

    def test_bne_taken(self):
        sim = run("addi x1, x0, 1\naddi x2, x0, 2\nbne x1, x2, done\naddi x3, x0, 99\ndone: halt")
        assert sim.registers[3] == 0

    def test_blt_taken(self):
        sim = run("addi x1, x0, -1\naddi x2, x0, 0\nblt x1, x2, done\naddi x3, x0, 99\ndone: halt")
        assert sim.registers[3] == 0

    def test_blt_unsigned_not_taken(self):
        sim = run("addi x1, x0, -1\naddi x2, x0, 0\nbltu x1, x2, done\naddi x3, x0, 1\ndone: halt")
        assert sim.registers[3] == 1

    def test_bge_taken(self):
        sim = run("addi x1, x0, 5\naddi x2, x0, 5\nbge x1, x2, done\naddi x3, x0, 99\ndone: halt")
        assert sim.registers[3] == 0

    def test_bgeu_taken(self):
        sim = run("addi x1, x0, -1\naddi x2, x0, 0\nbgeu x1, x2, done\naddi x3, x0, 99\ndone: halt")
        assert sim.registers[3] == 0


class TestJumps:
    def test_jal_jumps_and_links(self):
        sim = run("jal x1, target\naddi x5, x0, 99\ntarget: halt")
        assert sim.registers[1] == 4
        assert sim.registers[5] == 0

    def test_jalr_jumps_and_links(self):
        sim = run("addi x1, x0, 12\njalr x2, x1, 0\naddi x3, x0, 99\ntarget: halt")
        assert sim.registers[2] == 8
        assert sim.registers[3] == 0

    def test_jalr_clears_lsb(self):
        sim = run("addi x1, x0, 13\njalr x2, x1, 0\naddi x3, x0, 99\ntarget: halt")
        assert sim.registers[2] == 8

    def test_call_return(self):
        sim = run("addi a0, zero, 7\njal ra, func\nhalt\nfunc: addi a0, a0, 1\njalr zero, ra, 0")
        assert sim.registers[10] == 8


class TestUpper:
    def test_lui(self):
        sim = run("lui x1, 1\nhalt")
        assert sim.registers[1] == 0x00001000

    def test_lui_large(self):
        sim = run("lui x1, 524287\nhalt")
        assert sim.registers[1] == 0x7FFFF000

    def test_auipc(self):
        sim = run("auipc x1, 1\nhalt")
        assert sim.registers[1] == 0x00001000

    def test_auipc_pc_offset(self):
        sim = run("addi x0, x0, 0\nauipc x1, 0\nhalt")
        assert sim.registers[1] == 4


class TestCustom:
    def test_rvrs_bit_reversal(self):
        sim = run("addi x1, x0, 1\nrvrs x2, x1\nhalt")
        assert sim.registers[2] == 0x80000000

    def test_rvrs_palindrome(self):
        sim = run("lui x1, 0xF0F0F\nrvrs x2, x1\nhalt")
        assert sim.registers[2] == 0x000F0F0F

    def test_mul(self):
        sim = run("addi x1, x0, 6\naddi x2, x0, 7\nmul x3, x1, x2\nhalt")
        assert sim.registers[3] == 42

    def test_mul_overflow_wraps(self):
        sim = run("lui x1, 524288\naddi x1, x1, -1\naddi x2, x0, 2\nmul x3, x1, x2\nhalt")
        assert sim.registers[3] == (0x7FFFFFFF * 2) & 0xFFFFFFFF

    def test_rst_clears_registers(self):
        sim = run("addi x1, x0, 99\naddi x2, x0, 77\nrst\nhalt")
        assert sim.registers[1] == 0
        assert sim.registers[2] == INITIAL_SP

    def test_halt_stops_execution(self):
        sim = run("halt\naddi x1, x0, 99")
        assert sim.registers[1] == 0
        assert sim.halted


class TestSignExtension:
    def test_imm_12bit_boundary_positive(self):
        sim = run("addi x1, x0, 2047\nhalt")
        assert sim.registers[1] == 2047

    def test_imm_12bit_boundary_negative(self):
        sim = run("addi x1, x0, -2048\nhalt")
        assert sim.registers[1] == 0xFFFFF800

    def test_lw_negative_offset(self):
        sim = run(
            "addi x1, x0, 100\n"
            "sw x1, 0(sp)\n"
            "addi x2, sp, 4\n"
            "lw x3, -4(x2)\n"
            "halt"
        )
        assert sim.registers[3] == 100


class TestTrace:
    def test_trace_length(self):
        sim = run("addi x1, x0, 1\naddi x2, x0, 2\nhalt")
        assert len(sim.trace) == 3

    def test_trace_register_delta(self):
        sim = run("addi x5, x0, 42\nhalt")
        delta = sim.trace[0].register_delta
        assert "ra" not in delta
        assert delta["t0"] == (0, 42)

    def test_json_dict_structure(self):
        sim = run("addi x1, x0, 1\nhalt")
        d = sim.to_json_dict()
        assert "steps" in d
        assert "final_registers" in d
        assert "final_memory" in d
        assert len(d["final_registers"]) == 32

    def test_memory_write_in_trace(self):
        sim = run("addi x1, x0, 5\nsw x1, 0(sp)\nhalt")
        writes = [t.memory_writes for t in sim.trace if t.memory_writes]
        assert len(writes) == 1
        assert writes[0][0]["value"] == 5
