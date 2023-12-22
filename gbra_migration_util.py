#!/usr/bin/python
#
# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MigrationUtility - utlity functions for policy/group changes."""
from __future__ import print_function

import collections
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from change_client import migration_util_change_client
from utils import logger

_ORG_UNIT_SCOPE_STRING = 'ORG_UNIT'
RoleScope = collections.namedtuple(
    'RoleScope', ['roleId', 'scopeType', 'orgUnit']
)


def _get_list_of_dicts_matching(
    key: str, value: Any, data_list: List[Dict[str, Any]]
):
  """Returns a list of dictionaries from the given `data_list`.

  That have a key-value pair containing the given `key` and `value`.
  The matching is case-insensitive.

  Args:
    key: The key to match.
    value: The value to match.
    data_list: The list of dictionaries to search.

  Returns:
    A list of dictionaries that have a key-value pair matching the given `key`
    and `value`.

  Example:
    >>> data_list = [{'name': 'John Doe'}, {'name': 'Jane Doe'}]
    >>> _get_list_of_dicts_matching('name', 'john doe', data_list)
    [{'name': 'John Doe'}]
  """
  filtered_items = []

  for item in data_list:
    item_value = item.get(key, '')
    if item_value == value or (item_value and item_value.lower() == value):
      filtered_items.append(item)

  return filtered_items


def _rolescope_to_group_name(rolescope):
  return (
      rolescope.roleId
      + '-'
      + MigrationUtility.rolescope_to_scope_name(rolescope)
  )


