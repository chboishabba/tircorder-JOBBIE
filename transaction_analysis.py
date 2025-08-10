"""Tools for analysing flows of Transaction objects."""
from __future__ import annotations

from typing import Iterable, List, Dict, Set, Any

import networkx as nx
from networkx.algorithms import community

from integrations.banking.base import Transaction


def build_transaction_graph(transactions: Iterable[Transaction]) -> nx.DiGraph:
    """Build a directed graph where nodes are accounts and edges store transactions.

    Each transaction creates an edge from ``source_account`` to ``destination_account``.
    Multiple transactions between the same accounts are aggregated on the same edge
    with a ``transactions`` attribute holding the underlying ``Transaction`` objects
    and a ``weight`` attribute summing their amounts.
    """
    graph: nx.DiGraph = nx.DiGraph()
    for tx in transactions:
        if not tx.destination_account:
            continue
        graph.add_edge(tx.source_account, tx.destination_account)
        edge = graph[tx.source_account][tx.destination_account]
        edge.setdefault("transactions", []).append(tx)
        edge["weight"] = edge.get("weight", 0) + tx.amount
    return graph


def find_transaction_cycles(graph: nx.DiGraph) -> List[List[Transaction]]:
    """Return cycles of transactions using Johnson's algorithm.

    The underlying implementation leverages :func:`networkx.simple_cycles` which uses
    Johnson's algorithm under the hood.  Each returned cycle is represented as a list
    of ``Transaction`` objects in traversal order.
    """
    cycles: List[List[Transaction]] = []
    for node_cycle in nx.simple_cycles(graph):
        tx_cycle: List[Transaction] = []
        for i in range(len(node_cycle)):
            src = node_cycle[i]
            dst = node_cycle[(i + 1) % len(node_cycle)]
            tx_cycle.extend(graph[src][dst]["transactions"])
        cycles.append(tx_cycle)
    return cycles


def detect_transaction_communities(graph: nx.DiGraph) -> List[Set[str]]:
    """Detect communities of tightly connected accounts using Louvain method."""
    if graph.number_of_nodes() == 0:
        return []
    undirected = graph.to_undirected()
    try:
        return list(community.louvain_communities(undirected, weight="weight"))
    except Exception:  # pragma: no cover - fallback for older networkx
        return [set(c) for c in community.greedy_modularity_communities(undirected, weight="weight")]


def find_suspicious_cycles(transactions: Iterable[Transaction]) -> Dict[str, Any]:
    """Analyse transactions and return cycles and communities.

    Parameters
    ----------
    transactions:
        Iterable of :class:`Transaction` objects.

    Returns
    -------
    dict
        Dictionary with keys ``graph``, ``cycles`` and ``communities``.
    """
    graph = build_transaction_graph(transactions)
    cycles = find_transaction_cycles(graph)
    communities = detect_transaction_communities(graph)
    return {"graph": graph, "cycles": cycles, "communities": communities}
