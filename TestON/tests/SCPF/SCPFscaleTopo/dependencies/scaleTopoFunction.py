"""
    Wrapper function for FuncTopo
    Includes onosclidriver and mininetclidriver functions
"""
import time
import json
import re

def __init__( self ):
    self.default = ''

def getTimestampFromString( main, targetString ):
    #Get time string from the target string
    try:
        assert type( targetString ) is str
        timeString = targetString.split( ' | ' )
        timeString = timeString[ 0 ]
        from datetime import datetime
        # convert time string to timestamp
        t = datetime.strptime( timeString, "%Y-%m-%d %H:%M:%S,%f" )
        import time
        timestamp = time.mktime( t.timetuple() )
        timestamp += int( t.microsecond / 1000 ) / 1000.0
        return timestamp
    except AssertionError:
        main.log.error( "Got nothing firom log" )
        return -1
    except IndexError:
        main.log.error( "Time string index error" )
        return -1
    except ValueError:
        main.log.error( "Got wrong string from log" )
        return -1

def getRoleRequestTimeFromTshark( main ):
    try:
        main.log.info( "Get role request time" )
        with open(main.tsharkResultPath, "r" ) as resultFile:
            resultText = resultFile.readlines()
            # select the last role request string
            roleRequestString = resultText[ len( resultText ) - 1 ]
            main.log.info( roleRequestString )
            # get timestamp from role request string
            roleRequestTime = roleRequestString.split( " " )
            resultFile.close()
            return float(roleRequestTime[1])
    except IndexError:
        main.log.error("Got wrong role request string from Tshark file")
        return -1

def compareTimeDiffWithRoleRequest(main, term, Mode, index=0 ):
    '''
    Description:
        Compare the time difference between the time of target term and the time of role request
        Inclides onosclidriver functions

    '''
    try:
        termInfo = main.CLIs[ index ].logSearch( mode=Mode, searchTerm=term )
        termTime = getTimestampFromString( main, termInfo[ 0 ] )
        roleRequestTime = getRoleRequestTimeFromTshark( main )
        if termTime == -1 or roleRequestTime == -1:
            main.writeData = -1
            main.log.error( "Can't compare the difference with role request time" )
            return -1
        # Only concern about the absolute value of difference.
        return abs( roleRequestTime - termTime )
    except IndexError:
        main.log.error( "Catch the wrong information of search term " )
        main.writeData = -1
        return -1

def getInfoFromLog( main, term1, mode1, term2, mode2, index=0, funcMode='TD' ):
    '''
    Description:
        Get needed informations of the search term from karaf.log
        Includes onosclidriver functions
    Function mode:
        TD (time difference):
            Get time difference between start and end
            Term1: startTerm
            Term2: endTerm
        DR (disconnect rate):
            Get switch disconnect rate
            Term1: disconnectTerm
            Term2: connectTerm

    '''
    try:
        termInfo1 = main.CLIs[ index ].logSearch( mode=mode1, searchTerm=term1 )
        termInfo2 = main.CLIs[ index ].logSearch( mode=mode2, searchTerm=term2 )
        if funcMode == 'TD':
            startTime = getTimestampFromString( main, termInfo1[0] )
            endTime = getTimestampFromString ( main, termInfo2[0] )
            if startTime == -1 or endTime == -1:
                main.log.error( "Wrong Time!" )
                main.writeData = -1
                return -1
            return endTime - startTime
        if funcMode == 'DR':
            #In this mode, termInfo1 means the total number of switch disconnection and
            #termInfo2 means the total number of new switch connection
            #termInfo2 - termInfo1 means the actual real number of switch connection.
            disconnection = int( termInfo1 ) * 1.0
            expectConnection = int( main.currScale ) ** 2
            realConnection = int( termInfo2 ) - int( termInfo1 )
            if expectConnection != realConnection:
                main.log.error( "The number of real switch connection doesn't match the number of expected connection" )
                main.writeData = -1
                return -1
            rate = disconnection / expectConnection
            return rate
    except IndexError:
        main.log.error( "Catch the wrong information of search term" )
        main.writeData = -1
        return -1