class MigrationUtility:

  """MigrationUtility - utlity functions for policy/group changes."""

  def __init__(
      self,
      output_path: str,
      oa_client_id_creds: str,
      ra_limit: int,
      roles_to_force_gbra: List[int],
      roles_to_skip_gbra: List[int],
      dry_run: bool,
      is_test_env: bool,
  ):
    self.migration_util_change_util = (
        migration_util_change_client.MigrationUtilChangeClient(
            output_path, oa_client_id_creds, dry_run, is_test_env
        )
    )
    self.ra_limit = ra_limit
    self._dry_run = dry_run
    self.roles_to_force_gbra = roles_to_force_gbra
    self.roles_to_skip_gbra = roles_to_skip_gbra

  @classmethod
  def rolescope_to_scope_name(cls, rolescope: RoleScope) -> str:
    """Converts a RoleScope object to a scope name string."""
    scope_name = rolescope.scopeType
    if rolescope.scopeType == _ORG_UNIT_SCOPE_STRING:
      scope_name = scope_name + '-' + rolescope.orgUnit
    return scope_name

  @classmethod
  def get_scope_name_for_ra(cls, role_assignment: Dict[str, Any]) -> str:
    """Converts a RoleAssignment object to a scope name string."""
    scope_name = role_assignment.get('scopeType', '')
    if role_assignment.get('scopeType', '') == _ORG_UNIT_SCOPE_STRING:
      scope_name = scope_name + '-' + role_assignment.get('orgUnitId', '')
    return scope_name

  @property
  def dry_run(self) -> bool:
    return self._dry_run

  def get_human_scope_name(self, scope_type: str, org_unit_id: str) -> str:
    """Converts a RoleScope object to a human scope name string."""
    if scope_type == 'ORG_UNIT':
      ou = self.migration_util_change_util.get_ou(org_unit_id)
      return 'ORG_UNIT-' + ou['orgUnitPath'] if ou else org_unit_id
    else:
      return 'CUSTOMER'

  def create_groups(self, role_map: Mapping[RoleScope, Sequence[Any]]) -> None:
    """Creates groups per rolescope in the given role map.

    Args:
        role_map: A map of rolescopes to lists of role assignments which require
          modifications to role-assignments to migrate them from user assigned
          to group-based

    Returns:
        None.
    """

    domain = self.migration_util_change_util.get_customer()['customerDomain']
    customer_id = self.migration_util_change_util.get_customer()['id']
    for key in role_map.keys():
      group_name = _rolescope_to_group_name(key)
      group_email = group_name + '@' + domain

      if self.migration_util_change_util.get_group(group_email) is None:
        self.migration_util_change_util.create_group(
            customer_id,
            group_email,
            group_name,
            'Group to be assigned to RoleId-Scope {}'.format(
                MigrationUtility.rolescope_to_scope_name(key)
            ),
        )
        logger.Logger.get_instance().log_indented(
            'Created group with groupName={} and groupEmail={}'.format(
                group_name, group_email
            )
        )

  def _get_filtered_rolescope_to_ra_map(
      self, role_assignments_at_scope: Optional[List[Dict[str, Any]]] = None, filtered: bool = True
  ) -> Mapping[RoleScope, Sequence[Mapping[str, Any]]]:
    """Gets a map of role-scopes to lists of role-assignments.

    Args:
        role_assignments_at_scope: A list of role-assignments at a scope.

    Returns:
        A dictionary of role-scopes to lists of role-assignments.
        The returned dictionary has only those role-assignments that need to
        be converted to group-based role-assignments , such that the number of
        role-assignments for the scope falls under the limit.
    """
    role_scope_to_ra_map = {}
    for role_assignment in role_assignments_at_scope:
      scope_type = role_assignment['scopeType']
      role_id = role_assignment['roleId']
      assignee = role_assignment['assignedTo']
      assignee_type = role_assignment.get('assigneeType', None)
      if (
          assignee_type == 'user'
          and self.migration_util_change_util.get_user(assignee) is None
      ):
        logger.Logger.get_instance().debug(
            '.. Cannot retrieve user for userkey = {} '.format(assignee)
        )
        continue
      role_scope = RoleScope(
          roleId=role_id,
          scopeType=scope_type,
          orgUnit=role_assignment.get('orgUnitId', ''),
      )
      # Create a new list for the scopeType if it doesn't exist in the map
      if role_scope not in role_scope_to_ra_map:
        role_scope_to_ra_map[role_scope] = [role_assignment]
      else:
        role_scope_to_ra_map[role_scope].append(role_assignment)

    # Order the map by the number of role-assignments in each scope
    ordered_ra_scope_to_ra_map = collections.OrderedDict(
        sorted(
            role_scope_to_ra_map.items(), key=lambda x: len(x[1]), reverse=True
        )
    )
    if  not filtered:
      return ordered_ra_scope_to_ra_map

    filtered_role_scope_to_ra_map = {}
    for key, value in ordered_ra_scope_to_ra_map.items():
      logger.Logger.get_instance().debug(
          '..Processing role-scope:{}'.format(key)
      )
      # each filtered_role_scope_to_ra_map entry results in the reduction of
      # Role assignments by len( filtered_role_scope_to_ra_map[RoleScope]) - 1
      # -1 because one group role-assignment would be created
      # When the remaining role-assignent count is less than the limit defined
      # we may safely quit
      reduced_ra_count_for_scope = sum(
          len(values) for values in filtered_role_scope_to_ra_map.values()
      ) - len(filtered_role_scope_to_ra_map)

      remaining_ra_count_for_scope = (
          len(role_assignments_at_scope) - reduced_ra_count_for_scope
      )
      if self.roles_to_force_gbra and int(key.roleId) in self.roles_to_force_gbra:
        logger.Logger.get_instance().debug(
            '.. NOT filtering roleId = {} in the list --roles_to_force_gbra'
            .format(key.roleId)
        )
        filtered_role_scope_to_ra_map[key] = value
        continue

      if self.roles_to_skip_gbra and int(key.roleId) in self.roles_to_skip_gbra:
        logger.Logger.get_instance().debug(
            '.. FILTERING roleId = {} in the list --roles_to_skip_gbra'.format(
                key.roleId
            )
        )
        continue
      if remaining_ra_count_for_scope < self.ra_limit:
        logger.Logger.get_instance().debug(
            '... Reached reduction of ras per-scope by ={} for the given scope'
            ' which started with = {} role-assignments , not adding further'
            ' role-assignments to map  '.format(
                remaining_ra_count_for_scope, len(role_assignments_at_scope)
            )
        )
        continue

      if not self._can_role_be_processed(key.roleId):
        continue

      filtered_role_scope_to_ra_map[key] = value
    return filtered_role_scope_to_ra_map

  def get_scope_to_ra_map(
      self, filter_under_ra_limit=False, human_readable_scope_name=False
  ) -> Mapping[str, Sequence[Mapping[str, Any]]]:
    """Gets a map of scopes to lists of role assignments.

    Args: filter_under_ra_limit : Limit the scopes to those where the number of
    role-assignments is greater than the allowed limit

    Returns:
        A map of scopes to lists of role assignments.
    """

    role_assignments = self.migration_util_change_util.list_role_assignments(
        None, None
    )
    scope_to_ras_map = {}
    for role_assignment in role_assignments:
      if human_readable_scope_name:
        scope_name = self.get_human_scope_name(
            role_assignment.get('scopeType', ''),
            role_assignment.get('orgUnitId', ''),
        )
      else:
        scope_name = self.rolescope_to_scope_name(
            RoleScope(
                roleId=role_assignment.get('roleId', ''),
                scopeType=role_assignment.get('scopeType', ''),
                orgUnit=role_assignment.get('orgUnitId', ''),
            )
        )

      # Create a new list for the scopeType if it doesn't exist in the map
      if scope_name not in scope_to_ras_map:
        scope_to_ras_map[scope_name] = [role_assignment]
      else:
        scope_to_ras_map[scope_name].append(role_assignment)
    if filter_under_ra_limit:
      scope_to_ras_map = {
          k: v for k, v in scope_to_ras_map.items() if len(v) > self.ra_limit
      }

    return scope_to_ras_map

  def get_rolescope_to_ra_map(
      self, filtered=True
  ) -> Mapping[RoleScope, Sequence[Mapping[str, Any]]]:
    """Gets a map of rolescopes to lists of role assignments which will be 
    modified to group role-assignments in order to bring role-assignments 
    per-scope under limits.

    Filters roles that do not need to be modified

    Returns:
        A map of rolescopes to lists of role assignments.
    """
    scope_to_ras_map = self.get_scope_to_ra_map(
        filter_under_ra_limit=False, human_readable_scope_name=False
    )
    return_map = {}
    for key, value in scope_to_ras_map.items():
      logger.Logger.get_instance().debug(
          '..Processing role-assignments wihin scope = {} containing = {}'
          ' role-assignments '.format(key, len(value))
      )
      return_map.update(self._get_filtered_rolescope_to_ra_map(value, filtered))
    return return_map

  def add_assignees_to_group_at_scope(
      self, role_scope: RoleScope, role_assignments: Sequence[Mapping[str, Any]]
  ) -> None:
    """Adds role assignees to the assigned group at given role scope.

    Args:
        role_scope: The role scope to be processed
        role_assignments: A list of role assignments at the given scope.

    Returns:
        None.

    Example usage:

        # Add role assignees to the 'CUSTOMER' rolescope.
        add_role_assignees_at_role_scope('CUSTOMER', customer_role_assignments)
    """
    logger.Logger.get_instance().debug(
        '.add_role_assignees_at_role_scope = {}'.format(role_scope)
    )
    group_ras = _get_list_of_dicts_matching(
        'assigneeType', 'group', role_assignments
    )
    user_ras = _get_list_of_dicts_matching(
        'assigneeType', 'user', role_assignments
    )
    logger.Logger.get_instance().debug(
        ' User Role-assignments to be processed = {}\n Group Role assignments'
        ' to be processed {} '.format(user_ras, group_ras)
    )
    util_created_sec_groups = []
    for group_ra in group_ras:
      logger.Logger.get_instance().debug(
          'Analyzing groupRa = {} to find group '.format(group_ra)
      )
      group_id = group_ra.get('assignedTo', None)
      if group_id is None:
        logger.Logger.get_instance().debug('.. GroupId = None')
        continue
      if self.migration_util_change_util.get_group(group_id) is None:
        logger.Logger.get_instance().debug('.. get_group(GroupId) = None')
        continue
      group_name = self.migration_util_change_util.get_group(group_id)['name']
      group_email = self.migration_util_change_util.get_group(group_id)['email']
      if not re.search(r'\d+-ORG_UNIT-\d+', group_name) and not re.search(
          r'\d+-CUSTOMER', group_name
      ):
        logger.Logger.get_instance().debug(
            ".. user defined group - doesn't match format"
        )
        continue

      util_created_sec_groups.append(group_name)
      if len(util_created_sec_groups) > 1:
        raise AssertionError(
            'Unexpected >1 script created security groups {}'.format(
                util_created_sec_groups
            )
        )
      # add the user-role-assignments to the created-security-group
      for user_ra in user_ras:
        user = self.migration_util_change_util.get_user(user_ra['assignedTo'])
        logger.Logger.get_instance().debug(
            '..Attempting to insert user with id = {} retrievedUserObj={}'
            .format(user_ra['assignedTo'], user)
        )
        if user is None:
          logger.Logger.get_instance().debug('...Couldnt find user')
          continue
        user_email = user['primaryEmail']
        user_id = user['id']
        if self.migration_util_change_util.group_has_member(
            group_email, user_email
        ):
          logger.Logger.get_instance().debug('...Group already has member')
          continue
        if self.migration_util_change_util.insert_member_into_group(
            user_email, user_id, group_email
        ):
          logger.Logger.get_instance().log_indented(
              'Inserted user with userEmail={} into group with groupName={}'
              .format(user_email, group_email)
          )

  def make_ra_to_groups(
      self,
      role_scope_to_ra_map: Mapping[RoleScope, Sequence[Mapping[str, Any]]],
  ) -> None:
    """Assigns role assignments (RAs) to groups.

    It is expected that the groups already exist, created in a previous step

    Args:
        role_scope_to_ra_map: A dictionary mapping role scopes to lists of RAs.

    Raises:
        AssertionError: If the group for a given role scope does not exist.
    """
    domain = self.migration_util_change_util.get_customer()['customerDomain']
    for role_scope, ras in role_scope_to_ra_map.items():
      logger.Logger.get_instance().debug(
          'Making ra to groups for ra-scope={}'.format(role_scope)
      )
      group_email = (
          _rolescope_to_group_name(role_scope) + '@' + domain
      )
      customer_id = self.migration_util_change_util.get_customer()['id']
      org_unit = (
          role_scope.orgUnit
          if role_scope.scopeType == _ORG_UNIT_SCOPE_STRING
          else self.migration_util_change_util.get_root_ou(customer_id)
      )
      group = self.migration_util_change_util.get_group(group_email)
      if group is None:
        raise AssertionError(
            'Expected group to exist groupEmail={}'.format(group_email)
        )
      existing_ras_matching = _get_list_of_dicts_matching(
          'assigneeId', group['id'], ras
      )

      if len(existing_ras_matching) == 1:
        logger.Logger.get_instance().debug(
            '...ra to group already exists , skipping '
        )
        continue
      if len(existing_ras_matching) > 1:
        raise AssertionError(
            'Unexpected duplicate assignment of RoleId={} to groupEmail={}'
            .format(role_scope.roleId, group_email)
        )

      self.migration_util_change_util.insert_ra(
          role_scope.roleId,
          group_email,
          'group',
          role_scope.scopeType,
          org_unit,
      )

      logger.Logger.get_instance().log_indented(
          'Assigned group with groupEmail={} to Role with RoleId={}'.format(
              group_email, role_scope.roleId
          )
      )

  def _can_role_be_processed(self, role_id: str) -> bool:
    """Returns whether the given role can be processed.

    Args:
        role_id: The ID of the role.

    Returns:
        True if the role can be processed, False otherwise.

    Example usage:

        # Check if the role with ID '1234567890' can be processed.
        can_process = _can_role_be_processed('1234567890')
    """
    role = self.migration_util_change_util.get_role(role_id)

    if role and role.get('isSuperAdminRole', False):
      logger.Logger.get_instance().debug(
          'Not processing role = {} is superadmin'.format(role_id)
      )
      return False
    # Role-assignments should fail
    if (
        '_GCP_RESELLER_ADMIN_ROLE' in role['roleName']
        or '_RESELLER_ADMIN_ROLE' in role['roleName']
    ):
      logger.Logger.get_instance().debug(
          'Not processing role = {} is reseller'.format(role_id)
      )
      return False
    # MANAGE_HANGOUTS_SERVICE has service Id = 698697560117L
    # - obfuscated = 02w5ecyt3laroi5
    for priv_pair in role['rolePrivileges']:
      if (
          priv_pair['privilegeName'] == 'MANAGE_HANGOUTS_SERVICE'
          and priv_pair['serviceId'] == '02w5ecyt3laroi5'
      ):
        logger.Logger.get_instance().debug(
            'Not processing role = {} is invalid role'.format(role_id)
        )
        return False
    return True

  def cleanup_role_assignments(
      self,
      role_scope: RoleScope,
      role_assignments: Sequence[Mapping[str, Any]],
  ) -> None:
    """Cleans up duplicate role assignments from the given role scope.

    Args:
        role_scope: The role scope.
        role_assignments: A list of role assignments for the given role-scope.

    Example usage:

        # Clean up duplicate role assignments from the 'CUSTOMER' role scope.
        cleanup_role_assignments(RoleScope('roleId','CUSTOMER',''),
          role_assignments)
    """
    group_ras = _get_list_of_dicts_matching(
        'assigneeType', 'group', role_assignments
    )
    user_ras = _get_list_of_dicts_matching(
        'assigneeType', 'user', role_assignments
    )
    for group_ra in group_ras:
      logger.Logger.get_instance().debug(
          'cleanup_role_assignments for groupRa = {}'.format(group_ra)
      )
      group_id = group_ra.get('assignedTo', None)
      if group_id is None:
        logger.Logger.get_instance().debug('.. GroupId = None')
        continue
      if self.migration_util_change_util.get_group(group_id) is None:
        logger.Logger.get_instance().debug('.. get_group(GroupId) = None')
        continue
      group_name = self.migration_util_change_util.get_group(group_id)['name']
      group_email = self.migration_util_change_util.get_group(group_id)['email']
      logger.Logger.get_instance().debug(
          'Investigating group {} for duplicate assignments'.format(group_email)
      )

      if not re.search(r'\d+-ORG_UNIT-\d+', group_name) and not re.search(
          r'\d+-CUSTOMER', group_name
      ):
        logger.Logger.get_instance().debug('.. group is pre-existing')
        continue
      group_members = self.migration_util_change_util.get_group_members(
          group_email
      )
      logger.Logger.get_instance().debug(
          'Cleaning up duplicate role-assignments from group {}'.format(
              group_email
          )
      )
      for group_member in group_members:
        user_ras_to_delete = _get_list_of_dicts_matching(
            'assignedTo', group_member['id'], user_ras
        )
        logger.Logger.get_instance().debug(
            '.. role-assignments to delete={}'.format(user_ras_to_delete)
        )
        if not user_ras_to_delete:
          logger.Logger.get_instance().debug(
              '...Couldnt find ra for member={}'.format(group_member['id'])
          )
          continue
        if len(user_ras_to_delete) > 1:
          raise AssertionError(
              'Unexpected duplicate role-assignments for same user to same'
              ' role-scope user_ras_to_delete={}'.format(user_ras_to_delete)
          )
        # Should have found exactly one duplicate user-role-assignment
        # to be deleted
        user_ra_to_delete = user_ras_to_delete[0]

        self.migration_util_change_util.delete_role_assignment(
            user_ra_to_delete['roleAssignmentId']
        )

        user_ra_to_delete_user = self.migration_util_change_util.get_user(
            user_ra_to_delete['assignedTo']
        )

        # Get the email of the user whose ra has been removed for debugging only
        user_ra_to_delete_key_or_email = None
        if user_ra_to_delete_user is not None:
          user_ra_to_delete_key_or_email = user_ra_to_delete_user.get(
              'primaryEmail', user_ra_to_delete['assignedTo']
          )

        logger.Logger.get_instance().log_indented(
            'Deleted (duplicate) role-assignment from UserEmail/Key={} to'
            ' RoleId={}, role already assigned to group with groupEmail={}'
            ' containing this user.'.format(
                user_ra_to_delete_key_or_email, role_scope.roleId, group_email
            )
        )

  def _delete_dup_ra_to_sa_user(
      self, sa_user_key: str, super_admin_role_id: str
  ) -> None:
    """Deletes duplicate role assignments for a super admin user.

    This method finds all role assignments for the given super admin user. For
    each assignment, it checks if the assigned role is a super admin role. If
    the assigned role is not a super admin role, the assignment is deleted.

    This method is idempotent, meaning that it can be safely called multiple
    times without causing any harm.

    Args:
      sa_user_key: The user key of the super admin user.
      super_admin_role_id: The role ID of the super admin role.
    """
    all_ra_to_sa_user = self.migration_util_change_util.list_role_assignments(
        None, sa_user_key
    )
    # Get the scopes exceeding limit
    scope_to_ra_exceeding_map = self.get_scope_to_ra_map(
        filter_under_ra_limit=True, human_readable_scope_name=False
    )
    for ra_to_sa_user in all_ra_to_sa_user:
      if (
          self.get_scope_name_for_ra(ra_to_sa_user)
          not in scope_to_ra_exceeding_map.keys()
      ):
        continue
      if ra_to_sa_user['roleId'] != super_admin_role_id:
        if not self.migration_util_change_util.delete_role_assignment(
            ra_to_sa_user['roleAssignmentId']
        ):
          continue
        duplicate_role_info = self.migration_util_change_util.get_role(
            ra_to_sa_user['roleId']
        )
        sa_email = self.migration_util_change_util.get_user(sa_user_key)[
            'primaryEmail'
        ]
        logger.Logger.get_instance().log_indented(
            'Deleted duplicate role-assignment from super-admin-user={} to'
            ' non-super-admin-role with roleId={} role-name={}'
            ' role-assignment-id={}'.format(
                sa_email,
                duplicate_role_info['roleId'],
                duplicate_role_info['roleName'],
                ra_to_sa_user['roleAssignmentId'],
            )
        )

  def delete_dup_ra_to_sas(self) -> None:
    """Deletes duplicate role assignments to all super admins."""
    for sa_role in self.migration_util_change_util.list_roles():
      if not sa_role.get('isSuperAdminRole', False):
        continue
      sa_assignments = self.migration_util_change_util.list_role_assignments(
          sa_role['roleId'], None
      )
      for sa_assignment in sa_assignments:
        self._delete_dup_ra_to_sa_user(
            sa_user_key=sa_assignment['assignedTo'],
            super_admin_role_id=sa_role['roleId'],
        )

  def check_principal_is_super_admin(self) -> bool:
    """Precheck if the principal is super-admin."""
    try:
      email = self.migration_util_change_util.get_primary_email()
      if email is None:
        # allow the script to continue
        return True
    except RuntimeError as e:
      # allow the script to continue
      return True
    try:
      ras = self.migration_util_change_util.list_role_assignments(None, email)
      for ra in ras:
        if self.migration_util_change_util.get_role(ra['roleId']).get(
            'isSuperAdminRole', False
        ):
          return True
    except RuntimeError as e:
      # Couldnt retrieve role-assignments - not SA 
      return False
    return False
