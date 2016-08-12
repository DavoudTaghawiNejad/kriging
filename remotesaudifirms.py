


#pylint: disable=C0103, C0111, C0301, C0325, E1101
from __future__ import division
import zmq
import json
from time import time
import logging
import sys


logger = logging.getLogger('kriging.kriger')

dont_transform = lambda self, x: x

class RemoteSaudiFirms(object):
    def __init__(self, task=5557, result=5558, address_prefix="tcp://*:", input_transfromation=dont_transform):
        print(address_prefix + str(result))
        self.context = zmq.Context()
        self.sender = self.context.socket(zmq.REP)
        self.sender.bind(address_prefix + str(task))
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(address_prefix + str(result))
        self.input_transfromation = input_transfromation


    def vent(self, jobs, repetitions):
        i = 0
        for _ in range(repetitions):
            for job in jobs:
                self.sender.recv()
                job = self.input_transfromation(job)
                self.sender.send_string(json.dumps(job))
                i += 1
                print('\rout: %i/%i  ' % (i, len(jobs) * repetitions)),
                sys.stdout.flush()

    def sink(self, total_tasks):
        done_tasks = 0
        timeout = 0
        results = []
        while done_tasks < total_tasks:
            msg = self.receiver.recv()
            done_tasks += 1
            try:
                element = json.loads(msg)
            except ValueError:
                print("\r\t\t\t\t\t\t'%s'" % msg),
                if msg != 'java.lang.Exception: zero samples, timeout?':
                    print('')
                timeout += 1
                continue
            results.append(element)
            print('\rdone: %i/%i timeout: %i  ' % (done_tasks, total_tasks, timeout)),
            sys.stdout.flush()
        logger.error("timeouts: %i/%i" % (timeout, total_tasks))
        return results

    def run_D2D(self, jobs, repetitions):
        t = time()
        print("going to vent"),
        self.vent(jobs, repetitions)
        work_done = self.sink(len(jobs) * repetitions)
        print("finished in: %f" % (time() - t))
        return work_done

