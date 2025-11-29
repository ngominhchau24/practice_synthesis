#!/usr/bin/env python3
"""
Synthesis script for Makefile integration.

Generates BDD-based netlist with fixed filenames for simulation flow.
Files are generated in specific directories:
  - src/netlist.sv    : Gate-level netlist (DUT)
  - model/ref_model.v : Behavioral golden model
  - tb/testbench.sv   : Co-simulation testbench
"""

import sys
import os

# Add lab3 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lab3.bdd import BDD
from lab3.netlist import Netlist
from lab3.verilog_gen import VerilogGenerator
from lab1.truth_table import (
    parse_sum_of_minterms_file,
    build_outputs_from_minterm_indices,
)


def synthesize(spec_file, n_inputs, output_first_function_only=True):
    """
    Run BDD synthesis and generate fixed-name output files.

    Args:
        spec_file: Path to specification file
        n_inputs: Number of input variables
        output_first_function_only: Only synthesize first output (default: True)
    """
    print("=" * 70)
    print("BDD Synthesis for Simulation")
    print("=" * 70)
    print()

    # Parse specification
    print(f"Parsing: {spec_file}")
    spec = parse_sum_of_minterms_file(spec_file)
    inputs_bits, outputs_trits, out_names = build_outputs_from_minterm_indices(n_inputs, spec)

    input_names = [f"x{i}" for i in range(n_inputs)]

    print(f"  Inputs:  {n_inputs} variables: {', '.join(input_names)}")
    print(f"  Outputs: {len(out_names)} functions: {', '.join(out_names)}")
    print()

    # Process first output only (or all if specified)
    output_idx = 0
    output_name = out_names[output_idx]

    print(f"Synthesizing output: {output_name}")
    print("-" * 70)

    # Extract ON-set and DC-set
    on_set = set()
    dc_set = set()
    for i, out_trit in enumerate(outputs_trits):
        if output_idx < len(out_trit):
            val = out_trit[output_idx]
            if val == '1':
                on_set.add(i)
            elif val == '-':
                dc_set.add(i)

    print(f"  ON-set: {sorted(on_set)}")
    print(f"  DC-set: {sorted(dc_set)}")
    print()

    # Build BDD
    print("Building BDD...")
    bdd = BDD(num_vars=n_inputs)
    root = bdd.build_from_minterm_spec(n_inputs, on_set, dc_set)
    print(f"  BDD nodes: {bdd.get_node_count()} total, {bdd.get_non_terminal_count()} non-terminal")
    print()

    # Generate netlist
    print("Generating netlist...")
    netlist = Netlist(num_inputs=n_inputs, var_names=input_names)
    netlist.build_from_bdd(bdd, root, output_name="out")

    stats = netlist.get_stats()
    total_gates = sum(stats.values())
    print(f"  Total gates: {total_gates}")
    print()

    # Generate files with fixed names
    print("Generating output files...")

    # Determine paths relative to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    netlist_file = os.path.join(project_root, "src", "netlist.sv")
    model_file = os.path.join(project_root, "model", "ref_model.v")
    tb_file = os.path.join(project_root, "tb", "testbench.sv")

    vgen = VerilogGenerator(netlist, module_name="netlist", output_name="out",
                           testbench_name="testbench")

    # Generate netlist (DUT)
    vgen.generate_module(netlist_file)
    print(f"  ✓ Netlist:      {netlist_file}")

    # Generate golden model
    expected_outputs = [1 if i in on_set else 0 for i in range(2 ** n_inputs)]
    vgen.generate_golden_model(model_file, expected_outputs)
    print(f"  ✓ Golden model: {model_file}")

    # Generate testbench
    num_tests = 1000
    vgen.generate_testbench(tb_file, num_tests)
    print(f"  ✓ Testbench:    {tb_file} ({num_tests} random tests)")
    print()

    print("=" * 70)
    print("Synthesis Complete!")
    print("=" * 70)
    print()
    print("Generated files:")
    print(f"  DUT:       src/netlist.sv")
    print(f"  Reference: model/ref_model.v")
    print(f"  Testbench: tb/testbench.sv")
    print()
    print("Ready for simulation with 'make run'")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python3 synthesize.py <spec_file> <n_inputs>")
        print()
        print("Example:")
        print("  python3 synthesize.py ../lab3/test_spec.txt 3")
        sys.exit(1)

    spec_file = sys.argv[1]
    n_inputs = int(sys.argv[2])

    if not os.path.exists(spec_file):
        print(f"Error: Specification file '{spec_file}' not found")
        sys.exit(1)

    synthesize(spec_file, n_inputs)


if __name__ == "__main__":
    main()
