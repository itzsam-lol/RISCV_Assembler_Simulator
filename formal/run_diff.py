from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.differential import DifferentialHarness
from harness.program_gen import random_program, corner_case_programs


def main() -> None:
    parser = argparse.ArgumentParser(description="Differential testing harness")
    parser.add_argument("--dut", metavar="BINARY", help="path to compiled RTL testbench binary")
    parser.add_argument("--programs", type=int, default=20, metavar="N",
                        help="number of random programs to generate")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--corner-cases", action="store_true",
                        help="include corner case programs in the run")
    args = parser.parse_args()

    harness = DifferentialHarness(dut_binary=args.dut)

    programs: list[str] = []

    if args.corner_cases:
        programs.extend(corner_case_programs())
        print(f"Added {len(corner_case_programs())} corner case programs")

    for i in range(args.programs):
        programs.append(random_program(n_instructions=20, seed=args.seed + i))

    print(f"Running {len(programs)} programs...")
    summary = harness.run_suite(programs)

    print(harness.report())
    print(f"\nSummary: {summary['passed']}/{summary['total']} passed")

    if summary["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
