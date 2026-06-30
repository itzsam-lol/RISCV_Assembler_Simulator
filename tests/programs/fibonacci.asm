addi a0, zero, 0
addi a1, zero, 1
addi a2, zero, 9
loop:
    add  a3, a0, a1
    addi a0, a1, 0
    addi a1, a3, 0
    addi a2, a2, -1
    bne  a2, zero, loop
halt