def testTopology( main, topoFile='', args='', mnCmd='', timeout=300, clean=True ):
    """
    Description:
        This function combines different wrapper functions in this module
        to simulate a topology test
    Test Steps:
        - Load topology
        - Discover topology
        - Compare topology
        - pingall
        - Bring links down
        - Compare topology
        - pingall
        - Bring links up
        - Compare topology
        - pingall
    Options:
        clean: Does sudo mn -c to clean mininet residue
        Please read mininetclidriver.py >> startNet( .. ) function for details
    Returns:
        Returns main.TRUE if the test is successful, main.FALSE otherwise
    """
    testTopoResult = main.TRUE
    compareTopoResult = main.TRUE
    topoObjectResult = main.TRUE
    stopResult = main.TRUE

    if clean:
        # Cleans minient
        stopResult = stopMininet( main )

    # Restart ONOS to clear hosts test new mininet topology
    reinstallOnosResult = reinstallOnos( main )

    # Starts topology
    startResult = startNewTopology( main, topoFile, args, mnCmd, timeout=timeout )
    # onos needs time to see the links
    time.sleep(15)

    # Gets list of switches in mininet
    #assignSwitch( main )

    testTopoResult = startResult and topoObjectResult


    return testTopoResult

def startNewTopology( main, topoFile='', args='', mnCmd='', timeout=900 ):
    """
    Description:
        This wrapper function starts new topology
    Options:
        Please read mininetclidriver.py >> startNet( .. ) function for details
    Return:
        Returns main.TRUE if topology is successfully created by mininet,
        main.FALSE otherwise
    NOTE:
        Assumes Mininet1 is the name of the handler
    """
    assert main, "There is no main variable"
    assert main.Mininet1, "Mininet 1 is not created"
    result = main.TRUE

    main.log.info( main.topoName + ": Starting new Mininet topology" )

    # log which method is being used
    if topoFile:
        main.log.info( main.topoName + ": Starting topology with " +
                       topoFile + "topology file" )
    elif not topoFile and not mnCmd:
        main.log.info( main.topoName + ": Starting topology using" +
                       " the topo file" )
    elif topoFile and mnCmd:
        main.log.error( main.topoName + ": You can only use one " +
                        "method to start a topology" )
    elif mnCmd:
        main.log.info( main.topoName + ": Starting topology with '" +
                       mnCmd + "' Mininet command" )


    result = main.Mininet1.startNet( topoFile=topoFile,
                                     args=args,
                                     mnCmd=mnCmd,
                                     timeout=timeout)

    return result

def stopMininet( main ):
    """
        Stops current topology and execute mn -c basically triggers
        stopNet in mininetclidrivers

        NOTE: Mininet should be running when issuing this command other wise
        the this function will cause the test to stop
    """
    stopResult = main.TRUE
    stopResult = main.Mininet1.stopNet()
    time.sleep( 30 )
    if not stopResult:
        main.log.info(  main.topoName + ": Did not stop Mininet topology" )
    return stopResult

def compareTopo( main ):
    """
        Compare topology( devices, links, ports, hosts ) between ONOS and
        mininet using sts
    """
    devices = []
    links = []
    ports = []
    hosts = []
    switchResult = []
    linksResult = []
    portsResult = []
    hostsResult = []
    mnSwitches = main.Mininet1.getSwitches()
    mnLinks = main.Mininet1.getLinks()
    mnHosts = main.Mininet1.getHosts()
    compareTopoResult = main.TRUE

    for i in range( main.numCtrls ):
        devices.append( json.loads( main.CLIs[ i ].devices() ) )
        links.append( json.loads( main.CLIs[ i ].links() ) )
        ports.append( json.loads(  main.CLIs[ i ].ports() ) )
        hosts.append( json.loads( main.CLIs[ i ].hosts() ) )

    # Comparing switches
    main.log.info( main.topoName + ": Comparing switches in each ONOS nodes" +
                   " with Mininet" )
    for i in range( main.numCtrls ):
        tempResult = main.Mininet1.compareSwitches( mnSwitches,
                                                    devices[ i ],
                                                    ports[ i ] )
        switchResult.append( tempResult )
        if tempResult == main.FALSE:
            main.log.error( main.topoName + ": ONOS-" + str( i + 1 ) +
                            " switch view is incorrect " )

    if all( result == main.TRUE for result in switchResult ):
        main.log.info( main.topoName + ": Switch view in all ONOS nodes "+
                       "are correct " )
    else:
        compareTopoResult = main.FALSE

    # Comparing links
    main.log.info( main.topoName + ": Comparing links in each ONOS nodes" +
                   " with Mininet" )
    for i in range( main.numCtrls ):
        tempResult = main.Mininet1.compareLinks( mnSwitches,
                                                 mnLinks,
                                                 links[ i ] )
        linksResult.append( tempResult )
        if tempResult == main.FALSE:
            main.log.error( main.topoName + ": ONOS-" + str( i + 1 ) +
                            " links view are incorrect " )

    if all( result == main.TRUE for result in linksResult ):
        main.log.info( main.topoName + ": Links view in all ONOS nodes "+
                       "are correct " )
    else:
        compareTopoResult = main.FALSE

    # Comparing hosts
    main.log.info( main.topoName + ": Comparing hosts in each ONOS nodes" +
                   " with Mininet" )
    for i in range( main.numCtrls ):
        tempResult = main.Mininet1.compareHosts( mnHosts, hosts[ i ] )
        hostsResult.append( tempResult )
        if tempResult == main.FALSE:
            main.log.error( main.topoName + ": ONOS-" + str( i + 1 ) +
                            " hosts view are incorrect " )

    if all( result == main.TRUE for result in hostsResult ):
        main.log.info( main.topoName + ": Hosts view in all ONOS nodes "+
                       "are correct " )
    else:
        compareTopoResult = main.FALSE

    return compareTopoResult

