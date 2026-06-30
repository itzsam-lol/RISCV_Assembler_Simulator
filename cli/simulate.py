import sys
import json
import argparse
from riscv.simulator import Simulator


def main() -> None:
    parser = argparse.ArgumentParser(description="RV32I Simulator")
    parser.add_argument("input",  nargs="?", help="binary machine code file")
    parser.add_argument("output", nargs="?", help="trace output file")
    parser.add_argument("--json", action="store_true", help="emit JSON trace")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            lines = [l.strip() for l in f if l.strip()]
    elif not sys.stdin.isatty():
        lines = [l.strip() for l in sys.stdin if l.strip()]
    else:
        try:
            with open("SimpleSimulator/Input_Sim.txt") as f:
                lines = [l.strip() for l in f if l.strip()]
        except FileNotFoundError:
            parser.print_help()
            sys.exit(1)

    program = {i * 4: line for i, line in enumerate(lines)}

    sim = Simulator()
    sim.run(program)

    if args.json:
        output = json.dumps(sim.to_json_dict(), indent=2) + "\n"
    else:
        output = sim.text_trace() + "\n" + sim.memory_dump_text() + "\n"

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
