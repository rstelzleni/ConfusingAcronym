from pxr import Usd, UsdGeom


def stringify_target_list(rel):
    return str([target.name for target in rel.GetTargets()])


def print_rel_targets(rel):
    print(f"{str(rel.GetName()):16} - {stringify_target_list(rel)}")


def print_relationships(prim):
    for rel in prim.GetRelationships():
        # UsdGeomScope has a proxyPrim relationship that we're not interested in
        if rel != UsdGeom.Scope(prim).GetProxyPrimRel():
            print_rel_targets(rel)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("filename", default="./zoo/root.usda", nargs="?")
    parser.add_argument("primPath", default="/Example", nargs="?")
    args = parser.parse_args()

    stage = Usd.Stage.Open(args.filename)
    print_relationships(stage.GetPrimAtPath(args.primPath))
