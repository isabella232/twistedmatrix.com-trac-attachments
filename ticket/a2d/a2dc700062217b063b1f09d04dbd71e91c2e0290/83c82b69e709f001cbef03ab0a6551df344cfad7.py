#!/usr/bin/env python

import base64
import paramiko
import logging 


if __name__ == '__main__':
    hostname = 'localhost'
    port = 1234
    username = 'user'
    password = 'password'
    
    # setup logging
    paramiko.util.log_to_file('demo_sftp.log')
    #logging.getLogger("paramiko").setLevel(logging.DEBUG)

    # Connect and use paramiko Transport to negotiate SSH2 across the connection
    publicKey = 'AAAAB3NzaC1yc2EAAAABIwAAAGEArzJx8OYOnJmzf4tfBEvLi8DVPrJ3/c9k2I/Az64fxjHf9imyRJbixtQhlH9lfNjUIx+4LmrJH5QNRsFporcHDKOTwTTYLh5KmRpslkYHRivcJSkbh/C+BR3utDS555mV'
    pmServerPublicKey = paramiko.RSAKey(data=base64.decodestring(publicKey))

    trans = paramiko.Transport((hostname, port))
    trans.window_size = 134217727

    trans.connect(username=username, password=password, hostkey=pmServerPublicKey)
    trans.set_keepalive(1)

    chan = trans.open_session()
    chan.set_combine_stderr(True)


    sftp = paramiko.SFTPClient.from_transport(trans)

    sftp.get('C:/1Gbyte.bin', 'test_get.txt') # This file must be > 1MB in size to trigger rekeying
    
    trans.close()



