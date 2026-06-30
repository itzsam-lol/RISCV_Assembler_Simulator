# Verification Plan — RV32I Golden Reference vs RTL

## Scope

This document describes the properties proven, the proof methodology, and the abstraction choices made to achieve convergence for the RV32I base integer ISA as implemented in the PicoRV32 RTL core.

---

## 1. Proof Methodology

### 1.1 Bounded Model Checking (BMC)

The primary proof engine is BMC via SymbiYosys + Boolector. BMC unrolls the RTL circuit for `k` time steps and passes the resulting SAT/SMT formula to a solver. If the solver finds no counterexample in `k` steps, the property holds for all executions of length ≤ k.

For instruction-level properties (one instruction per `rvfi_valid` cycle), depth k=20 is sufficient to cover:
- All arithmetic/logical instructions: depth 2 (one pipeline bubble + commit)
- All branch instructions: depth 3–5 (pipeline fill + decode + commit)
- All load/store instructions: depth 4–6 (including memory latency)

### 1.2 k-Induction

For properties that need unbounded guarantees (e.g., x0 hardwiring, PC alignment), the tool chain is configured for k-induction after BMC confirms no shallow counterexample. k-induction requires an inductive invariant: a predicate P such that P(s) ∧ T(s,s') → P(s') for all transitions T. For register-file properties, the invariant is `registers[0] == 0` at every cycle with `rvfi_valid`. This is provably inductive because no instruction writes to rd=0 with a non-zero value (the RVFI spec mandates `rvfi_rd_wdata == 0` when `rvfi_rd_addr == 0`).

### 1.3 Differential Simulation

As a complementary technique, the differential harness runs programs through:
1. The Python simulator (golden reference — this codebase)
2. PicoRV32 compiled with Verilator and instrumented with RVFI

The harness diffs architectural state (all 32 registers + data memory) after each `halt`. This is not exhaustive but catches bugs that BMC might miss at shallow depth, and catches Python simulator bugs by cross-checking against a second implementation.

---

## 2. Properties Proven

### 2.1 Proven by formal (BMC depth 20)

| Property | Instruction | Encoding check | Value check |
|----------|------------|---------------|------------|
| ADD semantics | `add` | funct7=0b0000000, funct3=000 | `rd = rs1 + rs2` (mod 2^32) |
| SUB semantics | `sub` | funct7=0b0100000, funct3=000 | `rd = rs1 - rs2` (mod 2^32) |
| SLL semantics | `sll` | funct3=001 | `rd = rs1 << (rs2 & 0x1F)` |
| SLT semantics | `slt` | funct3=010 | `rd = (signed(rs1) < signed(rs2)) ? 1 : 0` |
| SLTU semantics | `sltu` | funct3=011 | `rd = (rs1 < rs2) ? 1 : 0` (unsigned) |
| XOR semantics | `xor` | funct3=100 | `rd = rs1 ^ rs2` |
| SRL semantics | `srl` | funct3=101, funct7=0 | `rd = rs1 >> (rs2 & 0x1F)` (logical) |
| SRA semantics | `sra` | funct3=101, funct7=0b0100000 | `rd = signed(rs1) >> (rs2 & 0x1F)` (arithmetic) |
| OR semantics | `or` | funct3=110 | `rd = rs1 \| rs2` |
| AND semantics | `and` | funct3=111 | `rd = rs1 & rs2` |
| ADDI semantics | `addi` | opcode=0010011, funct3=000 | `rd = rs1 + sign_extend(imm12)` |
| SLLI semantics | `slli` | funct3=001, funct7=0 | `rd = rs1 << shamt` |
| SRLI semantics | `srli` | funct3=101, funct7=0 | `rd = rs1 >> shamt` (logical) |
| SRAI semantics | `srai` | funct3=101, funct7=0b0100000 | `rd = signed(rs1) >> shamt` (arithmetic) |
| LUI semantics | `lui` | opcode=0110111 | `rd = {imm[31:12], 12'b0}` |
| AUIPC semantics | `auipc` | opcode=0010111 | `rd = pc + {imm[31:12], 12'b0}` |
| JAL semantics | `jal` | opcode=1101111 | `rd = pc+4`, `pc' = pc + sign_extend(imm21)` |
| JALR semantics | `jalr` | opcode=1100111, funct3=000 | `rd = pc+4`, `pc' = (rs1+imm12) & ~1` |
| BEQ semantics | `beq` | funct3=000 | `pc' = (rs1==rs2) ? pc+imm13 : pc+4` |
| BNE semantics | `bne` | funct3=001 | `pc' = (rs1!=rs2) ? pc+imm13 : pc+4` |
| BLT semantics | `blt` | funct3=100 | `pc' = (signed(rs1)<signed(rs2)) ? pc+imm13 : pc+4` |
| BGE semantics | `bge` | funct3=101 | `pc' = (signed(rs1)>=signed(rs2)) ? pc+imm13 : pc+4` |
| BLTU semantics | `bltu` | funct3=110 | `pc' = (rs1<rs2) ? pc+imm13 : pc+4` (unsigned) |
| BGEU semantics | `bgeu` | funct3=111 | `pc' = (rs1>=rs2) ? pc+imm13 : pc+4` (unsigned) |
| LW semantics | `lw` | funct3=010 | `rd = mem[rs1+imm12]`, `rmask = 4'b1111` |
| SW semantics | `sw` | funct3=010 | `mem[rs1+imm12] = rs2`, `wmask = 4'b1111` |
| LB semantics | `lb` | funct3=000 | `rd = sign_extend(mem_byte[rs1+imm12])` |
| x0 hardwiring | all | rd==0 in RVFI | `rvfi_rd_wdata == 0` |

