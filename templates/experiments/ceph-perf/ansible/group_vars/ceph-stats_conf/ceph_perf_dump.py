#! /usr/bin/python
import os
import pickle
import struct
import socket
import json
import argparse
import time

# recurse down the json object and convert to paths
def json_to_path(metrics, date, path, data):
  if type(data) == dict:
    for x in data:
      json_to_path(metrics, date, path + "." + x, data[x])
  else:
    metrics.append((path, (date, data)))
  return metrics

# get into pickle format that graphite wants
#   [(name, (timestamp, value)), ...]
def json_to_tuplelist(data):
  f = os.popen('date +%s')
  date = f.read().strip('\n')
  metrics = json_to_path([], date, socket.gethostname(), data)
  return date, metrics
  
# main
parser = argparse.ArgumentParser(description='Parse Ceph perf counter dump and send to graphite')
parser.add_argument('ip', metavar='ip', type=str,
                    help='where the graphite collector daemon (carbon) lives')
parser.add_argument('--port', metavar='p', type=int, default=2004,
                    help='port of the graphite collector daemon (carbon)')
parser.add_argument('--interval', metavar='i', type=int, default=1,
                    help='port of the graphite collector daemon (carbon)')
parser.add_argument('--jsonfile', metavar='f', type=str, default="/tmp/ceph_perf_dump.json",
                    help='where the json dump is')
args = parser.parse_args()
print "args:", args

# connect to graphite
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((args.ip, args.port))

while 1:
    time.sleep(args.interval)

    # read the perf dump
    os.popen("ceph --admin-daemon /var/run/ceph/ceph-mds* perf dump > " + args.jsonfile)
    try:
      with open(args.jsonfile) as f:
        date, metrics = json_to_tuplelist(json.load(f))
    except IOError:
      print "WARNING: couldn't find JSON dump, did you dump the Ceph JSON (" + args.jsonfile + ")?"
      continue
    except ValueError:
      print "ERROR: couldn't read the JSON dump, malformed"
      continue
 
    # send off to graphite 
    payload = pickle.dumps(metrics, protocol=2)
    header = struct.pack("!L", len(payload))
    s.send(header + payload)
    print "... sent at", date, "to", args.ip, " at port", args.port
