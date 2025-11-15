"""
Simplified BDD implementation for netlist synthesis.

This module provides a lightweight BDD implementation focused on
BDD-to-gate conversion. The main purpose is synthesis, not BDD manipulation.

For production use with optimization, install and use the 'dd' package:
    pip install dd
    from dd.autoref import BDD  # Optimized with variable reordering
"""

from __future__ import annotations
from typing import Dict, Tuple, Set, List, Optional


class BDDNode:
    """
    BDD node representing: if var then high else low.

    Terminal nodes have var=-1 and represent constants 0 or 1.
    """

    def __init__(self, var: int, low: Optional['BDDNode'], high: Optional['BDDNode'], node_id: int):
        self.var = var          # Variable index (-1 for terminals)
        self.low = low          # Low (else) child
        self.high = high        # High (then) child
        self.id = node_id       # Unique node ID

    def is_terminal(self) -> bool:
        """Check if this is a terminal (constant) node."""
        return self.var == -1

    def __repr__(self) -> str:
        if self.is_terminal():
            return f"Terminal({self.id})"
        return f"Node(id={self.id}, var=x{self.var}, low={self.low.id}, high={self.high.id})"


class BDD:
    """
    Binary Decision Diagram manager.

    Maintains canonical BDD representation with unique table and reduction.
    """

    def __init__(self, num_vars: int):
        """Initialize BDD manager for given number of variables."""
        self.num_vars = num_vars
        self.next_id = 2  # 0, 1 reserved for terminal nodes

        # Terminal nodes: constant 0 and 1
        self.zero = BDDNode(-1, None, None, 0)
        self.one = BDDNode(-1, None, None, 1)

        # Unique table: (var, low_id, high_id) -> BDDNode
        # Ensures canonical representation
        self.unique_table: Dict[Tuple[int, int, int], BDDNode] = {}

        # All nodes for traversal
        self.all_nodes: Dict[int, BDDNode] = {
            0: self.zero,
            1: self.one
        }

    def make_node(self, var: int, low: BDDNode, high: BDDNode) -> BDDNode:
        """
        Create or retrieve canonical BDD node.

        Applies reduction rule: if low == high, return low.
        Uses unique table to share isomorphic subgraphs.
        """
        # Reduction: eliminate redundant test
        if low.id == high.id:
            return low

        # Check unique table for existing node
        key = (var, low.id, high.id)
        if key in self.unique_table:
            return self.unique_table[key]

        # Create new canonical node
        node = BDDNode(var, low, high, self.next_id)
        self.next_id += 1
        self.unique_table[key] = node
        self.all_nodes[node.id] = node
        return node

    def build_from_truth_table(self, truth_table: List[int], var_names: List[str]) -> BDDNode:
        """
        Build BDD from truth table using Shannon expansion.

        Args:
            truth_table: List of output values (0 or 1) for each input combination
            var_names: Variable names (for reference)

        Returns:
            Root BDD node
        """
        if len(truth_table) != 2 ** self.num_vars:
            raise ValueError(
                f"Truth table size {len(truth_table)} != 2^{self.num_vars}"
            )

        return self._shannon_expand(truth_table, 0, len(truth_table), 0)

    def _shannon_expand(
        self,
        truth_table: List[int],
        start: int,
        end: int,
        var: int
    ) -> BDDNode:
        """
        Recursively build BDD using Shannon decomposition.

        Shannon expansion: f = var' * f_low + var * f_high
        where f_low is f with var=0 and f_high is f with var=1.
        """
        # Base case: check if function is constant
        values = truth_table[start:end]
        if all(v == 0 for v in values):
            return self.zero
        if all(v == 1 for v in values):
            return self.one

        # Shouldn't happen if truth table is correct size
        if var >= self.num_vars:
            return self.one if truth_table[start] == 1 else self.zero

        # Shannon decomposition on current variable
        mid = start + (end - start) // 2

        # f_low: function when var=0
        f_low = self._shannon_expand(truth_table, start, mid, var + 1)

        # f_high: function when var=1
        f_high = self._shannon_expand(truth_table, mid, end, var + 1)

        # Create node (with reduction via make_node)
        return self.make_node(var, f_low, f_high)

    def build_from_minterm_spec(
        self,
        n_inputs: int,
        on_set: Set[int],
        dc_set: Set[int]
    ) -> BDDNode:
        """
        Build BDD from minterm specification.

        Args:
            n_inputs: Number of input variables
            on_set: Set of ON minterms (where function = 1)
            dc_set: Set of don't-care minterms

        Returns:
            Root BDD node (don't-cares treated as 0)
        """
        # Convert to truth table (DC treated as 0 for canonical form)
        truth_table = [
            1 if i in on_set else 0
            for i in range(2 ** n_inputs)
        ]

        var_names = [f"x{i}" for i in range(n_inputs)]
        return self.build_from_truth_table(truth_table, var_names)

    def get_node_count(self) -> int:
        """Get total number of nodes (including terminals)."""
        return len(self.all_nodes)

    def get_non_terminal_count(self) -> int:
        """Get number of internal (non-terminal) nodes."""
        return sum(1 for n in self.all_nodes.values() if not n.is_terminal())

    def print_bdd(self, root: BDDNode, indent: int = 0):
        """Print BDD structure (for debugging)."""
        if root.is_terminal():
            print("  " * indent + f"Terminal({root.id})")
            return

        print("  " * indent + f"Node {root.id}: x{root.var}")
        print("  " * indent + "  LOW:")
        self.print_bdd(root.low, indent + 2)
        print("  " * indent + "  HIGH:")
        self.print_bdd(root.high, indent + 2)


def example_usage():
    """Example: Build BDD for AND gate."""
    print("Example: f = x0 AND x1")
    print()

    bdd = BDD(num_vars=2)

    # Truth table for AND: [0, 0, 0, 1]
    truth_table = [0, 0, 0, 1]
    var_names = ["x0", "x1"]

    root = bdd.build_from_truth_table(truth_table, var_names)

    print("BDD structure:")
    bdd.print_bdd(root)
    print()
    print(f"Total nodes: {bdd.get_node_count()}")
    print(f"Non-terminal nodes: {bdd.get_non_terminal_count()}")


if __name__ == "__main__":
    example_usage()
