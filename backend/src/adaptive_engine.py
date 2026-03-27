import json
import os
import re
from typing import Dict, List, Optional, Tuple

import networkx as nx


def load_topic_graph():
    base_dir = os.path.dirname(__file__)

    file_path = os.path.join(
        base_dir,
        "data",
        "skill_graph.json",
    )

    # Use utf-8-sig to tolerate Windows UTF-8 BOM.
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            raw = json.load(f)
    except json.JSONDecodeError:
        # If the file is being edited/saved or contains invalid JSON, don't crash the app.
        raw = {}

    # Normalize `skill_graph.json` (topic -> [prereqs]) into:
    # { "Topic": { "prerequisites": [...], "link": None } }
    topic_data = {}
    for topic, details in (raw or {}).items():
        if isinstance(details, dict):
            topic_data[topic] = {
                "prerequisites": details.get("prerequisites", []),
                "link": details.get("link"),
            }
        elif isinstance(details, list):
            topic_data[topic] = {"prerequisites": details, "link": None}
        else:
            topic_data[topic] = {"prerequisites": [], "link": None}

    G = nx.DiGraph()

    for topic, details in topic_data.items():
        prereqs = details.get(
            "prerequisites",
            [],
        )

        G.add_node(
            topic,
            link=details.get("link"),
        )

        for prereq in prereqs:
            G.add_edge(
                prereq,
                topic,
            )

    return G, topic_data


def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9.+# ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _build_node_index(graph: nx.DiGraph) -> Dict[str, str]:
    """
    Map normalized node label -> canonical node label.
    """
    idx: Dict[str, str] = {}
    for node in graph.nodes:
        idx[_norm(str(node))] = node
    return idx


def _canonicalize(name: str, node_index: Dict[str, str]) -> Optional[str]:
    """
    Convert incoming skill/topic name to a graph node when possible.
    """
    n = _norm(name)
    if not n:
        return None

    # 1) Exact normalized match
    if n in node_index:
        return node_index[n]

    # 2) A few high-value aliases (MVP)
    alias_map = {
        _norm("Automated Testing"): _norm("Test Automation"),
        _norm("Unit Testing"): _norm("Unit Testing"),
        _norm("Integration Testing"): _norm("Integration Testing"),
        _norm("Object-Oriented Design"): _norm("Design Patterns"),
        _norm("OOP"): _norm("Object-Oriented Programming"),
        _norm("DSA"): _norm("Data Structures"),
        _norm("REST API"): _norm("REST APIs"),
        _norm("Spring Framework"): _norm("Spring"),
    }
    aliased = alias_map.get(n)
    if aliased and aliased in node_index:
        return node_index[aliased]

    # 3) Substring match fallback
    for norm_node, canonical in node_index.items():
        if n in norm_node or norm_node in n:
            return canonical

    return None


def generate_learning_path(
    graph,
    topic_data,
    missing_skills,
    candidate_skills,
):
    node_index = _build_node_index(graph)

    known_skills = set()
    for s in candidate_skills:
        if isinstance(s, dict) and "skill_name" in s:
            canon = _canonicalize(s["skill_name"], node_index)
            if canon:
                known_skills.add(canon)

    required_topics = set()

    for skill in missing_skills:
        canon_skill = _canonicalize(skill, node_index)
        if not canon_skill or canon_skill not in graph:
            continue

        prereqs = nx.ancestors(
            graph,
            canon_skill,
        )

        required_topics.update(
            prereqs,
        )

        required_topics.add(
            canon_skill,
        )

    remaining_topics = [
        t
        for t in required_topics
        if t not in known_skills
    ]

    subgraph = graph.subgraph(
        remaining_topics,
    )

    ordered_topics = list(
        nx.topological_sort(
            subgraph,
        )
    )

    learning_path = []

    step = 1

    for topic in ordered_topics:
        learning_path.append(
            {
                "step": step,
                "skill": topic,
                "link": topic_data[topic][
                    "link"
                ],
            }
        )

        step += 1

    # Build a graph payload for UI rendering (nodes + edges).
    ordered_set = set(ordered_topics)
    edges = []
    for v in ordered_topics:
        prereqs = (topic_data.get(v) or {}).get("prerequisites", []) or []
        for u in prereqs:
            if u in ordered_set:
                edges.append({"source": u, "target": v})

    nodes = []
    for item in learning_path:
        skill = item["skill"]
        nodes.append(
            {
                "id": skill,
                "label": skill,
                "step": item["step"],
                "link": item.get("link"),
            }
        )

    learning_graph = {"nodes": nodes, "edges": edges}

    return learning_path, learning_graph

