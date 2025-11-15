# How Gate Connections Are Determined from BDD

## The Core Concept

**The BDD's parent-child structure directly defines the gate connections.**

Each BDD node represents: `if (variable) then high else low`

This becomes a gate with:
- **Input 1**: The variable being tested
- **Input 2**: Signal from the `high` child
- **Input 3**: Signal from the `low` child
- **Output**: A new wire that parent nodes can use

## The Signal Map: The Key Data Structure

The `signal_map` dictionary tracks: **BDD Node ID → Wire Name**

```python
signal_map = {
    0: "1'b0",      # Terminal 0 → constant 0
    1: "1'b1",      # Terminal 1 → constant 1
    2: "n0",        # Internal node 2 → wire n0
    3: "n1",        # Internal node 3 → wire n1
    # ... etc
}
```

## Step-by-Step Example: f = x0 AND x1

### Step 1: BDD Structure (Parent-Child Relationships)

```
         Node 3 (x0)                    ┌─────────────────┐
         /         \                    │ Node 3: var=x0  │
    [x0=0]         [x0=1]               │ low → Node 0    │
       /               \                │ high → Node 2   │
   Node 0            Node 2 (x1)        └─────────────────┘
 (Terminal 0)        /         \                ↓
               [x1=0]         [x1=1]    ┌─────────────────┐
                  /               \     │ Node 2: var=x1  │
              Node 0           Node 1   │ low → Node 0    │
           (Terminal 0)    (Terminal 1) │ high → Node 1   │
                                        └─────────────────┘
```

### Step 2: Post-Order Traversal (Children Before Parents)

**Traversal order**: 0 → 1 → 2 → 3

```
Order 1-2: Process Terminal Nodes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Node 0 (Terminal 0): Already mapped to "1'b0"
Node 1 (Terminal 1): Already mapped to "1'b1"

signal_map = {0: "1'b0", 1: "1'b1"}
```

```
Order 3: Process Node 2 (x1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BDD Node: var=x1, low=Node0, high=Node1

INPUTS (from children):
  - variable: x1 (primary input)
  - low child (Node 0) → signal_map[0] = "1'b0"
  - high child (Node 1) → signal_map[1] = "1'b1"

OUTPUT (new wire):
  - Create wire: "n0"
  - Store: signal_map[2] = "n0"

GATE CREATED:
  n0 = MUX(x1, 1'b1, 1'b0)
      ↑     ↑    ↑     ↑
      │     │    │     └─ low child signal
      │     │    └─────── high child signal
      │     └──────────── variable tested
      └────────────────── output wire

signal_map = {0: "1'b0", 1: "1'b1", 2: "n0"}
```

```
Order 4: Process Node 3 (x0) - ROOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BDD Node: var=x0, low=Node0, high=Node2

INPUTS (from children):
  - variable: x0 (primary input)
  - low child (Node 0) → signal_map[0] = "1'b0"
  - high child (Node 2) → signal_map[2] = "n0"  ← Uses previous output!

OUTPUT (new wire):
  - Create wire: "n1"
  - Store: signal_map[3] = "n1"

GATE CREATED:
  n1 = MUX(x0, n0, 1'b0)
      ↑     ↑   ↑    ↑
      │     │   │    └─ low child signal
      │     │   └────── high child signal (from previous gate!)
      │     └────────── variable tested
      └──────────────── output wire

signal_map = {0: "1'b0", 1: "1'b1", 2: "n0", 3: "n1"}
```

### Step 3: Final Connection to Output

```
The root node's output (n1) is connected to primary output 'f':
  f = BUF(n1)
```

### Step 4: Complete Netlist with Connections

```
Gate 1: n0 = MUX(x1, 1'b1, 1'b0)
        │          │    │     │
        │          │    │     └─────┐
        │          │    └───────────│─────┐
        │          └────────────────│─────│───┐
        │                           │     │   │
Gate 2: n1 = MUX(x0, n0, 1'b0) ←───┘     │   │
        │          │    │                 │   │
        │          │    └─────────────────┘   │
        │          └──────────────────────────┘
        │
Gate 3: f = BUF(n1) ←──────────────────────┘
```

## The Algorithm in Code

```python
def _traverse_and_build(self, node: BDDNode, visited: Set[int]):
    # 1. Process children first (post-order)
    self._traverse_and_build(node.low, visited)
    self._traverse_and_build(node.high, visited)

    # 2. Get signal names for children (they're already processed!)
    low_signal = self.signal_map[node.low.id]    # ← Connection!
    high_signal = self.signal_map[node.high.id]  # ← Connection!
    var_signal = self.var_names[node.var]

    # 3. Create new output wire for this node
    node_output = self.get_wire_name()  # e.g., "n0"
    self.signal_map[node.id] = node_output

    # 4. Create gate with connections
    gate = Gate(
        inputs=[var_signal, high_signal, low_signal],  # ← Inputs from map
        output=node_output                              # ← Output for parents
    )

    # 5. When parent nodes process, they'll use node_output as input
```

## Key Insights

### 1. **Parent-Child = Wire Connections**
   - BDD: Node 3 → child Node 2
   - Netlist: Gate for Node 3 has input from Gate for Node 2

### 2. **Post-Order Traversal is Essential**
   - Children must be processed before parents
   - Ensures signal names exist when parent needs them
   - Bottom-up: terminals → internal nodes → root

### 3. **Signal Map is the "Glue"**
   - Maps BDD structure to wire names
   - Allows parent nodes to find child signals
   - Maintains the connection information

### 4. **No Ambiguity**
   - Each BDD node has exactly one output wire
   - Each BDD node knows its exact children
   - Connections are deterministic and unique

## Example: Tracing a Connection

Let's trace how Node 3's gate gets Node 2's output as input:

```
1. Process Node 2:
   - Creates gate with output "n0"
   - Stores: signal_map[2] = "n0"

2. Process Node 3:
   - Node 3's BDD structure says: high child = Node 2
   - Look up signal: signal_map[2] = "n0"
   - Create gate: MUX(x0, n0, ...)
                          ↑
                          └─ This is the connection!
```

**The BDD pointer `node3.high → node2` becomes the wire connection `n1 input ← n0 output`**

## Verification: How to Check Connections

Given a BDD node's gate, you can verify its inputs:

```python
bdd_node = Node(id=3, var=0, low=Node0, high=Node2)

# The gate for this node has inputs from:
var_input = var_names[bdd_node.var]           # "x0"
low_input = signal_map[bdd_node.low.id]       # signal_map[0] = "1'b0"
high_input = signal_map[bdd_node.high.id]     # signal_map[2] = "n0"

# Gate: output = MUX(var_input, high_input, low_input)
#              = MUX(x0, n0, 1'b0)
```

## Summary

**Q: How do we know where to connect gates?**

**A: The BDD structure tells us!**

- **Each BDD node** = **One gate**
- **BDD parent-child pointers** = **Wire connections**
- **Signal map** = **Name resolution (node ID → wire name)**
- **Post-order traversal** = **Ensures children processed before parents**

**The netlist is just the BDD structure "flattened" into gates and wires, with the same connectivity.**
