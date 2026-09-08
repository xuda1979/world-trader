"""Team-level pytest config. Adds project root to sys.path so team tests can import
campaign/bt and campaign/team libs, and defines the ROOT + TEAM paths for roster tests."""
import os, sys
ROOT = "/Users/daxu/software/world-trader"
TEAM = f"{ROOT}/campaign/team"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")
