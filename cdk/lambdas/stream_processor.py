import os
import boto3
import json

from dynamo_handler import unsolved_exercises_below_amount

dynamodb = boto3.resource("dynamodb")
sns_client = boto3.client("sns")
table_name = os.environ.get("DYNAMODB_TABLE_NAME", "UserExercisesTable")
table = dynamodb.Table(table_name)


def handler(event, context):
    results = []

    for record in event["Records"]:
        if record["eventName"] in ("MODIFY"):
            print(f"Processing record: {record['eventName']}")
            new_image = record["dynamodb"].get("NewImage", {})
            user_id: str = new_image.get("PK", {}).get("S")  # Extract user ID
            if user_id.startswith("USER#"):
                user_id = user_id.replace("USER#", "")

            exercise_type_below_5 = unsolved_exercises_below_amount(user_id, 5)
            if exercise_type_below_5 is None:
                print(f"User {user_id} has enough unsolved exercises.")
                results.append(f"User {user_id} has enough unsolved exercises.")
                continue

            # Determine the SNS topic ARN for the exercise type
            topic_arn = os.environ.get(
                f"{exercise_type_below_5.value.upper()}_TOPIC_ARN"
            )
            if not topic_arn:
                results.append(
                    f"Invalid exercise type: {exercise_type_below_5.value} for user {user_id}."
                )
                continue

            # Publish a message to the SNS topic to generate more exercises
            try:
                sns_client.publish(
                    TopicArn=topic_arn,
                    Message=json.dumps(
                        {
                            "user_id": user_id,
                            "message": "Generate new exercises",
                        }
                    ),
                )
                print(
                    f"User {user_id} has too few unsolved exercises of type {exercise_type_below_5.value}. Generating more..."
                )
                results.append(
                    f"User {user_id} has too few unsolved exercises of type {exercise_type_below_5.value}. Generating more..."
                )
            except Exception as e:
                print(f"Failed to publish message to SNS topic {topic_arn}: {str(e)}")
                results.append(
                    f"Failed to publish message to SNS topic {topic_arn}: {str(e)}"
                )
        else:
            # Log unsupported event types
            print(f"Unsupported event type: {record['eventName']}.")
            results.append(f"Unsupported event type: {record['eventName']}.")

    print(f"Results: {results}")
    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }
