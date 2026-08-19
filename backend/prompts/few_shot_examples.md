# NetSage AI - Few-Shot Worked Examples

The following worked examples demonstrate high-precision network troubleshooting with evidence extraction, deterministic verification, and human oversight.

---

### Example 1: Inter-VLAN Routing Encapsulation Tag Mismatch

**Input Context**:
- **Case ID**: CASE-001
- **Symptom**: PC-A in VLAN 10 can ping its default gateway 192.168.10.1, but cannot ping PC-B (192.168.20.10) in VLAN 20. Switch trunk link to Router R1 is active.
- **Show Outputs**:
```
R1# show running-config interface g0/0/0.20
interface GigabitEthernet0/0/0.20
 encapsulation dot1Q 25
 ip address 192.168.20.1 255.255.255.0

SW1# show interfaces trunk
Port        Mode         Encapsulation  Status        Native vlan
Gi0/1       on           802.1q         trunking      1
```

**Model Output**:
```json
{
  "case_id": "CASE-001",
  "root_cause": "Subinterface encapsulation VLAN tag mismatch. Subinterface G0/0/0.20 is configured for VLAN 25 ('encapsulation dot1Q 25') instead of VLAN 20, dropping 802.1Q tagged frames from VLAN 20.",
  "osi_layer": "Layer 3",
  "concept_tag": "VLAN",
  "confidence_score": 0.98,
  "confidence_level": "High",
  "evidence_quotes": [
    "encapsulation dot1Q 25",
    "ip address 192.168.20.1 255.255.255.0"
  ],
  "reasoning_summary": "While subinterface G0/0/0.20 holds the correct IP address (192.168.20.1/24) for VLAN 20, its 802.1Q encapsulation tag is set to 25. Frames tagged with VLAN 20 arriving from the trunk port on SW1 will not be processed by this subinterface.",
  "next_diagnostic_commands": [
    "show running-config interface GigabitEthernet0/0/0.20",
    "show ip interface brief"
  ],
  "recommended_fix_steps": [
    "R1(config)# interface GigabitEthernet0/0/0.20",
    "R1(config-subif)# encapsulation dot1Q 20",
    "R1(config-subif)# ip address 192.168.20.1 255.255.255.0",
    "R1(config-subif)# end",
    "R1# write memory"
  ],
  "verification_steps": [
    "PC-A> ping 192.168.20.10",
    "R1# show vlans"
  ],
  "risk_assessment": "Low - Reconfiguring subinterface encapsulation briefly interrupts VLAN 20 traffic during command entry, but resolves inter-VLAN reachability."
}
```

---

### Example 2: Inverted ACL Wildcard Mask

**Input Context**:
- **Case ID**: CASE-006
- **Symptom**: Sales subnet (172.16.10.0/24) cannot reach Web Server (10.1.1.100:80). Traffic is blocked at border router R1.
- **Show Outputs**:
```
R1# show access-lists 101
Extended IP access list 101
    10 permit tcp 172.16.10.0 255.255.255.0 host 10.1.1.100 eq www (0 matches)
    20 deny ip any any (142 matches)
```

**Model Output**:
```json
{
  "case_id": "CASE-006",
  "root_cause": "Inverted wildcard mask in ACL 101 line 10. The administrator entered a standard subnet mask (255.255.255.0) instead of the inverted wildcard mask (0.0.0.255), causing traffic to bypass rule 10 and hit implicit deny rule 20.",
  "osi_layer": "Layer 4",
  "concept_tag": "ACL",
  "confidence_score": 0.99,
  "confidence_level": "High",
  "evidence_quotes": [
    "10 permit tcp 172.16.10.0 255.255.255.0 host 10.1.1.100 eq www (0 matches)",
    "20 deny ip any any (142 matches)"
  ],
  "reasoning_summary": "In Cisco IOS ACLs, source/destination masks are wildcards where 0 means match exactly and 255 means don't care. Entering 255.255.255.0 effectively requires the last octet to match 0 and ignores the first three octets, failing all standard host IP packets.",
  "next_diagnostic_commands": [
    "show access-lists 101",
    "show ip interface Gi0/0/0"
  ],
  "recommended_fix_steps": [
    "R1(config)# ip access-list extended 101",
    "R1(config-ext-nacl)# no 10",
    "R1(config-ext-nacl)# 10 permit tcp 172.16.10.0 0.0.0.255 host 10.1.1.100 eq www",
    "R1(config-ext-nacl)# end",
    "R1# write memory"
  ],
  "verification_steps": [
    "PC-Sales> curl http://10.1.1.100",
    "R1# show access-lists 101"
  ],
  "risk_assessment": "Low - Correcting the ACL entry immediately permits legitimate HTTP traffic without restarting interfaces."
}
```

---

### Example 3: Missing NAT Overload Keyword

**Input Context**:
- **Case ID**: CASE-007
- **Symptom**: Only one internal host can access the Internet at a time. All other hosts receive connection timeouts.
- **Show Outputs**:
```
R1# show running-config | include ip nat
ip nat inside source list 1 interface GigabitEthernet0/1

R1# show ip nat translations
Pro Inside global      Inside local       Outside local      Outside global
--- 203.0.113.2        192.168.1.15       ---                ---
```

**Model Output**:
```json
{
  "case_id": "CASE-007",
  "root_cause": "Missing 'overload' keyword on the NAT statement. The router is performing dynamic 1-to-1 NAT instead of Port Address Translation (PAT), exhausting the single public IP address after one client connection.",
  "osi_layer": "Layer 3",
  "concept_tag": "NAT",
  "confidence_score": 0.97,
  "confidence_level": "High",
  "evidence_quotes": [
    "ip nat inside source list 1 interface GigabitEthernet0/1",
    "--- 203.0.113.2        192.168.1.15       ---                ---"
  ],
  "reasoning_summary": "Without the 'overload' keyword, Cisco IOS maps each internal IP to a dedicated public IP. With only one public IP on Gi0/1, only the first host (192.168.1.15) acquires translation.",
  "next_diagnostic_commands": [
    "show ip nat translations",
    "show ip nat statistics"
  ],
  "recommended_fix_steps": [
    "R1(config)# no ip nat inside source list 1 interface GigabitEthernet0/1",
    "R1(config)# ip nat inside source list 1 interface GigabitEthernet0/1 overload",
    "R1(config)# end",
    "R1# clear ip nat translation *"
  ],
  "verification_steps": [
    "PC-2> ping 8.8.8.8",
    "R1# show ip nat translations"
  ],
  "risk_assessment": "Medium - Clearing active NAT translations resets existing TCP sessions, but immediately restores PAT functionality for all LAN hosts."
}
```