def assignSwitch( main ):
    """
        Returns switch list using getSwitch in Mininet driver
    """
    switchList = []
    assignResult = main.TRUE
    switchList =  main.Mininet1.getSwitch()
    assignResult = main.Mininet1.assignSwController( sw=switchList,
                                                     ip=main.ONOSip[ 0 ],
                                                     port=6633 )

    for sw in switchList:
        response = main.Mininet1.getSwController( sw )
        if re.search( "tcp:" + main.ONOSip[ 0 ], response ):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE

    return switchList

def connectivity( main, timeout=900, shortCircuit=True, acceptableFailed=20 ):
    """
        Use fwd app and pingall to discover all the hosts
    """
    activateResult = main.TRUE
    appCheck = main.TRUE
    getDataResult = main.TRUE
    main.log.info( main.topoName + ": Activating reactive forwarding app " )
    activateResult = main.CLIs[ 0 ].activateApp( "org.onosproject.fwd" )

    if main.hostsData:
        main.hostsData = {}
    for i in range( main.numCtrls ):
        appCheck = appCheck and main.CLIs[ i ].appToIDCheck()
        if appCheck != main.TRUE:
            main.log.warn( main.CLIs[ i ].apps() )
            main.log.warn( main.CLIs[ i ].appIDs() )

    time.sleep( main.fwdSleep )

    # Discover hosts using pingall
    pingResult = main.Mininet1.pingall( timeout=timeout,
                                        shortCircuit=shortCircuit,
                                        acceptableFailed=acceptableFailed )

    main.log.info( main.topoName + ": Deactivate reactive forwarding app " )
    activateResult = main.CLIs[ 0 ].deactivateApp( "org.onosproject.fwd" )
    for i in range( main.numCtrls ):
        appCheck = appCheck and main.CLIs[ i ].appToIDCheck()
        if appCheck != main.TRUE:
            main.log.warn( main.CLIs[ i ].apps() )
            main.log.warn( main.CLIs[ i ].appIDs() )

    return pingResult

def getHostsData( main ):
    """
        Use fwd app and pingall to discover all the hosts
    """
    activateResult = main.TRUE
    appCheck = main.TRUE
    getDataResult = main.TRUE
    main.log.info( main.topoName + ": Activating reactive forwarding app " )
    activateResult = main.CLIs[ 0 ].activateApp( "org.onosproject.fwd" )

    if main.hostsData:
        main.hostsData = {}
    for i in range( main.numCtrls ):
        appCheck = appCheck and main.CLIs[ i ].appToIDCheck()
        if appCheck != main.TRUE:
            main.log.warn( main.CLIs[ i ].apps() )
            main.log.warn( main.CLIs[ i ].appIDs() )

    time.sleep( main.fwdSleep )
    # Discover hosts using pingall
    pingResult = main.Mininet1.pingall( timeout=900 )

    hostsJson = json.loads( main.CLIs[ 0 ].hosts() )
    hosts = main.Mininet1.getHosts().keys()

    for host in hosts:
        main.hostsData[ host ] = {}
        main.hostsData[ host ][ 'mac' ] =  \
            main.Mininet1.getMacAddress( host ).upper()
        for hostj in hostsJson:
            if main.hostsData[ host ][ 'mac' ] == hostj[ 'mac' ]:
                main.hostsData[ host ][ 'id' ] = hostj[ 'id' ]
                main.hostsData[ host ][ 'vlan' ] = hostj[ 'vlan' ]
                main.hostsData[ host ][ 'location' ] = \
                            hostj[ 'location' ][ 'elementId' ] + '/' + \
                            hostj[ 'location' ][ 'port' ]
                main.hostsData[ host ][ 'ipAddresses' ] = hostj[ 'ipAddresses' ]

    if activateResult and main.hostsData:
        main.log.info( main.topoName + ": Successfully used fwd app" +
                       " to discover hosts " )
        getDataResult = main.TRUE
    else:
        main.log.info( main.topoName + ": Failed to use fwd app" +
                       " to discover hosts " )
        getDataResult = main.FALSE

    main.log.info( main.topoName + ": Deactivate reactive forwarding app " )
    activateResult = main.CLIs[ 0 ].deactivateApp( "org.onosproject.fwd" )
    for i in range( main.numCtrls ):
        appCheck = appCheck and main.CLIs[ i ].appToIDCheck()
        if appCheck != main.TRUE:
            main.log.warn( main.CLIs[ i ].apps() )
            main.log.warn( main.CLIs[ i ].appIDs() )

    # This data can be use later for intents
    print main.hostsData

    return getDataResult

