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

"""A utility class for managing role-assignment and group changes.

This class invokes Google admin-sdk/CIG APIs for CRUD operations if
dryRun=False,
otherwise writes to dry-run change records.
"""
from __future__ import print_function

from typing import Any, Dict, Sequence, Optional, Mapping

from googleapiclient import errors

# from overrides import overrides
# pytype: enable=signature-mismatch

from change_client import change_client_interface
from change_client import dry_run_change_client
from change_client import google_api_client


class MigrationUtilChangeClient(change_client_interface.ChangeClientInterface):
  """A utility class for managing role-assignment and group changes.

  This class invokes Google admin-sdk/CIG APIs for CRUD operations if
  dryRun=False,
  otherwise writes to dry-run change records.
  """

  def __init__(self, output_path, oa_client_id_creds, dry_run, is_test_envs):
    self.dry_run_changes = dry_run_change_client.DryRunChangeClient()
    self.google_api_client = google_api_client.GoogleApiClient(
        output_path, oa_client_id_creds, is_test_envs, dry_run
    )
    self.user_cache = {}
    self.ou_cache = {}
    self.dry_run = dry_run

  def is_dry_run(self) -> bool:
    return self.dry_run

  def insert_ra(
      self,
      role_id: str,
      assignee_email: str,
      assignee_type: str,
      scope_type: Any,
      org_unit: Optional[str] = None,
  ):
    if assignee_type != 'group':
      raise AssertionError(
          'Unexpected assignee type : expected to be group but is {}'.format(
              assignee_type
          )
      )
    else:
      assignee_id = self.get_group(assignee_email)['id']
      ra = {
          'roleId': role_id,
          'assignedTo': assignee_id,
          'assigneeType': assignee_type,
          'scopeType': scope_type,
      }

    if org_unit is not None:
      ra['orgUnitId'] = org_unit

    try:
      if self.get_role_assignment(ra) is None:
        self.insert_role_assignment(ra)
    except errors.HttpError as e:
      error_code = e.resp.status
      if error_code != 409:
        raise

  def get_role_assignment(
      self, ra_to_find: Dict[str, Any]
  ) -> Optional[Dict[str, Any]]:
    """Find role-assignments by checking matching fields."""
    ras_by_role = self.list_role_assignments(ra_to_find['roleId'])
    # Role-assignments have fields such as etag etc which neednt be exactly
    # matched and may not exist in dry run, therefore do a minimum
    # field by field match
    for ra_by_role in ras_by_role:
      if (
          ra_by_role['assignedTo'] == ra_to_find['assignedTo']
          and ra_by_role['assigneeType'] == ra_to_find['assigneeType']
          and ra_by_role['scopeType'] == ra_to_find['scopeType']
          and ra_by_role.get('orgUnitId', '') == ra_to_find.get('orgUnitId', '')
      ):
        return ra_to_find

    return None

  # Overrides below

  def create_group(
      self,
      customer_id: str,
      group_email: str,
      group_display_name: str,
      group_description: str,
  ) -> None:
    if self.is_dry_run():
      self.dry_run_changes.create_group(
          customer_id, group_email, group_display_name, group_description
      )
    else:
      self.google_api_client.create_group(
          customer_id, group_email, group_display_name, group_description
      )

  def get_ou(self, ou_id: str) -> Optional[Mapping[str, Any]]:
    if ou_id in self.ou_cache:
      return self.ou_cache[ou_id]
    return self.google_api_client.get_ou(ou_id)

  def get_user(self, user_email: str) -> Optional[Mapping[str, Any]]:
    if user_email in self.user_cache:
      return self.user_cache[user_email]
    self.user_cache[user_email] = self.google_api_client.get_user(user_email)
    return self.user_cache[user_email]

  def get_group(self, group_key: str) -> Optional[Mapping[str, Any]]:
    result = self.google_api_client.get_group(group_key)
    if result is None and self.is_dry_run():
      result = self.dry_run_changes.get_group(group_key)
    return result

  def get_group_members(self, group_email: str) -> Sequence[Mapping[str, Any]]:
    all_members = list(self.google_api_client.get_group_members(group_email))
    if self.is_dry_run():
      all_members.extend(self.dry_run_changes.get_group_members(group_email))
    return all_members

  def group_has_member(self, group_email: str, user_email: str) -> bool:
    has_member = self.google_api_client.group_has_member(
        group_email, user_email
    )
    if not has_member and self.is_dry_run():
      has_member = self.dry_run_changes.group_has_member(
          group_email, user_email
      )
    return has_member

  def get_root_ou(self, customer_id: str) -> str:
    return self.google_api_client.get_root_ou(customer_id)

  def list_role_assignments(
      self, role_id: Optional[str] = None, user_id: Optional[str] = None
  ) -> Sequence[Mapping[str, Any]]:
    if role_id is not None and user_id is not None:
      raise AssertionError(
          'list_role_assignments role_id and user_id may not be specified'
      )
    role_assignments = list(
        self.google_api_client.list_role_assignments(role_id, user_id)
    )
    if self.is_dry_run():
      role_assignments.extend(
          self.dry_run_changes.list_role_assignments(role_id, user_id)
      )
      dry_run_deleted_ra_ids = {
          item['roleAssignmentId']
          for item in self.dry_run_changes.list_deleted_role_assignments()
      }
      role_assignments = [
          ra
          for ra in role_assignments
          if ra['roleAssignmentId'] not in dry_run_deleted_ra_ids
      ]
    return role_assignments

  def list_roles(self) -> Sequence[Mapping[str, Any]]:
    return self.google_api_client.list_roles()

  def delete_role_assignment(self, role_assignment_id: str) -> bool:
    if self.is_dry_run():
      return self.dry_run_changes.delete_role_assignment(role_assignment_id)
    else:
      return self.google_api_client.delete_role_assignment(role_assignment_id)

  def insert_member_into_group(
      self, user_email: str, user_id: str, group_email: str
  ) -> None:
    if self.group_has_member(group_email, user_email):
      return None
    if self.is_dry_run():
      self.dry_run_changes.insert_member_into_group(
          user_email, user_id, group_email
      )
    else:
      self.google_api_client.insert_member_into_group(
          user_email, user_id, group_email
      )

  def insert_role_assignment(self, role_assignment: Dict[str, Any]) -> None:
    if self.is_dry_run():
      role_assignment['roleAssignmentId'] = 'dummy'
      self.dry_run_changes.insert_role_assignment(role_assignment)
    else:
      self.google_api_client.insert_role_assignment(role_assignment)

  def get_role(self, role_id: str) -> Optional[Mapping[str, Any]]:
    return self.google_api_client.get_role(role_id=role_id)

  def get_customer(self) -> Optional[Mapping[str, Any]]:
    return self.google_api_client.get_customer()
  
  def get_primary_email(self) -> str:
    return self.google_api_client.get_primary_email()
