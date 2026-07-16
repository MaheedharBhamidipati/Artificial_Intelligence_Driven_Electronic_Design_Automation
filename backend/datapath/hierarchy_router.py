# ================================================================
# HIERARCHY ROUTER
# ================================================================

class HierarchyRouter:

    def __init__(self):

        self.parent_map = {}

    # ============================================================
    # REGISTER HIERARCHY
    # ============================================================

    def register(

        self,

        child,

        parent
    ):

        self.parent_map[child] = parent

    # ============================================================
    # GET PARENT
    # ============================================================

    def get_parent(self, child):

        return self.parent_map.get(child)

    # ============================================================
    # HAS PARENT
    # ============================================================

    def has_parent(self, child):

        return child in self.parent_map