def reinstallOnos( main ):
    """
    Description:
        Stop and start ONOS that clears hosts,devices etc. in order to test
        new mininet topology
    Return:
        Retruns main.TRUE for a successful restart, main.FALSE otherwise.
    """
    uninstallResult = []
    installResult = []
    stopResult = []
    startResult = []
    onosIsUpResult = []
    restartResult = main.TRUE

    main.log.info( main.topoName + ": Uninstall ONOS cluster" )
    for ip in main.ONOSip:
        uninstallResult.append( main.ONOSbench.onosUninstall( nodeIp=ip ) )

    if all( result == main.TRUE for result in uninstallResult ):
        main.log.info( main.topoName + ": Successfully uninstall ONOS cluster" )
    else:
        restartResult = main.FALSE
        main.log.error( main.topoName + ": Failed to uninstall ONOS cluster" )

    time.sleep( main.startUpSleep )

    main.log.info( main.topoName + ": Installing ONOS cluster" )

    for i in range( main.numCtrls ):
        installResult.append( main.ONOSbench.onosInstall(
                                                    node=main.ONOSip[ i ] ) )

    if all( result == main.TRUE for result in installResult ):
        main.log.info( main.topoName + ": Successfully installed ONOS cluster" )
    else:
        restartResult = main.FALSE
        main.log.error( main.topoName + ": Failed to install ONOS cluster" )

    for i in range( main.numCtrls ):
        onosIsUpResult.append( main.ONOSbench.isup( main.ONOSip[ i ] ) )

    if all( result == main.TRUE for result in onosIsUpResult ):
        main.log.report( "ONOS instance is up and ready" )
    else:
        main.log.report( "ONOS instance may not be up, stop and " +
                         "start ONOS again " )
        for i in range( main.numCtrls ):
            stopResult.append( main.ONOSbench.onosStop( main.ONOSip[ i ] ) )

        if all( result == main.TRUE for result in stopResult ):
            main.log.info( main.topoName + ": Successfully stop ONOS cluster" )
        else:
            main.log.error( main.topoName + ": Failed to stop ONOS cluster" )

        for i in range( main.numCtrls ):
            startResult.append( main.ONOSbench.onosStart( main.ONOSip[ i ] ) )

        if all( result == main.TRUE for result in startResult ):
            main.log.info( main.topoName + ": Successfully start ONOS cluster" )
        else:
            main.log.error( main.topoName + ": Failed to start ONOS cluster" )

    main.log.info( main.topoName + ": set up ONOS secure SSH" )
    secureSshResult = []
    for i in range( int( main.numCtrls ) ):
        secureSshResult.append( main.onosSecureSSH( node=main.ONOSip[i] ) )
    if all( result == main.TRUE for result in secureSshResult ):
        main.log.info( main.topoName + ": Successfully set up ONOS secure SSH" )
    else:
        main.log.error( main.topoName + ": Failed to set up ONOS secure SSH" )
        restartResult = main.FALSE

    main.log.info( main.topoName + ": Starting ONOS CLI" )
    cliResult = []
    for i in range( main.numCtrls ):
        cliResult.append( main.CLIs[ i ].startOnosCli( main.ONOSip[ i ] ) )

    if all( result == main.TRUE for result in cliResult ):
        main.log.info( main.topoName + ": Successfully start ONOS cli" )
    else:
        main.log.error( main.topoName + ": Failed to start ONOS cli" )
        restartResult = main.FALSE


    return restartResult



