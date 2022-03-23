#!/usr/bin/python
#
# An exmaple of Ryu controller
# AUTHOR: David Lu (https://github.com/yungshenglu)

from ryu.base import app_manager
from ryu.controller import mac_to_port, ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
from ryu.lib import mac
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ether_types
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from ryu.topology import event, switches
from ryu.lib import hub
import networkx as nx
import time

class SimpleController(app_manager.RyuApp):
    # Let the Ryu controller running in protocol OpenFlow 1.3 
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    '''
    METHOD : __init__
    Class constructor and inherit from app_manager.RyuApp (DO NOT MODIFY)
    '''
    def __init__(self, *args, **kwargs):
        super(SimpleController, self).__init__(*args, **kwargs)
        self.topology_api = self
        self.mac_to_port = {}
        self.net = nx.DiGraph()
        self.nodes = {}
        self.links = {}
        self.datapaths = {}
        hub.spawn(self._timer)

    '''
    Method : __state_change_handler
    To make sure the connected switch is monitored (DO NOT MODIFY)
    '''
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self,ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]

    '''
    Method : _timer
    Request for statistical information for the registered switch every 10 seconds
    (No need to MODIFY) (You can modify the number if you think it's too slow :)
    '''
    def _timer(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)
    
    '''
    Method : _request_stats
    Request that the switch provide statistical information related to flow entry
    (DO NOT MODIFY)
    '''
    def _request_stats(self,datapath):
        # request stats
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    '''
    Method : _flow_stats_reply_handler
    Handler for FlowStatsReply message (DO NOT MODIFY)
    '''
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        
        body = ev.msg.body
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        for stat in sorted([flow for flow in body if flow.priority==3], 
            key=lambda flow: (flow.match['in_port'])):
                if ev.msg.datapath.id == 2 and stat.match['ipv4_dst']=='10.0.0.1':
                    print("switch %d: count %d packets" % (ev.msg.datapath.id, stat.packet_count))

    '''
    METHOD : add_flow
    Add a flow into flow table of each switch (DO NOT MODIFY)
    '''
    def add_flow(self, datapath, priority, match, actions,hard_timeout):
        # msg      : the information of packet-in (including switch, in_port number, etc.)
        # datapath : the switch in the topology using OpenFlow
        # ofproto  : get the protocol using in the switch
        # parser   : get the communication between switch and Ryu controller
        # inst     : the instruction that need to be executed
        # mod      : the flow-entry that need to add into the switch
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser      
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            command=ofproto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=hard_timeout,
            cookie=0,
            flags = ofproto.OFPFF_SEND_FLOW_REM)
        datapath.send_msg(mod)

        
    '''
    METHOD : switch_features_handler (@set_ev_cls)
    Handle the initial feature of each switch
    '''
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        # msg      : the information of packet-in (including switch, in_port number, etc.)
        # datapath : the switch in the topology using OpenFlow
        # ofproto  : get the protocol using in the switch
        # parser   : get the communication between switch and Ryu controller
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install table-miss entry
        # match   : the rule of matching specific packets
        # actions : the behavior triggered from packet-in
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(
            datapath=datapath,
            priority=0,
            match=match,
            actions=actions,
            hard_timeout=0
            )

        ############################################################################
        ## Modify this part in "controller1.py" and "controller2.py"              ##
	    ## not in "SimpleController.py".      					                  ##
        ## The example code shows the forwarding rules as the following figure.   ##
        ##                                                                        ##
        ## ex.             s1  s4 <===> h2                                        ##
        ##                    /                                                   ##
        ##                   /                                                    ##
        ##        h1 <===> s2  s3                                                 ##
	    ##                                                                        ##
        ## [TODO] Define the new forwarding rules in ppt.			                      ##
        ##                                                                        ##
        ############################################################################

        # TODO section BEGIN -----------------------------------------------------

	    # Add forwarding rule in s2
        if msg.datapath.id == 2:
            # For h1-h2 flow: h1 -> s2 -> s4
            match = parser.OFPMatch(
                in_port=1,
                eth_type=0x0800,
                ipv4_src="10.0.0.1",
                ipv4_dst="10.0.0.2"
                )
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(
                datapath=datapath,
                priority=3,
                match=match,
                actions=actions,
                hard_timeout=0)
            # For h2-h1 flow: s4 -> s2 -> h1
            match = parser.OFPMatch(
                in_port=2,
                eth_type=0x0800,
                ipv4_src="10.0.0.2",
                ipv4_dst="10.0.0.1"
                )
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(
                datapath=datapath,
                priority=3,
                match=match,
                actions=actions,
                hard_timeout=0)

        # Add forwarding rule in s4
        if msg.datapath.id == 4:
            # For h2-h1 flow: h2 -> s4 -> s2
            match = parser.OFPMatch(
                in_port=1,
                eth_type=0x0800,
                ipv4_src="10.0.0.2",
                ipv4_dst="10.0.0.1"
                )
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(
                datapath=datapath,
                priority=3,
                match=match,
                actions=actions,
                hard_timeout=0)
            # For h1-h2 flow: s2 -> s4 -> h2
            match = parser.OFPMatch(
                in_port=3,
                eth_type=0x0800,
                ipv4_src="10.0.0.1",
                ipv4_dst="10.0.0.2"
                )
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(
                datapath=datapath,
                priority=3,
                match=match,
                actions=actions,
                hard_timeout=0)

        # TODO Section END ------------------------------------------------------
    
    '''
    METHOD : packet_in_handler (@set_ev_cls)
    Handle the packet-in events (DO NOT MODIFY)
    '''
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        
        # Get the source and the destination ethernet address
        eth = pkt.get_protocol(ethernet.ethernet)
        eth_dst = eth.dst
        eth_src = eth.src
        # Get the ID of each switch
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        if eth_src not in self.net:
            self.net.add_node(eth_src)
            self.net.add_edge(dpid, eth_src, port=in_port)
            self.net.add_edge(eth_src, dpid)
        
        if eth_dst in self.net:
            path = nx.shortest_path(self.net, eth_src, eth_dst)  
            next = path[path.index(dpid) + 1]
            out_port = self.net[dpid][next]['port']
        else:
            out_port = ofproto.OFPP_FLOOD

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port,
            eth_dst=eth_dst)
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            in_port=in_port,
            actions=actions,
            buffer_id=msg.buffer_id)
        datapath.send_msg(out)
    
    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def flow_removed_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        if msg.reason == ofp.OFPRR_IDLE_TIMEOUT:
            reason = 'IDLE TIMEOUT'
        elif msg.reason == ofp.OFPRR_HARD_TIMEOUT:
            reason = 'HARD TIMEOUT'
        elif msg.reason == ofp.OFPRR_DELETE:
            reason = 'DELETE'
        elif msg.reason == ofp.OFPRR_GROUP_DELETE:
            reason = 'GROUP DELETE'
        else:
            reason = 'unknown'
        print('switch id:',dp.id)
        print('OFPFlowRemoved received: '
                        'cookie=%d priority=%d reason=%s table_id=%d '
                        'duration_sec=%d duration_nsec=%d '
                        'idle_timeout=%d hard_timeout=%d '
                        'packet_count=%d byte_count=%d match.fields=%s' % (
                        msg.cookie, msg.priority, reason, msg.table_id,
                        msg.duration_sec, msg.duration_nsec,
                        msg.idle_timeout, msg.hard_timeout,
                        msg.packet_count, msg.byte_count, msg.match))

    '''
    METHOD : get_topology_data (@set_ev_cls)
    Show the information of the topology (DO NOT MODIFY)
    '''
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        # Show all switches in the topology
        switches_list = get_switch(self.topology_api, None)  
        switches = [switch.dp.id for switch in switches_list]
        self.net.add_nodes_from(switches)
        # print('*** List of switches')
        #for switch in switches_list:
            #print(switch)
        time.sleep(2)

        # Show all links in the topology
        links_list = get_link(self.topology_api, None)
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links_list]
        self.net.add_edges_from(links)
        links = [(link.dst.dpid, link.src.dpid, {'port': link.dst.port_no}) for link in links_list]
        self.net.add_edges_from(links)
        # print('*** List of links')
  
        # print(self.net.edges())
