SNMP
====

This block provides a SNMP Manager that runs inside nio. 


Properties
----------

-  **agent_host**: The host IP for the SNMP Agent to which this manager will connect. Defaults to '127.0.0.1'.
-  **agent_port**: The desired port for the Agent. Defaults to 161
-  **pool_interval**: Interval between SNMP Gets to the Agent. Defaults to 10 seconds 
-  **timeout**: Timeout when executing a SNMP GET. Defaults to 1 second 
-  **retries**: Number of retries when executing a SNMP GET. Defaults to 5 
-  **lookup_names**: Lookup names when executing a SNMP GET. Converts to human readable string. Defaults to False 
-  **lookup_values**: Lookup values when executing a SNMP GET. Converts to human readable string. Defaults to False 
-  **oids**: List of oids . Example ["1.3.6.1.2.1.31.1.1.1.10.2", "1.3.6.1.2.1.31.1.1.1.6.2"] 

Dependencies
------------

  pysnmp module

Commands
--------


Input
-----


Output
------

  Signals with data attributes containing results of SNMP GET
  
  Example of Signals:

    With Error:
         { "error": "No response received" }
    
    Without lookup:
        {'1.3.6.1.2.1.1.1.0': "b'SunOS zeus.snmplabs.com 4.1.3_U1 1 sun4m'"}
    
    With lookup:
        {'SNMPv2-SMI::mib-2."31.1.1.1.6.2"': '227651521193'}
        {'SNMPv2-MIB::sysDescr."0"': "b'SunOS zeus.snmplabs.com 4.1.3_U1 1 sun4m'"}