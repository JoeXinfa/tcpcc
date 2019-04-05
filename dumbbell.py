# -*- coding: utf-8 -*-
"""
"""

import os
import time
from subprocess import Popen
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections, quietRun
from mininet.log import setLogLevel


class DumbbellTopo(Topo):
    def build(self, n=2, delay='21ms', bw=21):
        """ delay is one-way progagation delay """
        # Access router speed = bw = 21 packets/ms
        delay1w = int(delay[:-2]) # one-way propagation delay
        #delay2w = delay1w * 2 # RRT, round-trip-time
        bdp = bw * delay1w # BDP, bandwidth-delay-product
        buff = bdp * 0.2 # 20% BDP

        backboneRouter1 = self.addSwitch('sb1')
        accessRouter1 = self.addSwitch('sa1')
        self.addLink(backboneRouter1, accessRouter1, bw=bw,
                     max_queue_size=buff)
        for h in range(n):
    	    # Each host gets 50%/n of system CPU
            host = self.addHost('hs%s' % (h + 1), cpu=.5/n)
            self.addLink(host, accessRouter1, bw=80)

        backboneRouter2 = self.addSwitch('sb2')
        accessRouter2 = self.addSwitch('sa2')
        self.addLink(backboneRouter2, accessRouter2, bw=bw)
        for h in range(n):
    	    # Each host gets 50%/n of system CPU
            host = self.addHost('hr%s' % (h + 1), cpu=.5/n)
            self.addLink(host, accessRouter2, bw=80)
            
        speed = 82 # packets/ms, same as bandwidth
        buff = speed * delay1w # BDP, bandwidth-delay-product
        self.addLink(backboneRouter1, backboneRouter2, bw=speed,
                     delay=delay, max_queue_size=buff)


def start_tcpprobe(fn="cwnd.txt"):
    os.system("rmmod tcp_probe; modprobe tcp_probe full=1;")
    ffn = os.path.join("/home/mininet/data", fn)
    print("TCP probe save to {}".format(ffn))
    Popen("cat /proc/net/tcpprobe > {}".format(ffn), shell=True)


def perfTest(delay, alg, run_time=1000, hold_time=250):
#    short, medium, long = '21ms', '81ms', '162ms'
#    delay = short
    topo = DumbbellTopo(delay=delay)
    
    # Select TCP Reno
#    alg = 'reno'
#    output = quietRun('sysctl -w net.ipv4.tcp_congestion_control={}'.format(alg))
#    assert alg in output

    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    
    print("Dumping host connections")
    dumpNodeConnections(net.hosts)
    
    print("Testing network connectivity")
    net.pingAll()
    
    print("Testing bandwidth between hosts")

    fn = 'cwnd_' + alg + '_' + delay + '.txt'
    start_tcpprobe(fn=fn)

    hs1, hr1 = net.get('hs1', 'hr1')
    hs2, hr2 = net.get('hs2', 'hr2')
#    net.iperf((hs1, hr1), seconds=20)
#    net.iperf((hs2, hr2), seconds=20)
    
#    result = hs1.cmd('ifconfig')
#    print("hs1 ifconfig", result)
    
    hr1_IP = hr1.IP()
    hr2_IP = hr2.IP()

    hr1.cmd('iperf -s -p 5001 &')
    hr2.cmd('iperf -s -p 5002 &')
    hs1.cmd('iperf -c {} -p 5001 -i 1 -w 16m -Z {} -t {} > results1 &'.format(
            hr1_IP, alg, run_time))
    time.sleep(hold_time)
    remain_time = run_time - hold_time
    hs2.cmd('iperf -c {} -p 5002 -i 1 -w 16m -Z {} -t {} > results2 &'.format(
            hr2_IP, alg, remain_time))
    time.sleep(remain_time) # keep net alive

    print("Stopping test")
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    algorithms = ['reno', 'cubic', 'htcp', 'westwood']
    delays = ['21ms', '81ms', '162ms']
    for alg in algorithms:
        for delay in delays:
            perfTest(delay, alg)
