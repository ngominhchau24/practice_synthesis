// Behavioral golden model (reference implementation)
// Auto-generated from truth table

module ref_model (
    input  x0,
    input  x1,
    input  x2,
    output out
);

    // Behavioral implementation using truth table
    reg out_reg;

    always @(*) begin
        case ({x0, x1, x2})
            3'b000: out_reg = 1'b1;
            3'b001: out_reg = 1'b1;
            3'b010: out_reg = 1'b1;
            3'b011: out_reg = 1'b0;
            3'b100: out_reg = 1'b0;
            3'b101: out_reg = 1'b0;
            3'b110: out_reg = 1'b0;
            3'b111: out_reg = 1'b1;
            default: out_reg = 1'bx;
        endcase
    end

    assign out = out_reg;

endmodule
