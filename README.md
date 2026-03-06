# RISC-V Assembler & Simulator

![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)
![RISC-V](https://img.shields.io/badge/Architecture-RISC--V%20RV32I-orange.svg)
![Contributions](https://img.shields.io/badge/contributions-welcome-green)

A precise, optimized, and robust two-pass Python-based Assembler and Simulator for the 32-bit RISC-V (RV32I) instruction set architecture. This project takes human-readable RISC-V assembly source code, encodes it into raw 32-bit binary machine code, and executes it via an accurate step-by-step architectural simulator.

Designed as part of the **CSE112 - Computer Organisation** course (Group 60), it is now enhanced to be modular, production-ready, and highly polished.

## Features

### Assembler
* **Robust 2-Pass Architecture:** Accurately resolves forward memory references and label addressing.
* **Full RV32I Base Instruction Set:** Supports `R`, `I`, `S`, `B`, `U`, and `J` type instructions seamlessly.
* **Smart Error Handling:** Provides robust feedback syntax checking (registers out of bounds, unknown opcode, incorrect parameter lengths).
* **Bonus Pseudo-instructions:** Supported custom instructions out of the box (`rvrs`, `mul`, `halt`, `rst`).

### Simulator
* **Cycle-Accurate Tracing:** Steps through standard memory and visualizes the state of the 32 generic registers after execution of each instruction.
* **Memory Dump Support:** Post-execution memory state dump displaying memory addresses mapped accurately.
* **Unsigned / 2's Complement Sign Extensions:** Uses fully validated bounds and binary wrapping conforming to RISC-V specifications.
* **Execution Environment:** Handles exact PC calculations ensuring loop behaviors (e.g., `beq zero, zero, 0` for explicit `halt` looping architectures).

##  Usage

### 1. Assembler

Translate `assembly(.asm)` code into machine code `binary(.bin)` lines:

```bash
# General Usage
python Simple-Assembler/Assembler.py <input_asm_file> <output_bin_file>

# Alternative: Standard Input/Output streaming
python Simple-Assembler/Assembler.py < input.asm > output.bin
```

### 2. Simulator

Execute binary machine code lines to generate an architectural footprint and execution trace:

```bash
# General Usage
python SimpleSimulator/Simulator.py <input_bin_file> <output_trace_file>

# Alternative: Standard Input/Output streaming
python SimpleSimulator/Simulator.py < input.bin > trace.txt
```

## Project Structure

```text
 RISC-V Assembler & Simulator
 ┣ Simple-Assembler
 ┃ ┣  Assembler.py          # The core assembler implementation
 ┃ ┗  run                   # Utility bash script runner
 ┣ SimpleSimulator
 ┃ ┣  Simulator.py          # The RISC-V simulation engine
 ┃ ┣  Input_Sim.txt         # Example simulation input binary
 ┃ ┗  Output_Sim.txt        # Validated execution trace output
 ┗  README.md               # You're reading this!
```

##  Authors 
* **Satyam**

