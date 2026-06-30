# Injected Bug Corpus

Each subdirectory contains a modified copy of the PicoRV32 core with a single intentional bug.
The differential harness and formal tools are expected to catch every bug here.

| Directory | Bug | Caught by formal | Caught by diff harness |
|-----------|-----|-----------------|----------------------|
| `bug_lb_sign_extend/` | `LB` returns zero-extended byte instead of sign-extended | Yes (BMC depth 3) | Yes |
| `bug_branch_offset/` | Branch target is `pc + imm` instead of `pc + (imm << 1)` | Yes (BMC depth 4) | Yes |
| `bug_sra_logical/` | `SRA` performs logical right shift instead of arithmetic | Yes (BMC depth 2) | Yes |
| `bug_add_carry/` | `ADD` drops carry bit (result truncated to 31 bits) | Yes (BMC depth 2) | Yes |
| `bug_jalr_lsb/` | `JALR` does not clear LSB of target address | Yes (BMC depth 3) | Yes |

## How to reproduce

```bash
cd formal
make diff-test            # run differential harness on all bug variants
make formal-check-bugs    # run SymbiYosys on each bug — expect counterexamples
```

Each `make formal-check-bugs` run produces a `.vcd` witness file showing the exact
input sequence (instructions + register values) that triggers the violation.
