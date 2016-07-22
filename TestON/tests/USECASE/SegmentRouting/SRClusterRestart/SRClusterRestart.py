# CASE1: 2x2 topo + 3-node ONOS CLUSTER + IP connectivity test + CLUSTER restart
# CASE2: 4x4 topo + 3-node ONOS CLUSTER + IP connectivity test + CLUSTER restart
# CASE3: Single switch + 3-node ONOS CLUSTER + IP connectivity test + CLUSTER restart

class SRClusterRestart:
    def __init__( self ):
        self.default = ''

    def CASE1( self, main ):
        """
        Sets up 3-node Onos-cluster
        Start 2x2 Leaf-Spine topology
        Pingall
        Induce CLUSTER restart
        Pingall
        """
        description = "Cluster Restart test with 2x2 Leaf-spine "
        main.case( description )
        from tests.USECASE.SegmentRouting.dependencies.Testcaselib import \
            Testcaselib as run
        if not hasattr( main, 'apps' ):
            run.initTest( main )
        main.cfgName = '2x2'
        main.numCtrls = 3
        run.installOnos( main )
        run.startMininet( main, 'cord_fabric.py' )
        # pre-configured routing and bridging test
        run.checkFlows( main, minFlowCount=116 )
        run.pingAll( main, "CASE1" )
        run.killOnos( main, [ 0, 1, 2 ], '4', '8', '0' )
        run.pingAll( main, 'CASE1_Failure', dumpflows=False )
        run.recoverOnos( main, [ 0, 1, 2 ], '4', '8', '3' )
        run.checkFlows( main, minFlowCount=116 )
        run.pingAll( main, 'CASE1_Failure' )
        # TODO Dynamic config of hosts in subnet
        # TODO Dynamic config of host not in subnet
        # TODO Dynamic config of vlan xconnect
        # TODO Vrouter integration
        # TODO Mcast integration
        run.cleanup( main )

    def CASE2( self, main ):
        """
        Sets up 3-node Onos-cluster
        Start 4x4 Leaf-Spine topology
        Pingall
        Induce Cluster Restart
        Pingall
        """
        description = "Cluster Restart test with 4x4 Leaf-spine "
        main.case( description )
        from tests.USECASE.SegmentRouting.dependencies.Testcaselib import \
            Testcaselib as run
        if not hasattr( main, 'apps' ):
            run.initTest( main )
        main.cfgName = '4x4'
        main.numCtrls = 3
        run.installOnos( main )
        run.startMininet( main, 'cord_fabric.py', args="--leaf=4 --spine=4" )
        # pre-configured routing and bridging test
        run.checkFlows( main, minFlowCount=350 )
        run.pingAll( main, 'CASE2' )
        run.killOnos( main, [ 0, 1, 2 ], '8', '32', '0' )
        run.pingAll( main, 'CASE2_Failure', dumpflows=False )
        run.recoverOnos( main, [ 0, 1, 2 ], '8', '32', '3' )
        run.checkFlows( main, minFlowCount=350 )
        run.pingAll( main, 'CASE3_Recovery' )
        # TODO Dynamic config of hosts in subnet
        # TODO Dynamic config of host not in subnet
        # TODO Dynamic config of vlan xconnect
        # TODO Vrouter integration
        # TODO Mcast integration
        run.cleanup( main )

    def CASE3( self, main ):
        """
        Sets up 3-node Onos-cluster
        Start single switch topology
        Pingall
        Induce Cluster Restart
        Pingall
        """
        description = "Cluster Restart test with single switch "
        main.case( description )
        from tests.USECASE.SegmentRouting.dependencies.Testcaselib import \
            Testcaselib as run
        if not hasattr( main, 'apps' ):
            run.initTest( main )
        main.cfgName = '0x1'
        main.numCtrls = 3
        run.installOnos( main )
        run.startMininet( main, 'cord_fabric.py', args="--leaf=1 --spine=0" )
        # pre-configured routing and bridging test
        run.checkFlows( main, minFlowCount=15 )
        run.pingAll( main, 'CASE3' )
        run.killOnos( main, [ 0, 1, 2 ], '1', '0', '0' )
        run.pingAll( main, 'CASE3_Failure', dumpflows=False )
        run.recoverOnos( main, [ 0, 1, 2 ], '1', '0', '3' )
        run.checkFlows( main, minFlowCount=15 )
        run.pingAll( main, 'CASE3_Failure' )
        # TODO Dynamic config of hosts in subnet
        # TODO Dynamic config of host not in subnet
        # TODO Dynamic config of vlan xconnect
        # TODO Vrouter integration
        # TODO Mcast integration
        run.cleanup( main )