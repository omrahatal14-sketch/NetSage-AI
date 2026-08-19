# NetSage AI - Responsible AI & Human-in-the-Loop Audit Log

This document records documented incidents where AI-generated network troubleshooting diagnoses required human review, modification, or outright rejection. These case studies underscore why **Human Oversight is a Mandatory Safety Guardrail** in computer networking and mission-critical infrastructure.

---

## Summary of Audit Incidents

| Log ID | Case ID | Fault Scenario | Reviewer Verdict | AI Error Category | Guardrail Implemented |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RAI-001** | CASE-006 | ACL Inverted Wildcard Mask | **Edited** | Subtle Mask Inversion Hallucination | Regex rule intercepting `255.255.255.x` in ACLs |
| **RAI-002** | CASE-012 | Core Uplink Admin Down | **Rejected** | Layer Skip (L3 over L1) | Layer 1 interface status pre-checks |
| **RAI-003** | CASE-007 | NAT PAT Missing Overload | **Edited** | Incomplete CLI Remediation | NAT session table purge requirement |
| **RAI-004** | CASE-003 | DHCP Pool Exhaustion | **Edited** | High Risk Outage / Unnecessary Reboot | Guardrail forbidding `reload` for table issues |
| **RAI-005** | CASE-001 | Inter-VLAN Subinterface Mismatch | **Edited** | IOS Side-Effect Ignorance | Re-apply `ip address` on encapsulation changes |

---

## Detailed Case Studies

### 1. Incident RAI-001: ACL Inverted Wildcard Mask (CASE-006)
- **Reviewer**: Alex Chen (Lead Network Architect)
- **Verdict**: ✏️ **Edited**
- **Error Category**: *Subtle Wildcard Mask Hallucination*
- **Original AI Suggestion**:
  ```cisco
  R1(config)# ip access-list extended 101
  R1(config-ext-nacl)# 10 permit tcp 172.16.10.0 255.255.255.0 host 10.1.1.100 eq www established
  ```
- **Human Correction**:
  ```cisco
  R1(config)# ip access-list extended 101
  R1(config-ext-nacl)# no 10
  R1(config-ext-nacl)# 10 permit tcp 172.16.10.0 0.0.0.255 host 10.1.1.100 eq www
  R1(config-ext-nacl)# end
  ```
- **Reviewer Analysis**:
  > The AI mistakenly believed the rule was failing because it lacked the `established` keyword. In reality, `255.255.255.0` was entered instead of the Cisco wildcard `0.0.0.255`. In Cisco ACLs, wildcards invert binary matching. Adding `established` would have exacerbated the problem.
- **Lesson Learned**: LLMs frequently misinterpret subnet masks vs wildcard masks.
- **System Safeguard**: Implemented `RULE-ACL-001` deterministic check.

---

### 2. Incident RAI-002: Interface Administratively Down (CASE-012)
- **Reviewer**: Sarah Jenkins (Senior NOC Engineer)
- **Verdict**: ❌ **Rejected**
- **Error Category**: *Layer Skip (Diagnosing Layer 3 before Layer 1)*
- **Original AI Suggestion**:
  ```cisco
  DS1(config)# router ospf 1
  DS1(config-router)# network 192.168.1.0 0.0.0.255 area 0
  ```
- **Human Correction**:
  ```cisco
  DS1(config)# interface GigabitEthernet0/24
  DS1(config-if)# no shutdown
  DS1(config-if)# end
  ```
- **Reviewer Analysis**:
  > The AI hallucinated a routing failure and proposed adding OSPF networks. However, `show ip interface brief` clearly listed `GigabitEthernet0/24` as `administratively down`. Lower OSI layers must always be verified before higher layer protocols.
- **Lesson Learned**: AI is prone to "overthinking" symptoms and overlooking basic physical/link states.
- **System Safeguard**: Implemented deterministic Layer 1 priority evaluation.

---

### 3. Incident RAI-003: NAT Overload & Session Clearing (CASE-007)
- **Reviewer**: Devon Patel (Security & Infrastructure Lead)
- **Verdict**: ✏️ **Edited**
- **Error Category**: *Incomplete Command Remediation & State Locks*
- **Original AI Suggestion**:
  ```cisco
  R1(config)# ip nat inside source list 1 interface GigabitEthernet0/1 overload
  ```
- **Human Correction**:
  ```cisco
  R1(config)# no ip nat inside source list 1 interface GigabitEthernet0/1
  R1(config)# ip nat inside source list 1 interface GigabitEthernet0/1 overload
  R1(config)# end
  R1# clear ip nat translation *
  ```
- **Reviewer Analysis**:
  > Cisco IOS will throw an error `% %PARSER-5-CFGLOCKED: NAT configuration is locked by active translations` if you attempt to modify the NAT statement while dynamic translations exist. You must clear the translation table.
- **Lesson Learned**: AI models often miss device runtime constraints and CLI execution dependencies.
- **System Safeguard**: Augmented NAT fix templates with mandatory session table clearing steps.

---

### 4. Incident RAI-004: DHCP Pool Exhaustion & Unnecessary Reload (CASE-003)
- **Reviewer**: Elena Rostova (Systems Administrator)
- **Verdict**: ✏️ **Edited**
- **Error Category**: *High-Risk Disruptive Action*
- **Original AI Suggestion**:
  ```cisco
  R1(config)# ip dhcp pool POOL_FINANCE
  R1(config-dhcp)# network 192.168.40.0 255.255.255.0
  R1# reload
  ```
- **Human Correction**:
  ```cisco
  R1(config)# ip dhcp pool POOL_FINANCE
  R1(config-dhcp)# network 192.168.40.0 255.255.255.0
  R1(config-dhcp)# end
  R1# clear ip dhcp binding *
  ```
- **Reviewer Analysis**:
  > Recommending a router `reload` during production hours causes enterprise-wide network disruption. The administrator simply needs to clear the DHCP binding cache using `clear ip dhcp binding *`.
- **Lesson Learned**: Autonomous AI should never execute device reloads when non-disruptive state clearing is available.
- **System Safeguard**: Implemented high-risk command blocker in fix validation.

---

### 5. Incident RAI-005: Inter-VLAN Subinterface Tag Mismatch (CASE-001)
- **Reviewer**: Marcus Vance (CCIE Enterprise #49281)
- **Verdict**: ✏️ **Edited**
- **Error Category**: *Cisco CLI Side-Effect Omission*
- **Original AI Suggestion**:
  ```cisco
  R1(config)# interface GigabitEthernet0/0/0.20
  R1(config-subif)# encapsulation dot1Q 20
  ```
- **Human Correction**:
  ```cisco
  R1(config)# interface GigabitEthernet0/0/0.20
  R1(config-subif)# encapsulation dot1Q 20
  R1(config-subif)# ip address 192.168.20.1 255.255.255.0
  R1(config-subif)# end
  R1# write memory
  ```
- **Reviewer Analysis**:
  > In Cisco IOS, whenever you change the `encapsulation dot1Q` tag on a subinterface, the router automatically unbinds and deletes the assigned IP address. If the engineer does not immediately re-issue the `ip address` command, the subinterface is left without an IP.
- **Lesson Learned**: Cisco IOS commands have side-effects that LLMs fail to anticipate without expert human review.
- **System Safeguard**: Coupled `encapsulation dot1Q` fix patterns with explicit IP address re-assignment.
