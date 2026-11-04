"""
Cognito post-confirmation trigger (public Lambda, outside the VPC).

Creates the user's row through the private FairGradeDB Lambda and adds the
user to the Cognito 'Student' group. Instructors are promoted by hand.
"""
import json
import logging
import os

import boto3

REGION = "eu-north-1"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client("lambda", region_name=REGION)
cognito = boto3.client("cognito-idp", region_name=REGION)
DB_FUNCTION = os.environ.get("DB_FUNCTION_NAME", "FairGradeDB")


def lambda_handler(event, context):
    # Only act on a new sign-up, not on a password reset confirmation
    if event.get("triggerSource") != "PostConfirmation_ConfirmSignUp":
        return event

    attrs = event["request"]["userAttributes"]
    resp = lambda_client.invoke(
        FunctionName=DB_FUNCTION,
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "op": "create_user",
            "params": {"cognito_sub": attrs["sub"], "email": attrs.get("email")},
        }),
    )
    result = json.loads(resp["Payload"].read())
    if resp.get("FunctionError") or not result.get("ok"):
        logger.error("create_user failed: %s", result.get("code"))
        raise RuntimeError("Could not create the user record")

    cognito.admin_add_user_to_group(
        UserPoolId=event["userPoolId"],
        Username=event["userName"],
        GroupName="Student",
    )
    logger.info("Created users row and added to Student group")
    return event  # Cognito requires the event to be returned