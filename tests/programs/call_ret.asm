addi a0, zero, 7
jal  ra, func
halt
func:
    addi a0, a0, 1
    jalr zero, ra, 0
