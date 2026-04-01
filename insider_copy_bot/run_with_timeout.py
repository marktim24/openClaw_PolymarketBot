import subprocess
import sys
import os

print("Running main.py with 30 second timeout...")
try:
    # Run main.py with timeout
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        timeout=30,
        capture_output=True,
        text=True
    )
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print(f"Exit code: {result.returncode}")
except subprocess.TimeoutExpired:
    print("TIMEOUT: main.py took longer than 30 seconds")
    print("This indicates Hashdive API is timing out")
except Exception as e:
    print(f"Error: {e}")