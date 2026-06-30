# RISC-V Assembler · Simulator · Formal Verification Reference

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![ISA](https://img.shields.io/badge/ISA-RV32I-orange)
![Tests](https://img.shields.io/badge/tests-133%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A complete RV32I toolchain in Python: two-pass assembler, cycle-accurate simulator, and a formal verification harness that uses the simulator as a golden reference model to prove RTL correctness. The architecture mirrors how industrial formal verification works — the Python simulator is the *behavioral specification*, an RTL core is the *structural implementation*, and the formal layer provides *exhaustive proof of equivalence* for every reachable state.

---

## Architecture

```
  Assembly source (.asm)
        │
        ▼
  ┌─────────────┐
  │  Assembler  │  two-pass, full RV32I + custom pseudo-instructions
  └──────┬──────┘
         │  32-bit binary strings
         ▼
  ┌─────────────────────┐        ┌─────────────────────────┐
  │  Python Simulator   │◄──────►│  Differential Harness   │
  │  (golden reference) │        │  (diff vs RTL traces)   │
  └─────────────────────┘        └────────────┬────────────┘
         │  JSON execution trace              │
         │                                    ▼
         │                       ┌─────────────────────────┐
         │                       │  RTL Core (PicoRV32)    │
         │                       │  + RVFI trace port      │
         │                       └────────────┬────────────┘
         │                                    │
         └────────────────────────────────────┘
                  ▼
  ┌─────────────────────────────┐
  │  SymbiYosys Formal Flow     │
  │  SVA properties + riscv-    │
  │  formal → exhaustive proof  │
  └─────────────────────────────┘
```

---

## Project Structure

```
riscv/
  isa.py          register table, instruction encoding table, constants
  assembler.py    Assembler class — two-pass, importable
  simulator.py    Simulator class — step-by-step execution with trace
  __init__.py

cli/
  assemble.py     command-line assembler entry point
  simulate.py     command-line simulator entry point (--json flag)

tests/
  test_assembler.py     per-opcode encoding tests
  test_simulator.py     per-opcode execution + edge cases
  test_integration.py   assemble→simulate end-to-end programs
  programs/             .asm fixtures (fibonacci, mem_rw, call_ret)

formal/           (Phase 2 — in progress)
  picorv32/       RTL core submodule
  properties/     SVA properties for riscv-formal
  harness/        differential testing bridge

Simple-Assembler/Assembler.py   original script (kept for reference)
SimpleSimulator/Simulator.py    original script (kept for reference)
```

---

## Quickstart

```bash
git clone https://github.com/itzsam-lol/RISCV_Assembler_Simulator
cd RISCV_Assembler_Simulator
pip install -e ".[dev]"

python -m cli.assemble tests/programs/fibonacci.asm fibonacci.bin
python -m cli.simulate fibonacci.bin

python -m cli.simulate fibonacci.bin --json | python -m json.tool | head -40
```

---

## Supported Instructions

Full RV32I base integer ISA:

| Type | Instructions |
|------|-------------|
| R    | `add sub sll slt sltu xor srl sra or and` |
| I    | `addi slti sltiu xori ori andi slli srli srai` |
| I-Load | `lb lh lw lbu lhu` |
| S    | `sb sh sw` |
| B    | `beq bne blt bge bltu bgeu` |
| U    | `lui auipc` |
| J    | `jal jalr` |
| Custom | `rvrs mul halt rst` |

---

## Execution Trace

The simulator produces two trace formats. The default text format matches the original output exactly:

```
0b00000000000000000000000000000100 0b00000000000000000000000000000000 ... 
```

With `--json`, each step records the full architectural delta:

```json
{
  "steps": [
    {
      "step": 0,
      "pc": 0,
      "instruction": "00000000000100000000010010010011",
      "register_delta": { "t0": [0, 1] },
      "memory_writes": []
    }
  ],
  "final_registers": [0, 0, 256, ...],
  "final_memory": { "0x00010000": 0, ... }
}
```

This JSON trace is the machine-readable interface between the Python golden model and the differential harness in Phase 2.

---

## Test Suite

```bash
pytest tests/ -v
```

133 tests covering:
- Every opcode encoding (assembler)
- Every opcode execution (simulator): arithmetic, loads/stores, branches, jumps
- Edge cases: 32-bit overflow wrapping, sign extension boundaries (−2048, 2047), x0 hardwiring, JALR LSB clearing, SLL/SRL with shamt=0 and shamt=31
- End-to-end programs: Fibonacci, stack push/pop, call/return, countdown loop, power-of-two

---

## Formal Verification (Phase 2)

> **Concept**: simulation tests *sampled* states. Formal verification proves properties hold for *all reachable states* — exhaustively, not probabilistically.

The formal layer uses:
- **PicoRV32** — a small, widely-used RV32I RTL core with built-in RVFI (RISC-V Formal Interface) trace output
- **SymbiYosys** — open-source formal verification front-end (Yosys + Boolector/Z3)
- **riscv-formal** — a set of SVA (SystemVerilog Assertions) that check every RV32I instruction's semantics against the RVFI port
- **Differential harness** — runs programs through the Python simulator and PicoRV32 (via Verilator) and diffs architectural state word-by-word

### Key concepts

**RVFI (RISC-V Formal Interface)**: a standardized set of signals that an RTL core exposes per instruction — `rvfi_insn` (the instruction word), `rvfi_rs1_rdata`, `rvfi_rd_wdata`, `rvfi_mem_addr`, etc. Any RVFI-compliant core can be plugged into the riscv-formal framework.

**BMC (Bounded Model Checking)**: the solver unrolls the circuit for *k* clock cycles and tries to find an input sequence that violates a property. If none is found up to depth *k*, the property holds for all executions of length ≤ k. Covers most instruction-level bugs.

**Induction**: proves the property holds for *all* depths, not just bounded ones, by assuming it holds at step *n* and proving it at step *n+1*. Requires an inductive invariant — harder to set up but gives unbounded guarantees.

**SVA property example** (checking ADD semantics):
```systemverilog
property add_correct;
  @(posedge clk)
  (rvfi_valid && rvfi_insn[6:0] == 7'b0110011 && rvfi_insn[14:12] == 3'b000
   && rvfi_insn[31:25] == 7'b0000000)
  |-> (rvfi_rd_wdata == (rvfi_rs1_rdata + rvfi_rs2_rdata));
endproperty
assert property (add_correct);
```

### What formal proves that differential testing cannot

| Claim | Differential testing | Formal (BMC/induction) |
|-------|---------------------|----------------------|
| ADD correct for all 2^64 input pairs | No — only sampled | Yes — proven |
| Branch target calculation for all offsets | No | Yes |
| Sign extension correct at all boundaries | No | Yes |
| No interaction bug between two instructions | Unlikely to catch | Yes (if within BMC depth) |

### Setup (local — requires Linux/WSL)

```bash
sudo apt install yosys symbiyosys boolector
pip install meson ninja
git submodule update --init formal/picorv32 formal/riscv-formal
cd formal && make check-rv32i
```

---

## Why this matters for hardware verification

This project demonstrates the spec-vs-implementation methodology used by silicon teams:

1. **Golden reference** — a behaviorally correct, human-readable model (this Python simulator) defines *what* the hardware must do
2. **RTL implementation** — a structural description (Verilog) defines *how* to do it in gates
3. **Formal equivalence checking** — exhaustively proves the RTL matches the spec for every input and every reachable state

The Python simulator is intentionally kept simple and readable — it is the *source of truth*, not a performance model. The RTL is allowed to be pipelined, optimized, and micro-architecture-specific, as long as the RVFI output matches what the spec says it should be.

---

## Authors

Satyam
