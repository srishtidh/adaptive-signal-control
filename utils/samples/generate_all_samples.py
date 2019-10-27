import subprocess
import argparse
import json


parser = argparse.ArgumentParser()
parser.add_argument('--turns-file')
parser.add_argument('--sample-count')
parser.add_argument('--labels')
parser.add_argument('--runs', type=int)
parser.add_argument('--start', type=int)
args = parser.parse_args()

with open(args.labels, 'r') as fp:
    labels = json.load(fp)

for label in labels:
    for run in range(args.start, args.runs+args.start):
        print('Generating sample set # {} for {}'.format(run, label))
        cmd = ['python', '/home/srishti/adasco/utils/samples/generate_samples.py',
           '--turns-file', args.turns_file, '--route-file', '{}.rou.xml'.format(label),
           '--output-file', '{}-samples-{:03d}.pkl'.format(label, run), '--sample-count', args.sample_count]

        subprocess.call(cmd)
