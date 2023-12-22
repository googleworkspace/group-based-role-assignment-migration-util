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

"""Client to call CIG / Google-admin-sdk APIs."""
import random
import re
import time
from typing import Any, Callable, Mapping, Sequence, Optional, TypeVar
from googleapiclient import discovery
from googleapiclient import errors
from third_party import ratelimiter
from change_client import change_client_interface
from utils import credential_store
from utils import logger


REQUESTS_PER_SECOND_DEFAULT = 10
REQUESTS_PER_SECOND_ROLES = 1
MAX_RETRIES = 5
BASE_DELAY_SECONDS = 1
MAX_DELAY_SECONDS = 32
DEFAULT_PAGE_SIZE = 100
TEST_PAGE_SIZE = 10

# TODO(b/298438250) : unit tests for this file
T = TypeVar('T')  # TypeVar for the return type of the inner function


def retry_with_credential_refresh(func: Callable[..., T]) -> Callable[..., T]:
  """Retry with credential refresh if error code 503 is returned."""

  def retried_func(self, *args: Any, **kwargs: Any) -> T:
    for retries in range(MAX_RETRIES):
      try:
        result = func(self, *args, **kwargs)
        return result
      except errors.HttpError as e:
        error_code = e.resp.status
        if error_code == 401:
          logger.Logger.get_instance().log(
              'Oauth token expired , refreshed token'
          )
          self.reauth_and_refresh_clients()
        else:
          logger.Logger.get_instance().log(
              'Caught http error which will be retried {}'.format(str(e))
          )
          if not self.is_test_env:
            delay = min(BASE_DELAY_SECONDS * 2**retries, MAX_DELAY_SECONDS)
            time.sleep(delay + random.uniform(0, 0.1 * delay))
    raise RuntimeError('Max retries exceeded. The operation failed.')
  return retried_func


