import sys
import argparse

class Simulator:
    def __init__(self):
        self.registers = [0] * 32
        self.pc = 0
        self.data_memory = {}
        self.mem_start = 0x00010000
        for i in range(32):
            self.data_memory[self.mem_start + i * 4] = 0
        self.halted = False
        self.output_trace = []
        
        # Initial states as listed in original, sp=256
        self.registers[2] = 256
        
    def to_unsigned_bin(self, val, bits=32):
        val = int(val) & ((1 << bits) - 1)
        return '0b' + bin(val)[2:].zfill(bits)
        
    def sign_extend(self, val, bits):
        if val & (1 << (bits - 1)):
            return val - (1 << bits)
        return val

    def hex_pad(self, val, digits=8):
        return f"0x{val:0{digits}x}"

    def parse_instruction(self, inst_bin):
        opcode = inst_bin[25:32]
        if opcode == "0110011": # R-type
            return 'R', opcode
        elif opcode in ("0010011", "0000011", "1100111"): # I-type
            return 'I', opcode
        elif opcode == "0100011": # S-type
            return 'S', opcode
        elif opcode == "1100011": # B-type
            return 'B', opcode
        elif opcode in ("0110111", "0010111"): # U-type
            return 'U', opcode
        elif opcode == "1101111": # J-type
            return 'J', opcode
        elif opcode == "0000000": # Custom R
            return 'R', opcode
        return None, opcode

    def execute_line(self, inst_bin):
        self.registers[0] = 0 # zero register
        
        if inst_bin == "00000000000000000000000001100011":
            self.halted = True
            return
            
        if inst_bin == "00000000000000000000000000000000":
            # rst
            self.registers = [0] * 32
            self.registers[2] = 256
            self.pc += 4
            return

        itype, opcode = self.parse_instruction(inst_bin)
        
        # Extract fields
        rd = int(inst_bin[20:25], 2)
        funct3 = inst_bin[17:20]
        rs1 = int(inst_bin[12:17], 2)
        rs2 = int(inst_bin[7:12], 2)
        funct7 = inst_bin[0:7]
        
        next_pc = self.pc + 4
        
        if itype == 'R':
            if opcode == "0000000":
                if funct3 == "001": # rvrs
                    # Bit reversal
                    val_bin = bin(self.registers[rs1] & 0xFFFFFFFF)[2:].zfill(32)
                    self.registers[rd] = int(val_bin[::-1], 2)
                elif funct3 == "011": # mul
                    self.registers[rd] = (self.registers[rs1] * self.registers[rs2]) & 0xFFFFFFFF
                    # keep it within uint32 just in case
            else:
                if funct3 == "000":
                    if funct7 == "0000000": # add
                        self.registers[rd] = self.registers[rs1] + self.registers[rs2]
                    elif funct7 == "0100000": # sub
                        self.registers[rd] = self.registers[rs1] - self.registers[rs2]
                elif funct3 == "001": # sll
                    shift = self.registers[rs2] & 0x1F
                    self.registers[rd] = self.registers[rs1] << shift
                elif funct3 == "010": # slt
                    v1 = self.sign_extend(self.registers[rs1] & 0xFFFFFFFF, 32)
                    v2 = self.sign_extend(self.registers[rs2] & 0xFFFFFFFF, 32)
                    self.registers[rd] = 1 if v1 < v2 else 0
                elif funct3 == "011": # sltu
                    v1 = self.registers[rs1] & 0xFFFFFFFF
                    v2 = self.registers[rs2] & 0xFFFFFFFF
                    self.registers[rd] = 1 if v1 < v2 else 0
                elif funct3 == "100": # xor
                    self.registers[rd] = self.registers[rs1] ^ self.registers[rs2]
                elif funct3 == "101": # srl
                    shift = self.registers[rs2] & 0x1F
                    self.registers[rd] = (self.registers[rs1] & 0xFFFFFFFF) >> shift
                elif funct3 == "110": # or
                    self.registers[rd] = self.registers[rs1] | self.registers[rs2]
                elif funct3 == "111": # and
                    self.registers[rd] = self.registers[rs1] & self.registers[rs2]

        elif itype == 'I':
            imm = self.sign_extend(int(inst_bin[0:12], 2), 12)
            if opcode == "0000011":
                if funct3 == "010": # lw
                    addr = (self.registers[rs1] + imm) & 0xFFFFFFFF
                    if addr in self.data_memory:
                        self.registers[rd] = self.data_memory[addr]
                    else:
                        self.registers[rd] = 0 # uninitialized mem read
            elif opcode == "0010011":
                if funct3 == "000": # addi
                    self.registers[rd] = self.registers[rs1] + imm
                elif funct3 == "011": # sltiu
                    v1 = self.registers[rs1] & 0xFFFFFFFF
                    ext_imm = (imm & 0xFFFFFFFF)
                    self.registers[rd] = 1 if v1 < ext_imm else 0
            elif opcode == "1100111":
                if funct3 == "000": # jalr
                    self.registers[rd] = next_pc
                    target = (self.registers[rs1] + imm) & ~1
                    next_pc = target
                    
        elif itype == 'S':
            imm_str = inst_bin[0:7] + inst_bin[20:25]
            imm = self.sign_extend(int(imm_str, 2), 12)
            if funct3 == "010": # sw
                addr = (self.registers[rs1] + imm) & 0xFFFFFFFF
                self.data_memory[addr] = self.registers[rs2] & 0xFFFFFFFF

        elif itype == 'B':
            imm_str = inst_bin[0] + inst_bin[24] + inst_bin[1:7] + inst_bin[20:24] + "0"
            imm = self.sign_extend(int(imm_str, 2), 13)
            taken = False
            v1_s = self.sign_extend(self.registers[rs1] & 0xFFFFFFFF, 32)
            v2_s = self.sign_extend(self.registers[rs2] & 0xFFFFFFFF, 32)
            v1_u = self.registers[rs1] & 0xFFFFFFFF
            v2_u = self.registers[rs2] & 0xFFFFFFFF
            if funct3 == "000": taken = (v1_s == v2_s)      # beq
            elif funct3 == "001": taken = (v1_s != v2_s)    # bne
            elif funct3 == "100": taken = (v1_s < v2_s)     # blt
            elif funct3 == "101": taken = (v1_s >= v2_s)    # bge
            elif funct3 == "110": taken = (v1_u < v2_u)     # bltu
            elif funct3 == "111": taken = (v1_u >= v2_u)    # bgeu
            if taken:
                next_pc = self.pc + imm
                
        elif itype == 'U':
            imm_str = inst_bin[0:20] + "000000000000"
            imm = self.sign_extend(int(imm_str, 2), 32)
            if opcode == "0110111": # lui
                self.registers[rd] = imm
            elif opcode == "0010111": # auipc
                self.registers[rd] = self.pc + imm
                
        elif itype == 'J':
            imm_str = inst_bin[0] + inst_bin[12:20] + inst_bin[11] + inst_bin[1:11] + "0"
            imm = self.sign_extend(int(imm_str, 2), 21)
            # jal
            self.registers[rd] = next_pc
            next_pc = self.pc + imm

        self.registers[0] = 0 # enforce zero register
        
        # Keep registers in Python 32-bit uint bounds for display matching original behavior correctly
        for i in range(32):
            self.registers[i] &= 0xFFFFFFFF
            
        self.pc = next_pc

    def capture_trace(self):
        regs_str = " ".join([self.to_unsigned_bin(r) for r in self.registers]) + " "
        self.output_trace.append(self.to_unsigned_bin(self.pc) + " " + regs_str)

    def data_memory_dump(self):
        dump = []
        for i in range(32):
            addr = self.mem_start + i * 4
            val = self.data_memory.get(addr, 0)
            dump.append(f"{self.hex_pad(addr)}:{self.to_unsigned_bin(val)[2:]}") # Wait, original uses formatting like 0x00010000:0b00...
        # Let's adjust exact formatting to match original `Simulator.py`
        # f'0x000{str(dec_hex(65536+(4*i)))}:{mem[f"0x000{str(dec_hex(65536+(4*i)))}"]}'
        # This translates to: 0x00010000:0b000000...
        fixed_dump = []
        for i in range(32):
            addr = self.mem_start + i * 4
            val = self.data_memory.get(addr, 0)
            v_bin = bin(val)[2:].zfill(32)
            fixed_dump.append(f"0x000{addr:x}:0b{v_bin}")
        return "\n".join(fixed_dump)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?', help='Input binary memory file')
    parser.add_argument('output', nargs='?', help='Output trace execution')
    args = parser.parse_args()
    
    if args.input:
        with open(args.input, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
    elif not sys.stdin.isatty():
        lines = [l.strip() for l in sys.stdin.readlines() if l.strip()]
    else:
        # Fallback to hardcoded names to preserve completely original behavior if needed
        try:
            with open('Input_Sim.txt', 'r') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
        except FileNotFoundError:
            print("No input provided.")
            return

    sim = Simulator()
    instructions = {}
    for i, line in enumerate(lines):
        instructions[i * 4] = line

    while not sim.halted and sim.pc in instructions:
        inst = instructions[sim.pc]
        sim.execute_line(inst)
        sim.capture_trace()
        
    out_text = "\n".join(sim.output_trace) + "\n" + sim.data_memory_dump() + "\n"
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(out_text)
    elif not sys.stdin.isatty() and not sys.stdout.isatty():
        sys.stdout.write(out_text)
    else:
        try:
            with open('Output_Sim.txt', 'w') as f:
                f.write(out_text)
            print("Trace generated in Output_Sim.txt")
        except:
            sys.stdout.write(out_text)

if __name__ == "__main__":
    main()
