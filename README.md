# Group based role assignment migration utility

## Overview

This utility helps migrate customer's role assignments to users, to
[group based role assignments](https://support.google.com/a/users/answer/10385278).
This migration is limited to those role-assignments for a given role and
[scope](https://developers.google.com/admin-sdk/directory/reference/rest/v1/roleAssignments#resource:-roleassignment)
whose count exceeds [limit](https://support.google.com/a/answer/9807615)
(default : 500).

### How does it work

The utility runs in 3 phases : READ-ONLY, MODIFY, CLEANUP which are presented to
the user for selection.

A one-shot "ALL" option is also presented which runs following phases
sequentially and in the order : READ-ONLY , MODIFY , CLEANUP.

*   READ-ONLY :
    *   Identify Roles and scopes ( Organizational units ) where the
        role-assignments exceed a
        [limit](https://support.google.com/a/answer/9807615) (default:500).
        These will be referred to as role-assignments-to-be-migrated.
*   MODIFY :
    *   For each scope/organizational-unit where the number of assignments
        exceed the limit.
        *   We find the minimum set of roles to be migrated to group based
            role-assignments at the scope.
        *   For each of the roles in this minimum set
            *   Create a
                [security-group](https://support.google.com/a/answer/10607394?hl=en)
                named "\<RoleId>-\<OrganizationUnitName>"
            *   Create a role-assignment from the role to this group at the
                given scope.
            *   Insert the users belonging to role-assignments-to-be-migrated to
                this group.
*   CLEANUP :
    *   Cleanup the duplicate role-assignments-to-be-migrated.

### Authentication mechanism

*   This utility presents
    [OAuth-Client-ID-credentials to Google OAuth end-point](https://developers.google.com/workspace/guides/auth-overview#process_overview).
*   A link to OAuth consent screen is presented to the user running utility.
    *   This step requires user with super-admin credentials to login and
        consent.
*   The utility then obtains OAuth-token for the super-admin which will be used
    in the course of its run.
*   The token has a lifetime of 1 week during which time it will be exchanged ,
    access-token refreshed by the utility in the background every hour.
*   When the Oauth token refresh-lifetime of 1 week expires , the utility will
    present the user with a link to the Oauth-consent screen for Super-admin to
    consent and obtain a new Oauth-token.

## Usage

### Prerequisites

<a id="pre-req-client-id"></a>

1.  Enable APIs from Google Cloud Console (
    [How to enable APIs](https://cloud.google.com/apis/docs/getting-started#enabling_apis)
    )

    *   [ AdminSDK API ](https://console.cloud.google.com/apis/api/admin.googleapis.com)
    *   [ Cloud identity API ](https://console.cloud.google.com/apis/library/cloudidentity.googleapis.com)
    *   [ Google People API ](https://console.cloud.google.com/apis/library/people.googleapis.com)

2.  Get
    [ OAuth-Client ID credentials ](https://developers.google.com/workspace/guides/create-credentials#oauth-client-id)

    *   For the use-case of this utility , the steps are modified to those below
        *   In the
            [Google Cloud console](https://console.cloud.google.com/apis/credentials),
            go to Menu menu > APIs & Services > Credentials.
        *   Click Create Credentials > OAuth client ID.
        *   Click Application type > Desktop application.
        *   Click Create. The OAuth client created screen appears, showing your
            new Client ID and Client secret.
        *   Click 'Download JSON' these credentials will be used by the utility
            and referred to below as 'Oauth-Client-ID-Credentials'

3.  A user with [super-admin](https://support.google.com/a/answer/2405986?hl=en)
    role assigned is required to run utility.

4.  `pip install -r requirements.txt` to install required libraries.

### How to run the utility

**Run the utility in dry-run/simulation mode, review the changes in the run-log
before running in wet-run mode by setting the flag --wet_run.**

**Note that the utility has no undo mechanism.**

**Utility run times may be very long ( hours ), please run as background
process**

To use the utility, you will need to provide the following:

*   `--oa_client_id_creds` The path to the
    [OAuth client ID credentials](#pre-req-client-id).
*   `--output_path` The path to the output directory. The run-log and OAuth
    tokens will be written to this directory.

*   `--help` For explanation of flags

The following arguments are also available:

*   `--dry_run`: Run the utility in the dry_run/read_only mode. Set
    --dry_run=false only **after** you validate the changes to be made in the
    run-log.
*   `--roles_to_force_gbra`: Role ID that should be converted to
    Group-based-role-assignments, regardless of the number of role assignments
    per role scope. In order to provide a list , re-use the flag multiple times.
    "--roles_to_force_gbra=123 --roles_to_force_gbra=456"
*   `--roles_to_skip_gbra`: Role ID that should NOT be converted to
    Group-based-role-assignments, regardless of the number of role assignments
    per role scope. In order to provide a list , re-use the flag multiple times.
    "--roles_to_skip_gbra=123 --roles_to_skip_gbra=456"
*   `--delete_dup_ras_to_sa`: Delete duplicate role assignments to super admins.
    Default = False.

Sample run command

`python run_me.py --oa_client_id_creds="/path/to/oa-client-id-creds.json"
--output_path="/path/to/output/dir" --dry_run=True`
