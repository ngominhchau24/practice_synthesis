"""
SystemVerilog code generation from gate-level netlist.

Generates:
1. Structural SystemVerilog module from netlist (DUT)
2. Behavioral golden model for reference
3. Testbench with random stimulus and co-simulation
"""

from __future__ import annotations
from typing import List, TextIO

# Handle both module import and direct execution
try:
    from lab3.netlist import Netlist
    from lab3.ite_table import Gate, GateType
except ModuleNotFoundError:
    from netlist import Netlist
    from ite_table import Gate, GateType


class VerilogGenerator:
    """Generates SystemVerilog code from netlist."""

    def __init__(self, netlist: Netlist, module_name: str = "circuit", output_name: str = "out",
                 testbench_name: str = None):
        """Initialize generator.

        Args:
            netlist: Gate-level netlist
            module_name: Name for the SystemVerilog module (DUT)
            output_name: Name for the output port (default: "out")
            testbench_name: Name for the testbench module (default: "{module_name}_tb")
        """
        self.netlist = netlist
        self.module_name = module_name
        self.output_name = output_name
        self.testbench_name = testbench_name if testbench_name else f"{module_name}_tb"

    def generate_module(self, filename: str):
        """Generate SystemVerilog module file.

        Args:
            filename: Output .sv file path
        """
        with open(filename, 'w') as f:
            self._write_module_header(f)
            self._write_wire_declarations(f)
            self._write_gate_instances(f)
            self._write_module_footer(f)

        print(f"Generated SystemVerilog module: {filename}")

    def _write_module_header(self, f: TextIO):
        """Write module header with ports."""
        f.write(f"// Generated SystemVerilog module from BDD netlist\n")
        f.write(f"// Inputs: {', '.join(self.netlist.var_names)}\n")
        f.write(f"// Gates: {len(self.netlist.gates)}\n\n")

        f.write(f"module {self.module_name} (\n")

        # Input ports
        for i, var in enumerate(self.netlist.var_names):
            f.write(f"    input  logic {var},\n")

        # Output port
        f.write(f"    output logic {self.output_name}\n")
        f.write(");\n\n")

    def _write_wire_declarations(self, f: TextIO):
        """Write internal wire declarations."""
        # Collect all internal wires (n0, n1, n2, ...)
        wires = set()
        for gate in self.netlist.gates:
            # Output wire
            if gate.output.startswith('n'):
                wires.add(gate.output)
            # Input wires (excluding primary inputs and constants)
            for inp in gate.inputs:
                if inp.startswith('n'):
                    wires.add(inp)

        if wires:
            f.write("    // Internal wires\n")
            for wire in sorted(wires):
                f.write(f"    logic {wire};\n")
            f.write("\n")

        # Assign constants if used
        has_const_0 = any("1'b0" in gate.inputs for gate in self.netlist.gates)
        has_const_1 = any("1'b1" in gate.inputs for gate in self.netlist.gates)

        if has_const_0 or has_const_1:
            f.write("    // Constants\n")
        if has_const_0:
            f.write("    logic const_0 = 1'b0;\n")
        if has_const_1:
            f.write("    logic const_1 = 1'b1;\n")
        if has_const_0 or has_const_1:
            f.write("\n")

    def _write_gate_instances(self, f: TextIO):
        """Write gate instances using standard cell primitives."""
        f.write("    // Gate instances (standard cells)\n")

        self.mux_wire_counter = 0  # Counter for MUX decomposition wires

        for i, gate in enumerate(self.netlist.gates):
            self._write_gate_instance(f, gate, i)

        f.write("\n")

    def _write_gate_instance(self, f: TextIO, gate: Gate, index: int):
        """Write a single gate instance using standard cell primitives.

        Args:
            f: File handle
            gate: Gate to instantiate
            index: Gate index for unique naming
        """
        # Replace constants with signal names
        inputs = []
        for inp in gate.inputs:
            if inp == "1'b0":
                inputs.append("const_0")
            elif inp == "1'b1":
                inputs.append("const_1")
            else:
                inputs.append(inp)

        # Use Verilog standard cell primitives
        if gate.gate_type == GateType.BUFFER:
            f.write(f"    buf g{index} ({gate.output}, {inputs[0]});\n")

        elif gate.gate_type == GateType.NOT:
            f.write(f"    not g{index} ({gate.output}, {inputs[0]});\n")

        elif gate.gate_type == GateType.AND:
            f.write(f"    and g{index} ({gate.output}, {inputs[0]}, {inputs[1]});\n")

        elif gate.gate_type == GateType.OR:
            f.write(f"    or g{index} ({gate.output}, {inputs[0]}, {inputs[1]});\n")

        elif gate.gate_type == GateType.NAND:
            f.write(f"    nand g{index} ({gate.output}, {inputs[0]}, {inputs[1]});\n")

        elif gate.gate_type == GateType.NOR:
            f.write(f"    nor g{index} ({gate.output}, {inputs[0]}, {inputs[1]});\n")

        elif gate.gate_type == GateType.XOR:
            f.write(f"    xor g{index} ({gate.output}, {inputs[0]}, {inputs[1]});\n")

        elif gate.gate_type == GateType.XNOR:
            f.write(f"    xnor g{index} ({gate.output}, {inputs[0]}, {inputs[1]});\n")

        elif gate.gate_type == GateType.GT:
            # GT: f > g = f·ḡ = AND(f, NOT(g))
            # Decompose into: NOT + AND
            not_wire = f"gt{index}_not"
            f.write(f"    wire {not_wire};\n")
            f.write(f"    not g{index}_0 ({not_wire}, {inputs[1]});\n")
            f.write(f"    and g{index}_1 ({gate.output}, {inputs[0]}, {not_wire});\n")

        elif gate.gate_type == GateType.LT:
            # LT: f < g = f̄·g = AND(NOT(f), g)
            # Decompose into: NOT + AND
            not_wire = f"lt{index}_not"
            f.write(f"    wire {not_wire};\n")
            f.write(f"    not g{index}_0 ({not_wire}, {inputs[0]});\n")
            f.write(f"    and g{index}_1 ({gate.output}, {not_wire}, {inputs[1]});\n")

        elif gate.gate_type == GateType.GTE:
            # GTE: f ≥ g = f + ḡ = OR(f, NOT(g))
            # Decompose into: NOT + OR
            not_wire = f"gte{index}_not"
            f.write(f"    wire {not_wire};\n")
            f.write(f"    not g{index}_0 ({not_wire}, {inputs[1]});\n")
            f.write(f"    or g{index}_1 ({gate.output}, {inputs[0]}, {not_wire});\n")

        elif gate.gate_type == GateType.LTE:
            # LTE: f ≤ g = f̄ + g = OR(NOT(f), g)
            # Decompose into: NOT + OR
            not_wire = f"lte{index}_not"
            f.write(f"    wire {not_wire};\n")
            f.write(f"    not g{index}_0 ({not_wire}, {inputs[0]});\n")
            f.write(f"    or g{index}_1 ({gate.output}, {not_wire}, {inputs[1]});\n")

        elif gate.gate_type == GateType.MUX:
            # Decompose MUX into standard cells
            # MUX: out = sel ? a : b
            # out = (sel & a) | (~sel & b)
            sel, a, b = inputs[0], inputs[1], inputs[2]

            # Generate intermediate wire names
            sel_n = f"mux{self.mux_wire_counter}_sel_n"
            sel_and_a = f"mux{self.mux_wire_counter}_and0"
            sel_n_and_b = f"mux{self.mux_wire_counter}_and1"
            self.mux_wire_counter += 1

            # Declare intermediate wires
            f.write(f"    wire {sel_n}, {sel_and_a}, {sel_n_and_b};\n")

            # Decompose: out = (sel & a) | (~sel & b)
            f.write(f"    not g{index}_0 ({sel_n}, {sel});\n")
            f.write(f"    and g{index}_1 ({sel_and_a}, {sel}, {a});\n")
            f.write(f"    and g{index}_2 ({sel_n_and_b}, {sel_n}, {b});\n")
            f.write(f"    or g{index}_3 ({gate.output}, {sel_and_a}, {sel_n_and_b});\n")

    def _write_module_footer(self, f: TextIO):
        """Write module footer."""
        f.write("endmodule\n")

    def generate_golden_model(self, filename: str, truth_table: List[int]):
        """Generate behavioral golden model from truth table.

        Args:
            filename: Output .v file path for golden model
            truth_table: Expected output for each input combination
        """
        with open(filename, 'w') as f:
            self._write_golden_header(f)
            self._write_golden_logic(f, truth_table)
            self._write_golden_footer(f)

        print(f"Generated golden model: {filename}")

    def _write_golden_header(self, f: TextIO):
        """Write golden model header."""
        f.write("// Behavioral golden model (reference implementation)\n")
        f.write(f"// Auto-generated from truth table\n\n")
        f.write("module ref_model (\n")

        # Input ports
        for i, var in enumerate(self.netlist.var_names):
            f.write(f"    input  {var},\n")

        # Output port
        f.write(f"    output {self.output_name}\n")
        f.write(");\n\n")

    def _write_golden_logic(self, f: TextIO, truth_table: List[int]):
        """Write behavioral logic using truth table.

        Uses a case statement for clarity and direct mapping from truth table.
        """
        num_inputs = self.netlist.num_inputs

        # Concatenate inputs for case statement
        input_concat = "{" + ", ".join(self.netlist.var_names) + "}"

        f.write("    // Behavioral implementation using truth table\n")
        f.write(f"    reg {self.output_name}_reg;\n\n")
        f.write("    always @(*) begin\n")
        f.write(f"        case ({input_concat})\n")

        # Generate case for each input combination
        for i in range(2 ** num_inputs):
            pattern = format(i, f'0{num_inputs}b')
            output_val = truth_table[i] if i < len(truth_table) else 0

            # Format: 3'b000: out_reg = 1'b0;
            f.write(f"            {num_inputs}'b{pattern}: {self.output_name}_reg = 1'b{output_val};\n")

        f.write("            default: {}_reg = 1'bx;\n".format(self.output_name))
        f.write("        endcase\n")
        f.write("    end\n\n")
        f.write(f"    assign {self.output_name} = {self.output_name}_reg;\n\n")

    def _write_golden_footer(self, f: TextIO):
        """Write golden model footer."""
        f.write("endmodule\n")

    def generate_testbench(self, filename: str, num_random_tests: int = 1000):
        """Generate SystemVerilog testbench with random stimulus and co-simulation.

        Args:
            filename: Output testbench .sv file path
            num_random_tests: Number of random test vectors (default: 1000)
        """
        with open(filename, 'w') as f:
            self._write_tb_cosim_header(f)
            self._write_tb_cosim_signals(f)
            self._write_tb_cosim_instances(f)
            self._write_tb_cosim_test(f, num_random_tests)
            self._write_tb_cosim_footer(f)

        print(f"Generated co-simulation testbench: {filename}")

    def _write_tb_cosim_header(self, f: TextIO):
        """Write co-simulation testbench header."""
        f.write(f"// Co-simulation testbench for {self.module_name}\n")
        f.write(f"// Compares gate-level netlist (DUT) against behavioral golden model\n")
        f.write(f"// Uses random stimulus for verification\n\n")
        f.write(f"module {self.testbench_name};\n\n")

    def _write_tb_cosim_signals(self, f: TextIO):
        """Write co-simulation testbench signals."""
        f.write("    // Testbench signals\n")
        for var in self.netlist.var_names:
            f.write(f"    logic {var};\n")
        f.write(f"\n")
        f.write(f"    // DUT outputs\n")
        f.write(f"    logic dut_{self.output_name};\n")
        f.write(f"\n")
        f.write(f"    // Golden model outputs\n")
        f.write(f"    logic ref_{self.output_name};\n")
        f.write(f"\n")
        f.write("    int errors = 0;\n")
        f.write("    int test_count = 0;\n\n")

    def _write_tb_cosim_instances(self, f: TextIO):
        """Write DUT and golden model instantiations."""
        # DUT (netlist) instantiation
        f.write("    // DUT: Gate-level netlist\n")
        f.write(f"    {self.module_name} dut (\n")
        for var in self.netlist.var_names:
            f.write(f"        .{var}({var}),\n")
        f.write(f"        .{self.output_name}(dut_{self.output_name})\n")
        f.write("    );\n\n")

        # Golden model instantiation
        f.write("    // Golden Model: Behavioral reference\n")
        f.write("    ref_model u_ref (\n")
        for var in self.netlist.var_names:
            f.write(f"        .{var}({var}),\n")
        f.write(f"        .{self.output_name}(ref_{self.output_name})\n")
        f.write("    );\n\n")

    def _write_tb_cosim_test(self, f: TextIO, num_tests: int):
        """Write random stimulus test with co-simulation.

        Args:
            f: File handle
            num_tests: Number of random test vectors
        """
        num_inputs = self.netlist.num_inputs

        f.write("    // Test stimulus with random inputs\n")
        f.write("    initial begin\n")
        f.write("        $display(\"=\" * 70);\n")
        f.write("        $display(\"Co-Simulation Testbench\");\n")
        f.write("        $display(\"DUT: Gate-level netlist\");\n")
        f.write("        $display(\"REF: Behavioral golden model\");\n")
        f.write("        $display(\"=\" * 70);\n")
        f.write("        $display(\"\");\n\n")

        # Random seed
        f.write("        // Initialize random seed\n")
        f.write("        $display(\"Starting random verification with %0d test vectors...\", {});\n".format(num_tests))
        f.write("        $display(\"\");\n\n")

        # Test loop
        f.write(f"        repeat ({num_tests}) begin\n")
        f.write("            // Generate random inputs\n")

        for var in self.netlist.var_names:
            f.write(f"            {var} = $random;\n")

        f.write("            #10;  // Wait for propagation\n\n")

        f.write("            // Compare outputs\n")
        f.write("            test_count++;\n")
        f.write(f"            if (dut_{self.output_name} !== ref_{self.output_name}) begin\n")
        f.write("                errors++;\n")

        # Format error message
        input_display = "  ".join([f"%b" for _ in self.netlist.var_names])
        f.write(f"                $display(\"ERROR [Test %0d]: Mismatch!\", test_count);\n")
        f.write(f"                $display(\"  Inputs:  {input_display}\", {', '.join(self.netlist.var_names)});\n")
        f.write(f"                $display(\"  DUT out: %b\", dut_{self.output_name});\n")
        f.write(f"                $display(\"  REF out: %b\", ref_{self.output_name});\n")
        f.write("                $display(\"\");\n")
        f.write("            end\n")

        # Progress indicator (every 100 tests)
        f.write("            if (test_count % 100 == 0)\n")
        f.write("                $display(\"  Progress: %0d/%0d tests completed...\", test_count, {});\n".format(num_tests))

        f.write("        end\n\n")

        # Final report
        f.write("        $display(\"\");\n")
        f.write("        $display(\"=\" * 70);\n")
        f.write("        $display(\"Test Summary\");\n")
        f.write("        $display(\"=\" * 70);\n")
        f.write("        $display(\"Total tests: %0d\", test_count);\n")
        f.write("        $display(\"Passed:      %0d\", test_count - errors);\n")
        f.write("        $display(\"Failed:      %0d\", errors);\n")
        f.write("        $display(\"\");\n\n")

        f.write("        if (errors == 0) begin\n")
        f.write("            $display(\"*** VERIFICATION PASSED ***\");\n")
        f.write("            $display(\"DUT matches golden model on all test vectors!\");\n")
        f.write("        end else begin\n")
        f.write("            $display(\"*** VERIFICATION FAILED ***\");\n")
        f.write("            $display(\"%0d mismatches detected!\", errors);\n")
        f.write("        end\n")
        f.write("        $display(\"=\" * 70);\n\n")

        f.write("        $finish;\n")
        f.write("    end\n\n")

    def _write_tb_cosim_footer(self, f: TextIO):
        """Write co-simulation testbench footer."""
        f.write("endmodule\n")

    def _write_tb_test(self, f: TextIO, expected_outputs: List[int]):
        """Write test stimulus and checking.

        Args:
            f: File handle
            expected_outputs: Expected output for each input combination
        """
        f.write("    // Test stimulus\n")
        f.write("    initial begin\n")
        f.write("        $display(\"Starting exhaustive test...\");\n")
        f.write(f"        $display(\"Testing {2 ** self.netlist.num_inputs} input combinations\");\n")
        f.write("        $display(\"\");\n\n")

        # Header
        output_col_name = self.output_name if len(self.output_name) <= 3 else "out"
        header = f"        $display(\"  " + "  ".join(self.netlist.var_names) + f"  | {output_col_name} | exp | status\");\n"
        f.write(header)
        f.write("        $display(\"  " + "-" * (len(self.netlist.var_names) * 4 + 20) + "\");\n\n")

        # Test each combination
        num_inputs = self.netlist.num_inputs
        for i in range(2 ** num_inputs):
            # Generate input pattern
            pattern = format(i, f'0{num_inputs}b')

            # Set inputs
            f.write("        // Test case {}\n".format(i))
            for j, bit in enumerate(pattern):
                f.write(f"        {self.netlist.var_names[j]} = 1'b{bit};\n")

            # Expected output
            exp_out = expected_outputs[i] if i < len(expected_outputs) else 0
            f.write(f"        expected = 1'b{exp_out};\n")
            f.write("        #10;\n\n")

            # Check result
            f.write(f"        if ({self.output_name} !== expected) begin\n")
            f.write("            errors++;\n")

            # Format output display
            input_display = "  ".join([f"%b" for _ in range(num_inputs)])
            f.write(f"            $display(\"  {input_display}  |  %b  |  %b  | FAIL\", " +
                   ", ".join(self.netlist.var_names) + f", {self.output_name}, expected);\n")
            f.write("        end else begin\n")
            f.write(f"            $display(\"  {input_display}  |  %b  |  %b  | PASS\", " +
                   ", ".join(self.netlist.var_names) + f", {self.output_name}, expected);\n")
            f.write("        end\n\n")

        # Final report
        f.write("        $display(\"\");\n")
        f.write("        if (errors == 0)\n")
        f.write("            $display(\"*** TEST PASSED: All test cases passed! ***\");\n")
        f.write("        else\n")
        f.write("            $display(\"*** TEST FAILED: %0d errors detected ***\", errors);\n\n")

        f.write("        $finish;\n")
        f.write("    end\n\n")

    def _write_tb_footer(self, f: TextIO):
        """Write testbench footer."""
        f.write("endmodule\n")


def example_verilog():
    """Example: Generate Verilog for f = x0 AND x1."""
    try:
        from lab3.bdd import BDD
        from lab3.netlist import Netlist
    except ModuleNotFoundError:
        from bdd import BDD
        from netlist import Netlist

    print("Example: Generate SystemVerilog for f = x0 AND x1\n")

    # Build BDD
    bdd = BDD(num_vars=2)
    truth_table = [0, 0, 0, 1]
    var_names = ["x0", "x1"]
    root = bdd.build_from_truth_table(truth_table, var_names)

    # Generate netlist
    netlist = Netlist(num_inputs=2, var_names=var_names)
    netlist.build_from_bdd(bdd, root, output_name="out")

    # Generate Verilog
    vgen = VerilogGenerator(netlist, module_name="and_gate")
    vgen.generate_module("and_gate.sv")
    vgen.generate_testbench("and_gate_tb.sv", truth_table)


if __name__ == "__main__":
    example_verilog()
