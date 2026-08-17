# Detection rules for UniFi networks

The display only shows what your detection rules generate. If your Elastic
deployment ingests logs from Ubiquiti UniFi gear (a UniFi gateway, switches
and access points behind a UniFi Network application), this page lists the
prebuilt Elastic rules that actually fire on that data, and what to ship so
they have something to work with.

There is no official UniFi integration, so this uses generic integrations
that match the formats UniFi emits.

## 1. Ship the data

**Firewall and gateway logs over syslog.** In the UniFi Network application,
enable remote syslog (Settings > System > Advanced > Remote Logging on
current versions) and point it at an Elastic Agent running the
[Iptables integration](https://www.elastic.co/docs/reference/integrations/iptables)
with its syslog input. UniFi gateways log firewall accepts and denies in
iptables format, which this integration parses into ECS network events.

**IPS/IDS alerts.** UniFi's intrusion prevention is Suricata underneath.
With remote logging enabled, its detections go out over syslog too; the
[CEF integration](https://www.elastic.co/docs/reference/integrations/cef)
decodes them into ECS with `event.kind: alert`, which is what the promotion
rule below keys on. Check one ingested IPS document to confirm the
`event.kind` value before relying on it.

**Flow records.** If your gateway supports NetFlow/IPFIX export (UniFi OS
gateways do on recent Network application versions), point it at the
[NetFlow Records integration](https://www.elastic.co/docs/reference/integrations/netflow).
Flows give the machine learning rules much more signal than firewall logs
alone.

## 2. Enable these prebuilt rules

In Kibana: **Security > Rules > Detection rules > Add Elastic rules**, then
search by name.

| Rule | Type | What it does with UniFi data |
| --- | --- | --- |
| External Alerts | Promotion | Turns every UniFi IPS detection (`event.kind: alert` in `logs-*`) into a Security alert. The single highest-value rule for a UniFi network: your IPS findings land on the display's severity tiles. |
| Threat Intel IP Address Indicator Match | Indicator match | Matches source and destination IPs in your firewall and flow events against threat intelligence feeds. Needs a threat intel source ingesting too, for example the free [AbuseCH integration](https://www.elastic.co/docs/reference/integrations/ti_abusech). |
| Spike in Network Traffic | Machine learning | Flags unusual bursts of network events. |
| Spike in Firewall Denies | Machine learning | Flags bursts of denied traffic: scanning, misbehaving devices, or C2 retry loops. Pairs well with UniFi's default-deny logging on IoT VLANs. |
| Spike in Network Traffic To a Country | Machine learning | Flags unusual volumes to a specific destination country. |
| Network Traffic to Rare Destination Country | Machine learning | Flags first-seen or rare destination countries, a common C2 and exfiltration tell. |

Notes on the machine learning rules:

- They need a Platinum licence or better, and enabling the rule starts the
  associated anomaly detection job automatically.
- The jobs read ECS network events from the Security solution's data view,
  so iptables and NetFlow data qualifies. Elastic's docs list packet-based
  integrations (Packetbeat, Network Packet Capture, Elastic Defend) as the
  supported sources, so treat results on firewall-only data as best effort;
  flow export improves them considerably.
- Anomaly jobs baseline your network first. Expect little for the first few
  days, then alerts only when something deviates.

## 3. What not to expect

Most of the prebuilt rule catalogue targets host telemetry (process,
registry, authentication events from Elastic Defend or system logs) and
will never fire on network-only data. Enabling the whole catalogue does no
harm, but the rules above are the ones UniFi data can actually trigger. If
you also enrol endpoints with Elastic Defend, enable the platform-relevant
rule set for those separately.

A quiet display is therefore not necessarily a broken one. Generate a test
IPS event (the EICAR download test works if IPS signatures cover it) or
temporarily lower an ML rule's severity threshold to confirm the pipeline
end to end.
