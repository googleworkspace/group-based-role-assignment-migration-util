import argparse
import difflib
import glob
import os
import os.path
import random
import re
import unittest
from change_client import google_api_client
from googleapiclient import errors
import phase_wise_runner
import timeout_decorator

ROLE_ID = '44750167542333480'
ROLE_ID_FORCE_GBRA = '44750167542333483'
ROLE_ID_SKIP_GBRA = '44750167542333484'
ROLE_ID_SA = '44750167542333444'
ROLE_ID_GROUPS_ADMIN = '44750167542333442'
ROLE_ID_CUSTOM_ROLE = '44750167542333441'
ORG_UNIT_ID = '03ph8a2z47c38bl'
ORG_UNIT_ID_2 = '03ph8a2z399p6ug'
RA_PER_SCOPE_LIMIT = 25


class TestOptions:

  def __init__(self, oa_client_creds):
    self.output_path = os.getcwd() + '/'
    self.ra_per_scope_limit = RA_PER_SCOPE_LIMIT
    self.oa_client_creds = oa_client_creds
    self.dry_run = True
    self.debug = True
    self.run_assertions = True
    self.roles_to_skip_gbra = []
    self.roles_to_force_gbra = []


class LiveTest(unittest.TestCase):

  def __init__(self, testoptions):
    self.testoptions = testoptions
    super().__init__()
    self.phase_wise_runner = phase_wise_runner.PhaseWiseRunner(
        testoptions.output_path,
        testoptions.oa_client_creds,
        testoptions.ra_per_scope_limit,
        testoptions.roles_to_force_gbra,
        testoptions.roles_to_skip_gbra,
        True,
        testoptions.dry_run,
        True,
        testoptions.debug,
    )
    self.google_api_client = google_api_client.GoogleApiClient(
        testoptions.output_path, testoptions.oa_client_creds, True, False
    )

  @classmethod
  def lookup_lists_of_dicts(cls, key, value, data_list):
    return [
        item
        for item in data_list
        if item.get(key) is not None
        and (item.get(key) == value or item.get(key).lower() == value)
    ]

  def assert_no_change(self):
    if self.testoptions.dry_run:
      return
    # Assert role-assignments to users 0-100
    role_assignments = self.google_api_client.list_role_assignments(
        role_id='44750167542333480'
    )
    self.assertGreater(
        len(
            LiveTest.lookup_lists_of_dicts(
                'assigneeType', 'user', role_assignments
            )
        ),
        50,
    )
    self.assertEquals(
        len(
            LiveTest.lookup_lists_of_dicts(
                'assigneeType', 'group', role_assignments
            )
        ),
        0,
    )

  def assert_group_assignments_done(self):
    if self.testoptions.dry_run:
      return
    # Assert role-assignments to users 0-100 are 0
    role_assignments = self.google_api_client.list_role_assignments(
        role_id=ROLE_ID
    )
    self.assertLen(
        LiveTest.lookup_lists_of_dicts(
            'assigneeType', 'group', role_assignments
        ),
        2,
    )

    role_assignments = self.google_api_client.list_role_assignments(
        role_id=ROLE_ID_SKIP_GBRA
    )
    self.assertEmpty(
        LiveTest.lookup_lists_of_dicts(
            'assigneeType', 'group', role_assignments
        )
    )

  def assert_duplicate_role_assignments_removed(self):
    if self.testoptions.dry_run:
      return
    role_assignments = self.google_api_client.list_role_assignments(
        role_id=ROLE_ID
    )
    self.assertLen(
        LiveTest.lookup_lists_of_dicts(
            'assigneeType', 'group', role_assignments
        ),
        2,
        'Expected group-role assignments to be 2 groupRole-assignments ={}'
        .format(
            LiveTest.lookup_lists_of_dicts(
                'assigneeType', 'group', role_assignments
            )
        ),
    )
    self.assertEquals(
        len(
            LiveTest.lookup_lists_of_dicts(
                'assigneeType', 'user', role_assignments
            )
        ),
        0,
        ' Expected user role assignments = 0 , user role-assignments = {}'
        .format(
            LiveTest.lookup_lists_of_dicts(
                'assigneeType', 'user', role_assignments
            )
        ),
    )

    role_assignments = self.google_api_client.list_role_assignments(
        role_id=ROLE_ID_FORCE_GBRA
    )
    self.assertLen(
        LiveTest.lookup_lists_of_dicts(
            'assigneeType', 'group', role_assignments
        ),
        1,
        'Expected group-role assignments to be 2 groupRole-assignments ={}'
        .format(
            LiveTest.lookup_lists_of_dicts(
                'assigneeType', 'group', role_assignments
            )
        ),
    )
    self.assertEquals(
        len(
            LiveTest.lookup_lists_of_dicts(
                'assigneeType', 'user', role_assignments
            ),
            ' Expected user role assignments = 0 , user role-assignments = {}'
            .format(
                LiveTest.lookup_lists_of_dicts(
                    'assigneeType', 'user', role_assignments
                )
            ),
        ),
        0,
    )

  def setup(self):
    print(
        'Deleting role-assignments to role = {} {} {}....'.format(
            ROLE_ID, ROLE_ID_FORCE_GBRA, ROLE_ID_SKIP_GBRA
        )
    )
    # delete all role-assignments
    for ra in self.google_api_client.list_role_assignments():
      if (
          ra['roleId'] == ROLE_ID
          or ra['roleId'] == ROLE_ID_FORCE_GBRA
          or ra['roleId'] == ROLE_ID_SKIP_GBRA
      ):
        self.google_api_client.delete_role_assignment(ra['roleAssignmentId'])

    print('Cleaningup/Deleting created groups...')
    groups = (
        self.google_api_client.get_admin_sdk_client()
        .groups()
        .list(customer='my_customer')
        .execute()
    )
    for group in groups['groups']:
      group_name = group['name']
      group_email = group['email']
      if not re.search(r'\d+-ORG_UNIT-\d+', group_name) and not re.search(
          r'\d+-CUSTOMER', group_name
      ):
        continue
      self.google_api_client.get_admin_sdk_client().groups().delete(
          groupKey=group_email
      ).execute()

    print(
        'Creating user role-assignments to Roles = {} {}  at org-unit scope'
        ' orgUnit={}'.format(ROLE_ID, ROLE_ID_SKIP_GBRA, ORG_UNIT_ID)
    )
    for i in range(1, 51):
      user_email = 'user{0}@gkeshavdas.focustest.org'.format(i)
      user = self.google_api_client.get_user(user_email)
      if user is None:
        continue
      user_id = user.get('id', None)
      try:
        self.google_api_client.insert_role_assignment({
            'roleId': ROLE_ID,
            'assignedTo': user_id,
            'assigneeType': 'USER',
            'scopeType': 'ORG_UNIT',
            'orgUnitId': ORG_UNIT_ID,
        })
        self.google_api_client.insert_role_assignment({
            'roleId': ROLE_ID_SKIP_GBRA,
            'assignedTo': user_id,
            'assigneeType': 'USER',
            'scopeType': 'ORG_UNIT',
            'orgUnitId': ORG_UNIT_ID,
        })
        if i < 3:
          self.google_api_client.insert_role_assignment({
              'roleId': ROLE_ID_FORCE_GBRA,
              'assignedTo': user_id,
              'assigneeType': 'USER',
              'scopeType': 'ORG_UNIT',
              'orgUnitId': ORG_UNIT_ID,
          })
      except errors.HttpError as e:
        print(f'An error occurred: {e}')

    print(
        'Creating user role-assignments to Role={} {}  at customer scope'
        .format(ROLE_ID, ROLE_ID_SKIP_GBRA)
    )
    for i in range(51, 100):
      user_email = 'user{0}@gkeshavdas.focustest.org'.format(i)
      user = self.google_api_client.get_user(user_email)
      if user is None:
        continue
      user_id = user.get('id', None)
      try:
        self.google_api_client.insert_role_assignment({
            'roleId': ROLE_ID,
            'assignedTo': user_id,
            'assigneeType': 'USER',
            'scopeType': 'CUSTOMER',
        })
      except errors.HttpError as e:
        print(f'An error occurred: {e}')

    sa_user_email_1 = 'user101@gkeshavdas.focustest.org'
    sa_user_email_2 = 'user102@gkeshavdas.focustest.org'
    sa_user_1 = self.google_api_client.get_user(sa_user_email_1)
    sa_user_2 = self.google_api_client.get_user(sa_user_email_2)
    self.google_api_client.insert_role_assignment({
        'roleId': ROLE_ID_SA,
        'assignedTo': sa_user_1['id'],
        'assigneeType': 'USER',
        'scopeType': 'CUSTOMER',
    })
    self.google_api_client.insert_role_assignment({
        'roleId': ROLE_ID_SA,
        'assignedTo': sa_user_2['id'],
        'assigneeType': 'USER',
        'scopeType': 'CUSTOMER',
    })
    self.google_api_client.insert_role_assignment({
        'roleId': ROLE_ID_GROUPS_ADMIN,
        'assignedTo': sa_user_1['id'],
        'assigneeType': 'USER',
        'scopeType': 'CUSTOMER',
    })
    self.google_api_client.insert_role_assignment({
        'roleId': ROLE_ID_CUSTOM_ROLE,
        'assignedTo': sa_user_2['id'],
        'assigneeType': 'USER',
        'scopeType': 'ORG_UNIT',
        'orgUnitId': ORG_UNIT_ID_2,
    })


