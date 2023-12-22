import sys
import unittest
from unittest.mock import Mock
from change_client.dry_run_change_client import DryRunChangeClient

sys.modules["utils.logger"] = Mock()
sys.modules["utils.credential_store"] = Mock()


class TestDryRunChangeClient(unittest.TestCase):

  def setUp(self):
    self.client = DryRunChangeClient()

  def test_create_group(self):
    customer_id = "12345"
    group_email = "group@example.com"
    group_display_name = "Test Group"
    group_description = "This is a test group"

    self.client.create_group(
        customer_id, group_email, group_display_name, group_description
    )

    group = self.client.get_group(group_email)
    self.assertIsNotNone(group)
    self.assertEqual(group["email"], group_email)
    self.assertEqual(group["name"], group_display_name)
    self.assertEqual(group["description"], group_description)

  def test_insert_member_into_group(self):
    user_email = "user@example.com"
    user_id = "67890"
    group_email = "group@example.com"

    self.client.insert_member_into_group(user_email, user_id, group_email)

    group_members = self.client.get_group_members(group_email)
    self.assertTrue(
        any(member["email"] == user_email for member in group_members)
    )

  def test_insert_and_delete_role_assignment(self):
    role_assignment = {
        "roleAssignmentId": "123",
        "roleId": "456",
        "userId": "789",
    }

    self.client.insert_role_assignment(role_assignment)
    self.assertTrue(
        any(
            ra["roleAssignmentId"] == "123"
            for ra in self.client.list_role_assignments()
        )
    )

    self.client.delete_role_assignment("123")
    self.assertFalse(
        any(
            ra["roleAssignmentId"] == "123"
            for ra in self.client.list_role_assignments()
        )
    )
    self.assertTrue("123" in self.client.list_deleted_role_assignments())

  def test_list_role_assignments_with_role_id(self):
    role_assignment1 = {
        "roleAssignmentId": "1",
        "roleId": "456",
        "userId": "789",
    }
    role_assignment2 = {
        "roleAssignmentId": "2",
        "roleId": "789",
        "userId": "123",
    }

    self.client.insert_role_assignment(role_assignment1)
    self.client.insert_role_assignment(role_assignment2)

    assignments = self.client.list_role_assignments(role_id="456")
    self.assertEqual(len(assignments), 1)
    self.assertEqual(assignments[0]["roleAssignmentId"], "1")
    
  def test_list_role_assignments_with_user_id(self):
    role_assignment1 = {
        "roleAssignmentId": "1",
        "roleId": "456",
        "userId": "789",
    }
    role_assignment2 = {
        "roleAssignmentId": "2",
        "roleId": "789",
        "userId": "123",
    }

    self.client.insert_role_assignment(role_assignment1)
    self.client.insert_role_assignment(role_assignment2)

    assignments = self.client.list_role_assignments(user_id="123")
    self.assertEqual(len(assignments), 1)
    self.assertEqual(assignments[0]["roleAssignmentId"], "2")

  def test_list_deleted_role_assignments(self):
    self.client.insert_role_assignment({"roleAssignmentId": "1"})
    self.client.delete_role_assignment("1")

    deleted_assignments = self.client.list_deleted_role_assignments()
    self.assertEqual(len(deleted_assignments), 1)
    self.assertEqual(deleted_assignments[0], "1")


if __name__ == "__main__":
  unittest.main()
