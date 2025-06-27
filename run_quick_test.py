#!/usr/bin/env python3
"""
Standalone script to run the quick flow test with proper path setup
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now we can import the test
from tests.test_quick_flow import run_quick_tests

if __name__ == "__main__":
    run_quick_tests()