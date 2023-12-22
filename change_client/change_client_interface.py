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

"""Change-client abstract class for.

1.Google api client 
2.Dry run client 
3.Migration util change client forcing them to uniformly implement ( or assert )
functionality
"""
import abc
from typing import Any, Dict, Optional, Sequence, Mapping


class ChangeClientInterface(abc.ABC):

  """Change-client abstract class."""

  @abc.abstractmethod
  def get_root_ou(self, customer_id: str) -> str:
    """Returns the root organizational unit (OU) for the given customer ID."""

  @abc.abstractmethod
  def get_user(self, user_email: str) -> Optional[Mapping[str, Any]]:
    """Returns the user information for the given user email."""
    
  @abc.abstractmethod
  def get_ou(self, user_email: str) -> Optional[Mapping[str, Any]]:
    """Returns the organizational-unit information for the given ou id."""

  @abc.abstractmethod
  def get_group(self, group_key: str) -> Optional[Mapping[str, Any]]:
    """Returns the group information for the given group key."""

  @abc.abstractmethod
  def group_has_member(self, group_email: str, user_email: str) -> bool:
    """Returns whether the given user is a member of the given group."""

  @abc.abstractmethod
  def get_group_members(self, group_email: str) -> Sequence[Mapping[str, Any]]:
    """Returns the members of the given group."""

  @abc.abstractmethod
  def insert_member_into_group(
      self, user_email: str, user_id: str, group_email: str
  ) -> None:
    """Inserts the given user into the given group."""

  @abc.abstractmethod
  def create_group(
      self,
      customer_id: str,
      group_email: str,
      group_display_name: str,
      group_description: str,
  ) -> None:
    """Creates a new group with the given information."""

  @abc.abstractmethod
  def list_roles(self) -> Sequence[Mapping[str, Any]]:
    """Returns a list of all roles."""

  @abc.abstractmethod
  def list_role_assignments(
      self, role_id: Optional[str] = None, user_id: Optional[str] = None
  ) -> Sequence[Mapping[str, Any]]:
    """Returns a list of role assignments."""

  @abc.abstractmethod
  def delete_role_assignment(self, role_assignment_id: str) -> bool:
    """Deletes the given role assignment."""

  @abc.abstractmethod
  def insert_role_assignment(self, role_assignment: Dict[str, Any]) -> None:
    """Inserts a new role assignment."""

  @abc.abstractmethod
  def get_role(self, role_id: str) -> Optional[Mapping[str, Any]]:
    """Returns the role information for the given role ID."""

  @abc.abstractmethod
  def get_customer(self) -> Optional[Mapping[str, Any]]:
    """Returns the customer information for the current customer."""
  
  @abc.abstractmethod
  def get_primary_email(self) -> str:
    """Returns the Oauth token principals email"""
