# Compatibility entry point: the old phase-2 handoff is superseded.
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('create-sprint3-summary.py')),run_name='__main__')
