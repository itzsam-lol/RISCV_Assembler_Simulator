import sys
input_ = sys.argv[-2]
output = sys.argv[-1]


registers_encd = {'zero': '00000', 'ra': '00001', 'sp': '00010', 'gp': '00011', 'tp': '00100',
                  't0': '00101', 't1': '00110', 't2': '00111', 's0': '01000', 'fp': '01000',
                  's1': '01001', 'a0': '01010', 'a1': '01011', 'a2': '01100', 'a3': '01101',
                  'a4': '01110', 'a5': '01111', 'a6': '10000', 'a7': '10001', 's2': '10010',
                  's3': '10011', 's4': '10100', 's5': '10101', 's6': '10110', 's7': '10111',
                  's8': '11000', 's9': '11001', 's10': '11010', 's11': '11011', 't3': '11100', 't4': '11101',
                  't5': '11110', 't6': '11111'}

R_opcode = {'add': '0110011', 'sub': '0110011', 'sll': '0110011', 'slt': '0110011',
            'sltu': '0110011', 'xor': '0110011', 'srl': '0110011', 'or': '0110011', 'and': '0110011'}
I_opcode = {'lw': '0000011', 'addi': '0010011', 'sltiu': '0010011', 'jalr': '1100111'}
S_opcode = {'sw': '0100011'}
B_opcode = {'beq': '1100011', 'bne': '1100011', 'blt': '1100011', 'bge': '1100011',
            'bltu': '1100011', 'bgeu': '1100011'}
U_opcode = {'lui': '0110111', 'auipc': '0010111'}
J_opcode = {'jal': '1101111'}

registers_data = {'zero': 0, 'ra': '', 'sp': '', 'gp': '', 'tp': '', 't0': '', 't1': '', 't2': '', 's0': '', 'fp': '',
                  's1': '', 'a0': '', 'a1': '', 'a2': '', 'a3': '', 'a4': '', 'a5': '', 'a6': '', 'a7': '', 's2': '',
                  's3': '', 's4': '', 's5': '', 's6': '', 's7': '', 's8': '', 's9': '', 's10': '', 's11': '', 't3': '',
                  't4': '', 't5': '', 't6': ''}


def add(rd, rs1, rs2):
    registers_data[rd] = registers_data[rs1] + registers_data[rs2]


def sub(rd, rs1, rs2):
    registers_data[rd] = registers_data[rs1] - registers_data[rs2]


def slt(rd, rs1, rs2):
    if registers_data[rs1] < registers_data[rs2]:
        registers_data[rd] = 1


def sltu(rd, rs1, rs2):
    if abs(registers_data[rs1]) < abs(registers_data[rs2]):
        registers_data[rd] = 1


def sll(rd, rs1, rs2):
    bin_x = (32 - len(bin(registers_data[rs2]))) * '0' + bin(registers_data[rs2])
    registers_data[rd] = registers_data[rs1] << bin_to_int(bin_x[len(bin_x) - 1] + bin_x[len(bin_x) - 2] +
                                                           bin_x[len(bin_x) - 3] + bin_x[len(bin_x) - 4] +
                                                           bin_x[len(bin_x) - 5])


def srl(rd, rs1, rs2):
    bin_x = (32 - len(bin(registers_data[rs2]))) * '0' + bin(registers_data[rs2])
    registers_data[rd] = registers_data[rs1] >> bin_to_int(bin_x[len(bin_x) - 1] + bin_x[len(bin_x) - 2] +
                                                           bin_x[len(bin_x) - 3] + bin_x[len(bin_x) - 4] +
                                                           bin_x[len(bin_x) - 5])


def Or(rd, rs1, rs2):
    registers_data[rd] = registers_data[rs1] or registers_data[rs2]


def And(rd, rs1, rs2):
    registers_data[rd] = registers_data[rs1] and registers_data[rs2]


def Xor(rd, rs1, rs2):
    registers_data[rd] = registers_data[rs1] ^ registers_data[rs2]


def addi(rs, rd, imm):
    registers_data[rd] = registers_data[rs] + imm


def sltiu(rs, rd, imm):
    if abs(registers_data[rs]) < abs(imm):
        registers_data[rd] = 1


