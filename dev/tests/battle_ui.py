"""Battle UI verification for dedicated skill/strategy slots.

Legacy command: battle_ui.py HTML BEFORE_HTML OUT.
BEFORE_HTML is retained for CLI compatibility; the six new strategy effects
intentionally change combat, so equality with the old mixed-hand build is
no longer a valid assertion. General regressions are covered by smoke.py.
"""
import runpy
import sys
from pathlib import Path

if len(sys.argv) == 4:
    sys.argv = [sys.argv[0], sys.argv[1], sys.argv[3]]
runpy.run_path(str(Path(__file__).with_name('strategy_slots.py')), run_name='__main__')
