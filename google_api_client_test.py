import sys
import unittest
from unittest.mock import MagicMock, Mock, call
from googleapiclient import errors
import pytest

sys.modules['google_auth_oauthlib'] = Mock()
sys.modules['utils.logger'] = Mock()
sys.modules['utils.credential_store'] = Mock()

from change_client.google_api_client import GoogleApiClient


class TestGoogleApiClient(unittest.TestCase):

  def setUp(self):
    self.client = GoogleApiClient(
        output_path='output',
        oa_client_creds='credentials',
        is_test_envs=True,
        is_dry_run=False,
    )

  def assert_mock_retries_n_times(self, mock):
    mock.assert_has_calls(
        [
            call.execute(),
            call.execute(),
            call.execute(),
            call.execute(),
            call.execute(),
        ],
        any_order=True,
    )

  def test_get_user_404_error_expect_not_thrown(self):
    mock_admin_sdk_client = MagicMock()
    mock_users = MagicMock()
    mock_get = MagicMock()
    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.users.return_value = mock_users
    mock_users.get.return_value = mock_get
    mock_get.execute.side_effect = errors.HttpError(
        Mock(status=404), 'User not found'.encode('utf-8')
    )
    result = self.client.get_user('user@example.com')
    self.assertIsNone(result)

  def test_get_user_generic_error_retried_failure(self):
    mock_admin_sdk_client = MagicMock()
    mock_users = MagicMock()
    mock_get = MagicMock()
    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.users.return_value = mock_users
    mock_users.get.return_value = mock_get
    with pytest.raises(RuntimeError):
      mock_get.execute.side_effect = errors.HttpError(
          Mock(status=555), 'Some generic error '.encode('utf-8')
      )
      result = self.client.get_user('user@example.com')
    self.assert_mock_retries_n_times(mock_get)

  def test_get_group_credential_expired_retry_once_nothrow(self):
    mock_admin_sdk_client = MagicMock()
    mock_groups = MagicMock()
    mock_get = MagicMock()
    mock_reauth_and_refresh_clients = MagicMock()
    self.client.get_admin_sdk_client = MagicMock(
        return_value=mock_admin_sdk_client
    )
    self.client.reauth_and_refresh_clients = mock_reauth_and_refresh_clients
    mock_admin_sdk_client.groups.return_value = mock_groups
    mock_groups.get.return_value = mock_get
    # mock substution is lost in retry_with_credential_refresh
    # instead test that at least reauth_and_refresh_clients invoked
    mock_get.execute.side_effect = [
        errors.HttpError(Mock(status=401), 'Group not found'.encode('utf-8')),
        None,
    ]
    result = self.client.get_group('group@example.com')
    mock_reauth_and_refresh_clients.assert_called_once()

  def test_group_has_member_found(self):
    mock_admin_sdk_client = MagicMock()
    mock_members = MagicMock()
    mock_get = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.members.return_value = mock_members
    mock_members.get.return_value = mock_get
    mock_get.execute.return_value = {
        'email': 'user@example.com',
        'active': True,
    }

    # Assuming group_has_member returns True if member is found and active
    result = self.client.group_has_member(
        'group@example.com', 'user@example.com'
    )
    self.assertTrue(result)

  def test_group_has_member_not_found(self):
    # Create a mock for the admin sdk client
    mock_admin_sdk_client = MagicMock()
    mock_members = MagicMock()
    mock_get = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.members.return_value = mock_members
    mock_members.get.return_value = mock_get
    mock_get.execute.side_effect = errors.HttpError(
        Mock(status=404), 'Member not found'.encode('utf-8')
    )

    result = self.client.group_has_member(
        'group@example.com', 'user@example.com'
    )
    self.assertFalse(result)

  def test_group_has_member_generic_error(self):
    mock_admin_sdk_client = MagicMock()
    mock_members = MagicMock()
    mock_get = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.members.return_value = mock_members
    mock_members.get.return_value = mock_get

    with pytest.raises(RuntimeError):
      mock_get.execute.side_effect = errors.HttpError(
          Mock(status=555), 'Some generic error'.encode('utf-8')
      )
      self.client.group_has_member('group@example.com', 'user@example.com')
    self.assert_mock_retries_n_times(mock_get)

  def test_get_group_members_success(self):
    mock_admin_sdk_client = MagicMock()
    mock_members = MagicMock()
    mock_list = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.members.return_value = mock_members
    mock_members.list.return_value = mock_list
    mock_list.execute.return_value = {
        'members': [
            {'email': 'user1@example.com'},
            {'email': 'user2@example.com'},
        ]
    }
    result = self.client.get_group_members('group@example.com')
    self.assertEqual(
        result, [{'email': 'user1@example.com'}, {'email': 'user2@example.com'}]
    )

  def test_get_group_members_no_members(self):
    # Create a mock for the admin sdk client
    mock_admin_sdk_client = MagicMock()
    mock_members = MagicMock()
    mock_list = MagicMock()
    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.members.return_value = mock_members
    mock_members.list.return_value = mock_list
    mock_list.execute.return_value = {}

    result = self.client.get_group_members('group@example.com')
    self.assertEqual(result, [])

  def test_get_group_members_generic_error(self):
    mock_admin_sdk_client = MagicMock()
    mock_members = MagicMock()
    mock_list = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.members.return_value = mock_members
    mock_members.list.return_value = mock_list

    with pytest.raises(RuntimeError):
      mock_list.execute.side_effect = errors.HttpError(
          Mock(status=555), 'Some generic error'.encode('utf-8')
      )
      self.client.get_group_members('group@example.com')
    self.assert_mock_retries_n_times(mock_list)

  def test_create_group_success(self):
    mock_identity_client = MagicMock()
    mock_groups = MagicMock()
    mock_create = MagicMock()

    self.client.get_identity_client = MagicMock(
        return_value=mock_identity_client
    )
    mock_identity_client.groups.return_value = mock_groups
    mock_groups.create.return_value = mock_create
    mock_create.execute.return_value = None

    customer_id = 'some_customer_id'
    group_email = 'newgroup@example.com'
    group_display_name = 'New Group'
    group_description = 'This is a new group'
    self.client.create_group(
        customer_id, group_email, group_display_name, group_description
    )
    mock_create.execute.assert_called_once()

  def test_create_group_group_exists(self):
    mock_identity_client = MagicMock()
    mock_groups = MagicMock()
    mock_create = MagicMock()

    self.client.get_identity_client = MagicMock(
        return_value=mock_identity_client
    )
    mock_identity_client.groups.return_value = mock_groups
    mock_groups.create.return_value = mock_create
    mock_create.execute.side_effect = errors.HttpError(
        Mock(status=409), 'Group already exists'.encode('utf-8')
    )

    customer_id = 'some_customer_id'
    group_email = 'newgroup@example.com'
    group_display_name = 'New Group'
    group_description = 'This is a new group'

    # Running the method should not raise any exception
    self.client.create_group(
        customer_id, group_email, group_display_name, group_description
    )

  def test_create_group_generic_error(self):
    mock_identity_client = MagicMock()
    mock_groups = MagicMock()
    mock_create = MagicMock()

    self.client.get_identity_client = MagicMock(
        return_value=mock_identity_client
    )
    mock_identity_client.groups.return_value = mock_groups
    mock_groups.create.return_value = mock_create
    mock_create.execute.side_effect = errors.HttpError(
        Mock(status=555), 'Some generic error'.encode('utf-8')
    )

    customer_id = 'some_customer_id'
    group_email = 'newgroup@example.com'
    group_display_name = 'New Group'
    group_description = 'This is a new group'

    with pytest.raises(RuntimeError):
      self.client.create_group(
          customer_id, group_email, group_display_name, group_description
      )
    self.assert_mock_retries_n_times(mock_create)

  def test_list_roles_single_page(self):
    mock_admin_sdk_client = MagicMock()
    mock_roles = MagicMock()
    roles_response = {'items': [{'id': 'role1', 'name': 'Role 1'}]}
    self.client.get_admin_sdk_client = MagicMock(
        return_value=mock_admin_sdk_client
    )
    mock_admin_sdk_client.roles.return_value = mock_roles
    mock_roles.list.return_value.execute.return_value = roles_response

    roles = self.client.list_roles()
    self.assertEqual(roles, roles_response['items'])

  def test_list_roles_pagination(self):
    mock_admin_sdk_client = MagicMock()
    mock_roles = MagicMock()

    first_page_response = {
        'items': [{'id': 'role1', 'name': 'Role 1'}],
        'nextPageToken': 'next_page',
    }
    second_page_response = {'items': [{'id': 'role2', 'name': 'Role 2'}]}

    mock_roles.list.return_value.execute.side_effect = [
        first_page_response,
        second_page_response,
    ]
    self.client.get_admin_sdk_client = MagicMock(
        return_value=mock_admin_sdk_client
    )
    mock_admin_sdk_client.roles.return_value = mock_roles

    roles = self.client.list_roles()
    self.assertEqual(
        roles,
        [{'id': 'role1', 'name': 'Role 1'}, {'id': 'role2', 'name': 'Role 2'}],
    )

  def test_list_role_assignments_role_and_user_set(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    role_assignments_response = {
        'items': [{'roleId': 'role1', 'assignedTo': 'user@example.com'}]
    }

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.list.return_value.execute.return_value = (
        role_assignments_response
    )

    with pytest.raises(AssertionError):
      assignments = self.client.list_role_assignments( 'role1','user@example.com',)
      self.assertIsNone(assignments)

  def test_list_role_assignments_role_set_user_unset(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    role_assignments_response = {'items': [{'roleId': 'role1'}]}

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.list.return_value.execute.return_value = (
        role_assignments_response
    )

    assignments = self.client.list_role_assignments(None, 'role1')
    self.assertEqual(assignments, role_assignments_response['items'])

  def test_list_role_assignments_user_set_role_unset(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    role_assignments_response = {'items': [{'assignedTo': 'user@example.com'}]}

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.list.return_value.execute.return_value = (
        role_assignments_response
    )

    assignments = self.client.list_role_assignments('user@example.com')
    self.assertEqual(assignments, role_assignments_response['items'])

  def test_list_role_assignments_neither_set(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    role_assignments_response = {}

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.list.return_value.execute.return_value = (
        role_assignments_response
    )

    assignments = self.client.list_role_assignments()
    self.assertEqual(assignments, [])

  def test_list_role_assignments_forbidden(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    mock_execute = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.list.return_value = mock_execute
    mock_execute.execute.side_effect = errors.HttpError(
        Mock(status=403), 'Forbidden'.encode('utf-8')
    )

    with pytest.raises(RuntimeError):
      self.client.list_role_assignments()
    self.assert_mock_retries_n_times(mock_execute)

  def test_list_role_assignments_not_found(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    mock_execute = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.list.return_value = mock_execute
    mock_execute.execute.side_effect = errors.HttpError(
        Mock(status=404), 'Not Found'.encode('utf-8')
    )

    with pytest.raises(RuntimeError):
      self.client.list_role_assignments()
    self.assert_mock_retries_n_times(mock_execute)

  def test_list_role_assignments_paginated_response(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    first_page_response = {
        'items': [{'roleId': 'role1', 'assignedTo': 'user@example.com'}],
        'nextPageToken': 'nextToken',
    }
    second_page_response = {
        'items': [{'roleId': 'role2', 'assignedTo': 'user2@example.com'}]
    }

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.list.side_effect = [
        Mock(execute=Mock(return_value=first_page_response)),
        Mock(execute=Mock(return_value=second_page_response)),
    ]

    assignments = self.client.list_role_assignments()
    combined_response = (
        first_page_response['items'] + second_page_response['items']
    )
    self.assertEqual(assignments, combined_response)

  def test_delete_role_assignment_success(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.delete.return_value.execute.return_value = None

    self.assertTrue(self.client.delete_role_assignment('role_assignment_id_1'))
    mock_role_assignments.delete.assert_called_once_with(
        customer='my_customer', roleAssignmentId='role_assignment_id_1'
    )

  def test_delete_role_assignment_dry_run(self):
    self.client.is_dry_run = True

    with pytest.raises(
        AssertionError,
        match='GoogleApiClient.delete_role_assignment invoked when dryRun=True',
    ):
      self.client.delete_role_assignment('role_assignment_id_1')

  def test_delete_role_assignment_not_found(self):
    # HTTP 404 error (not found)
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    mock_execute = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.delete.return_value = mock_execute
    mock_execute.execute.side_effect = errors.HttpError(
        Mock(status=404), 'Not Found'.encode('utf-8')
    )
    self.assertFalse(self.client.delete_role_assignment('role_assignment_id_1'))

  def test_delete_role_assignment_admin_self_revoke(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    mock_execute = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.delete.return_value = mock_execute
    mock_execute.execute.side_effect = errors.HttpError(
        Mock(status=403), 'AdminSelfRevokeNotAllowed'.encode('utf-8')
    )
    self.assertFalse(self.client.delete_role_assignment('role_assignment_id_1'))

  def test_delete_role_assignment_forbidden(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    mock_execute = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.delete.return_value = mock_execute
    mock_execute.execute.side_effect = errors.HttpError(
        Mock(status=403), 'Forbidden Action'.encode('utf-8')
    )

    with pytest.raises(RuntimeError):
      self.client.delete_role_assignment('role_assignment_id_1')
    self.assertFalse(self.assert_mock_retries_n_times(mock_execute))

  def test_delete_role_assignment_generic_error(self):
    mock_admin_sdk_client = MagicMock()
    mock_role_assignments = MagicMock()
    mock_execute = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.roleAssignments.return_value = mock_role_assignments
    mock_role_assignments.delete.return_value = mock_execute
    mock_execute.execute.side_effect = errors.HttpError(
        Mock(status=500), 'Internal Server Error'.encode('utf-8')
    )

    with pytest.raises(RuntimeError):
      self.client.delete_role_assignment('role_assignment_id_1')
    self.assertFalse(self.assert_mock_retries_n_times(mock_execute))

  def test_insert_member_into_group_success(self):
    mock_admin_sdk_client = MagicMock()
    mock_members = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.members.return_value = mock_members
    mock_members.insert.return_value.execute.return_value = None

    self.client.insert_member_into_group(
        'user@example.com', 'user_id_1', 'group@example.com'
    )
    mock_members.insert.assert_called_once_with(
        groupKey='group@example.com',
        body={'email': 'user@example.com', 'role': 'MEMBER'},
    )

  def test_insert_member_into_group_dry_run(self):
    self.client.is_dry_run = True

    with pytest.raises(
        AssertionError,
        match=(
            'GoogleApiClient.insert_member_into_group invoked when dryRun=False'
        ),
    ):
      self.client.insert_member_into_group(
          'user@example.com', 'user_id_1', 'group@example.com'
      )

  def test_insert_member_into_group_already_member(self):
    mock_admin_sdk_client = MagicMock()
    mock_members = MagicMock()
    mock_execute = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.members.return_value = mock_members
    mock_members.insert.return_value = mock_execute
    mock_execute.execute.side_effect = errors.HttpError(
        Mock(status=409), 'Conflict'.encode('utf-8')
    )

    self.client.insert_member_into_group(
        'user@example.com', 'user_id_1', 'group@example.com'
    )

  def test_insert_member_into_group_generic_error(self):
    mock_admin_sdk_client = MagicMock()
    mock_members = MagicMock()
    mock_execute = MagicMock()

    self.client._adminsdk_client = mock_admin_sdk_client
    mock_admin_sdk_client.members.return_value = mock_members
    mock_members.insert.return_value = mock_execute
    mock_execute.execute.side_effect = errors.HttpError(
        Mock(status=500), 'Internal Server Error'.encode('utf-8')
    )

    with pytest.raises(RuntimeError):
      self.client.insert_member_into_group(
          'user@example.com', 'user_id_1', 'group@example.com'
      )
    self.assert_mock_retries_n_times(mock_execute)

if __name__ == '__main__':
  unittest.main()