def beq(rs1, rs2):
    if registers_data[rs1] == registers_data[rs2]:
        return '1'


def bne(rs1, rs2):
    if registers_data[rs1] != registers_data[rs2]:
        return '1'
    else:
        return '0'


def bge(rs1, rs2):
    if registers_data[rs1] >= registers_data[rs2]:
        return '1'
    else:
        return '0'


def bgeu(rs1, rs2):
    if abs(registers_data[rs1]) >= abs(registers_data[rs2]):
        return '1'
    else:
        return '0'


def blt(rs1, rs2):
    if registers_data[rs1] < registers_data[rs2]:
        return '1'
    else:
        return '0'


def bltu(rs1, rs2):
    if abs(registers_data[rs1]) < abs(registers_data[rs2]):
        return '1'
    else:
        return '0'


def lw(rd, rs1, imm):
    addr = bin(registers_data[rs1] + imm)
    reg_addr = (32 - len(addr)) * '0' + addr


def sw(rd, rs1, imm):
    addr = bin(registers_data[rs1] + imm)
    reg_addr = (32 - len(addr)) * '0' + addr


def bin_to_int(bin):  # function to convert given bin into integer
    val = 0
    for bin_i in range(0, len(bin)):
        if bin[bin_i] == '1':
            val += 2 ** ((len(bin) - 1) - bin_i)
    return val


def int_to_bin(num):  # function to convert an integer to binary used in later instructions
    bin = ''
    while num // 2 != 0:
        bin += str(num % 2)
        num = num // 2
    bin += str(num % 2)
    bin_final = ''
    k = len(bin) - 1
    while k != -1:
        bin_final += bin[k]
        k -= 1
    return bin_final


def twos_compl(bin):  # function to return two's complement of an integer by passing  its binary
    bin_imm = list(bin)
    for j_ in range(0, len(bin_imm)):
        if bin_imm[j_] == '0':
            bin_imm[j_] = '1'
        else:
            bin_imm[j_] = '0'
    carry = '1'
    j__ = len(bin_imm) - 1
    while j__ != -1:
        if bin_imm[j__] == '1':
            if carry == '1':
                bin_imm[j__] = '0'
                carry = '1'
            else:
                carry = '0'
        else:
            if carry == '1':
                bin_imm[j__] = '1'
                carry = '0'
            else:
                carry = '0'
        j__ -= 1

    final_bin = ''

    for index in range(0, len(bin_imm)):  # concatenating the final two's complement bin values
        final_bin += bin_imm[index]

    return final_bin


bin_instr = []  # Here, the bin_instr will store the list of various authorised bin values


def R_instr(instr, rd, rs1, rs2):  # As same, there are functions in X_instr format to convert it into machine language
    R_funct3 = {'add': '000', 'sub': '000', 'sll': '001', 'slt': '010',
                'sltu': '011', 'xor': '100', 'srl': '101', 'or': '110', 'and': '111'}
    R_funct7 = {'add': '0000000', 'sub': '0100000', 'sll': '0000000', 'slt': '0000000',
                'sltu': '0000000', 'xor': '0000000', 'srl': '0000000', 'or': '0000000', 'and': '0000000'}

    bin_temp = [R_opcode.get(instr), registers_encd.get(rd), R_funct3.get(instr),
                registers_encd.get(rs1), registers_encd.get(rs2), R_funct7.get(instr)]

    ''' --> here, the bin_temp in all functions store the bin in reverse order as per prescribed in guidelines but will
            print the data as written and specified which will managed later.'''

    bin_instr.append(bin_temp)


def I_instr(instr, rd, rs, imm):
    I_funct3 = {'lw': '010', 'addi': '000', 'sltiu': '011', 'jalr': '000'}

    bin_tem = int_to_bin(abs(imm))  # store the value of bin of imm
    bin_imm = '0' * (12 - len(bin_tem)) + bin_tem  # adjust the bin as per 12 bits

    if imm < 0:  # if no. is negative then pass it to the twos complement func to give
        bin_imm = twos_compl(bin_imm)

    bin_temp = [I_opcode.get(instr), registers_encd.get(rd), I_funct3.get(instr),
                registers_encd.get(rs), bin_imm]

    bin_instr.append(bin_temp)


