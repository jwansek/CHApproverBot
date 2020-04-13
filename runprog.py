from time import sleep
import subprocess
import multiprocessing
import json

def thread_():
    subprocess.run(["python3", "CHApproverBot.py"])

while True:
    thread = multiprocessing.Process(target = thread_, args = ())
    thread.start()

    # sleep(60 * 60 * 2)
    sleep(15)

    print("closing...")

    with open("pid.json", "r") as f:
        pid = json.load(f)

    subprocess.run(["kill", str(pid)])
    thread.terminate()

    print("killed ", pid)

