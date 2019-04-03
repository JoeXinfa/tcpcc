# -*- coding: utf-8 -*-
"""
"""

import os
from subprocess import Popen
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections, quietRun
from mininet.log import setLogLevel


class DumbbellTopo(Topo):
    def build(self, n=2, delay='21ms', bw=21):
        backboneRouter1 = self.addSwitch('sb1')
        accessRouter1 = self.addSwitch('sa1')
        self.addLink(backboneRouter1, accessRouter1, bw=bw)
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
            
        self.addLink(backboneRouter1, backboneRouter2, bw=82, delay=delay)


def start_tcpprobe(fn="cwnd.txt"):
#    os.system("rmmod tcp_probe; modprobe tcp_probe full=1;")
    os.system("modprobe tcp_probe full=1;")
    ffn = os.path.join("/tmp", fn)
    Popen("cat /proc/net/tcpprobe > {}".format(ffn), shell=True)


def perfTest():
    "Create network and run simple performance test"
    delay = '21ms'
    topo = DumbbellTopo(delay=delay)
    
    # Select TCP Reno
    alg = 'reno'
    output = quietRun('sysctl -w net.ipv4.tcp_congestion_control={}'.format(alg))
    assert alg in output

    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    
    print("Dumping host connections")
    dumpNodeConnections(net.hosts)
    
    print("Testing network connectivity")
    net.pingAll()
    
    print("Testing bandwidth between hs1 and hr1")

    fn = 'cwnd_' + alg + '_' + delay + '.txt'
    start_tcpprobe(fn=fn)

    hs1, hr1 = net.get('hs1', 'hr1')
    net.iperf( (hs1, hr1) )
    
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    perfTest()