def find_in_log(in_regex, output_path):
  with open(find_log(output_path), 'r') as f:
    for line in f:
      if re.search(in_regex, line):
        return True
    return False


def find_log(output_path):
  log_directory = os.path.dirname(output_path)
  log_files = glob.glob(os.path.join(log_directory, 'log*'))
  print(log_files)
  log_files.sort(key=os.path.getmtime, reverse=True)
  if log_files:
    return log_files[0]
  else:
    raise AssertionError('Couldnt find log file')


def diff_files(wet_run_log, dry_run_log):
  with open(wet_run_log, 'r') as file1, open(dry_run_log, 'r') as file2:
    file1_lines = file1.readlines()
    file2_lines = file2.readlines()

  differ = difflib.Differ()
  diff_result = list(differ.compare(file1_lines, file2_lines))
  print('Dry run vs wet run diff {}'.format(diff_result))


def test_wet_vs_dry_run(test_options):
  test_options.dry_run = True
  test_dry_run(test_options)
  print('output_path={}'.format(test_options.output_path))
  dry_run_log = find_log(test_options.output_path)
  test_options.dry_run = False
  test_wet_run(test_options)
  wet_run_log = find_log(test_options.output_path)
  diff_files(wet_run_log, dry_run_log)


def setup(testoptions):
  live_test = LiveTest(testoptions)
  live_test.setup()