def S_instr(instr, rs1, rs2, imm):
    bin_tem = int_to_bin(abs(imm))
    bin_imm = '0' * (12 - len(bin_tem)) + bin_tem

    if imm < 0:
        bin_imm = twos_compl(bin_imm)

    bin_temp = [S_opcode.get(instr), bin_imm[7:12], '010', registers_encd.get(rs1),
                registers_encd.get(rs2), bin_imm[0:7]]  # adjust the bin bits in said format

    bin_instr.append(bin_temp)


def B_instr(instr, rs1, rs2, imm):
    B_funct3 = {'beq': '000', 'bne': '001', 'blt': '100', 'bge': '101',
                'bltu': '110', 'bgeu': '111'}

    bin_tem = int_to_bin(abs(imm))
    bin_imm = '0' * (12 - len(bin_tem)) + bin_tem

    if imm < 0:
        bin_imm = twos_compl(bin_imm)
    bin_temp = [B_opcode.get(instr), bin_imm[7:12], B_funct3.get(instr), registers_encd.get(rs1),
                registers_encd.get(rs2), bin_imm[0:7]]

    bin_instr.append(bin_temp)


def U_instr(instr, rd, imm):
    bin_tem = int_to_bin(abs(imm))
    bin_imm = '0' * (32 - len(bin_tem)) + bin_tem
    if imm < 0:
        bin_imm = twos_compl(bin_imm)
    bin_temp = [U_opcode.get(instr), registers_encd.get(rd), bin_imm[0:len(bin_imm) - 12]]

    bin_instr.append(bin_temp)


def J_instr(instr, rd, imm):
    bin_tem = int_to_bin(abs(imm))
    bin_imm = '0' * (20 - len(bin_tem)) + bin_tem

    if imm < 0:
        bin_imm = twos_compl(bin_imm)

    bin_temp = [J_opcode.get(instr), registers_encd.get(rd), bin_imm[8:19] + bin_imm[0:9]]

    bin_instr.append(bin_temp)


# no_inst = int(input())  # Integer that will decide the no of instructions need to ask

lst_given_instr = []

labels_i, labels_ii = [], []  # label_i store label name and label_ii stores label index

Error = ''


# Open the file for reading
with open(input_, 'r') as file:
    # Read the lines from the file
    lines = file.readlines()

# Initialize an empty list to store the extracted data
extracted_data = []

# Iterate over each line
for line in lines:
    # Strip whitespace from the beginning and end of the line
    line = line.strip()
    # Check if the line is empty or starts with 'end:'
    extracted_data.append(line)


for ii in range(0, len(extracted_data)):
    ins = extracted_data[ii]
    if ':' in ins:  # Situation when there is label instruction
        lst_given_instr.append(list(ins.split(':')))
        labels_i.append(list(ins.split(':'))[0])
        labels_ii.append(ii)
    else:
        lst_given_instr.append(ins)

