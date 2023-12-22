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

"""Phase wise runner for migration utlity."""
from __future__ import print_function
import time
from typing import Sequence
import gbra_migration_util
from utils import logger


class PhaseWiseRunner:
  """Phase wise runner for migration utlity.

  Phases are :
  1. Read
  2. Modify
  3. Cleanup.
  """

  def __init__(
      self,
      output_path: str,
      oa_client_id_creds: str,
      ra_per_scope_limit: int,
      roles_to_force_gbra: Sequence[int],
      roles_to_skip_gbra: Sequence[int],
      delete_dup_ras_to_sa: bool,
      dry_run: bool,
      is_test_env: bool = False,
      debug: bool = False,
  ):
    logger.Logger.initialize(output_path, debug)
    self.migration_util = gbra_migration_util.MigrationUtility(
        output_path,
        oa_client_id_creds,
        ra_per_scope_limit,
        roles_to_force_gbra,
        roles_to_skip_gbra,
        dry_run,
        is_test_env,
    )
    self.delete_dup_ras_to_sa = delete_dup_ras_to_sa

  def do_precheck(self):
    """Precheck phase."""
    if not self.migration_util.check_principal_is_super_admin():
      raise RuntimeError(
          'Must run script with authority ( Oauth consent ) of super-admin. See'
          ' README for details'
      )

  def do_phase_read(self):
    """Run read phase."""
    start_time = time.time()
    logger.Logger.get_instance().header(
        '[1]Executing READ phase in mode Dry_run={}'.format(
            self.migration_util.dry_run
        )
    )
    rolescope_to_ra_map = self.migration_util.get_rolescope_to_ra_map()
    scope_to_ra_map = self.migration_util.get_scope_to_ra_map(
        filter_under_ra_limit=True, human_readable_scope_name=True
    )

    if not rolescope_to_ra_map.keys() or not scope_to_ra_map.keys():
      return
    table_rolescope_to_modify = []
    table_scope_exceed_limit = []
    for (
        role_scope,
        role_assignments_at_role_scope,
    ) in rolescope_to_ra_map.items():
      table_rolescope_to_modify.append([
          self.migration_util.migration_util_change_util.get_role(
              role_scope.roleId
          )['roleName'],
          role_scope.roleId,
          self.migration_util.get_human_scope_name(
              role_scope.scopeType, role_scope.orgUnit
          ),
          len(role_assignments_at_role_scope),
      ])

    for scope, role_assignments_at_scope in scope_to_ra_map.items():
      if len(role_assignments_at_scope) < self.migration_util.ra_limit:
        continue
      table_scope_exceed_limit.append([
          scope,
          len(role_assignments_at_scope),
      ])

    logger.Logger.get_instance().log(
        'Number of scopes exceeding scope limit({}) =  {}'.format(
            self.migration_util.ra_limit, len(table_scope_exceed_limit)
        )
        + '\n'
    )
    logger.Logger.get_instance().log_table(
        ['Scope', '#Role-Assignments'],
        table_scope_exceed_limit,
    )

    logger.Logger.get_instance().log(
        '\n\nRole-assignments at each scope that *will* be modified to group'
        ' based role-assignments to reduce role-assignments per-scope such that'
        ' they are less than {} role-assignments per-scope listed below.'
        .format(self.migration_util.ra_limit)
    )
    logger.Logger.get_instance().log_table(
        ['Role Name', 'Role Id', 'Scope', 'Role-Assignments'],
        table_rolescope_to_modify,
    )
    end_time = time.time()
    logger.Logger.get_instance().log(
        '[1]Phase completed in {} seconds.'.format(int(end_time - start_time))
    )

  def do_phase_modify(self):
    """Run modify phase."""
    start_time = time.time()
    logger.Logger.get_instance().header(
        '[2]Executing WRITE/MODIFY  phase in mode Dry_run={}'.format(
            self.migration_util.dry_run
        )
    )

    rolescope_to_ra_map = self.migration_util.get_rolescope_to_ra_map()
    logger.Logger.get_instance().log('[2.1] Creating groups')
    self.migration_util.create_groups(rolescope_to_ra_map)

    logger.Logger.get_instance().log(
        '[2.2] Assigning roles to newly created groups '
    )
    self.migration_util.make_ra_to_groups(rolescope_to_ra_map)
    logger.Logger.get_instance().log(
        '[2.3] Inserting users into newly created groups'
    )
    # Add members to the groups
    # Regenerate the role-scope to role-assignments map since the hierarchy is
    # modified above.
    for (
        role_scope,
        role_assignments_at_role_scope,
    ) in self.migration_util.get_rolescope_to_ra_map().items():
      self.migration_util.add_assignees_to_group_at_scope(
          role_scope, role_assignments_at_role_scope
      )
    end_time = time.time()
    logger.Logger.get_instance().log(
        '[2]Phase completed in {} seconds.'.format(int(end_time - start_time))
    )

  def do_phase_cleanup(self):
    """Run cleanup phase."""
    start_time = time.time()
    logger.Logger.get_instance().header(
        '[3]Executing CLEANUP phase in mode Dry_run={}'.format(
            self.migration_util.dry_run
        )
    )
    if self.delete_dup_ras_to_sa:
      logger.Logger.get_instance().log(
          '[3] Deleting un-needed non-superadmin role-assignments to'
          ' super-admins.'
      )
      self.migration_util.delete_dup_ra_to_sas()

    logger.Logger.get_instance().log(
        "[3] Deleting duplicate role-assignments to user's for which"
        ' group based role-assignments exist.'
    )
    for (
        role_scope,
        role_assignments_at_role_scope,
    ) in self.migration_util.get_rolescope_to_ra_map(filtered=False).items():
      # No need to filter role-assignments for cleanup
      # Cleanup only removes duplicates from script created groups
      self.migration_util.cleanup_role_assignments(
          role_scope, role_assignments_at_role_scope
      )
    end_time = time.time()
    logger.Logger.get_instance().log(
        '[3]Phase completed in {} seconds.'.format(int(end_time - start_time))
    )
