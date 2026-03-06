import sys
import argparse

REGISTERS = {
    'zero': 0, 'ra': 1, 'sp': 2, 'gp': 3, 'tp': 4, 't0': 5, 't1': 6, 't2': 7,
    's0': 8, 'fp': 8, 's1': 9, 'a0': 10, 'a1': 11, 'a2': 12, 'a3': 13, 'a4': 14,
    'a5': 15, 'a6': 16, 'a7': 17, 's2': 18, 's3': 19, 's4': 20, 's5': 21, 's6': 22,
    's7': 23, 's8': 24, 's9': 25, 's10': 26, 's11': 27, 't3': 28, 't4': 29, 't5': 30, 't6': 31
}

# (type, opcode, funct3, funct7)
INSTRUCTIONS = {
    'add':  ('R', '0110011', '000', '0000000'),
    'sub':  ('R', '0110011', '000', '0100000'),
    'sll':  ('R', '0110011', '001', '0000000'),
    'slt':  ('R', '0110011', '010', '0000000'),
    'sltu': ('R', '0110011', '011', '0000000'),
    'xor':  ('R', '0110011', '100', '0000000'),
    'srl':  ('R', '0110011', '101', '0000000'),
    'or':   ('R', '0110011', '110', '0000000'),
    'and':  ('R', '0110011', '111', '0000000'),
    'lw':   ('I', '0000011', '010', None),
    'addi': ('I', '0010011', '000', None),
    'sltiu':('I', '0010011', '011', None),
    'jalr': ('I', '1100111', '000', None),
    'sw':   ('S', '0100011', '010', None),
    'beq':  ('B', '1100011', '000', None),
    'bne':  ('B', '1100011', '001', None),
    'blt':  ('B', '1100011', '100', None),
    'bge':  ('B', '1100011', '101', None),
    'bltu': ('B', '1100011', '110', None),
    'bgeu': ('B', '1100011', '111', None),
    'lui':  ('U', '0110111', None, None),
    'auipc':('U', '0010111', None, None),
    'jal':  ('J', '1101111', None, None),
    
    # Custom/Bonus
    'mul':  ('R', '0000000', '011', '0000000'),
    'rvrs': ('R', '0000000', '001', '0000000'),
    'rst':  ('Z', '0000000', '000', '0000000'),
    'halt': ('Z', '1100011', '000', '0000000'),
}

def to_bin(val, bits):
    """Convert integer to two's complement binary string of given bit length."""
    val = int(val)
    if val < 0:
        val = (1 << bits) + val
    return bin(val & ((1 << bits) - 1))[2:].zfill(bits)

