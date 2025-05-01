import os
import json
import boto3

def handler(event, context):
    sns = boto3.client("sns")

    try:
        body = json.loads(event["body"])
        user_id = "USER#" + body.get("user_id")
        exercise_id = body.get("exercise_id")
        topic = body.get("topic")
        user_answer = body.get("user_answer")

        print(f"{body}")

        if not all([user_id, exercise_id, topic, user_answer]):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required parameters"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                }
            }

        # Determine evaluation topic ARN
        topic_arn = os.environ.get(
            f"{topic.upper()}_TOPIC_ARN"
        )

        print(f"{topic_arn}")

        if not topic_arn:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid topic"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                }
            }

        # Publish message to the evaluation queue via SNS
        print(f"Publishing message to. Topic arn: {topic_arn}, user_id: {user_id}, exercise_id: {exercise_id}, user_answer: {user_answer}")
        sns.publish(
            TopicArn=topic_arn,
            Message=json.dumps({
                'user_id': user_id,
                'exercise_id': exercise_id,
                'user_answer': user_answer
            }),
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Solution posted successfully"}),
            "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
            }
        }

    except Exception as e:
        print(f"Error posting solution to SNS: {e}")
        return event