
import subprocess
try:
    print("Checking HamClock processes...")
    result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, text=True)
    for line in result.stdout.split('\n'):
        if 'hamclock' in line.lower() or 'python' in line.lower():
            print(line[:100]) # truncated
            
    print("\nChecking Ports...")
    result = subprocess.run(['netstat', '-tuln'], stdout=subprocess.PIPE, text=True)
    for line in result.stdout.split('\n'):
        if '80' in line:
            print(line)
except Exception as e:
    print(e)
