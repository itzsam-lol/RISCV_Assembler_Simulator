`default_nettype none

module rv32i_check (
    input wire        clk,
    input wire        rvfi_valid,
    input wire [31:0] rvfi_insn,
    input wire [31:0] rvfi_pc_rdata,
    input wire [31:0] rvfi_pc_wdata,
    input wire [ 4:0] rvfi_rs1_addr,
    input wire [ 4:0] rvfi_rs2_addr,
    input wire [31:0] rvfi_rs1_rdata,
    input wire [31:0] rvfi_rs2_rdata,
    input wire [ 4:0] rvfi_rd_addr,
    input wire [31:0] rvfi_rd_wdata,
    input wire [31:0] rvfi_mem_addr,
    input wire [ 3:0] rvfi_mem_rmask,
    input wire [ 3:0] rvfi_mem_wmask,
    input wire [31:0] rvfi_mem_rdata,
    input wire [31:0] rvfi_mem_wdata
);

    wire [6:0] opcode  = rvfi_insn[6:0];
    wire [2:0] funct3  = rvfi_insn[14:12];
    wire [6:0] funct7  = rvfi_insn[31:25];
    wire [4:0] rd      = rvfi_insn[11:7];

    wire signed [31:0] rs1_s = $signed(rvfi_rs1_rdata);
    wire signed [31:0] rs2_s = $signed(rvfi_rs2_rdata);
    wire [4:0] shamt = rvfi_rs2_rdata[4:0];

    wire is_valid = rvfi_valid;

    property rd_zero_never_written;
        @(posedge clk) is_valid |-> (rvfi_rd_addr == 5'b0 -> rvfi_rd_wdata == 32'b0);
    endproperty

    property add_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110011 && funct3 == 3'b000 && funct7 == 7'b0000000)
        |-> (rvfi_rd_wdata == rvfi_rs1_rdata + rvfi_rs2_rdata);
    endproperty

    property sub_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110011 && funct3 == 3'b000 && funct7 == 7'b0100000)
        |-> (rvfi_rd_wdata == rvfi_rs1_rdata - rvfi_rs2_rdata);
    endproperty

    property sll_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110011 && funct3 == 3'b001 && funct7 == 7'b0000000)
        |-> (rvfi_rd_wdata == (rvfi_rs1_rdata << shamt));
    endproperty

    property slt_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110011 && funct3 == 3'b010 && funct7 == 7'b0000000)
        |-> (rvfi_rd_wdata == (rs1_s < rs2_s ? 32'b1 : 32'b0));
    endproperty

    property sltu_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110011 && funct3 == 3'b011 && funct7 == 7'b0000000)
        |-> (rvfi_rd_wdata == (rvfi_rs1_rdata < rvfi_rs2_rdata ? 32'b1 : 32'b0));
    endproperty

    property xor_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110011 && funct3 == 3'b100 && funct7 == 7'b0000000)
        |-> (rvfi_rd_wdata == (rvfi_rs1_rdata ^ rvfi_rs2_rdata));
    endproperty

    property srl_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110011 && funct3 == 3'b101 && funct7 == 7'b0000000)
        |-> (rvfi_rd_wdata == (rvfi_rs1_rdata >> shamt));
    endproperty

    property sra_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110011 && funct3 == 3'b101 && funct7 == 7'b0100000)
        |-> (rvfi_rd_wdata == 32'($signed(rvfi_rs1_rdata) >>> shamt));
    endproperty

    property or_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110011 && funct3 == 3'b110 && funct7 == 7'b0000000)
        |-> (rvfi_rd_wdata == (rvfi_rs1_rdata | rvfi_rs2_rdata));
    endproperty

    property and_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110011 && funct3 == 3'b111 && funct7 == 7'b0000000)
        |-> (rvfi_rd_wdata == (rvfi_rs1_rdata & rvfi_rs2_rdata));
    endproperty

    property addi_correct;
        wire signed [31:0] imm = $signed(rvfi_insn[31:20]);
        @(posedge clk)
        (is_valid && opcode == 7'b0010011 && funct3 == 3'b000)
        |-> (rvfi_rd_wdata == rvfi_rs1_rdata + 32'(imm));
    endproperty

    property slli_correct;
        wire [4:0] imm_shamt = rvfi_insn[24:20];
        @(posedge clk)
        (is_valid && opcode == 7'b0010011 && funct3 == 3'b001 && funct7 == 7'b0000000)
        |-> (rvfi_rd_wdata == (rvfi_rs1_rdata << imm_shamt));
    endproperty

    property srli_correct;
        wire [4:0] imm_shamt = rvfi_insn[24:20];
        @(posedge clk)
        (is_valid && opcode == 7'b0010011 && funct3 == 3'b101 && funct7 == 7'b0000000)
        |-> (rvfi_rd_wdata == (rvfi_rs1_rdata >> imm_shamt));
    endproperty

    property srai_correct;
        wire [4:0] imm_shamt = rvfi_insn[24:20];
        @(posedge clk)
        (is_valid && opcode == 7'b0010011 && funct3 == 3'b101 && funct7 == 7'b0100000)
        |-> (rvfi_rd_wdata == 32'($signed(rvfi_rs1_rdata) >>> imm_shamt));
    endproperty

    property lui_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0110111)
        |-> (rvfi_rd_wdata == {rvfi_insn[31:12], 12'b0});
    endproperty

    property auipc_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0010111)
        |-> (rvfi_rd_wdata == rvfi_pc_rdata + {rvfi_insn[31:12], 12'b0});
    endproperty

    property jal_correct;
        wire signed [31:0] offset = $signed({rvfi_insn[31], rvfi_insn[19:12],
                                              rvfi_insn[20], rvfi_insn[30:21], 1'b0});
        @(posedge clk)
        (is_valid && opcode == 7'b1101111)
        |-> (rvfi_rd_wdata == rvfi_pc_rdata + 32'd4 &&
             rvfi_pc_wdata == 32'(rvfi_pc_rdata + offset));
    endproperty

    property jalr_correct;
        wire signed [31:0] offset = $signed(rvfi_insn[31:20]);
        @(posedge clk)
        (is_valid && opcode == 7'b1100111 && funct3 == 3'b000)
        |-> (rvfi_rd_wdata == rvfi_pc_rdata + 32'd4 &&
             rvfi_pc_wdata == (32'(rvfi_rs1_rdata + offset) & ~32'b1));
    endproperty

    property beq_correct;
        wire signed [31:0] offset = $signed({rvfi_insn[31], rvfi_insn[7],
                                              rvfi_insn[30:25], rvfi_insn[11:8], 1'b0});
        @(posedge clk)
        (is_valid && opcode == 7'b1100011 && funct3 == 3'b000)
        |-> (rvfi_pc_wdata == (rvfi_rs1_rdata == rvfi_rs2_rdata
                               ? 32'(rvfi_pc_rdata + offset)
                               : rvfi_pc_rdata + 32'd4));
    endproperty

    property bne_correct;
        wire signed [31:0] offset = $signed({rvfi_insn[31], rvfi_insn[7],
                                              rvfi_insn[30:25], rvfi_insn[11:8], 1'b0});
        @(posedge clk)
        (is_valid && opcode == 7'b1100011 && funct3 == 3'b001)
        |-> (rvfi_pc_wdata == (rvfi_rs1_rdata != rvfi_rs2_rdata
                               ? 32'(rvfi_pc_rdata + offset)
                               : rvfi_pc_rdata + 32'd4));
    endproperty

    property blt_correct;
        wire signed [31:0] offset = $signed({rvfi_insn[31], rvfi_insn[7],
                                              rvfi_insn[30:25], rvfi_insn[11:8], 1'b0});
        @(posedge clk)
        (is_valid && opcode == 7'b1100011 && funct3 == 3'b100)
        |-> (rvfi_pc_wdata == (rs1_s < rs2_s
                               ? 32'(rvfi_pc_rdata + offset)
                               : rvfi_pc_rdata + 32'd4));
    endproperty

    property bge_correct;
        wire signed [31:0] offset = $signed({rvfi_insn[31], rvfi_insn[7],
                                              rvfi_insn[30:25], rvfi_insn[11:8], 1'b0});
        @(posedge clk)
        (is_valid && opcode == 7'b1100011 && funct3 == 3'b101)
        |-> (rvfi_pc_wdata == (rs1_s >= rs2_s
                               ? 32'(rvfi_pc_rdata + offset)
                               : rvfi_pc_rdata + 32'd4));
    endproperty

    property bltu_correct;
        wire signed [31:0] offset = $signed({rvfi_insn[31], rvfi_insn[7],
                                              rvfi_insn[30:25], rvfi_insn[11:8], 1'b0});
        @(posedge clk)
        (is_valid && opcode == 7'b1100011 && funct3 == 3'b110)
        |-> (rvfi_pc_wdata == (rvfi_rs1_rdata < rvfi_rs2_rdata
                               ? 32'(rvfi_pc_rdata + offset)
                               : rvfi_pc_rdata + 32'd4));
    endproperty

    property bgeu_correct;
        wire signed [31:0] offset = $signed({rvfi_insn[31], rvfi_insn[7],
                                              rvfi_insn[30:25], rvfi_insn[11:8], 1'b0});
        @(posedge clk)
        (is_valid && opcode == 7'b1100011 && funct3 == 3'b111)
        |-> (rvfi_pc_wdata == (rvfi_rs1_rdata >= rvfi_rs2_rdata
                               ? 32'(rvfi_pc_rdata + offset)
                               : rvfi_pc_rdata + 32'd4));
    endproperty

    property lw_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0000011 && funct3 == 3'b010)
        |-> (rvfi_rd_wdata == rvfi_mem_rdata &&
             rvfi_mem_addr == 32'(rvfi_rs1_rdata + $signed(rvfi_insn[31:20])) &&
             rvfi_mem_rmask == 4'b1111);
    endproperty

    property sw_correct;
        @(posedge clk)
        (is_valid && opcode == 7'b0100011 && funct3 == 3'b010)
        |-> (rvfi_mem_wdata == rvfi_rs2_rdata &&
             rvfi_mem_addr == 32'(rvfi_rs1_rdata +
                 $signed({rvfi_insn[31:25], rvfi_insn[11:7]})) &&
             rvfi_mem_wmask == 4'b1111);
    endproperty

    property lb_correct;
        wire signed [11:0] imm12 = rvfi_insn[31:20];
        wire [1:0] byte_sel = (rvfi_rs1_rdata + 32'(imm12))[1:0];
        wire [7:0] raw_byte = rvfi_mem_rdata >> (byte_sel * 8);
        @(posedge clk)
        (is_valid && opcode == 7'b0000011 && funct3 == 3'b000)
        |-> (rvfi_rd_wdata == 32'($signed(raw_byte)));
    endproperty

    assert property (rd_zero_never_written);
    assert property (add_correct);
    assert property (sub_correct);
    assert property (sll_correct);
    assert property (slt_correct);
    assert property (sltu_correct);
    assert property (xor_correct);
    assert property (srl_correct);
    assert property (sra_correct);
    assert property (or_correct);
    assert property (and_correct);
    assert property (addi_correct);
    assert property (slli_correct);
    assert property (srli_correct);
    assert property (srai_correct);
    assert property (lui_correct);
    assert property (auipc_correct);
    assert property (jal_correct);
    assert property (jalr_correct);
    assert property (beq_correct);
    assert property (bne_correct);
    assert property (blt_correct);
    assert property (bge_correct);
    assert property (bltu_correct);
    assert property (bgeu_correct);
    assert property (lw_correct);
    assert property (sw_correct);
    assert property (lb_correct);

endmodule
