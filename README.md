SNMPGet
=======
This block provides a SNMP Manager that runs inside nio.

Properties
----------
- **agent_host**: The host IP for the SNMP Agent to which this manager will connect. Defaults to `127.0.0.1`.
- **agent_port**: The desired port for the Agent. Defaults to `161`.
- **community**: SNMP community. Defaults to `public`.
- **exclude_existing**: If `False`, the original input signal attributes will be included in the output signal.
- **lookup_names**: Lookup names when executing a SNMP GET. Converts to human readable string. Defaults to `False`.
- **lookup_values**: Lookup values when executing a SNMP GET. Converts to human readable string. Defaults to `False`.
- **oids**: List of oids . Example `['1.3.6.1.2.1.31.1.1.1.10.2', '1.3.6.1.2.1.31.1.1.1.6.2']`.
- **retries**: Number of retries when executing a SNMP GET. Defaults to `5`.
- **snmp_version**: SNMP v1 or v2.
- **timeout**: Timeout when executing a SNMP GET. Defaults to `1` second.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: Signals with data attributes containing results of SNMP GET.

Commands
--------
None

Dependencies
------------
-   [pysnmp](https://pypi.python.org/pypi/pysnmp/)

Output Example
--------------
Example of Signals:
  **With Error**:
  ```
  { "error": "No response received" }
  ```
  **Without lookup**:
  ```
  {'1.3.6.1.2.1.1.1.0': "b'SunOS zeus.snmplabs.com 4.1.3_U1 1 sun4m'"}
  ```
  **With lookup**:
  ```
  {'SNMPv2-SMI::mib-2."31.1.1.1.6.2"': '227651521193'}
  {'SNMPv2-MIB::sysDescr."0"': "b'SunOS zeus.snmplabs.com 4.1.3_U1 1 sun4m'"}
  ```

SNMPTrap
========
This block provides a SNMP Trap catcher that runs inside nio.

Properties
----------
- **ip_address**: The IP address this block binds to, this address will be used by Agent to send traps to. Defaults to `127.0.0.1`.
- **port**: The port Agent will be connecting to. Defaults to `162`.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **trap**: Signals with trap data attributes.

Commands
--------
None

Dependencies
------------
-   [pysnmp](https://pypi.python.org/pypi/pysnmp/)

Output Example
--------------
Example of Signal:
  ```
  {
  	'var-binds': {
  		'1.3.6.1.3.6.1.1': {
  			'value': {
  				'simple': {
  					'string-value': b'configured'
  				}
  			}
  		},
     	'1.3.6.1.3.6.1.0': {
     		'value': {
     			'simple': {
     				'string-value': b'SNMPTrapService'
     			}
     		}
     	},
     	'1.3.6.1.2.1.1.3.0': {
     		'value': {
     			'application-wide': {
     				'timeticks-value': 206042
     			}
     		}
     	},
     	'1.3.6.1.6.3.1.1.4.1.0': {
     		'value': {
     			'simple': {
     				'objectID-value': '1.3.6.1.3.6.6.1'
     			}
     		}
     	}
    },
	'transport_address': '127.0.0.1.9100',
  	'transport_domain': '1.3.6.1.6.1.1'
  }
  ```

SNMPWalk
========
This block provides a SNMP walker than runs inside nio.

Properties
----------
- **agent_host**: The host IP for the SNMP Agent to which this manager will connect. Defaults to `127.0.0.1`.
- **agent_port**: The desired port for the Agent. Defaults to `161`.
- **community**: SNMP community. Defaults to `public`.
- **exclude_existing**: If false, the original input signal attributes will be included in the output signal.
- **lookup_names**: Lookup names when executing a SNMP GET. Converts to human readable string. Defaults to `False`.
- **lookup_values**: Lookup values when executing a SNMP GET. Converts to human readable string. Defaults to `False`.
- **oids**: List of oids . Example `['1.3.6.1.2.1.31.1.1.1.10.2', '1.3.6.1.2.1.31.1.1.1.6.2']`.
- **retries**: Number of retries when executing a SNMP GET. Defaults to `5`.
- **snmp_version**: SNMP v1 or v2.
- **timeout**: Timeout when executing a SNMP GET. Defaults to `1` second.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: Signals with walk data attributes.

Commands
--------
None

Dependencies
------------
-   [pysnmp](https://pypi.python.org/pypi/pysnmp/)
