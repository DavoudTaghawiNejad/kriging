
from __future__ import division
import zmq
import json
from time import time
import logging

logger = logging.getLogger('kriging.kriger')

class RemoteSaudiFirms:
    def __init__(self, task=5557, result=5558, kill=5559, address_prefix="tcp://*:"):
        logger.info(address_prefix + str(result))
        self.context = zmq.Context()
        self.sender = self.context.socket(zmq.PUSH)
        self.sender.bind(address_prefix + str(task))
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(address_prefix + str(result))
        self.controller = self.context.socket(zmq.PUB)
        self.controller.bind(address_prefix + str(kill))
        #logger.info("start up Simulations and hit ENTER")
        #raw_input()
        self.total_tasks = 0

    def vent(self, jobs):
        self.total_tasks += len(jobs)
        for job in jobs:
            self.sender.send_string(json.dumps(job))

    def sink(self):
        done_tasks = 0
        results = []
        t = time()
        while done_tasks < self.total_tasks:
            results.append(self.receiver.recv())
            done_tasks += 1
            print('\rdone: %i/%i time per task: %6.2f' % (done_tasks, self.total_tasks, done_tasks / (time() - t))),
        self.total_tasks = 0
        return results

    def run_D2D(self, jobs, repetitions):
        logger.info("going to vent"),
        t = time()
        for i in range(repetitions):
            self.vent(jobs)
        logger.info("\r%i tasks given 0 done" % self.total_tasks),
        work_done = []
        timeout = 0
        for element in self.sink():
            return_json = json.loads(element)
            if return_json['result'] == "timeout":
                timeout += 1
                continue
            try:
                work_done.append(return_json)
            except ValueError:
                logger.info("++++++++++")
                logger.info(element)
                raise
        logger.info("(%i timeouts)\tfinished in: %f" % (timeout, time() - t))
        return work_done

    def kill(self, force=False):
        self.controller.send(b'kill')

if __name__ == "__main__":
    rsf = RemoteSaudiFirms()
    rsf.kill()