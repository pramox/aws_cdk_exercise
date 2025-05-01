import json
from dynamo_handler import fetch_all_user_data


def handler(event, context):
    try:
        user_id = event["queryStringParameters"].get("user_id")
        print(user_id)

        if not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required parameters: user_id"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            }

        results = fetch_all_user_data(user_id)
        if not results:
            return {
                "statusCode": 404,
                "body": json.dumps(
                    {
                        "error": "No unsolved exercises found for this topic",
                        "user_id": user_id,
                    }
                ),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            }

        return {
            "statusCode": 200,
            "body": json.dumps({"results": str(results)}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        }

    except Exception as e:
        print(f"Error fetching user data: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        }
