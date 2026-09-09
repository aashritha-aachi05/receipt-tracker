import sys
import os

os.environ["TABLE_NAME"] = "test-table"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda"))