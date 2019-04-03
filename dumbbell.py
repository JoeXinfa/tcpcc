# -*- coding: utf-8 -*-
"""
"""
                                                                                             
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


def perfTest():
    "Create network and run simple performance test"
    topo = DumbbellTopo()
    
    # Select TCP Reno
    output = quietRun('sysctl -w net.ipv4.tcp_congestion_control=reno')
    assert 'reno' in output
    
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    
    print("Dumping host connections")
    dumpNodeConnections(net.hosts)
    
    print("Testing network connectivity")
    net.pingAll()
    
    print("Testing bandwidth between hs1 and hr1")
    hs1, hr1 = net.get('hs1', 'hr1')
    net.iperf( (hs1, hr1) )
    
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    perfTest()
