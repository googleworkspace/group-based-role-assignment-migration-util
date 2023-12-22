import sys
import unittest
from unittest.mock import Mock, patch

sys.modules['google_auth_oauthlib'] = Mock()
sys.modules['googleapiclient'] = Mock()
sys.modules['utils.logger'] = Mock()
sys.modules['change_client.dry_run_change_client'] = Mock()
sys.modules['change_client.google_api_client'] = Mock()
from change_client.migration_util_change_client import MigrationUtilChangeClient


class TestMigrationUtilChangeClient(unittest.TestCase):

  def setUp(self):
    # Create a mock for dry_run_change_client.DryRunChangeClient
    self.mock_dry_run_change_client = Mock()

    # Create a mock for google_api_client.GoogleApiClient
    self.mock_google_api_client = Mock()

    # Create an instance of MigrationUtilChangeClient for testing
    self.client = MigrationUtilChangeClient(
        output_path='output_path',
        oa_client_id_creds='oa_client_id_creds',
        dry_run=True,  # Set dry_run to True for testing
        is_test_envs=True,
    )
    # Replace the real clients with the mocks
    self.client.dry_run_changes = self.mock_dry_run_change_client
    self.client.google_api_client = self.mock_google_api_client

  def test_insert_ra_with_group_dry_run(self):
    self.client.dry_run = True
    # Define test data
    role_id = 'test_role_id'
    assignee_email = 'test_group@example.com'
    assignee_type = 'group'
    scope_type = 'scope_type'
    org_unit = None

    # Mock the get_group method to return a group
    self.mock_google_api_client.get_group.return_value = {
        'id': 'test_group_id',
        'email': assignee_email,
    }
    # self.mock_google_api_client.get_role_assignment.return_value = []
    self.mock_google_api_client.list_role_assignments.return_value = []
    self.mock_dry_run_change_client.list_role_assignments.return_value = []
    self.mock_dry_run_change_client.list_deleted_role_assignments.return_value = (
        []
    )
    # Call the insert_ra method
    self.client.insert_ra(
        role_id, assignee_email, assignee_type, scope_type, None
    )

  def test_insert_ra_with_group_wet_run(self):
    self.client.dry_run = False
    # Define test data
    role_id = 'test_role_id'
    assignee_email = 'test_group@example.com'
    assignee_type = 'group'
    scope_type = 'scope_type'
    org_unit = None

    # Mock the get_group method to return a group
    self.mock_google_api_client.get_group.return_value = {
        'id': 'test_group_id',
        'email': assignee_email,
    }
    self.mock_google_api_client.list_role_assignments.return_value = []
    self.mock_dry_run_change_client.list_role_assignments.return_value = []
    self.mock_dry_run_change_client.list_deleted_role_assignments.return_value = (
        []
    )
    # Call the insert_ra method
    self.client.insert_ra(
        role_id, assignee_email, assignee_type, scope_type, None
    )

  def test_create_group_dry_run(self):
    # Define test data for group creation
    customer_id = 'test_customer_id'
    group_email = 'test_group@example.com'
    group_display_name = 'Test Group'
    group_description = 'This is a test group.'

    # Set dry_run to True for testing
    self.client.dry_run = True

    # Call the create_group method
    self.client.create_group(
        customer_id, group_email, group_display_name, group_description
    )
    self.client.dry_run_changes.create_group.assert_called_once_with(
        customer_id, group_email, group_display_name, group_description
    )
    self.client.google_api_client.create_group.assert_not_called()

  def test_create_group_not_dry_run(self):
    # Define test data for group creation
    customer_id = 'test_customer_id'
    group_email = 'test_group@example.com'
    group_display_name = 'Test Group'
    group_description = 'This is a test group.'
    self.client.dry_run = False
    self.client.create_group(
        customer_id, group_email, group_display_name, group_description
    )
    self.client.google_api_client.create_group.assert_called_once_with(
        customer_id, group_email, group_display_name, group_description
    )
    self.client.dry_run_changes.create_group.assert_not_called()

  def test_get_user_found(self):
    user_email = 'test_user@example.com'
    user_data = {
        'id': 'test_user_id',
        'email': user_email,
        'name': 'Test User',
        'other_data': 'other_data',
    }
    self.mock_google_api_client.get_user.return_value = user_data
    result = self.client.get_user(user_email)
    self.assertEqual(result, user_data)
    self.assertEqual(self.client.user_cache[user_email], user_data)

  def test_get_user_not_found(self):
    user_email = 'nonexistent_user@example.com'
    self.mock_google_api_client.get_user.return_value = None
    result = self.client.get_user(user_email)
    self.assertIsNone(result)

  def test_get_group_members_dry_run(self):
    self.client.dry_run = True
    group_email = 'test_group@example.com'
    members_data_1 = [
        {
            'id': 'user1_id',
            'email': 'user1@example.com',
            'name': 'User 1',
        },
        {
            'id': 'user2_id',
            'email': 'user2@example.com',
            'name': 'User 2',
        },
    ]
    members_data_2 = [
        {
            'id': 'user3_id',
            'email': 'user3@example.com',
            'name': 'User 3',
        },
        {
            'id': 'user4_id',
            'email': 'user4@example.com',
            'name': 'User 4',
        },
    ]

    self.mock_google_api_client.get_group_members.return_value = members_data_1
    self.mock_dry_run_change_client.get_group_members.return_value = (
        members_data_2
    )
    result = self.client.get_group_members(group_email)

    self.assertEqual(result, members_data_1 + members_data_2)

  def test_get_group_members_wet_run(self):
    self.client.dry_run = False
    group_email = 'test_group@example.com'
    members_data_1 = [
        {
            'id': 'user1_id',
            'email': 'user1@example.com',
            'name': 'User 1',
        },
        {
            'id': 'user2_id',
            'email': 'user2@example.com',
            'name': 'User 2',
        },
    ]
    members_data_2 = [
        {
            'id': 'user3_id',
            'email': 'user3@example.com',
            'name': 'User 3',
        },
        {
            'id': 'user4_id',
            'email': 'user4@example.com',
            'name': 'User 4',
        },
    ]
    self.mock_google_api_client.get_group_members.return_value = members_data_1
    self.mock_dry_run_change_client.get_group_members.return_value = (
        members_data_2
    )
    result = self.client.get_group_members(group_email)
    self.assertEqual(result, members_data_1)

  def test_group_has_member_dry_run(self):
    group_email = 'test_group@example.com'
    user_email = 'user1@example.com'
    self.mock_google_api_client.group_has_member.return_value = False
    self.mock_dry_run_change_client.group_has_member.return_value = True
    self.assertEqual(
        self.client.group_has_member(group_email, user_email), True
    )

  def test_group_has_member_wet_run(self):
    group_email = 'test_group@example.com'
    user_email = 'user1@example.com'
    self.client.dry_run = False
    self.mock_google_api_client.group_has_member.return_value = True
    self.mock_dry_run_change_client.group_has_member.return_value = False
    self.mock_dry_run_change_client.assert_not_called()
    self.assertEqual(
        self.client.group_has_member(group_email, user_email), True
    )

  def test_list_role_assignments_with_role_id_wet_run(self):
    self.client.dry_run = False
    # Test when a specific role_id is provided, and role assignments are found.
    mock_role_assignments = [
        {
            'roleId': 'role1',
            'assignedTo': 'group1',
            'assigneeType': 'group',
            'roleAssignmentId': 'ra1',
            'scopeType': 'scope1',
        },
        {
            'roleId': 'role2',
            'assignedTo': 'group2',
            'assigneeType': 'group',
            'roleAssignmentId': 'ra2',
            'scopeType': 'scope2',
        },
    ]

    with patch.object(
        self.client.google_api_client,
        'list_role_assignments',
        return_value=mock_role_assignments,
    ):
      role_assignments = self.client.list_role_assignments(role_id='role1')

    self.assertEqual(role_assignments, mock_role_assignments)

  def test_list_role_assignments_without_role_id_wet_run(self):
    self.client.dry_run = False
    # Test when no role_id is provided, and role assignments are found.
    mock_role_assignments = [
        {
            'roleId': 'role1',
            'assignedTo': 'group1',
            'assigneeType': 'group',
            'roleAssignmentId': 'ra1',
            'scopeType': 'scope1',
        },
        {
            'roleId': 'role2',
            'assignedTo': 'group2',
            'assigneeType': 'group',
            'roleAssignmentId': 'ra2',
            'scopeType': 'scope2',
        },
    ]

    with patch.object(
        self.client.google_api_client,
        'list_role_assignments',
        return_value=mock_role_assignments,
    ):
      role_assignments = self.client.list_role_assignments()

    self.assertEqual(role_assignments, mock_role_assignments)

  def test_list_role_assignments_dry_run(self):
    # Test when in dry run mode, and role assignments are found.
    # Set dry_run to False for this test.
    self.client.dry_run = True

    mock_role_assignments_1 = [
        {
            'roleId': 'role1',
            'assignedTo': 'group1',
            'assigneeType': 'group',
            'roleAssignmentId': 'ra1',
            'scopeType': 'scope1',
        },
        {
            'roleId': 'role1',
            'assignedTo': 'group2',
            'roleAssignmentId': 'ra2',
            'assigneeType': 'group',
            'scopeType': 'scope2',
        },
    ]

    mock_role_assignments_2 = [
        {
            'roleId': 'role1',
            'assignedTo': 'group3',
            'roleAssignmentId': 'ra3',
            'assigneeType': 'group',
            'scopeType': 'scope3',
        },
        {
            'roleId': 'role1',
            'assignedTo': 'group4',
            'roleAssignmentId': 'ra4',
            'assigneeType': 'group',
            'scopeType': 'scope4',
        },
    ]
    self.mock_google_api_client.list_role_assignments.return_value = (
        mock_role_assignments_1
    )
    self.mock_dry_run_change_client.list_role_assignments.return_value = (
        mock_role_assignments_2
    )
    self.mock_dry_run_change_client.list_deleted_role_assignments.return_value = (
        []
    )

    role_assignments = self.client.list_role_assignments(role_id='role1')

    self.assertEqual(
        role_assignments, mock_role_assignments_1 + mock_role_assignments_2
    )

  def test_list_role_assignments_dry_run_deleted_ras(self):
    # Test when in dry run mode, and role assignments are found.
    # Set dry_run to False for this test.
    self.client.dry_run = True

    mock_role_assignments_1 = [
        {
            'roleId': 'role1',
            'assignedTo': 'group1',
            'roleAssignmentId': 'raId1',
            'assigneeType': 'group',
            'scopeType': 'scope1',
        },
        {
            'roleId': 'role1',
            'assignedTo': 'group2',
            'roleAssignmentId': 'raId2',
            'assigneeType': 'group',
            'scopeType': 'scope2',
        },
    ]

    mock_role_assignments_2 = [
        {
            'roleId': 'role1',
            'assignedTo': 'group3',
            'roleAssignmentId': 'raId3',
            'assigneeType': 'group',
            'scopeType': 'scope3',
        },
        {
            'roleId': 'role1',
            'assignedTo': 'group4',
            'roleAssignmentId': 'raId4',
            'assigneeType': 'group',
            'scopeType': 'scope4',
        },
    ]

    self.mock_google_api_client.list_role_assignments.return_value = (
        mock_role_assignments_1
    )
    self.mock_dry_run_change_client.list_role_assignments.return_value = (
        mock_role_assignments_2
    )
    self.mock_dry_run_change_client.list_deleted_role_assignments.return_value = (
        mock_role_assignments_2
    )
    role_assignments = self.client.list_role_assignments(role_id='role1')
    self.assertEqual(role_assignments, mock_role_assignments_1)

  def test_insert_member_into_group_with_dry_run_false(self):
    self.client.dry_run = False

    self.mock_google_api_client.group_has_member.return_value = False
    user_email = 'user@example.com'
    user_id = 'user_id'
    group_email = 'group@example.com'

    self.client.insert_member_into_group(user_email, user_id, group_email)
    self.mock_google_api_client.group_has_member.assert_called_once_with(
        group_email, user_email
    )
    self.mock_dry_run_change_client.insert_member_into_group.assert_not_called()

  def test_insert_member_into_group_with_dry_run_true(self):
    self.client.dry_run = True
    self.mock_google_api_client.group_has_member.return_value = False
    user_email = 'user@example.com'
    user_id = 'user_id'
    group_email = 'group@example.com'

    self.client.insert_member_into_group(user_email, user_id, group_email)
    self.mock_google_api_client.insert_member_into_group.assert_not_called()
    self.mock_dry_run_change_client.group_has_member.assert_called_once_with(
        group_email, user_email
    )    


if __name__ == '__main__':
  unittest.main()
