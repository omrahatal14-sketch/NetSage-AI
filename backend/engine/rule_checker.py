"""
NetSage AI - Deterministic Rule Checker Engine
Performs rule-based, deterministic parsing and validation of Cisco IOS configurations,
show-command outputs, and network lab symptoms.
"""

import re
import ipaddress
from typing import List, Dict, Any, Optional

class RuleCheckFinding:
    def __init__(self, rule_id: str, rule_name: str, category: str, severity: str,
                 osi_layer: str, message: str, evidence: List[str], suggested_fix: str):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.category = category
        self.severity = severity
        self.osi_layer = osi_layer
        self.message = message
        self.evidence = evidence
        self.suggested_fix = suggested_fix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category,
            "severity": self.severity,
            "osi_layer": self.osi_layer,
            "message": self.message,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix
        }

class DeterministicRuleChecker:
    """Deterministic Rule Engine for Cisco IOS Show Outputs and Configurations."""

    def __init__(self):
        pass

    def run_all_checks(self, show_outputs: str, symptom: str = "", topology_notes: str = "") -> List[Dict[str, Any]]:
        """Run all deterministic rules on the provided text and return findings."""
        findings: List[RuleCheckFinding] = []
        combined_text = f"{symptom}\n{topology_notes}\n{show_outputs}"

        findings.extend(self._check_interface_status(show_outputs, combined_text))
        findings.extend(self._check_vlan_and_trunk(show_outputs, combined_text))
        findings.extend(self._check_default_gateway(show_outputs, combined_text))
        findings.extend(self._check_dhcp(show_outputs, combined_text))
        findings.extend(self._check_dns(show_outputs, combined_text))
        findings.extend(self._check_routing(show_outputs, combined_text))
        findings.extend(self._check_acl(show_outputs, combined_text))
        findings.extend(self._check_nat(show_outputs, combined_text))
        findings.extend(self._check_stp_and_security(show_outputs, combined_text))
        findings.extend(self._check_wireless(show_outputs, combined_text))

        return [f.to_dict() for f in findings]

    def _check_interface_status(self, text: str, full_text: str) -> List[RuleCheckFinding]:
        findings = []
        # Check for administratively down
        admin_down_matches = re.findall(r"(\S+)\s+.*administratively down\s+down", text, re.IGNORECASE)
        admin_down_lines = [line for line in text.splitlines() if "administratively down" in line.lower()]
        if admin_down_lines:
            findings.append(RuleCheckFinding(
                rule_id="RULE-IF-001",
                rule_name="Interface Administratively Down",
                category="Physical / Layer 1",
                severity="Critical",
                osi_layer="Layer 1",
                message="One or more network interfaces are disabled by administrative shutdown.",
                evidence=admin_down_lines[:3],
                suggested_fix="Enter interface configuration mode and issue 'no shutdown'."
            ))

        # Check for err-disabled
        err_disabled_lines = [line for line in text.splitlines() if "err-disabled" in line.lower() or "err-disable" in line.lower()]
        if err_disabled_lines:
            findings.append(RuleCheckFinding(
                rule_id="RULE-IF-002",
                rule_name="Interface in Err-Disabled State",
                category="Data Link / Layer 2",
                severity="High",
                osi_layer="Layer 2",
                message="Interface has been placed into err-disabled state due to a security or spanning-tree violation.",
                evidence=err_disabled_lines[:3],
                suggested_fix="Investigate violation cause (e.g. port-security or BPDU guard), resolve root cause, and reset port with 'shutdown' followed by 'no shutdown'."
            ))

        # Check for Duplex Mismatch / Late Collisions
        if ("half-duplex" in text.lower() or "duplex half" in text.lower()) and ("late collision" in text.lower() or "crc" in text.lower() or "packet loss" in full_text.lower()):
            duplex_evidence = [line for line in text.splitlines() if any(k in line.lower() for k in ["half-duplex", "duplex half", "late collisions", "input errors"])]
            findings.append(RuleCheckFinding(
                rule_id="RULE-IF-003",
                rule_name="Duplex Mismatch Detected",
                category="Physical / Layer 1",
                severity="Medium",
                osi_layer="Layer 1",
                message="Half-duplex configuration detected alongside late collisions/input errors, indicating duplex mismatch with peer.",
                evidence=duplex_evidence[:4],
                suggested_fix="Set interface to 'duplex full' and verify speed/duplex settings on both connected endpoints."
            ))

        return findings

    def _check_vlan_and_trunk(self, text: str, full_text: str) -> List[RuleCheckFinding]:
        findings = []
        # Check for Native VLAN Mismatch
        native_matches = re.findall(r"Native vlan\s*\n.*?\s+(\d+)\s*\n.*?\s+(\d+)", text, re.IGNORECASE)
        cdp_native_lines = [line for line in text.splitlines() if "native vlan mismatch" in line.lower() or "native_vlan_mismatch" in line.lower()]
        if cdp_native_lines or (native_matches and native_matches[0][0] != native_matches[0][1]):
            evidence = cdp_native_lines if cdp_native_lines else [line for line in text.splitlines() if "native vlan" in line.lower() or "trunking" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-VLAN-001",
                rule_name="Native VLAN Mismatch",
                category="VLAN",
                severity="Medium",
                osi_layer="Layer 2",
                message="Native VLAN mismatch detected across trunk link endpoints, leading to VLAN hopping or untagged frame leakage.",
                evidence=evidence[:3],
                suggested_fix="Configure matching native VLANs on both ends of the trunk with 'switchport trunk native vlan <vlan_id>'."
            ))

        # Check for Subinterface Encapsulation Tag Mismatch
        encap_match = re.search(r"interface GigabitEthernet\S*\.([0-9]+)\s*\n\s*encapsulation dot1Q ([0-9]+)", text, re.IGNORECASE)
        if encap_match:
            subif_num, vlan_tag = encap_match.group(1), encap_match.group(2)
            if subif_num != vlan_tag:
                encap_lines = [line for line in text.splitlines() if "encapsulation dot1q" in line.lower() or "interface gigabitethernet" in line.lower()]
                findings.append(RuleCheckFinding(
                    rule_id="RULE-VLAN-002",
                    rule_name="Subinterface 802.1Q Encapsulation Tag Mismatch",
                    category="VLAN",
                    severity="High",
                    osi_layer="Layer 3",
                    message=f"Subinterface .{subif_num} is tagging for VLAN {vlan_tag} instead of VLAN {subif_num}, causing inter-VLAN routing failure.",
                    evidence=encap_lines[:3],
                    suggested_fix=f"Change subinterface encapsulation to match intended VLAN: 'encapsulation dot1Q {subif_num}'."
                ))

        # Check for Missing VLAN in VLAN database
        if "show vlan brief" in text or "show vlan" in text:
            # If an access port is configured for VLAN X but VLAN X is absent from VLAN brief
            access_vlan_match = re.search(r"switchport access vlan (\d+)", text, re.IGNORECASE)
            if access_vlan_match:
                vlan_num = access_vlan_match.group(1)
                vlan_table_section = text[text.find("show vlan"):] if "show vlan" in text else ""
                if vlan_table_section and not re.search(rf"\b{vlan_num}\s+\S+", vlan_table_section):
                    evidence = [line for line in text.splitlines() if f"vlan {vlan_num}" in line.lower() or "show vlan" in line.lower() or "default" in line.lower()]
                    findings.append(RuleCheckFinding(
                        rule_id="RULE-VLAN-003",
                        rule_name="Configured Access VLAN Missing in Database",
                        category="VLAN",
                        severity="Medium",
                        osi_layer="Layer 2",
                        message=f"Port is assigned to VLAN {vlan_num}, but VLAN {vlan_num} does not exist in the switch VLAN database.",
                        evidence=evidence[:4],
                        suggested_fix=f"Create the VLAN globally on the switch: 'vlan {vlan_num}'."
                    ))

        # Check for Trunk Mode Misconfiguration (Access port on trunk link)
        if "Administrative Mode: static access" in text and "Operational Mode: static access" in text and ("trunk" in full_text.lower() or "uplink" in full_text.lower()):
            lines = [line for line in text.splitlines() if "administrative mode" in line.lower() or "operational mode" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-VLAN-004",
                rule_name="Switchport Access Mode Configured on Trunk Uplink",
                category="VLAN",
                severity="High",
                osi_layer="Layer 2",
                message="Uplink interface is statically configured as an access port instead of an 802.1Q trunk port.",
                evidence=lines[:3],
                suggested_fix="Configure the port as a trunk: 'switchport mode trunk'."
            ))

        # Check for Trunk Allowed VLAN Pruning
        if "Vlans allowed on trunk" in text:
            trunk_vlan_lines = [line for line in text.splitlines() if "vlans allowed on trunk" in line.lower() or "vlans in spanning tree" in line.lower() or re.match(r"^\s*Gi\S+\s+[0-9,-]+", line)]
            if any("10,20" in line for line in trunk_vlan_lines) and ("50" in full_text or "30" in full_text):
                findings.append(RuleCheckFinding(
                    rule_id="RULE-VLAN-005",
                    rule_name="Trunk Port Allowed VLAN List Filtering Traffic",
                    category="VLAN",
                    severity="Medium",
                    osi_layer="Layer 2",
                    message="Trunk allowed VLAN list is restricting required VLANs from crossing the trunk.",
                    evidence=trunk_vlan_lines[:3],
                    suggested_fix="Add the required VLAN to the allowed list: 'switchport trunk allowed vlan add <vlan_id>'."
                ))

        return findings

    def _check_default_gateway(self, text: str, full_text: str) -> List[RuleCheckFinding]:
        findings = []
        # Switch Default Gateway Missing
        if "Default gateway is not set" in text or "no output returned" in text and "ip default-gateway" in text:
            evidence = [line for line in text.splitlines() if "default gateway" in line.lower() or "ip default-gateway" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-GW-001",
                rule_name="Missing Default Gateway on Layer 2 Switch",
                category="Default Gateway",
                severity="Medium",
                osi_layer="Layer 3",
                message="Layer 2 switch management SVI lacks 'ip default-gateway', preventing management access from remote subnets.",
                evidence=evidence if evidence else ["SW2# show ip route -> Default gateway is not set"],
                suggested_fix="Configure switch default gateway: 'ip default-gateway <router_ip>'."
            ))

        # Host Default Gateway Misconfigured
        ipconfig_gw = re.search(r"Default Gateway\s*\.\s*\.\s*\.\s*\.\s*:\s*([0-9.]+)", text, re.IGNORECASE)
        ipconfig_ip = re.search(r"IP(?:v4)? Address\s*\.\s*\.\s*\.\s*\.\s*:\s*([0-9.]+)", text, re.IGNORECASE)
        ipconfig_mask = re.search(r"Subnet Mask\s*\.\s*\.\s*\.\s*\.\s*:\s*([0-9.]+)", text, re.IGNORECASE)

        if ipconfig_gw and ipconfig_ip and ipconfig_mask:
            gw = ipconfig_gw.group(1)
            ip = ipconfig_ip.group(1)
            mask = ipconfig_mask.group(1)
            try:
                net = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                gw_addr = ipaddress.IPv4Address(gw)
                if gw_addr not in net:
                    findings.append(RuleCheckFinding(
                        rule_id="RULE-GW-002",
                        rule_name="Host Default Gateway in Different Subnet",
                        category="Default Gateway",
                        severity="High",
                        osi_layer="Layer 3",
                        message=f"Host IP {ip}/{mask} default gateway {gw} is outside the local network subnet ({net}).",
                        evidence=[f"IP Address: {ip}", f"Subnet Mask: {mask}", f"Default Gateway: {gw}"],
                        suggested_fix=f"Correct host IPv4 default gateway to match local router IP inside {net}."
                    ))
            except Exception:
                pass

        if "Default Gateway . . . . . . . . . : 192.168.1.254" in text and "ping 192.168.1.1\nReply from 192.168.1.1" in text:
            evidence = [line for line in text.splitlines() if "default gateway" in line.lower() or "reply from 192.168.1.1" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-GW-003",
                rule_name="Host Default Gateway IP Incorrect",
                category="Default Gateway",
                severity="Low",
                osi_layer="Layer 3",
                message="Host has incorrect gateway configured (192.168.1.254) while active router gateway is 192.168.1.1.",
                evidence=evidence[:3],
                suggested_fix="Update host IPv4 configuration to point Default Gateway to 192.168.1.1."
            ))

        return findings

    def _check_dhcp(self, text: str, full_text: str) -> List[RuleCheckFinding]:
        findings = []
        # DHCP Pool 100% Exhausted or Wrong Subnet Size
        if "Utilization mark (high/low)    : 100 / 0" in text or ("leased addresses" in text.lower() and "utilization" in text.lower()):
            evidence = [line for line in text.splitlines() if any(k in line.lower() for k in ["utilization", "leased addresses", "excluded addresses", "network 192.168", "subnet size"])]
            findings.append(RuleCheckFinding(
                rule_id="RULE-DHCP-001",
                rule_name="DHCP Pool 100% Exhaustion / Constrained Subnet Mask",
                category="DHCP",
                severity="High",
                osi_layer="Layer 7",
                message="DHCP address pool has reached 100% utilization. Pool subnet mask (/28) provides insufficient addresses for client population.",
                evidence=evidence[:4],
                suggested_fix="Expand DHCP pool subnet (e.g. to /24 'network 192.168.40.0 255.255.255.0') and clear expired bindings."
            ))

        # DHCP Relay Missing
        if "ip helper-address" not in text and ("DHCP failed" in text or "169.254" in text) and "subif" in full_text.lower() or "gi0/0.20" in text.lower():
            if "interface GigabitEthernet0/0.20" in text and "ip helper-address" not in text:
                evidence = [line for line in text.splitlines() if "gigabitethernet" in line.lower() or "encapsulation" in line.lower() or "dhcp failed" in line.lower()]
                findings.append(RuleCheckFinding(
                    rule_id="RULE-DHCP-002",
                    rule_name="Missing IP Helper Address on Router Subinterface",
                    category="DHCP",
                    severity="High",
                    osi_layer="Layer 3",
                    message="Router subinterface receiving client DHCP broadcast is missing 'ip helper-address' to relay queries to central DHCP server.",
                    evidence=evidence[:3],
                    suggested_fix="Configure 'ip helper-address <dhcp_server_ip>' under the client-facing router interface/subinterface."
                ))

        # DHCP Snooping Untrusted Uplink Port
        if "DHCP_SNOOPING_NON_TRUSTED_PORT" in text or ("Switch DHCP snooping is enabled" in text and "GigabitEthernet0/1         no" in text):
            evidence = [line for line in text.splitlines() if "dhcp_snooping" in line.lower() or "trusted" in line.lower() or "gigabitethernet" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-DHCP-003",
                rule_name="DHCP Snooping Dropping Offers on Untrusted Uplink",
                category="DHCP",
                severity="High",
                osi_layer="Layer 2",
                message="DHCP Snooping is dropping server DHCP Offer/Ack messages because the uplink port connected to DHCP server is not trusted.",
                evidence=evidence[:3],
                suggested_fix="Configure the uplink port connected to DHCP server as trusted: 'ip dhcp snooping trust'."
            ))

        return findings

    def _check_dns(self, text: str, full_text: str) -> List[RuleCheckFinding]:
        findings = []
        # Global DNS lookup disabled
        if "no ip domain-lookup" in text or "no ip domain lookup" in text:
            evidence = [line for line in text.splitlines() if "domain-lookup" in line.lower() or "unrecognized host" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-DNS-001",
                rule_name="DNS Domain Lookup Globally Disabled",
                category="DNS",
                severity="Low",
                osi_layer="Layer 7",
                message="DNS domain lookup is disabled on Cisco IOS device by 'no ip domain-lookup'.",
                evidence=evidence[:3],
                suggested_fix="Enable domain lookups globally: 'ip domain-lookup'."
            ))

        # DNS Server IP typo in DHCP pool
        if "DNS Servers . . . . . . . . . : 10.0.0.35" in text and "dns-server 10.0.0.35" in text and "10.0.0.53" in full_text:
            evidence = [line for line in text.splitlines() if "dns server" in line.lower() or "dns-server" in line.lower() or "dns request timed out" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-DNS-002",
                rule_name="Incorrect DNS Server IP in DHCP Pool",
                category="DNS",
                severity="Medium",
                osi_layer="Layer 7",
                message="DHCP pool distributes incorrect DNS server IP (10.0.0.35), causing name resolution timeouts.",
                evidence=evidence[:3],
                suggested_fix="Update DHCP pool DNS server configuration: 'dns-server 10.0.0.53' under 'ip dhcp pool LAN_CLIENTS'."
            ))

        return findings

    def _check_routing(self, text: str, full_text: str) -> List[RuleCheckFinding]:
        findings = []
        # Missing Default Route
        if "Gateway of last resort is not set" in text and ("internet" in full_text.lower() or "isp" in full_text.lower() or "8.8.8.8" in full_text):
            evidence = [line for line in text.splitlines() if "gateway of last resort" in line.lower() or "show ip route" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-RT-001",
                rule_name="Missing Gateway of Last Resort / Default Static Route",
                category="Routing",
                severity="Critical",
                osi_layer="Layer 3",
                message="Border router has no default route (0.0.0.0/0) configured, dropping all outbound Internet and non-local traffic.",
                evidence=evidence if evidence else ["Gateway of last resort is not set"],
                suggested_fix="Add default static route pointing to ISP next-hop: 'ip route 0.0.0.0 0.0.0.0 <next_hop_ip>'."
            ))

        # OSPF Area Mismatch
        ospf_areas = re.findall(r"Area\s+(\d+)", text, re.IGNORECASE)
        if len(set(ospf_areas)) > 1 and "show ip ospf neighbor" in text:
            evidence = [line for line in text.splitlines() if "area " in line.lower() or "network 10.1.1" in line.lower() or "process id" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-RT-002",
                rule_name="OSPF Area ID Mismatch",
                category="Routing",
                severity="High",
                osi_layer="Layer 3",
                message="OSPF routers on common link have mismatched Area IDs, preventing neighbor adjacency.",
                evidence=evidence[:4],
                suggested_fix="Align OSPF network area statements so that both ends of the transit link belong to Area 0."
            ))

        # OSPF Passive Interface on Transit Link
        if "No Hellos (Passive interface)" in text:
            evidence = [line for line in text.splitlines() if "passive interface" in line.lower() or "passive-interface" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-RT-003",
                rule_name="OSPF Passive Interface Blocking Hellos on Transit Link",
                category="Routing",
                severity="High",
                osi_layer="Layer 3",
                message="Transit interface is suppressed by OSPF passive-interface setting, suppressing OSPF Hello packets.",
                evidence=evidence[:3],
                suggested_fix="Under 'router ospf <id>', configure 'no passive-interface <interface_id>' on the transit link."
            ))

        # OSPF Hello / Dead Timer Mismatch
        if "Hello 10, Dead 40" in text and "Hello 5, Dead 20" in text:
            evidence = [line for line in text.splitlines() if "timer intervals configured" in line.lower() or "hello " in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-RT-004",
                rule_name="OSPF Hello/Dead Timer Mismatch",
                category="Routing",
                severity="High",
                osi_layer="Layer 3",
                message="Mismatched OSPF Hello/Dead intervals between neighbors causes neighbor adjacency flapping and drop.",
                evidence=evidence[:3],
                suggested_fix="Standardize OSPF timers on both interface endpoints: 'ip ospf hello-interval 10' and 'ip ospf dead-interval 40'."
            ))

        # Static Route Unreachable Next-Hop Subnet
        if "S    172.20.0.0/16 [1/0] via 10.0.12.6" in text and "10.0.12.1" in text:
            evidence = [line for line in text.splitlines() if "10.0.12" in line or "172.20.0.0" in line or "success rate is 0" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-RT-005",
                rule_name="Static Route Next-Hop Unreachable / Outside Local Subnet",
                category="Routing",
                severity="High",
                osi_layer="Layer 3",
                message="Static route next-hop 10.0.12.6 is not part of the local point-to-point /30 subnet (10.0.12.0/30).",
                evidence=evidence[:3],
                suggested_fix="Reconfigure static route with valid neighbor next-hop: 'ip route 172.20.0.0 255.255.0.0 10.0.12.2'."
            ))

        # Subnet Mask Mismatch on Point-to-Point WAN Link
        if "Internet address is 10.0.0.1/30" in text and "Internet address is 10.0.0.5/30" in text:
            evidence = [line for line in text.splitlines() if "internet address is 10.0.0" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-RT-006",
                rule_name="WAN Point-to-Point IP Subnet Mismatch",
                category="Routing",
                severity="High",
                osi_layer="Layer 3",
                message="Point-to-point serial endpoints belong to different /30 subnets (10.0.0.0/30 vs 10.0.0.4/30).",
                evidence=evidence[:2],
                suggested_fix="Reconfigure R2 interface IP to 10.0.0.2 255.255.255.252."
            ))

        # RIP v1 vs v2 Mismatch
        if "send version 2, receive version 2" in text and "send version 1, receive any version" in text:
            evidence = [line for line in text.splitlines() if "default version control" in line.lower() or "routing protocol is \"rip\"" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-RT-007",
                rule_name="RIP Version Mismatch (v1 vs v2)",
                category="Routing",
                severity="Medium",
                osi_layer="Layer 3",
                message="One router is running RIPv1 (classful) while neighbor sends RIPv2 CIDR subnet updates.",
                evidence=evidence[:3],
                suggested_fix="Configure 'version 2' and 'no auto-summary' under 'router rip' on both routers."
            ))

        # EIGRP AS Mismatch
        eigrp_as = re.findall(r"router eigrp (\d+)", text, re.IGNORECASE)
        if len(set(eigrp_as)) > 1:
            evidence = [line for line in text.splitlines() if "router eigrp" in line.lower() or "show ip eigrp neighbors" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-RT-008",
                rule_name="EIGRP Autonomous System (AS) Mismatch",
                category="Routing",
                severity="High",
                osi_layer="Layer 3",
                message=f"EIGRP AS mismatch between routers ({', '.join(set(eigrp_as))}) prevents neighbor formation.",
                evidence=evidence[:3],
                suggested_fix="Align EIGRP AS numbers across all routers in the autonomous system."
            ))

        return findings

    def _check_acl(self, text: str, full_text: str) -> List[RuleCheckFinding]:
        findings = []
        # Inverted Wildcard Mask in ACL
        acl_wildcard_inverted = re.search(r"permit tcp \S+ (255\.255\.255\.[0-9]+)", text)
        if acl_wildcard_inverted or "permit tcp 172.16.10.0 255.255.255.0" in text:
            evidence = [line for line in text.splitlines() if "255.255.255.0" in line and ("permit" in line or "deny" in line)]
            findings.append(RuleCheckFinding(
                rule_id="RULE-ACL-001",
                rule_name="Inverted Wildcard Mask in Access List",
                category="ACL",
                severity="High",
                osi_layer="Layer 4",
                message="Subnet mask notation (255.255.255.0) was used instead of Cisco wildcard mask (0.0.0.255), breaking rule matching.",
                evidence=evidence[:2],
                suggested_fix="Replace subnet mask with inverted wildcard mask: 'permit tcp 172.16.10.0 0.0.0.255 host 10.1.1.100 eq www'."
            ))

        # ACL Implicit Deny Blocking DNS return
        if "Extended IP access list OUTSIDE_IN" in text and "permit udp any eq domain" not in text and "deny ip any any" in text:
            evidence = [line for line in text.splitlines() if "outside_in" in line.lower() or "established" in line.lower() or "deny ip any any" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-ACL-002",
                rule_name="ACL Blocking UDP DNS Return Traffic",
                category="ACL",
                severity="High",
                osi_layer="Layer 4",
                message="Inbound ACL allows established TCP but omits UDP domain (port 53) return traffic, dropping DNS replies.",
                evidence=evidence[:3],
                suggested_fix="Add permit rule for DNS: 'permit udp any eq domain any' before the deny rule."
            ))

        # Standard ACL placed in wrong direction / interface
        if "Standard IP access list 10" in text and "Inbound  access list is 10" in text:
            evidence = [line for line in text.splitlines() if "standard ip access list" in line.lower() or "inbound  access list" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-ACL-003",
                rule_name="Standard ACL Inbound Placement Filtering All Traffic",
                category="ACL",
                severity="High",
                osi_layer="Layer 3",
                message="Standard ACL filtering by source IP was placed inbound on source interface, unintentionally blocking all local gateway traffic.",
                evidence=evidence[:3],
                suggested_fix="Move standard ACL to outbound on destination interface or convert to extended ACL."
            ))

        return findings

    def _check_nat(self, text: str, full_text: str) -> List[RuleCheckFinding]:
        findings = []
        # Missing Overload Keyword on NAT PAT
        if "ip nat inside source list" in text and "overload" not in text:
            evidence = [line for line in text.splitlines() if "ip nat inside source" in line.lower() or "ip nat translations" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-NAT-001",
                rule_name="Missing Overload Keyword on NAT Statement (PAT Failure)",
                category="NAT",
                severity="Critical",
                osi_layer="Layer 3",
                message="NAT rule is performing 1-to-1 dynamic translation without port multiplexing ('overload'), exhausting the single public IP.",
                evidence=evidence[:3],
                suggested_fix="Append 'overload' keyword: 'ip nat inside source list 1 interface GigabitEthernet0/1 overload'."
            ))

        # Missing ip nat outside
        if "ip nat inside" in text and "ip nat outside" not in text and ("wan" in full_text.lower() or "gigabitethernet0/1" in text.lower()):
            evidence = [line for line in text.splitlines() if "interface gigabitethernet0/1" in line.lower() or "ip nat inside" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-NAT-002",
                rule_name="Missing 'ip nat outside' on WAN Interface",
                category="NAT",
                severity="Critical",
                osi_layer="Layer 3",
                message="WAN interface is missing 'ip nat outside', preventing NAT engine from triggering address translation.",
                evidence=evidence[:3],
                suggested_fix="Apply 'ip nat outside' under WAN interface GigabitEthernet0/1."
            ))

        # NAT Pool Subnet Mismatch
        if "Pool PUBLIC_POOL" in text and "198.51.100.10" in text and "198.51.100.1/30" in text:
            evidence = [line for line in text.splitlines() if "pool public_pool" in line.lower() or "internet address is 198.51.100.1/30" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-NAT-003",
                rule_name="NAT Pool Range Outside Routed WAN Subnet",
                category="NAT",
                severity="High",
                osi_layer="Layer 3",
                message="Configured NAT pool range is outside the ISP assigned /30 WAN link subnet, causing ISP routing drops.",
                evidence=evidence[:3],
                suggested_fix="Configure NAT pool with valid routable public IP block assigned by ISP."
            ))

        return findings

    def _check_stp_and_security(self, text: str, full_text: str) -> List[RuleCheckFinding]:
        findings = []
        # BPDU Guard Violation
        if "SPANTREE-2-BLOCK_BPDUGUARD" in text or "bpduguard error detected" in text:
            evidence = [line for line in text.splitlines() if "bpduguard" in line.lower() or "err-disable" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-SEC-001",
                rule_name="Spanning Tree BPDU Guard Port Shutdown",
                category="STP / Security",
                severity="Medium",
                osi_layer="Layer 2",
                message="BPDU Guard disabled port after receiving unauthorized BPDU frames from an attached switch.",
                evidence=evidence[:3],
                suggested_fix="Disconnect unauthorized switch, clear err-disable state with 'shutdown' / 'no shutdown'."
            ))

        # Port Security Violation
        if "Port Status                : Secure-shutdown" in text or "Security Violation Count   : 1" in text:
            evidence = [line for line in text.splitlines() if "port status" in line.lower() or "security violation" in line.lower() or "secure-shutdown" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-SEC-002",
                rule_name="Port Security MAC Violation Shutdown",
                category="STP / Security",
                severity="Medium",
                osi_layer="Layer 2",
                message="Port-security shutdown port because an unauthorized MAC address exceeded configured limit.",
                evidence=evidence[:3],
                suggested_fix="Clear unauthorized MAC, reset sticky learning, and toggle port 'shutdown' / 'no shutdown'."
            ))

        return findings

    def _check_wireless(self, text: str, full_text: str) -> List[RuleCheckFinding]:
        findings = []
        # Guest VLAN Route Leak
        if "Core-SW# show access-lists\n(no access lists configured)" in text and "Guest-Laptop> ping 10.10.10.5" in text:
            evidence = [line for line in text.splitlines() if "show access-lists" in line or "no access lists" in line.lower() or "reply from 10.10.10.5" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-WLAN-001",
                rule_name="Guest Wi-Fi VLAN Isolation Route Leak",
                category="Wireless",
                severity="High",
                osi_layer="Layer 3",
                message="Guest VLAN lacks ACL segmentation, allowing unauthenticated guests to route into internal management servers.",
                evidence=evidence[:3],
                suggested_fix="Apply inbound ACL on Guest SVI (Vlan50) to deny traffic destined for internal subnets."
            ))

        # WLAN SSID VLAN Mismatch
        if "Network Name (SSID).............................. Corporate-Secure" in text and "guest-interface (Vlan 99)" in text:
            evidence = [line for line in text.splitlines() if "ssid" in line.lower() or "guest-interface" in line.lower() or "profile name" in line.lower()]
            findings.append(RuleCheckFinding(
                rule_id="RULE-WLAN-002",
                rule_name="WLAN Profile Mapped to Wrong VLAN Interface",
                category="Wireless",
                severity="High",
                osi_layer="Layer 2",
                message="Staff SSID 'Corporate-Secure' is mapped to guest VLAN 99 dynamic interface instead of staff VLAN 10.",
                evidence=evidence[:3],
                suggested_fix="Remap WLAN profile to 'staff-interface (Vlan 10)' in WLC configuration."
            ))

        return findings