class Assembler:
    def __init__(self):
        self.labels = {}
        self.code_lines = []
        self.address = 0
    
    def parse_register(self, reg_str):
        reg_str = reg_str.strip()
        if reg_str not in REGISTERS:
            raise ValueError(f"Unknown register '{reg_str}'")
        return to_bin(REGISTERS[reg_str], 5)

    def extract_imm_and_reg(self, token):
        # Extracts immediate and register from format like `imm(reg)`
        if '(' in token and token.endswith(')'):
            imm_str, reg_str = token[:-1].split('(')
            return int(imm_str.strip()), reg_str.strip()
        raise ValueError(f"Invalid format expected imm(reg), got {token}")

    def pass_one(self, lines):
        """First pass: find labels and build clean instructions."""
        self.address = 0
        cleaned_lines = []
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Remove inline comments
            if '#' in line:
                line = line[:line.index('#')].strip()

            if ':' in line:
                label, instr = line.split(':', 1)
                label = label.strip()
                instr = instr.strip()
                self.labels[label] = self.address
                if not instr:
                    continue  # Just a label on a line
                line = instr
                
            cleaned_lines.append((line_num + 1, self.address, line))
            self.address += 4
        return cleaned_lines

    def pass_two(self, cleaned_lines):
        """Second pass: convert assembly to binary."""
        binary_output = []
        for line_num, address, line in cleaned_lines:
            try:
                # Split instruction name and operands
                parts = line.replace(',', ' ').split()
                inst_name = parts[0]
                
                if inst_name not in INSTRUCTIONS:
                    raise ValueError(f"Unknown instruction '{inst_name}'")
                
                itype, opcode, funct3, funct7 = INSTRUCTIONS[inst_name]
                args = parts[1:]

                if itype == 'R':
                    if inst_name == 'rvrs':
                        # rvrs rd, rs1 (assumes rs2=0)
                        if len(args) != 2:
                            raise ValueError(f"{inst_name} expects 2 arguments")
                        rd, rs1 = self.parse_register(args[0]), self.parse_register(args[1])
                        rs2 = "00000"
                    else:
                        if len(args) != 3:
                            raise ValueError(f"{inst_name} expects 3 arguments")
                        rd = self.parse_register(args[0])
                        rs1 = self.parse_register(args[1])
                        rs2 = self.parse_register(args[2])
                    encoded = funct7 + rs2 + rs1 + funct3 + rd + opcode
                    
                elif itype == 'I':
                    if inst_name == 'lw':
                        if len(args) != 2: # lw rd, imm(rs1)
                            raise ValueError(f"lw expects rd, imm(rs1)")
                        rd = self.parse_register(args[0])
                        imm_val, rs1_str = self.extract_imm_and_reg(args[1])
                        rs1 = self.parse_register(rs1_str)
                        imm = to_bin(imm_val, 12)
                    else:
                        if len(args) != 3:
                            raise ValueError(f"{inst_name} expects 3 arguments")
                        rd = self.parse_register(args[0])
                        rs1 = self.parse_register(args[1])
                        imm = to_bin(int(args[2]), 12)
                    encoded = imm + rs1 + funct3 + rd + opcode

                elif itype == 'S':
                    if len(args) != 2: # sw rs2, imm(rs1)
                        raise ValueError(f"sw expects rs2, imm(rs1)")
                    rs2 = self.parse_register(args[0])
                    imm_val, rs1_str = self.extract_imm_and_reg(args[1])
                    rs1 = self.parse_register(rs1_str)
                    imm = to_bin(imm_val, 12)
                    encoded = imm[:7] + rs2 + rs1 + funct3 + imm[7:] + opcode

                elif itype == 'B':
                    if len(args) != 3:
                        raise ValueError(f"{inst_name} expects 3 arguments")
                    rs1 = self.parse_register(args[0])
                    rs2 = self.parse_register(args[1])
                    target = args[2]
                    if target in self.labels:
                        offset = self.labels[target] - address
                    else:
                        offset = int(target)
                    
                    imm = to_bin(offset, 13) # the 0th bit is always 0 in RISC-V branches
                    # Format: imm[12] imm[10:5] rs2 rs1 funct3 imm[4:1] imm[11] opcode
                    encoded = imm[0] + imm[2:8] + rs2 + rs1 + funct3 + imm[8:12] + imm[1] + opcode

                elif itype == 'U':
                    if len(args) != 2:
                        raise ValueError(f"{inst_name} expects 2 arguments")
                    rd = self.parse_register(args[0])
                    imm = to_bin((int(args[1]) & 0xFFFFF), 20) # already upper bits
                    encoded = imm + rd + opcode
                    
                elif itype == 'J':
                    if len(args) != 2:
                        raise ValueError(f"{inst_name} expects 2 arguments")
                    rd = self.parse_register(args[0])
                    target = args[1]
                    if target in self.labels:
                        offset = self.labels[target] - address
                    else:
                        offset = int(target)
                        
                    imm = to_bin(offset, 21) # 21 bits, LSB is 0
                    # Format: imm[20] imm[10:1] imm[11] imm[19:12] rd opcode
                    encoded = imm[0] + imm[10:20] + imm[9] + imm[1:9] + rd + opcode

                elif itype == 'Z':
                    if inst_name == 'rst':
                        encoded = "0" * 32
                    elif inst_name == 'halt':
                        encoded = "00000000000000000000000001100011"
                
                binary_output.append(encoded)

            except Exception as e:
                return (None, f"Error at line {line_num}: {e}")
        
        return (binary_output, None)

def main():
    parser = argparse.ArgumentParser(description="RISC-V Assembler")
    parser.add_argument('input', nargs='?', help='Input assembly file')
    parser.add_argument('output', nargs='?', help='Output binary file')

    args = parser.parse_args()

    if args.input:
        with open(args.input, 'r') as f:
            lines = f.readlines()
    else:
        if sys.stdin.isatty():
            return
        lines = sys.stdin.readlines()

    assembler = Assembler()
    cleaned = assembler.pass_one(lines)
    binary_lines, err = assembler.pass_two(cleaned)

    if err:
        output_txt = err + "\n"
    else:
        output_txt = "\n".join(binary_lines) + "\n"

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_txt)
    else:
        sys.stdout.write(output_txt)

if __name__ == "__main__":
    main()
