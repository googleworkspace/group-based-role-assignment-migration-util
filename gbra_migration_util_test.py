import sys
import unittest
from unittest.mock import ANY, MagicMock, Mock, call

sys.modules["change_client.migration_util_change_client"] = Mock()
sys.modules["utils.logger"] = Mock()
from gbra_migration_util import MigrationUtility, RoleScope

ROLE_TO_FORCE_GBRA_1 = 100
ROLE_TO_FORCE_GBRA_2 = 101
ROLE_TO_SKIP_GBRA_1 = 200

class TestMigrationUtility(unittest.TestCase):

  def setUp(self):
    # Create a mock instance of MigrationUtilChangeClient
    self.mock_migration_util_change_client = MagicMock()
    self.migration_util = MigrationUtility(
        output_path="/output",
        oa_client_id_creds="your_creds",
        ra_limit=5,
        roles_to_force_gbra=[ROLE_TO_FORCE_GBRA_1, ROLE_TO_FORCE_GBRA_2],
        roles_to_skip_gbra=[ROLE_TO_SKIP_GBRA_1],
        dry_run=True,
        is_test_env=True,
    )
    self.migration_util.migration_util_change_util = (
        self.mock_migration_util_change_client
    )
    self.mock_migration_util_change_client.get_role.return_value = {
        "isSuperAdminRole": False,
        "roleName": "DEFAULT_ROLE",
        "roleId": "dummyRoleId",
        "rolePrivileges": [{
            "privilegeName": "PRIV1",
            "serviceId": "dummyServiceId",
        }],
    }
    self.mock_migration_util_change_client.get_customer.return_value = {
        "id": "customerId",
        "customerDomain": "domain.com",
    }
    self.mock_migration_util_change_client.get_root_ou.return_value = "rootOuId"

  def test_get_rolescope_to_ra_map_force_gbra(self):
    self.maxDiff = None
    # Mock role_assignments data
    ra_force_gbra_1 = [
        {
            "roleId": ROLE_TO_FORCE_GBRA_1,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser1",
        },
        {
            "roleId": ROLE_TO_FORCE_GBRA_1,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser2",
        },
        {
            "roleId": ROLE_TO_FORCE_GBRA_1,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser3",
        },
    ]
    ra_force_gbra_2 = [
        {
            "roleId": ROLE_TO_FORCE_GBRA_2,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU2",
            "assignedTo": "gaiaUser4",
        },
    ]
    self.mock_migration_util_change_client.list_role_assignments.return_value = (
        ra_force_gbra_1 + ra_force_gbra_2
    )

    filtered_map = self.migration_util.get_rolescope_to_ra_map()

    # Ensure the filtered map contains the expected data
    expected_map = {
        RoleScope(
            roleId=ROLE_TO_FORCE_GBRA_1, scopeType="ORG_UNIT", orgUnit="OU1"
        ): ra_force_gbra_1,
        RoleScope(
            roleId=ROLE_TO_FORCE_GBRA_2, scopeType="ORG_UNIT", orgUnit="OU2"
        ): ra_force_gbra_2,
    }
    self.assertEqual(filtered_map, expected_map)

  def test_get_rolescope_to_ra_map_skip_gbra(self):
    self.maxDiff = None
    # Mock role_assignments data
    role_assignments = [
        {
            "roleId": ROLE_TO_SKIP_GBRA_1,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser1",
        },
        {
            "roleId": ROLE_TO_SKIP_GBRA_1,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser2",
        },
        {
            "roleId": ROLE_TO_SKIP_GBRA_1,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser3",
        },
        {
            "roleId": ROLE_TO_SKIP_GBRA_1,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser4",
        },
        {
            "roleId": ROLE_TO_SKIP_GBRA_1,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser5",
        },
        {
            "roleId": ROLE_TO_SKIP_GBRA_1,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser6",
        },
    ]
    self.mock_migration_util_change_client.list_role_assignments.return_value = (
        role_assignments
    )
    filtered_map = self.migration_util.get_rolescope_to_ra_map()
    self.assertEqual(filtered_map, {})

  def test_get_rolescope_to_ra_map_skip_gbra_no_filter(self):
    self.maxDiff = None
    # Mock role_assignments data
    role_assignments = [
        {
            "roleId": str(ROLE_TO_SKIP_GBRA_1),
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser1",
        },
        {
            "roleId": str(ROLE_TO_SKIP_GBRA_1),
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser2",
        },
        {
            "roleId": str(ROLE_TO_SKIP_GBRA_1),
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser3",
        },
        {
            "roleId": str(ROLE_TO_SKIP_GBRA_1),
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser4",
        },
        {
            "roleId": str(ROLE_TO_SKIP_GBRA_1),
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser5",
        },
        {
            "roleId": str(ROLE_TO_SKIP_GBRA_1),
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser6",
        },
    ]
    self.mock_migration_util_change_client.list_role_assignments.return_value = (
        role_assignments
    )
    filtered_map = self.migration_util.get_rolescope_to_ra_map(filtered=False)
    expected_map = {
        RoleScope(
            roleId="200", scopeType="ORG_UNIT", orgUnit="OU1"
        ): role_assignments
    }
    self.assertEqual(filtered_map, expected_map)

  def test_get_rolescope_to_ra_map_role_2_not_expected(self):
    self.maxDiff = None
    # Mock role_assignments data
    role_assignments = [
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser1",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser2",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser3",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser4",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser5",
        },
        {
            "roleId": "1002",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser6",
        },
    ]
    self.mock_migration_util_change_client.list_role_assignments.return_value = (
        role_assignments
    )
    filtered_map = self.migration_util.get_rolescope_to_ra_map()
    expected_map = {
        RoleScope(roleId="1001", scopeType="ORG_UNIT", orgUnit="OU1"): [
            {
                "assignedTo": "gaiaUser1",
                "orgUnitId": "OU1",
                "roleId": "1001",
                "scopeType": "ORG_UNIT",
            },
            {
                "assignedTo": "gaiaUser2",
                "orgUnitId": "OU1",
                "roleId": "1001",
                "scopeType": "ORG_UNIT",
            },
            {
                "assignedTo": "gaiaUser3",
                "orgUnitId": "OU1",
                "roleId": "1001",
                "scopeType": "ORG_UNIT",
            },
            {
                "assignedTo": "gaiaUser4",
                "orgUnitId": "OU1",
                "roleId": "1001",
                "scopeType": "ORG_UNIT",
            },
            {
                "assignedTo": "gaiaUser5",
                "orgUnitId": "OU1",
                "roleId": "1001",
                "scopeType": "ORG_UNIT",
            },
        ]
    }

    self.assertEqual(filtered_map, expected_map)

  def test_get_rolescope_to_ra_map_unfiltered(self):
    self.maxDiff = None
    # Mock role_assignments data
    ra_role_1 = [
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser1",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser2",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser3",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser4",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser5",
        },
    ]
    ra_role_2 = [
        {
            "roleId": "1002",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser6",
        },
    ]
    self.mock_migration_util_change_client.list_role_assignments.return_value = (
        ra_role_1 + ra_role_2
    )
    filtered_map = self.migration_util.get_rolescope_to_ra_map(filtered=False)
    expected_map = {
        RoleScope(
            roleId="1001", scopeType="ORG_UNIT", orgUnit="OU1"
        ): ra_role_1,
        RoleScope(
            roleId="1002", scopeType="ORG_UNIT", orgUnit="OU1"
        ): ra_role_2,
    }
    self.assertEqual(filtered_map, expected_map)

  def test_get_rolescope_to_ra_map_role_1_2_expected_added(self):
    self.maxDiff = None
    role_ra_1 = [
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser1",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser2",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser3",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser4",
        },
        {
            "roleId": "1001",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser5",
        },
    ]
    role_ra_2 = [
        {
            "roleId": "1002",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser6",
        },
        {
            "roleId": "1002",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser7",
        },
        {
            "roleId": "1002",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser8",
        },
        {
            "roleId": "1002",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser9",
        },
    ]
    self.mock_migration_util_change_client.list_role_assignments.return_value = (
        role_ra_1 + role_ra_2
    )
    filtered_map = self.migration_util.get_rolescope_to_ra_map()
    expected_map = {
        RoleScope(
            roleId="1001", scopeType="ORG_UNIT", orgUnit="OU1"
        ): role_ra_1,
        RoleScope(
            roleId="1002", scopeType="ORG_UNIT", orgUnit="OU1"
        ): role_ra_2,
    }
    self.assertEqual(filtered_map, expected_map)

  def test_get_rolescope_to_ra_map_invalid_role(self):
    self.maxDiff = None
    invalid_role_id = "10"
    role_assignments = [
        {
            "roleId": invalid_role_id,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser1",
        },
        {
            "roleId": invalid_role_id,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser2",
        },
        {
            "roleId": invalid_role_id,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser3",
        },
        {
            "roleId": invalid_role_id,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser4",
        },
        {
            "roleId": invalid_role_id,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser5",
        },
        {
            "roleId": invalid_role_id,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser6",
        },
    ]
    self.mock_migration_util_change_client.list_role_assignments.return_value = (
        role_assignments
    )
    self.mock_migration_util_change_client.get_role.return_value = {
        "isSuperAdminRole": True,
        "roleName": "SA_ROLE_NAME",
        "rolePrivileges": [{
            "privilegeName": "SA_PRIV1",
            "serviceId": "dummyServiceId",
        }],
    }
    self.assertEqual(self.migration_util.get_rolescope_to_ra_map(), {})
    self.mock_migration_util_change_client.get_role.return_value = {
        "isSuperAdminRole": False,
        "roleName": "_RESELLER_ADMIN_ROLE",
        "rolePrivileges": [{
            "privilegeName": "DEF_PRIV",
            "serviceId": "dummyServiceId",
        }],
    }
    self.assertEqual(self.migration_util.get_rolescope_to_ra_map(), {})
    self.mock_migration_util_change_client.get_role.return_value = {
        "isSuperAdminRole": False,
        "roleName": "_GCP_RESELLER_ADMIN_ROLE",
        "rolePrivileges": [{
            "privilegeName": "DEF_PRIV",
            "serviceId": "dummyServiceId",
        }],
    }
    self.assertEqual(self.migration_util.get_rolescope_to_ra_map(), {})
    self.mock_migration_util_change_client.get_role.return_value = {
        "isSuperAdminRole": False,
        "roleName": "DEF_ROLE",
        "rolePrivileges": [{
            "privilegeName": "MANAGE_HANGOUTS_SERVICE",
            "serviceId": "02w5ecyt3laroi5",
        }],
    }
    self.assertEqual(self.migration_util.get_rolescope_to_ra_map(), {})

  def test_create_groups_ou_scoped(self):
    role_id = "role1"
    self.migration_util.migration_util_change_util.get_group.return_value = None
    input_role_map = {
        RoleScope(roleId=role_id, scopeType="ORG_UNIT", orgUnit="OU1"): [
            {
                "roleId": role_id,
                "scopeType": "ORG_UNIT",
                "orgUnitId": "OU1",
                "assignedTo": "gaiaUser1",
            },
            {
                "roleId": role_id,
                "scopeType": "ORG_UNIT",
                "orgUnitId": "OU1",
                "assignedTo": "gaiaUser2",
            },
            {
                "roleId": role_id,
                "scopeType": "ORG_UNIT",
                "orgUnitId": "OU1",
                "assignedTo": "gaiaUser3",
            },
        ]
    }

    self.migration_util.create_groups(input_role_map)
    self.migration_util.migration_util_change_util.create_group.assert_called_with(
        "customerId",
        "role1-ORG_UNIT-OU1@domain.com",
        "role1-ORG_UNIT-OU1",
        ANY,
    )

  def test_create_groups_customer_scoped_multiple_role_scopes(self):
    input_role_map = {
        RoleScope(roleId="role1", scopeType="CUSTOMER", orgUnit=""): [
            {
                "roleId": "role1",
                "scopeType": "CUSTOMER",
                "assignedTo": "gaiaUser1",
            },
            {
                "roleId": "role1",
                "scopeType": "CUSTOMER",
                "assignedTo": "gaiaUser2",
            },
            {
                "roleId": "role1",
                "scopeType": "CUSTOMER",
                "assignedTo": "gaiaUser3",
            },
        ],
        RoleScope(roleId="role1", scopeType="ORG_UNIT", orgUnit="OU1"): [
            {
                "roleId": "role1",
                "scopeType": "ORG_UNIT",
                "orgUnit": "OU1",
                "assignedTo": "gaiaUser4",
            },
            {
                "roleId": "role1",
                "scopeType": "ORG_UNIT",
                "orgUnit": "OU1",
                "assignedTo": "gaiaUser5",
            },
        ],
    }
    self.mock_migration_util_change_client.get_group.side_effect = (
        lambda *args: {"id": "role1Id1"}
        if args == ("role1-CUSTOMER@domain.com",)
        else {"id": "role1Id2"}
        if args == ("role1-ORG_UNIT-OU1@domain.com",)
        else None
    )
    self.migration_util.make_ra_to_groups(input_role_map)
    self.migration_util.migration_util_change_util.insert_any_call(
        "role1", "role1-CUSTOMER@domain.com", "group", "CUSTOMER", "rootOuId"
    )
    self.migration_util.migration_util_change_util.insert_ra.insert_any_call(
        "role1", "role1-ORG_UNIT-OU1@domain.com", "group", "ORG_UNIT", "OU1"
    )

  def test_create_groups_customer_scoped_group_not_found(self):
    input_role_map = {
        RoleScope(roleId="role1", scopeType="CUSTOMER", orgUnit=""): [
            {
                "roleId": "role1",
                "scopeType": "CUSTOMER",
                "assignedTo": "gaiaUser1",
            },
            {
                "roleId": "role1",
                "scopeType": "CUSTOMER",
                "assignedTo": "gaiaUser2",
            },
            {
                "roleId": "role1",
                "scopeType": "CUSTOMER",
                "assignedTo": "gaiaUser3",
            },
        ]
    }
    self.mock_migration_util_change_client.get_group.return_value = None
    with self.assertRaises(AssertionError):
      self.migration_util.make_ra_to_groups(input_role_map)

  def test_cleanup_role_assignments(self):
    input_role_scope = RoleScope(
        roleId="111", scopeType="ORG_UNIT", orgUnit="222"
    )
    input_role_assignments = [
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "222",
            "assignedTo": "gaiaUser1",
            "assigneeType": "user",
            "roleAssignmentId": "raId1",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "222",
            "assignedTo": "gaiaUser2",
            "assigneeType": "user",
            "roleAssignmentId": "raId2",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "222",
            "assignedTo": "gaiaUser3",
            "assigneeType": "user",
            "roleAssignmentId": "raId3",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "222",
            "assignedTo": "gaiaUser4",
            "assigneeType": "user",
            "roleAssignmentId": "raId4",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "222",
            "assignedTo": "gaiaUser5",
            "assigneeType": "user",
            "roleAssignmentId": "raId5",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "222",
            "assignedTo": "group1@domain.com",
            "assigneeType": "group",
            "roleAssignmentId": "raId6",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "222",
            "assignedTo": "111-ORG_UNIT-222@domain.com",
            "assigneeType": "group",
            "roleAssignmentId": "raId7",
        },
    ]
    self.mock_migration_util_change_client.get_group.side_effect = (
        lambda *args: {
            "id": "groupId1",
            "email": "111-ORG_UNIT-222@domain.com",
            "name": "111-ORG_UNIT-222",
        }
        if args == ("111-ORG_UNIT-222@domain.com",)
        else None
    )
    self.mock_migration_util_change_client.get_group_members.side_effect = (
        lambda *args: [
            {"id": "gaiaUser1"},
            {"id": "gaiaUser2"},
            {"id": "gaiaUser3"},
            {"id": "gaiaUser4"},
            {"id": "gaiaUser5"},
        ]
        if args == ("111-ORG_UNIT-222@domain.com",)
        else None
    )

    self.migration_util.cleanup_role_assignments(
        input_role_scope, input_role_assignments
    )
    self.migration_util.migration_util_change_util.delete_role_assignment.assert_has_calls(
        [
            call("raId1"),
            call("raId2"),
            call("raId3"),
            call("raId4"),
            call("raId5"),
        ],
        any_order=True,
    )

  def test_delete_dup_ra_to_sas(
      self,
  ):
    role1_info = {
        "roleId": "role1",
        "isSuperAdminRole": True,
        "roleName": "role1Name",
    }
    role2_info = {
        "roleId": "role2",
        "isSuperAdminRole": True,
        "roleName": "role2Name",
    }
    self.migration_util.migration_util_change_util.list_roles.return_value = [
        role1_info,
        role2_info,
    ]

    ras_to_role1 = [
        {
            "roleId": "role1",
            "assignedTo": "user1",
            "roleAssignmentId": "1",
            "orgUnitId": "OU1",
            "scopeType": "ORG_UNIT",
        },
    ]
    ras_to_user1 = ras_to_role1 + [
        {
            "roleId": "role2",
            "assignedTo": "user1",
            "roleAssignmentId": "2",
            "orgUnitId": "OU1",
            "scopeType": "ORG_UNIT",
        },
    ]

    all_ras = [
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user10",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user11",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user12",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user13",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user14",
        },
    ] + ras_to_user1
    self.migration_util.migration_util_change_util.list_role_assignments.side_effect = (
        lambda *args: ras_to_role1
        if args == ("role1", None)
        else ras_to_user1
        if args == (None, "user1")
        else all_ras
        if args == (None, None)
        else []
    )
    self.migration_util.migration_util_change_util.get_ou.side_effect = (
        lambda *args: {"orgUnitId": "OU1", "orgUnitPath": "/OU1"}
        if args == "OU1"
        else None
    )
    self.migration_util.delete_dup_ra_to_sas()

    self.migration_util.migration_util_change_util.delete_role_assignment.assert_has_calls(
        [call("2")], any_order=True
    )

  def test_scope_to_ra_map(
      self,
  ):
    customer_scoped_ras = [
        {
            "roleId": "role1",
            "scopeType": "CUSTOMER",
            "orgUnitId": "",
            "assignedTo": "user10",
        },
    ]
    org_unit_scoped_ras = [
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user10",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user11",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user12",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user13",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user14",
        },
    ]
    self.migration_util.migration_util_change_util.list_role_assignments.return_value = (
        customer_scoped_ras + org_unit_scoped_ras
    )
    returned_map = self.migration_util.get_scope_to_ra_map(
        filter_under_ra_limit=False, human_readable_scope_name=False
    )
    self.assertEqual(
        returned_map,
        {"CUSTOMER": customer_scoped_ras, "ORG_UNIT-OU1": org_unit_scoped_ras},
    )

  def test_scope_to_ra_map_human_reaadable(
      self,
  ):
    customer_scoped_ras = [
        {
            "roleId": "role1",
            "scopeType": "CUSTOMER",
            "orgUnitId": "",
            "assignedTo": "user10",
        },
    ]
    org_unit_scoped_ras = [
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user10",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user11",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user12",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user13",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user14",
        },
    ]
    self.migration_util.migration_util_change_util.list_role_assignments.return_value = (
        customer_scoped_ras + org_unit_scoped_ras
    )
    self.migration_util.migration_util_change_util.get_ou.side_effect = (
        lambda *args: {"orgUnitId": "OU1", "orgUnitPath": "/OU1"}
        if args == ("OU1",)
        else None
    )
    returned_map = self.migration_util.get_scope_to_ra_map(
        filter_under_ra_limit=False, human_readable_scope_name=True
    )
    self.assertEqual(
        returned_map,
        {"CUSTOMER": customer_scoped_ras, "ORG_UNIT-/OU1": org_unit_scoped_ras},
    )

  def test_scope_to_ra_map_human_reaadable_filter_under_ra_limit(
      self,
  ):
    customer_scoped_ras = [
        {
            "roleId": "role1",
            "scopeType": "CUSTOMER",
            "orgUnitId": "",
            "assignedTo": "user10",
        },
    ]
    org_unit_scoped_ras = [
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user10",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user11",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user12",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user13",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user14",
        },
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user17",
        },
    ]
    self.migration_util.migration_util_change_util.list_role_assignments.return_value = (
        customer_scoped_ras + org_unit_scoped_ras
    )
    self.migration_util.migration_util_change_util.get_ou.side_effect = (
        lambda *args: {"orgUnitId": "OU1", "orgUnitPath": "/OU1"}
        if args == ("OU1",)
        else None
    )
    returned_map = self.migration_util.get_scope_to_ra_map(
        filter_under_ra_limit=True, human_readable_scope_name=True
    )
    self.assertEqual(returned_map, {"ORG_UNIT-/OU1": org_unit_scoped_ras})

  def test_delete_dup_ra_to_sas_scope_doesnt_exceed_no_deletion(
      self,
  ):
    self.migration_util.migration_util_change_util.list_roles.return_value = [
        {"roleId": "role1", "isSuperAdminRole": True},
        {"roleId": "role2", "isSuperAdminRole": False},
    ]

    ras_to_role1 = [
        {
            "roleId": "role1",
            "assignedTo": "user1",
            "roleAssignmentId": "1",
            "orgUnitId": "OU1",
            "scopeType": "ORG_UNIT",
        },
    ]
    ras_to_user1 = ras_to_role1 + [
        {
            "roleId": "role2",
            "assignedTo": "user1",
            "roleAssignmentId": "2",
            "orgUnitId": "OU1",
            "scopeType": "ORG_UNIT",
        },
    ]

    all_ras = [
        {
            "roleId": "role3",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "user10",
        },
    ] + ras_to_user1
    self.migration_util.migration_util_change_util.list_role_assignments.side_effect = (
        lambda *args: ras_to_role1
        if args == ("role1", None)
        else ras_to_user1
        if args == (None, "user1")
        else all_ras
        if args == (None, None)
        else []
    )

    self.migration_util.delete_dup_ra_to_sas()

    self.migration_util.migration_util_change_util.delete_role_assignment.assert_not_called()

  def test_create_groups_customer_scoped_ra_to_group_exists(self):
    input_role_map = {
        RoleScope(roleId="role1", scopeType="CUSTOMER", orgUnit=""): [
            {
                "roleId": "role1",
                "scopeType": "CUSTOMER",
                "assignedTo": "gaiaUser1",
            },
            {
                "roleId": "role1",
                "scopeType": "CUSTOMER",
                "assignedTo": "gaiaUser2",
            },
            {
                "roleId": "role1",
                "scopeType": "CUSTOMER",
                "assignedTo": "gaiaUser3",
            },
        ]
    }

  def test_get_rolescope_to_ra_map_less_than_limit(self):
    self.maxDiff = None

    role_assignments = [
        {
            "roleId": 10,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser1",
        },
        {
            "roleId": 10,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser2",
        },
        {
            "roleId": 10,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser3",
        },
        {
            "roleId": 10,
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser5",
        },
    ]
    self.mock_migration_util_change_client.list_role_assignments.return_value = (
        role_assignments
    )
    filtered_map = self.migration_util.get_rolescope_to_ra_map()
    self.assertEqual(filtered_map, {})

  def test_get_rolescope_to_ra_map_gt_limit(self):
    self.maxDiff = None
    role_assignments = [
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser1",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser2",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser3",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser5",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser6",
        },
        {
            "roleId": "111",
            "scopeType": "ORG_UNIT",
            "orgUnitId": "OU1",
            "assignedTo": "gaiaUser7",
        },
    ]
    self.mock_migration_util_change_client.list_role_assignments.return_value = (
        role_assignments
    )
    filtered_map = self.migration_util.get_rolescope_to_ra_map()
    self.assertEqual(
        filtered_map,
        {
            RoleScope(
                roleId="111", scopeType="ORG_UNIT", orgUnit="OU1"
            ): role_assignments
        },
    )

  def test_principal_is_super_admin(self):
    self.mock_migration_util_change_client.get_primary_email.return_value = (
        "admin@example.com"
    )
    self.mock_migration_util_change_client.list_role_assignments.return_value = [
        {"roleId": "superadminrole"}
    ]
    self.mock_migration_util_change_client.get_role.return_value = {
        "isSuperAdminRole": True
    }
    self.assertTrue(self.migration_util.check_principal_is_super_admin())

  def test_principal_is_not_super_admin(self):
    self.mock_migration_util_change_client.get_primary_email.return_value = (
        "admin@example.com"
    )
    self.mock_migration_util_change_client.list_role_assignments.return_value = [
        {"roleId": "normaluserrole"}
    ]
    self.mock_migration_util_change_client.get_role.return_value = {
        "isSuperAdminRole": False
    }
    self.assertFalse(self.migration_util.check_principal_is_super_admin())

  def test_runtime_error(self):
    # Mocking the necessary dependencies
    self.mock_migration_util_change_client.get_primary_email.return_value = (
        "admin@example.com"
    )
    self.mock_migration_util_change_client.list_role_assignments.side_effect = (
        RuntimeError()
    )

    result = self.migration_util.check_principal_is_super_admin()
    self.assertFalse(result)


if __name__ == "__main__":
  unittest.main()
