class EGraph:
    """Hash-consed e-graph with union-find and congruence rebuilding."""

    def __init__(self):
        self.parent = []
        self.nodes = []
        self.memo = {}
        self.classes = {}
        self.constant = {}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def add(self, op, children=(), value=None, depth=0):
        children = tuple(self.find(c) for c in children)
        key = (op, children, value, depth)
        if key in self.memo:
            return self.find(self.memo[key])
        c = len(self.parent)
        self.parent.append(c)
        self.nodes.append(
            {"id": c, "op": op, "children": list(children), "value": value, "depth": depth}
        )
        self.classes[c] = [c]
        self.memo[key] = c
        if op == "const":
            self.constant[c] = value
        return c

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        self.parent[b] = a
        self.classes.setdefault(a, []).extend(self.classes.pop(b, [b]))
        if b in self.constant:
            self.constant.setdefault(a, self.constant.pop(b))
        return True

    def rebuild(self):
        changed = True
        while changed:
            changed = False
            self.memo = {}
            for node in self.nodes:
                node["children"] = [self.find(c) for c in node["children"]]
                key = (node["op"], tuple(node["children"]), node["value"], node["depth"])
                if key in self.memo:
                    changed |= self.union(node["id"], self.memo[key])
                else:
                    self.memo[key] = node["id"]
        return self

    def import_peg(self, nodes):
        ids = {}
        for n in nodes:
            # Imported PEG node identifiers must remain distinct until their edges
            # are wired; hash-consing empty placeholders would merge unlike nodes.
            idx = len(self.parent)
            ids[n["id"]] = idx
            self.parent.append(idx)
            self.nodes.append(
                {
                    "id": idx,
                    "op": n["op"],
                    "children": [],
                    "value": n["value"],
                    "depth": n["depth"],
                }
            )
            self.classes[idx] = [idx]
            if n["op"] == "const":
                self.constant[idx] = n["value"]
        for n in nodes:
            self.nodes[ids[n["id"]]]["children"] = [ids[c] for c in n["children"]]
        self.rebuild()
        return ids