class GoogleApiClient(change_client_interface.ChangeClientInterface):
  """GoogleAPIClient following ChangeClientInterface.

  Implementing actual invocation of adminsdk and CIG client.
  """

  def __init__(self, output_path, oa_client_creds, is_test_envs, is_dry_run):
    self.is_test_env = is_test_envs
    self.is_dry_run = is_dry_run
    self._credential_store = credential_store.CredentialStore(
        output_path, oa_client_creds
    )
    self.reauth_and_refresh_clients()

  def get_admin_sdk_client(self) -> Any:
    return self._adminsdk_client

  def get_identity_client(self) -> Any:
    return self._identity_client

  def get_people_client(self) -> Any:
    return self._people_client

  def reauth_and_refresh_clients(self):
    self._credential_store.authenticate()
    self._create_or_refresh_clients()

  def _create_or_refresh_clients(self):
    self._adminsdk_client = discovery.build(
        'admin',
        'directory_v1',
        credentials=self._credential_store.get_oauth_token(),
        cache_discovery=False,
    )
    self._identity_client = discovery.build(
        'cloudidentity',
        'v1',
        credentials=self._credential_store.get_oauth_token(),
        cache_discovery=False,
    )
    self._people_client = discovery.build(
        'people',
        'v1',
        credentials=self._credential_store.get_oauth_token(),
        cache_discovery=False,
    )

  @retry_with_credential_refresh
  def get_primary_email(self) -> str:
    person_info = (
        self._people_client.people()
        .get(resourceName='people/me', personFields='emailAddresses')
        .execute()
    )
    authenticated_email = None

    if 'emailAddresses' in person_info:
      for email_info in person_info['emailAddresses']:
        if (
            'metadata' in email_info
            and 'primary' in email_info['metadata']
            and email_info['metadata']['primary']
        ):
          authenticated_email = email_info['value']
          break
    return authenticated_email

  @retry_with_credential_refresh
  def get_customer(self) -> Optional[Mapping[str, Any]]:
    return (
        self.get_admin_sdk_client()
        .customers()
        .get(customerKey='my_customer')
        .execute()
    )

  @retry_with_credential_refresh
  def get_root_ou(self, customer_id: str) -> str:
    result = (
        self.get_admin_sdk_client()
        .orgunits()
        .list(customerId=customer_id)
        .execute()
    )
    ous = set()
    parent_ous = set()
    for ou in result['organizationUnits']:
      ous.add(ou['orgUnitId'])
      parent_ous.add(ou['parentOrgUnitId'])
    root_ous = parent_ous.difference(ous)
    if len(root_ous) > 1:
      raise AssertionError(
          'Unexpected error:multiple-root-ou, please contact Google support'
      )
    if not root_ous:
      raise AssertionError("Unexpected error: couldn't find root OU")
    root_ou_id = list(root_ous)[0]
    # orgUnits.list returns them in string format "id:<ou-name>""
    match = re.search(r'id:(.*)', root_ou_id)
    if match:
      return match.group(1)
    else:
      raise AssertionError('Unexpected error:invalid ouId patterns')

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_DEFAULT, period=1)
  @retry_with_credential_refresh
  def get_ou(self, ou_id: str) -> Optional[Mapping[str, Any]]:
    try:
      return (
          self.get_admin_sdk_client()
          .orgunits()
          .get(customerId='my_customer', orgUnitPath='id:' + ou_id)
          .execute()
      )
    except errors.HttpError as e:
      error_code = e.resp.status
      if error_code == 404:
        return None
      else:
        raise

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_DEFAULT, period=1)
  @retry_with_credential_refresh
  def get_user(self, user_email: str) -> Optional[Mapping[str, Any]]:
    try:
      return (
          self.get_admin_sdk_client().users().get(userKey=user_email).execute()
      )
    except errors.HttpError as e:
      error_code = e.resp.status
      if error_code == 404:
        return None
      else:
        raise

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_DEFAULT, period=1)
  @retry_with_credential_refresh
  def get_group(self, group_key: str) -> Optional[Mapping[str, Any]]:
    result = None
    try:
      result = (
          self.get_admin_sdk_client().groups().get(groupKey=group_key).execute()
      )
    except errors.HttpError as e:
      error_code = e.resp.status
      if error_code != 404:
        raise
    return result

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_DEFAULT, period=1)
  @retry_with_credential_refresh
  def group_has_member(self, group_email: str, user_email: str) -> bool:
    has_member = False
    try:
      member = (
          self.get_admin_sdk_client()
          .members()
          .get(groupKey=group_email, memberKey=user_email)
          .execute()
      )
      if member is not None and member['email'] == user_email:
        has_member = True
    except errors.HttpError as e:
      error_code = e.resp.status
      if error_code != 404:
        raise

    return has_member

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_DEFAULT, period=1)
  @retry_with_credential_refresh
  def get_group_members(self, group_email: str) -> Sequence[Mapping[str, Any]]:
    all_members = []
    page_token = None
    page_size = DEFAULT_PAGE_SIZE
    if self.is_test_env:
      page_size = TEST_PAGE_SIZE
    if self.get_group(group_email) is None:
      return []
    while True:
      members_list = (
          self.get_admin_sdk_client()
          .members()
          .list(
              groupKey=group_email, pageToken=page_token, maxResults=page_size
          )
          .execute()
      )
      if 'members' in members_list:
        all_members.extend(members_list['members'])
      page_token = members_list.get('nextPageToken')
      if not page_token:
        break
    return all_members

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_DEFAULT, period=1)
  @retry_with_credential_refresh
  def create_group(
      self,
      customer_id: str,
      group_email: str,
      group_display_name: str,
      group_description: str,
  ) -> None:
    if self.is_dry_run:
      raise AssertionError(
          'GoogleApiClient.create_group invoked when dryRun=True '
      )
    group_key = {'id': group_email}
    group = {
        'parent': 'customers/' + customer_id,
        'description': group_description,
        'displayName': group_display_name,
        'groupKey': group_key,
        'labels': {
            'cloudidentity.googleapis.com/groups.security': '',
            'cloudidentity.googleapis.com/groups.discussion_forum': '',
        },
    }
    # Create group if it doesn't exist
    try:
      request = self.get_identity_client().groups().create(body=group)
      request.uri += '&initialGroupConfig=WITH_INITIAL_OWNER'
      request.execute()
      return
    except errors.HttpError as e:
      error_code = e.resp.status
      if error_code == 409:
        return
      else:
        raise

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_ROLES, period=1)
  @retry_with_credential_refresh
  def list_roles(
      self,
  ) -> Sequence[Mapping[str, Any]]:
    all_roles = []
    page_token = 'first_page'

    if self.is_test_env:
      page_size = TEST_PAGE_SIZE
    else:
      page_size = DEFAULT_PAGE_SIZE
    while page_token is not None:
      if page_token == 'first_page':
        roles_response = (
            self.get_admin_sdk_client()
            .roles()
            .list(
                customer='my_customer',
                maxResults=page_size,
            )
            .execute()
        )
      else:
        roles_response = (
            self.get_admin_sdk_client()
            .roles()
            .list(
                customer='my_customer',
                pageToken=page_token,
                maxResults=page_size,
            )
            .execute()
        )
      page_token = roles_response.get('nextPageToken')
      all_roles.extend(roles_response.get('items', []))

    return all_roles

  @retry_with_credential_refresh
  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_ROLES, period=1)
  def list_role_assignments(
      self, role_id: Optional[str] = None, user_id: Optional[str] = None
  ) -> Sequence[Mapping[str, Any]]:
    all_role_assignments = []
    page_token = None
    page_size = DEFAULT_PAGE_SIZE

    if self.is_test_env:
      page_size = TEST_PAGE_SIZE
    while True:
      if role_id is None and user_id is None:
        ra_response = (
            self.get_admin_sdk_client()
            .roleAssignments()
            .list(
                customer='my_customer',
                pageToken=page_token,
                maxResults=page_size,
            )
            .execute()
        )
      elif role_id is not None and user_id is None:
        ra_response = (
            self.get_admin_sdk_client()
            .roleAssignments()
            .list(
                customer='my_customer',
                roleId=role_id,
                pageToken=page_token,
                maxResults=page_size,
            )
            .execute()
        )
      elif user_id is not None and role_id is None:
        ra_response = (
            self.get_admin_sdk_client()
            .roleAssignments()
            .list(
                customer='my_customer',
                userKey=user_id,
                pageToken=page_token,
                maxResults=page_size,
            )
            .execute()
        )
      else:
        raise AssertionError(
            'google_api_client.list_role_assignments user_id and role_id may'
            ' not be both specified'
        )

      page_token = ra_response.get('nextPageToken')
      all_role_assignments.extend(ra_response.get('items', []))
      if not page_token:
        break
    return all_role_assignments

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_ROLES, period=1)
  @retry_with_credential_refresh
  def delete_role_assignment(self, role_assignment_id: str) -> bool:
    if self.is_dry_run:
      raise AssertionError(
          'GoogleApiClient.delete_role_assignment invoked when dryRun=True '
      )
    try:
      self.get_admin_sdk_client().roleAssignments().delete(
          customer='my_customer', roleAssignmentId=role_assignment_id
      ).execute()
    except errors.HttpError as e:
      error_code = e.resp.status
      if error_code == 404:
        return False
      # The asserted user -i.e. admin cannot perform actions on itself
      if error_code == 403 and re.search(r'AdminSelfRevokeNotAllowed', str(e)):
        logger.Logger.get_instance().debug(
            ' ....AdminSelfRevokeNotAllowed! {}'.format(str(e))
        )
        return False
      else:
        raise
    return True

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_DEFAULT, period=1)
  @retry_with_credential_refresh
  def insert_member_into_group(
      self, user_email: str, user_id: str, group_email: str
  ) -> None:
    if self.is_dry_run:
      raise AssertionError(
          'GoogleApiClient.insert_member_into_group invoked when dryRun=False '
      )
    try:
      member = {
          'email': user_email,
          'role': 'MEMBER',
      }  # Use 'OWNER' if you want to add as an owner
      self.get_admin_sdk_client().members().insert(
          groupKey=group_email, body=member
      ).execute()
    except errors.HttpError as e:
      error_code = e.resp.status
      if error_code == 409:
        return
      else:
        raise
    return

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_ROLES, period=1)
  @retry_with_credential_refresh
  def insert_role_assignment(self, role_assignment: Mapping[str, Any]) -> None:
    if self.is_dry_run:
      raise AssertionError(
          'GoogleApiClient.insert_role_assignment invoked when dryRun=False '
      )
    try:
      self.get_admin_sdk_client().roleAssignments().insert(
          customer='my_customer', body=role_assignment
      ).execute()
    except errors.HttpError as e:
      error_code = e.resp.status
      if error_code != 409:
        raise

  @ratelimiter.RateLimiter(max_calls=REQUESTS_PER_SECOND_ROLES, period=1)
  @retry_with_credential_refresh
  def get_role(self, role_id: str) -> Optional[Mapping[str, Any]]:
    return (
        self.get_admin_sdk_client()
        .roles()
        .get(customer='my_customer', roleId=role_id)
        .execute()
    )
