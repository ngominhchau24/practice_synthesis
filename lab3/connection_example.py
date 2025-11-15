"""
Example: How BDD Structure Determines Gate Connections

This demonstrates how parent-child relationships in the BDD
translate to wire connections in the gate-level netlist.
"""

try:
    from lab3.bdd import BDD
    from lab3.netlist import Netlist
except ModuleNotFoundError:
    from bdd import BDD
    from netlist import Netlist

print("=" * 70)
print("BDD-to-Netlist Connection Mapping Example")
print("=" * 70)
print()

# Example: f = x0 AND x1
# Truth table: [0, 0, 0, 1] for inputs [00, 01, 10, 11]
print("Function: f = x0 AND x1")
print("Truth table:")
print("  x0  x1  | f")
print("  -----------")
print("   0   0  | 0")
print("   0   1  | 0")
print("   1   0  | 0")
print("   1   1  | 1")
print()

# Build BDD
bdd = BDD(num_vars=2)
truth_table = [0, 0, 0, 1]
var_names = ["x0", "x1"]
root = bdd.build_from_truth_table(truth_table, var_names)

print("-" * 70)
print("STEP 1: BDD Structure (Parent-Child Relationships)")
print("-" * 70)
print()
print("BDD Tree:")
print()
print("         Node 3 (x0)")
print("         /         \\")
print("    [x0=0]         [x0=1]")
print("       /               \\")
print("   Terminal(0)      Node 2 (x1)")
print("                    /         \\")
print("               [x1=0]         [x1=1]")
print("                  /               \\")
print("            Terminal(0)       Terminal(1)")
print()

print("Node Details:")
print(f"  Root: {root}")
print(f"    - Variable: x{root.var}")
print(f"    - Low child (x{root.var}=0): {root.low}")
print(f"    - High child (x{root.var}=1): {root.high}")
if not root.high.is_terminal():
    print(f"\n  Node {root.high.id}: {root.high}")
    print(f"    - Variable: x{root.high.var}")
    print(f"    - Low child (x{root.high.var}=0): {root.high.low}")
    print(f"    - High child (x{root.high.var}=1): {root.high.high}")
print()

print("-" * 70)
print("STEP 2: Signal Map (BDD Node ID → Wire Name)")
print("-" * 70)
print()
print("Initial mapping (before gate generation):")
print("  Terminal 0 (node 0) → '1'b0'  (constant 0)")
print("  Terminal 1 (node 1) → '1'b1'  (constant 1)")
print()

# Generate netlist and show signal map
netlist = Netlist(num_inputs=2, var_names=var_names)
netlist.build_from_bdd(bdd, root, output_name="f")

print("After post-order traversal:")
for node_id in sorted(netlist.signal_map.keys()):
    signal = netlist.signal_map[node_id]
    if node_id == 0:
        print(f"  Node 0 (Terminal 0) → '{signal}'")
    elif node_id == 1:
        print(f"  Node 1 (Terminal 1) → '{signal}'")
    else:
        bdd_node = bdd.all_nodes[node_id]
        if bdd_node.is_terminal():
            print(f"  Node {node_id} (Terminal) → '{signal}'")
        else:
            print(f"  Node {node_id} (var=x{bdd_node.var}, low={bdd_node.low.id}, high={bdd_node.high.id}) → '{signal}'")
print()

print("-" * 70)
print("STEP 3: Gate Generation (Using Parent-Child Relationships)")
print("-" * 70)
print()
print("Post-order traversal (children before parents):")
print()

# Simulate the traversal order
print("Visit order:")
print("  1. Node 0 (Terminal 0) - already mapped to '1'b0'")
print("  2. Node 1 (Terminal 1) - already mapped to '1'b1'")

if not root.high.is_terminal():
    node2 = root.high
    low_sig = netlist.signal_map[node2.low.id]
    high_sig = netlist.signal_map[node2.high.id]
    var_sig = var_names[node2.var]
    out_sig = netlist.signal_map[node2.id]

    print(f"  3. Node {node2.id} (x{node2.var}):")
    print(f"     - Inputs come from children:")
    print(f"       • Variable: {var_sig} (primary input)")
    print(f"       • Low child (node {node2.low.id}): {low_sig}")
    print(f"       • High child (node {node2.high.id}): {high_sig}")
    print(f"     - Output: create new wire '{out_sig}'")
    print(f"     - Gate: {out_sig} = ITE({var_sig}, {high_sig}, {low_sig})")
    print(f"            = {var_sig} ? {high_sig} : {low_sig}")
    print()

low_sig = netlist.signal_map[root.low.id]
high_sig = netlist.signal_map[root.high.id]
var_sig = var_names[root.var]
out_sig = netlist.signal_map[root.id] if root.id in netlist.signal_map else "n_root"

print(f"  4. Node {root.id} (x{root.var}) - ROOT:")
print(f"     - Inputs come from children:")
print(f"       • Variable: {var_sig} (primary input)")
print(f"       • Low child (node {root.low.id}): {low_sig}")
print(f"       • High child (node {root.high.id}): {high_sig}")
print(f"     - Output: this becomes 'f' (primary output)")
print(f"     - Gate: f = ITE({var_sig}, {high_sig}, {low_sig})")
print(f"            = {var_sig} ? {high_sig} : {low_sig}")
print()

print("-" * 70)
print("STEP 4: Final Netlist (Gate Connections)")
print("-" * 70)
print()
netlist.print_netlist()

print()
print("-" * 70)
print("KEY INSIGHT: How Connections Are Determined")
print("-" * 70)
print()
print("1. Each BDD node knows its children (via .low and .high pointers)")
print("2. We maintain a 'signal_map': BDD_node_id → wire_name")
print("3. Post-order traversal ensures children are processed first")
print("4. When creating a gate for a node:")
print("   - INPUTS: Look up signal names of children from signal_map")
print("   - OUTPUT: Assign new wire name, store in signal_map")
print("5. Parent nodes later use these outputs as their inputs")
print()
print("The BDD structure IS the connection information!")
print("  Parent-child in BDD → Wire connections in netlist")
print()
