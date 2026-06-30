import sys
import argparse
from riscv.assembler import Assembler, AssemblerError


def main() -> None:
    parser = argparse.ArgumentParser(description="RV32I Assembler")
    parser.add_argument("input",  nargs="?", help="assembly source file")
    parser.add_argument("output", nargs="?", help="binary output file")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            source = f.read()
    elif not sys.stdin.isatty():
        source = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    asm = Assembler()
    try:
        binary = asm.assemble(source)
    except AssemblerError as e:
        sys.stderr.write(f"assembler error: {e}\n")
        sys.exit(1)

    output = "\n".join(binary) + "\n"
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
