# ================================================================
# HIERARCHY EXPLORER
# ================================================================

class HierarchyExplorer:

    def __init__(self):

        self.hierarchy = {}

    # ============================================================
    # REGISTER NODE
    # ============================================================

    def register(

        self,

        parent,

        child
    ):

        if parent not in self.hierarchy:

            self.hierarchy[parent] = []

        self.hierarchy[parent].append(child)

    # ============================================================
    # GET CHILDREN
    # ============================================================

    def get_children(self, parent):

        return self.hierarchy.get(parent, [])

    # ============================================================
    # EXPORT TREE
    # ============================================================

    def export(self):

        return self.hierarchy