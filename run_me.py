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

"""Entry point for gbra_migration utility."""
from __future__ import print_function

import os
import os.path
import phase_wise_runner

from absl import app
from absl import flags
from utils import logger


FLAGS = flags.FLAGS

_OUTPUT_PATH = flags.DEFINE_string(
    'output_path',
    default=os.getcwd(),
    help='Output path.',
)
_OAUTH_CLIENT_ID_CREDS = flags.DEFINE_string(
    'oa_client_id_creds',
    default=None,
    required=True,
    help=(
        'Absolute path to oauth client id credentials. See README for'
        ' setting up OAuth client-ID creds.'
    ),
)
_DRY_RUN = flags.DEFINE_boolean(
    'dry_run',
    default=True,
    help=(
        'Run utility in dry_run/read_only mode. Set to false by'
        ' --dry_run=false       Default/unset/incorrectly set value defaults'
        ' to true.       Setting to false modifies the customers      '
        ' entities and policies ( Role-assignments, Groups ).'
    ),
)
_ROLES_TO_FORCE_GBRA = flags.DEFINE_multi_integer(
    'roles_to_force_gbra',
    default=[],
    help=(
        'Role-ids whose role-assignments should be converted to group-based'
        ' role-assignments, irrespective of the number of role-assignments per'
        ' role-scope. Provide a list by re-using the command line to add roles'
        ' such as "--roles_to_force_gbra=123 --roles_to_force_gbra=456"'
    ),
)
_ROLES_TO_SKIP_GBRA = flags.DEFINE_multi_integer(
    'roles_to_skip_gbra',
    default=[],
    help=(
        'Role-ids whose role-assignments should NOT be converted to group-based'
        ' role-assignments, irrespective of the number of role-assignments per'
        ' role-scope. Provide a list by re-using the command line to add roles'
        ' such as "--roles_to_skip_gbra=123 --roles_to_skip_gbra=456"'
    ),
)
_DELETE_DUP_RAS_TO_SA = flags.DEFINE_boolean(
    'delete_dup_ras_to_sa',
    default=True,
    help=(
        'Delete non-superadmin role assignments to super-admins, since they'
        ' have no effect ( Super-admin role is the superset of all'
        ' roles/privileges.)'
    ),
)

# Hidden only, role-assignment per-scope limit - modifiable for testing
_RA_PER_SCOPE_LIMIT = flags.DEFINE_integer(
    'ra_per_scope_limit', default=500, help=None
)
# Hidden only, is-test, smaller page size, no rate-limiting
_IS_TEST = flags.DEFINE_boolean('is_test', default=False, help=None)

# Hidden only, log-level / verbosity
_DEBUG = flags.DEFINE_boolean('debug', default=False, help=None)


def main(unused_argv):
  # Initialize the client, which also performs the credential exchange
  runner = phase_wise_runner.PhaseWiseRunner(
      _OUTPUT_PATH.value,
      _OAUTH_CLIENT_ID_CREDS.value,
      _RA_PER_SCOPE_LIMIT.value,
      _ROLES_TO_FORCE_GBRA.value,
      _ROLES_TO_SKIP_GBRA.value,
      _DELETE_DUP_RAS_TO_SA.value,
      _DRY_RUN.value,
      _IS_TEST.value,
      _DEBUG.value,
  )

  if _DRY_RUN.value:
    logger.Logger.get_instance().log(
        '\nRunning utility in dry_run=True mode. Will **NOT** modify customers'
        ' policies ( Role-assignments ) and entities ( Groups ) '
    )
  else:
    logger.Logger.get_instance().log(
        "\nRunning utility in dry_run=False mode. **WILL** modify customer's"
        ' policies ( Role-assignments ) and entities ( Groups ) '
    )
  logger.Logger.get_instance().log(
      '\nLogs written to : {} '.format(
          logger.Logger().get_instance().get_log_path()
      )
  )
  runner.do_precheck()
  while True:
    logger.Logger.get_instance().log(
        '\nEnter the phase that you would like to execute:'
    )
    logger.Logger.get_instance().log(
        '(1) READ/ANALYZE: Analyze role-assignments that exceed limits that are'
        ' in scope for processing.'
    )
    logger.Logger.get_instance().log(
        '(2) WRITE/MODIFY: Modify role-assignments to bring them under limits.'
    )
    logger.Logger.get_instance().log(
        '(3) CLEANUP: Cleanup duplicate role-assignments.'
    )
    logger.Logger.get_instance().log('(4) All: Perform all phases 1,2,3.')

    user_input = input('\nEnter your choice (1/2/3/4): ')
    if user_input == '1':
      runner.do_phase_read()
      break
    elif user_input == '2':
      runner.do_phase_modify()
      break
    elif user_input == '3':
      runner.do_phase_cleanup()
      break
    elif user_input == '4':
      runner.do_phase_read()
      runner.do_phase_modify()
      runner.do_phase_cleanup()
      break
    else:
      logger.Logger.get_instance().log(
          '\nInvalid input. Valid inputs are the phase numbers : 1 / 2 / 3 / 4'
      )
  logger.Logger.get_instance().log('Exiting')


if __name__ == '__main__':
  try:
    app.run(main)
  except Exception as e:
    logger.Logger.get_instance().log(e)
    raise e