### 2.2 Proven by k-induction (unbounded)

| Property | Description |
|----------|------------|
| x0 == 0 invariant | After any sequence of instructions, register 0 is always 0 |
| PC alignment | After any JAL/JALR, PC[0] == 0 (JALR clears LSB) |

### 2.3 Covered by differential testing only (not formal)

| Property | Reason not formal |
|----------|------------------|
| Multi-instruction data hazard | Requires pipeline model, not just RVFI port |
| Custom instructions (rvrs, mul) | Not in riscv-formal — bespoke encoding |
| rst pseudo-instruction | Non-standard; requires custom property |
| 128+ instruction sequences | BMC depth limited to 20 for convergence |

---

## 3. Abstraction Choices

### 3.1 Memory model

The RVFI port exposes single-instruction memory transactions (`rvfi_mem_addr`, `rvfi_mem_rdata`, `rvfi_mem_wdata`, `rvfi_mem_rmask`, `rvfi_mem_wmask`). The formal properties check these fields directly. The underlying memory implementation (BRAM, cache, etc.) is abstracted out — we only verify that the RTL reports the correct address and data through RVFI, not how it fetches from physical memory. This is the standard approach; memory model correctness is verified separately.

### 3.2 Interrupt handling

PicoRV32 supports interrupts. The formal properties here are conditioned on `rvfi_valid` being asserted, which the core only does for committed, non-interrupted instructions. Interrupt handling is out of scope for this verification plan.

### 3.3 Reset sequence

The formal tool starts with an unconstrained initial state after reset (Yosys default). A `restrict` constraint limits the first `rvfi_valid` cycle to occur after at least 4 clock cycles post-reset. This prevents the solver from exploring reset glitches.

---

## 4. What Simulation Cannot Guarantee

| Claim | Why simulation fails | Formal coverage |
|-------|---------------------|----------------|
| ADD correct for ALL 2^64 input pairs | Infeasible to enumerate | ✓ proven |
| SRA sign-extends for ALL 2^32 inputs | Random testing misses rare sign bits | ✓ proven |
| Branch offset correct for ALL 4096 possible 12-bit offsets | Testing samples ~100 | ✓ proven |
| JALR LSB cleared for ALL 2^32 base addresses | Only specific values tested | ✓ proven |
| x0 stays zero after any sequence of writes | Finite tests can't cover all instruction sequences | ✓ proven (induction) |
| LB sign-extends even when byte value is 0x80 | Easy to miss in random testing | ✓ proven |

---

## 5. Bug Detection Summary

The following bugs were injected into PicoRV32 and verified to be caught:

| Bug | Formal (BMC) | Differential harness | Depth to find |
|-----|-------------|---------------------|---------------|
| LB returns zero-extended byte | ✓ counterexample | ✓ (seed 3 corner case) | 3 |
| Branch offset not shifted left by 1 | ✓ counterexample | ✓ (loop program) | 4 |
| SRA performs logical shift | ✓ counterexample | ✓ (seed 7) | 2 |
| ADD drops carry | ✓ counterexample | ✓ (overflow program) | 2 |
| JALR does not clear LSB | ✓ counterexample | ✓ (call_ret program) | 3 |

All bugs required only shallow BMC (depth ≤ 4), confirming that instruction-level semantic bugs are easily reachable without deep state exploration.
