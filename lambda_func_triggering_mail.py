import os
import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError


def send_email(sender, recipient, url):
    SENDER = sender  # must be verified in AWS SES Email
    RECIPIENT = recipient  # must be verified in AWS SES Email

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"

    # The subject line for the email.
    SUBJECT = "Billing Memo"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Hello\r\n"
                 "This email contains the billing memo"
                 )

    # The HTML body of the email.
    BODY_HTML = f"""<html>
    <head></head>
    <body>
    <h1>Hey </h1>
    <p>You can download this file from this url</p>
    <p>{url}</p>
    </body>
    </html>
                """

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {

                        'Data': BODY_HTML
                    },
                    'Text': {

                        'Data': BODY_TEXT
                    },
                },
                'Subject': {

                    'Data': SUBJECT
                },
            },
            Source=SENDER
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
        return e.response['Error']['Message']
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
        return response['MessageId']


def lambda_handler(event, context):
    url = event['url']
    sender = event['sender']
    recipient_lst = event['recipient']
    successfull_mail_lst = []
    if len(recipient_lst) > 0:
        for i in recipient_lst:
            mail = send_email(sender, i, url)
            successfull_mail_lst.append(mail)

    return {"success": successfull_mail_lst}