@timeout_decorator.timeout(random.randint(30, 60))
def test_wet_run_cancellation(testoptions):
  test_wet_run(testoptions)


def test_wet_run(testoptions):
  testoptions.dry_run = False
  wet_run_live_test = LiveTest(testoptions)
  wet_run_live_test.phase_wise_runner.do_phase_read()
  if testoptions.run_assertions:
    wet_run_live_test.assert_no_change()

  wet_run_live_test.phase_wise_runner.do_phase_modify()
  if testoptions.run_assertions:
    wet_run_live_test.assert_group_assignments_done()

  wet_run_live_test.phase_wise_runner.do_phase_cleanup()
  if testoptions.run_assertions:
    wet_run_live_test.assert_group_assignments_done()
    wet_run_live_test.assert_duplicate_role_assignments_removed()


def test_dry_run(testoptions):
  testoptions.dry_run = True
  dry_run_live_test = LiveTest(testoptions)
  dry_run_live_test.phase_wise_runner.do_phase_read()
  if testoptions.run_assertions:
    dry_run_live_test.assert_no_change()

  dry_run_live_test.phase_wise_runner.do_phase_modify()
  if testoptions.run_assertions:
    dry_run_live_test.assert_group_assignments_done()

  dry_run_live_test.phase_wise_runner.do_phase_cleanup()
  if testoptions.run_assertions:
    dry_run_live_test.assert_group_assignments_done()
    dry_run_live_test.assert_duplicate_role_assignments_removed()


def test_intermediate_cancellation(testoptions):
  testoptions.run_assertions = False
  testoptions.dry_run = False
  try:
    test_wet_run_cancellation(testoptions)
  except timeout_decorator.TimeoutError:
    print('Expected timeout')
  testoptions.run_assertions = False
  test_wet_run(testoptions)


def test_sa_unneeded_deleted(testoptions):
  testoptions.dry_run = True
  dry_run_live_test = LiveTest(testoptions)
  dry_run_live_test.phase_wise_runner.do_phase_cleanup()
  assert (
      find_in_log(
          'Deleted duplicate role-assignment from'
          ' super-admin-user.*user101@gkeshavdas.focustest.org',
          testoptions.output_path,
      )
      is True
  )
  assert (
      find_in_log(
          'Deleted duplicate role-assignment from'
          ' super-admin-user.*user102@gkeshavdas.focustest.org',
          testoptions.output_path,
      )
      is False
  )


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='Group-based-role-assignment-migration utility.'
  )
  parser.add_argument(
      '--oa_client_id_creds',
      type=str,
      default=os.getcwd(),
      required=True,
      help=(
          'Absolute path to oauth client id credentials . See README for'
          ' setting up OAuth client-ID creds.'
      ),
  )
  args = parser.parse_args()
  options = TestOptions(args.oa_client_id_creds)
  options.roles_to_skip_gbra = [ROLE_ID_SKIP_GBRA]
  options.roles_to_force_gbra = [ROLE_ID_FORCE_GBRA]
  # setup(options)
  test_sa_unneeded_deleted(options)
  # Explicitly setup before every test
  # setup(options)
  # test_wet_vs_dry_run(options)
#  setup(options)
#  test_intermediate_cancellation(options)
