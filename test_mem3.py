import os, subprocess
out = subprocess.check_output(f'tasklist /FI "PID eq {os.getpid()}" /NH /FO CSV', shell=True).decode()
mem_str = out.strip().split(',')[-1].replace('"', '').replace('K', '').replace(' ', '').replace(',', '').replace('.', '')
print(float(mem_str) / 1024)
