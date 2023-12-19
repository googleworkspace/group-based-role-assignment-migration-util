"""Change client for Dry-run role-assignment/group changes.

This class is responsible for recording changes to policy and hierarchy
in a local copy. These changes are not actually applied in the customer's
domain due to the use of the dryRun=True parameter.
"""
from __future__ import print_function

import collections
from typing import Any, Mapping, Optional, Sequence

from change_client import change_client_interface


class DryRunChangeClient(change_client_interface.ChangeClientInterface):
  """Dry-Run change client to simulate dry-run role-assignment / group changes."""

  def __init__(self):
    self._ras = []
    self._groups = {}
    self._group_to_members = collections.defaultdict(list)

  def get_root_ou(self, customer_id: str) -> str:
    raise ValueError('Unexpected dry-run client check for get_root_ou')

  def get_customer(self) -> Optional[Mapping[str, Any]]:
    raise ValueError('Unexpected dry-run client check for get_customer')

  def get_role(self, role_id: str) -> Optional[Mapping[str, Any]]:
    raise ValueError('Unexpected dry-run client check for get_role')

  def get_user(self, user_email: str) -> Optional[Mapping[str, Any]]:
    raise ValueError('Unexpected dry-run client check for get_user')
  
  def get_ou(self, ou_id: str) -> Optional[Mapping[str, Any]]:
    raise ValueError('Unexpected dry-run client check for get_ou')

  def list_roles(self) -> Sequence[Mapping[str, Any]]:
    raise ValueError('Unexpected dry-run client check for list_roles')

  def create_group(
      self,
      customer_id: str,
      group_email: str,
      group_display_name: str,
      group_description: str,
  ) -> None:
    self._groups[group_email] = {
        'email': group_email,
        'id': group_email,
        'customerId': customer_id,
        'name': group_display_name,
        'description': group_description,
        'adminCreated': True,
    }
    return

  def get_group(self, group_key: str) -> Optional[Mapping[str, Any]]:
    return self._groups.get(group_key, None)

  def insert_member_into_group(
      self, user_email: str, user_id: str, group_email: str
  ) -> None:
    self._group_to_members[group_email].append(
        {'email': user_email, 'id': user_id}
    )

  def group_has_member(self, group_email: str, user_email: str) -> bool:
    for member in self._group_to_members[group_email]:
      if member['email'] == user_email:
        return True
    return False

  def get_group_members(self, group_email: str) -> Sequence[Mapping[str, Any]]:
    return self._group_to_members[group_email]

  def insert_role_assignment(self, role_assignment: Mapping[str, Any]) -> None:
    self._ras.append(role_assignment)

  def delete_role_assignment(self, role_assignment_id: str) -> bool:
    self._ras = [
        item
        for item in self._ras
        if item['roleAssignmentId'] != role_assignment_id
    ]
    return True

  def list_role_assignments(
      self, role_id: Optional[str] = None, user_id: Optional[str] = None
  ) -> Sequence[Mapping[str, Any]]:
    if role_id is not None and user_id is not None:
      raise AssertionError(
          'DryRunChangeClient.list_role_assignments should not be invoked with'
          ' both role_id and user_id set. '
      )
    elif role_id is not None:
      return [
          assignment
          for assignment in self._ras
          if assignment.get('roleId') == role_id
      ]
    elif user_id is not None:
      return [
          assignment
          for assignment in self._ras
          if assignment.get('userId') == user_id
      ]
    else:
      return self._ras
