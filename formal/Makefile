PYTHON := python3
HARNESS := harness/differential.py
PROGRAM_GEN := harness/program_gen.py

.PHONY: all diff-test formal-check formal-check-bugs clean help

all: diff-test

diff-test:
	$(PYTHON) -m pytest ../tests/ -v

diff-test-with-dut:
	@echo "Usage: make diff-test-with-dut DUT_BINARY=./build/picorv32_tb"
	$(PYTHON) run_diff.py --dut $(DUT_BINARY) --programs 50 --seed 42

formal-check:
	@echo "Requires: symbiyosys, yosys, boolector"
	@echo "Run: cd formal && sby -f properties/picorv32_bmc.sby"
	sby -f properties/picorv32_bmc.sby

formal-check-bugs:
	@for bug in bugs/bug_*/; do \
		echo "Checking $$bug ..."; \
		sby -f $$bug/check.sby 2>&1 | tail -3; \
	done

setup-picorv32:
	git clone https://github.com/YosysHQ/picorv32.git picorv32
	cd picorv32 && git checkout adf63fd

clean:
	rm -rf picorv32_bmc/ *.log

help:
	@echo "Targets:"
	@echo "  diff-test          run pytest suite (no RTL needed)"
	@echo "  diff-test-with-dut run differential harness against compiled RTL"
	@echo "  formal-check       run SymbiYosys BMC on PicoRV32 (needs yosys+sby)"
	@echo "  formal-check-bugs  verify that each injected bug is caught"
	@echo "  setup-picorv32     clone and pin PicoRV32 source"
