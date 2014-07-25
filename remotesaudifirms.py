
from __future__ import division
import zmq
import json
from time import time
import logging

logger = logging.getLogger('kriging.kriger')

class RemoteSaudiFirms:
    def __init__(self, task=5557, result=5558, kill=5559, address_prefix="tcp://*:"):
        print(address_prefix + str(result))
        self.context = zmq.Context()
        self.sender = self.context.socket(zmq.PUSH)
        self.sender.bind(address_prefix + str(task))
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(address_prefix + str(result))
        self.poller = zmq.Poller()
        self.poller.register(self.receiver, zmq.POLLIN)
        self.controller = self.context.socket(zmq.PUB)
        self.controller.bind(address_prefix + str(kill))
        #logger.info("start up Simulations and hit ENTER")
        #raw_input()
        self.total_tasks = 0
        self.out_standing = 0

    def vent(self, jobs):
        for i in range(self.out_standing):
            try:
                self.receiver.recv(zmq.NOBLOCK)
            except:
                pass
            else:
                print("outstanding %i" % self.out_standing)
                self.out_standing -= 1

        self.total_tasks += len(jobs)
        for job in jobs:
            self.sender.send_string(json.dumps(job))

    def sink(self):
        done_tasks = 0
        results = []
        t = time()
        while done_tasks < self.total_tasks:
            socks = dict(self.poller.poll(4 * 60000 + 10000))  # in minutes 60000
            if socks:
                results.append(self.receiver.recv())
            else:
                print "error: message timeout"
                self.out_standing += 1
            done_tasks += 1
            print('\rdone: %i/%i time per task: %6.2f' % (done_tasks, self.total_tasks, done_tasks / (time() - t))),
        self.total_tasks = 0
        return results

    def run_D2D(self, jobs, repetitions):
        print("going to vent"),
        t = time()
        for i in range(repetitions):
            self.vent(jobs)
        print("\r%i tasks given 0 done" % self.total_tasks),
        work_done = []
        timeout = 0
        for element in self.sink():
            try:
                return_json = json.loads(element)
            except ValueError:
                logger.error(element)
                continue
            if return_json['result'] == "timeout":
                timeout += 1
            else:
                work_done.append(return_json)
        print("(%i timeouts)\tfinished in: %f" % (timeout, time() - t))
        return work_done

    def kill(self, force=False):
        self.controller.send(b'kill')

if __name__ == "__main__":
    rsf = RemoteSaudiFirms()
    rsf.kill()