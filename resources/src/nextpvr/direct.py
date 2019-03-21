def LiveTV (parm):
        #return None
        try:
            #import hdhr
            #lineUp = hdhr.LineUp()
            #for channel in lineUp.channels.values():
            #    if parm[0]==channel.name:
            #        print channel.name
            #        print channel.sources
            #        return channel.sources[0]['url'] +  '?transcode=internet540'
            ##responses = hdhr.discovery.discover(discovery.TUNER_DEVICE)
    
            #if not responses: raise NoDevicesException()
    
            #if not lineUps: raise NoCompatibleDevicesException()
        catch:
            print "HDHR Not configured"

        if parm == '961':
            channel = 24
            program = 1
        elif parm == '968':
            channel = 42
            program = 1
        elif parm == '969':
            channel = 13
            program = 1
        elif parm == '978':
            channel = 43
            program = 1
        elif parm == '980':
            channel = 17
            program = 2
        elif parm == '981':
            channel = 20
            program = 3
        elif parm == '985':
            channel = 27
            program = 2
        elif parm == '989':
            channel = 22
            program = 3
        elif parm == '992':
            channel = 34
            program = 1
        elif parm == '993':
            channel = 30
            program = 2
        elif parm == '994':
            channel = 40
            program = 1
        elif parm == '995':
            channel = 25
            program = 3
        elif parm == '996':
            channel = 33
            program = 3
        elif parm == '6.1':
            channel = 14
            program = 1
        elif parm == '6.2':
            channel = 14
            program = 2
        else:            
            return None

        url = 'hdhomerun://103B4218-0/tuner0?channel=auto:' + `channel`+ '&program=' + `program`
        return url

