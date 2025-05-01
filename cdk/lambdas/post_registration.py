import json
import boto3
import os


def handler(event, context):
    print("Received Cognito event:", json.dumps(event, indent=2))
    # Initialize SNS client
    sns = boto3.client("sns")

    try:
        # Extract relevant information from the Cognito event
        user_sub = event["request"]["userAttributes"]["sub"]
        email = event["request"]["userAttributes"]["email"]

        # Prepare message content
        message = {"user_id": user_sub, "email": email, "is_initial": True}

        # Publish to all exercise topics
        topics = [
            os.environ["ADDITION_TOPIC_ARN"],
            os.environ["MULTIPLICATION_TOPIC_ARN"],
            os.environ["DERIVATIVES_TOPIC_ARN"],
        ]

        for topic_arn in topics:
            response = sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(message),
                MessageAttributes={
                    "event_type": {
                        "DataType": "String",
                        "StringValue": "user_registration",
                    }
                },
            )
            print(f"Message published to {topic_arn}")
            print(f"MessageId: {response['MessageId']}")
            print(f"Message content: {json.dumps(message, indent=2)}")

        return event

    except Exception as e:
        print(f"Error publishing to SNS: {str(e)}")
        # Don't block user registration if SNS publish fails
        return event
