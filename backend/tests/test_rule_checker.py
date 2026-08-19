import unittest
from engine.rule_checker import DeterministicRuleChecker

class TestDeterministicRuleChecker(unittest.TestCase):
    def setUp(self):
        self.checker = DeterministicRuleChecker()

    def test_admin_down_rule(self):
        sample = """
        Interface              IP-Address      OK? Method Status                Protocol
        GigabitEthernet0/24    unassigned      YES unset  administratively down down
        """
        findings = self.checker.run_all_checks(sample)
        rule_ids = [f["rule_id"] for f in findings]
        self.assertIn("RULE-IF-001", rule_ids)

    def test_acl_inverted_wildcard(self):
        sample = """
        Extended IP access list 101
            10 permit tcp 172.16.10.0 255.255.255.0 host 10.1.1.100 eq www (0 matches)
            20 deny ip any any (142 matches)
        """
        findings = self.checker.run_all_checks(sample)
        rule_ids = [f["rule_id"] for f in findings]
        self.assertIn("RULE-ACL-001", rule_ids)

    def test_nat_missing_overload(self):
        sample = """
        R1# show running-config | include ip nat
        ip nat inside source list 1 interface GigabitEthernet0/1
        """
        findings = self.checker.run_all_checks(sample)
        rule_ids = [f["rule_id"] for f in findings]
        self.assertIn("RULE-NAT-001", rule_ids)

    def test_missing_default_route(self):
        sample = """
        R1# show ip route
        Gateway of last resort is not set
        """
        findings = self.checker.run_all_checks(sample, symptom="Cannot reach internet public IPs like 8.8.8.8")
        rule_ids = [f["rule_id"] for f in findings]
        self.assertIn("RULE-RT-001", rule_ids)

    def test_subinterface_vlan_mismatch(self):
        sample = """
        interface GigabitEthernet0/0/0.20
         encapsulation dot1Q 25
         ip address 192.168.20.1 255.255.255.0
        """
        findings = self.checker.run_all_checks(sample)
        rule_ids = [f["rule_id"] for f in findings]
        self.assertIn("RULE-VLAN-002", rule_ids)

    def test_dhcp_pool_exhaustion(self):
        sample = """
        Pool POOL_FINANCE :
         Utilization mark (high/low)    : 100 / 0
         Subnet size (total/usable)       : 10 / 8
         Leased addresses                : 8
         Excluded addresses              : 2
        """
        findings = self.checker.run_all_checks(sample)
        rule_ids = [f["rule_id"] for f in findings]
        self.assertIn("RULE-DHCP-001", rule_ids)

if __name__ == "__main__":
    unittest.main()
