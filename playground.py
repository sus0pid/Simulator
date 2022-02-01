from simulation_modes import test_mode
import os
# from experiments import plotting
from metrics import anonymity_metrics
import pandas as pd
import json
import argparse
import multiprocessing as mp
import csv
import pprint as pp
import numpy as np

DEFAULT_ITERATION = 10
parser = argparse.ArgumentParser()
parser.add_argument("--rate_sending", type=float, help="sending rate of clients ranging from 1 to 10")


def worker(rate_sending, avg_delay, q):
    logs = []
    with open('test_config.json') as json_file:
        config = json.load(json_file)
    config['clients']['rate_sending'] = rate_sending
    config['mixnodes']['avg_delay']   = avg_delay
    config['logging']['dir']          = 's{0}_d{1}_logs'.format(rate_sending, avg_delay)
    print("-------------------------------------------------------")
    pp.pprint(config)
    print("-------------------------------------------------------")
    log_path = os.path.join('./playground_experiment', 's{0}_d{1}_logs'.format(rate_sending, avg_delay))
    print(f'log_path:{log_path}')

    for i in range(DEFAULT_ITERATION):
        print(f"{i}th Iteration of Mix-network Simulator\n")
        print("Insert the following network parameters to test: ")
       
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        else:
            try:
                os.remove(os.path.join(log_path, 'packet_log.csv'))
                os.remove(os.path.join(log_path, 'last_mix_entropy.csv'))
            except:
                pass

        test_mode.run(exp_dir='playground_experiment', conf_file=None, conf_dic=config)
        throughput = test_mode.throughput

        packetLogsDir = os.path.join(log_path, 'packet_log.csv')
        entropyLogsDir = os.path.join(log_path, 'last_mix_entropy.csv')
        packetLogs = pd.read_csv(packetLogsDir, delimiter=';')
        entropyLogs = pd.read_csv(entropyLogsDir, delimiter=';')

        unlinkability = anonymity_metrics.getUnlinkability(packetLogs)
        entropy = anonymity_metrics.getEntropy(entropyLogs, config["misc"]["num_target_packets"])
        latency = anonymity_metrics.computeE2ELatency(packetLogs)

        log_row = [i, rate_sending, avg_delay, entropy, unlinkability[0], unlinkability[1], latency, throughput]
        logs.append(log_row)

    print(f'Process {os.getpid()} spent xxx seconds')
    q.put(logs)
    return logs


def listener(q, rate_sending):
    """listens for messages on the q, writes to file"""
 
    print('.'*10 + 'listening' + '.'*10)

    with open(os.path.join('./playground_experiment', 's{}_log.csv'.format(rate_sending)), 'a') as log_file:
        while True:
            logs = q.get()
            if logs == 'kill':
                print('Listener has been killed......')
                break
            else:
                logwriter = csv.writer(log_file)
                logwriter.writerows(logs)
                print("\n\n")
                print("Simulation finished. Below, you can check your results.")
                print("-------------------------------------------------------")
                pp.pprint(f"logs: {logs}")
                print("-------------------------------------------------------")


def run():
    # use Manager queue
    manager  = mp.Manager()
    q        = manager.Queue()
    args     = parser.parse_args()

    log_header = ['iteration', 'rate_sending', 'avg_delay', 'entropy', 'episilon', 'delta', 'latency', 'throughput']
    with open(os.path.join('./playground_experiment', 's{}_log.csv'.format(args.rate_sending)), 'w') as logfile:
        row = (',').join(log_header)
        logfile.write(row)
        logfile.write('\n')

    with mp.Pool(processes=30) as pool:
        # Put listener to work first
        watcher = pool.apply_async(listener, (q, args.rate_sending))

        #fire off workers
        jobs = []
        for avg_delay in [round(d, 1) for d in np.linspace(0.2, 6, 30).tolist()]:
            print("-------------------------------------------------------")
            print(f"Mix-networks Simulator (send rate = {args.rate_sending}, avg delay = {avg_delay})")
            job = pool.apply_async(worker, (args.rate_sending, avg_delay, q))
            jobs.append(job)

        #collect results from the workers through the pool result queue
        for job in jobs:
            job.get()

        #now we are done, kill the listenser
        q.put('kill')
        pool.close()
        pool.join()

if __name__ == "__main__":
    run()