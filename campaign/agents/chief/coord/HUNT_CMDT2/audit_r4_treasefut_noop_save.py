#!/usr/bin/env python3
"""ROUND 4 AUDIT (HUNT_CMDT2): run campaign/scripts/HUNT_TREASFUT_round2.py verbatim,
EXCEPT save_sleeve is patched to a no-op so the reproduction writes nothing into
HUNT_TREASFUT's directory (charter: never modify other agents' dirs). All computation,
prints, gates and numbers are the original script's own."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")

import runpy
mod = runpy.run_path("/Users/daxu/software/world-trader/campaign/scripts/HUNT_TREASFUT_round2.py",
                     run_name="hunt_treasefut_r2_audit_module")
# patch BEFORE executing its __main__ body: re-exec main statements via the module globals
mod["save_sleeve"] = lambda name, net, meta_lines: print(f"  [audit-noop] would save {name}")

src = open("/Users/daxu/software/world-trader/campaign/scripts/HUNT_TREASFUT_round2.py").read()
body = src.split("if __name__ == '__main__':", 1)[1]
body = body.replace("\n    ", "\n")            # dedent one level
exec(compile(body, "HUNT_TREASFUT_round2.__main__", "exec"), mod)
