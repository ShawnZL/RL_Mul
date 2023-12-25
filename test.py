from subprocess import Popen, PIPE

abc_command = 'read asap7.lib; read adder.v; strash; write playground/1/1.v; map -D 1800; write playground/1/1-mapped.v; topo; stime;'

try:
    # 使用 Popen 启动子进程
    proc = Popen(['yosys-abc', '-c', abc_command], stdout=PIPE, stderr=PIPE, text=True)

    # 迭代读取输出的行
    for line in proc.stdout:
        print(line.strip())

    # 等待子进程结束
    proc.wait()
except KeyboardInterrupt:
    print("Keyboard interrupt received.")
finally:
    # 确保子进程在退出之前被杀死
    if proc.poll() is None:
        proc.terminate()
