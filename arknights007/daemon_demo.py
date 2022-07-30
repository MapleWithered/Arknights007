from prts import daemon
import time

if __name__ == '__main__':

    daemon.PRTSDaemon.run_task()
    while daemon.PRTSDaemon.get_status() == daemon.Status.RUN_TASK:
        time.sleep(1)
        print(daemon.PRTSDaemon.get_status())
    for i in range(5):
        time.sleep(1)
        print(daemon.PRTSDaemon.get_status())
    print("Rerun")
    daemon.PRTSDaemon.run_task()
    for i in range(5):
        time.sleep(1)
        print(daemon.PRTSDaemon.get_status())
    print("killing")
    daemon.PRTSDaemon.kill_process()
    print(daemon.PRTSDaemon.get_status())
    for i in range(5):
        time.sleep(1)
        print(daemon.PRTSDaemon.get_status())