import json
from dynamo_handler import fetch_unsolved_exercise


def handler(event, context):
    try:
        user_id = event["queryStringParameters"].get("user_id")
        topic = event["queryStringParameters"].get("topic")

        if not user_id or not topic:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "Missing required parameters: user_id or topic"}
                ),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        exercise = fetch_unsolved_exercise(user_id, topic)
        if not exercise:
            return {
                "statusCode": 404,
                "body": json.dumps(
                    {
                        "error": "No unsolved exercises found for this topic",
                        "user_id": user_id,
                        "topic": topic
                    }
                ),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        return {
            "statusCode": 200,
            "body": json.dumps({"exercise": str(exercise)}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    except Exception as e:
        print(f"Error fetching exercise: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "message": str(e)}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
