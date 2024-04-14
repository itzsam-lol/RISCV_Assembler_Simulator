

import sys

# Initialize registers and memory
registers = [0] * 32
memory = [0] * 32

# Program counter
pc = 0

# Function to sign extend a binary string
def sign_extend(binary, target_length):
    sign_bit = binary[0]
    return sign_bit * (target_length - len(binary)) + binary

# Function to execute R-type instructions
def execute_r_type(instruction):
    funct7 = instruction[:7]
    rs2 = int(instruction[7:12], 2)
    rs1 = int(instruction[12:17], 2)
    funct3 = instruction[17:20]
    rd = int(instruction[20:25], 2)
    opcode = instruction[25:]

    if funct3 == '000' and funct7 == '0000000':
        registers[rd] = registers[rs1] + registers[rs2]
    elif funct3 == '000' and funct7 == '0100000':
        registers[rd] = registers[rs1] - registers[rs2]
    elif funct3 == '001' and funct7 == '0000000':
        registers[rd] = registers[rs1] << (registers[rs2] & 0x1F)
    elif funct3 == '010' and funct7 == '0000000':
        registers[rd] = 1 if registers[rs1] < registers[rs2] else 0
    elif funct3 == '011' and funct7 == '0000000':
        registers[rd] = 1 if registers[rs1] < registers[rs2] else 0
    elif funct3 == '100' and funct7 == '0000000':
        registers[rd] = registers[rs1] ^ registers[rs2]
    elif funct3 == '101' and funct7 == '0000000':
        registers[rd] = registers[rs1] >> (registers[rs2] & 0x1F)
    elif funct3 == '110' and funct7 == '0000000':
        registers[rd] = registers[rs1] | registers[rs2]
    elif funct3 == '111' and funct7 == '0000000':
        registers[rd] = registers[rs1] & registers[rs2]
    else:
        raise ValueError("Invalid R-type instruction")

# Function to execute I-type instructions
def execute_i_type(instruction):
    imm = sign_extend(instruction[:12], 12)
    rs1 = int(instruction[12:17], 2)
    funct3 = instruction[17:20]
    rd = int(instruction[20:25], 2)
    opcode = instruction[25:]

    if funct3 == '010' and opcode == '0000011':
        registers[rd] = memory[registers[rs1] + int(imm, 2)]
    elif funct3 == '000' and opcode == '0010011':
        registers[rd] = registers[rs1] + int(imm, 2)
    elif funct3 == '011' and opcode == '0010011':
        registers[rd] = 1 if registers[rs1] < int(imm, 2) else 0
    elif funct3 == '000' and opcode == '1100111':
        registers[rd] = pc + 4
        pc = registers[6] + int(imm, 2)
        pc &= ~1
    else:
        raise ValueError("Invalid I-type instruction")

# Function to execute S-type instructions
def execute_s_type(instruction):
    imm = sign_extend(instruction[:7] + instruction[20:25], 12)
    rs2 = int(instruction[7:12], 2)
    rs1 = int(instruction[12:17], 2)
    funct3 = instruction[17:20]
    opcode = instruction[25:]

    if funct3 == '010' and opcode == '0100011':
        memory[registers[rs1] + int(imm, 2)] = registers[rs2]
    else:
        raise ValueError("Invalid S-type instruction")

# Function to execute B-type instructions
def execute_b_type(instruction):
    imm = sign_extend(instruction[:7] + instruction[20:24] + instruction[24] + instruction[12:20], 13)
    rs2 = int(instruction[7:12], 2)
    rs1 = int(instruction[12:17], 2)
    funct3 = instruction[17:20]
    opcode = instruction[25:]

    if funct3 == '000' and opcode == '1100011':
        if registers[rs1] == registers[rs2]:
            pc += int(imm, 2) - 4
    elif funct3 == '001' and opcode == '1100011':
        if registers[rs1] != registers[rs2]:
            pc += int(imm, 2) - 4
    elif funct3 == '100' and opcode == '1100011':
        if registers[rs1] < registers[rs2]:
            pc += int(imm, 2) - 4
    elif funct3 == '101' and opcode == '1100011':
        if registers[rs1] >= registers[rs2]:
            pc += int(imm, 2) - 4
    elif funct3 == '110' and opcode == '1100011':
        if registers[rs1] < registers[rs2]:
            pc += int(imm, 2) - 4
    elif funct3 == '111' and opcode == '1100011':
        if registers[rs1] >= registers[rs2]:
            pc += int(imm, 2) - 4
    else:
        raise ValueError("Invalid B-type instruction")

# Function to execute U-type instructions
def execute_u_type(instruction):
    imm = sign_extend(instruction[:20], 32)
    rd = int(instruction[20:25], 2)
    opcode = instruction[25:]

    if opcode == '0110111':
        registers[rd] = int(imm, 2)
    elif opcode == '0010111':
        registers[rd] = pc + int(imm, 2)
    else:
        raise ValueError("Invalid U-type instruction")

# Function to execute J-type instructions
def execute_j_type(instruction):
    imm = sign_extend(instruction[:20], 21)
    rd = int(instruction[20:25], 2)
    opcode = instruction[25:]

    if opcode == '1101111':
        registers[rd] = pc + 4
        pc += int(imm, 2) - 4
    else:
        raise ValueError("Invalid J-type instruction")

# Function to execute instructions
def execute_instruction(instruction):
    opcode = instruction[25:]

    try:
        if opcode == '0110011':
            execute_r_type(instruction)
        elif opcode in ['0000011', '0010011', '1100111']:
            execute_i_type(instruction)
        elif opcode == '0100011':
            execute_s_type(instruction)
        elif opcode == '1100011':
            execute_b_type(instruction)
        elif opcode in ['0110111', '0010111']:
            execute_u_type(instruction)
        elif opcode == '1101111':
            execute_j_type(instruction)
        else:
            raise ValueError("Invalid instruction")
    except ValueError as e:
        print(f"Error: {str(e)}")

# Main function
def main():
    global pc

    while True:
        # Get the input binary instruction from the user
        instruction = input("Enter a 32-bit binary instruction (or 'q' to quit): ")

        if instruction == 'q':
            break

        if len(instruction) != 32:
            print("Error: Instruction must be 32 bits long")
            continue

        # Execute the instruction
        execute_instruction(instruction)

        # Print the register values in binary format
        print("Register values:")
        for i in range(32):
            print(f'0b{registers[i]:032b}', end=' ')
        print()  # Newline after printing all registers

        # Print the memory contents
        print("Memory contents:")
        for i in range(32):
            print(f"0x{i:08x}: {memory[i]}")

        print()

if __name__ == '__main__':
    main()
