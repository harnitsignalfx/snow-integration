# snow-integration

Usage:

1. Place xmlStats.py in the folder `/usr/share/collectd/snow-plugin/`
2. Either copy the `collectd/custom` snippet from agent.yaml provided or overwrite the existing agent.yaml (should be under /etc/signalfx/ by default)
3. Modify the agent.yaml with the correct path of the xml file. Its currently set to `http://localhost:8080/snow/xmlstats.do.xml`
4. The agent should automatically pick up the changes to the yaml. You should start seeing metrics soon.