for i in range(0, len(extracted_data)):
    if type(lst_given_instr[i]) is str:
        lst_instr = list(
            lst_given_instr[i].split(' '))  # separate the string format of instructions and pass it in parts

    else:
        lst_instr = list(lst_given_instr[i][1].split(' '))  # when there is label in instr
        lst_instr.remove(lst_instr[0])  # deleting extra str as shown in data given ['', 'add', 'rd,rs2,rs3']

    if lst_instr[0] in R_opcode:  # whether instruction is in listed opcodes

        lst_instr_part = list(lst_instr[1].split(','))  # again separate the instr string which by comma and fragments

        if (lst_instr_part[0] in registers_encd) and (lst_instr_part[1] in registers_encd) and (
                lst_instr_part[2] in registers_encd):  # whether the register is in encodings avail or not

            # Passing the instruction fragments to the R_instr function for further processing
            R_instr(lst_instr[0], lst_instr_part[0], lst_instr_part[1], lst_instr_part[2])

        else:
            Error = f"Incorrect register name at instruction no. {i + 1}."  # storing errors and move on
            break

    elif lst_instr[0] in B_opcode:
        lst_instr_part = list(lst_instr[1].split(','))  # making instr fragments as specified before

        if (lst_instr_part[0] in registers_encd) and (lst_instr_part[1] in registers_encd):

            if lst_instr_part[2][0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                # if label is an integer then check such condition
                B_instr(lst_instr[0], lst_instr_part[0], lst_instr_part[1], int(lst_instr_part[2]))
            else:
                # if label is str given to some instr then checking the relative distance between both instructions
                imm_ = (i - labels_ii[labels_i.index(lst_instr_part[2])]) * 4
                B_instr(lst_instr[0], lst_instr_part[0], lst_instr_part[1], imm_)
        else:
            Error = f"Incorrect register name at instruction no. {i + 1}."  # print error and stop
            break

    elif lst_instr[0] in U_opcode:
        lst_instr_part = list(lst_instr[1].split(','))

        if lst_instr_part[0] in registers_encd:

            U_instr(lst_instr[0], lst_instr_part[0], int(lst_instr_part[1]))

        else:
            Error = f"Incorrect register name at instruction no. {i + 1}."  # print error and stop
            break

    elif lst_instr[0] in J_opcode:
        lst_instr_part = list(lst_instr[1].split(','))

        if lst_instr_part[0] in registers_encd:

            J_instr(lst_instr[0], lst_instr_part[0], int(lst_instr_part[1]))

        else:
            Error = f"Incorrect register name at instruction no. {i + 1}."
            break

    elif lst_instr[0] in I_opcode:

        if lst_instr[0] == 'lw':  # Handling special case of I_instr listed in project guidelines

            # Extracting instr fragments carefully to pass it on the I_instr funct to process further
            lst_instr_part_1 = list(lst_instr[1].split(','))
            lst_instr_part_2 = list(lst_instr_part_1[1].split('('))

            if lst_instr_part_2[1][0:len(lst_instr_part_2[1]) - 1] in registers_encd:

                # After instr fragmentation, the instr parts has to be pass carefully
                I_instr(lst_instr[0], lst_instr_part_1[0], lst_instr_part_2[1][0:len(lst_instr_part_2[1]) - 1],
                        int(lst_instr_part_2[0]))

            else:
                Error = f"Incorrect register name at instruction no. {i + 1}."  # storing errors and move on
                break

        else:
            lst_instr_part = list(lst_instr[1].split(','))

            if (lst_instr_part[0] in registers_encd) and (lst_instr_part[1] in registers_encd):

                # general case of I_instructions
                I_instr(lst_instr[0], lst_instr_part[0], lst_instr_part[1], int(lst_instr_part[2]))

            else:
                Error = f"Incorrect register name at instruction no. {i + 1}."  # storing errors and move on
                break

    elif lst_instr[0] in S_opcode:

        # There are only one instr avail in S_instr which is most same as the special case of I_instr
        lst_instr_part_1 = list(lst_instr[1].split(','))
        lst_instr_part_2 = list(lst_instr_part_1[1].split('('))

        if (lst_instr_part_2[1][0:len(lst_instr_part_2[1]) - 1] in registers_encd and lst_instr_part_1[0]
                in registers_encd):

            S_instr(lst_instr[0], lst_instr_part_2[1][0:len(lst_instr_part_2[1]) - 1], lst_instr_part_1[0],
                    int(lst_instr_part_2[0]))

        else:
            Error = f"Incorrect register name at instruction no. {i + 1}."
            break

    else:
        Error = f"Incorrect instruction name at instruction no. {i + 1}."
        break
with open(output, 'w') as file:
    for i in range(0, len(bin_instr)):  # After storing all bin formats of each instr, convert the result in str
        bin_result = ''
        j = len(bin_instr[i]) - 1

        while j != -1:  # Make sure the bin values in order as specified cause, the bin store in reverse order
            bin_result += bin_instr[i][j]
            # bin_result += ' '  # For simplicity, whitespace created temporarily to match the bin before submission of code
            j -= 1

        file.write(bin_result + '\n')  # Here you go, bin values of following instr provided

    if Error != '':  # Writing error if it exists
        file.write(Error + '\n')
