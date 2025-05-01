import json
import os
import re
from decimal import Decimal
from typing import Optional
import uuid
import boto3
from boto3.dynamodb.conditions import Attr, Key
from datetime import datetime, timezone
from constants import ExerciseType
from collections import Counter

dynamodb = boto3.resource("dynamodb")
table_name = os.environ.get("DYNAMODB_TABLE_NAME", "UserExercisesTable")
table = dynamodb.Table(table_name)

print(f"Using DynamoDB table: {table_name}")

try:
    table = dynamodb.Table(table_name)
    print(f"Table description: {table}")
except Exception as e:
    print(f"Error accessing table: {str(e)}")


def valid_uuid(uuid_str: str) -> bool:
    return (
        re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            uuid_str,
        )
        is not None
    )


def valid_user_id(user_id: str) -> bool:
    return (
        re.match(
            r"^USER#[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            user_id,
        )
        is not None
    )


def valid_exercise_id(exercise_id: str) -> bool:
    return (
        re.match(
            r"^EXERCISE#[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            exercise_id,
        )
        is not None
    )


def store_exercise(
    user_id: str,
    exercise_type: ExerciseType,
    question: str,
) -> None:
    if not valid_uuid(user_id):
        raise ValueError(f"Invalid user ID: {user_id}")

    pk = f"USER#{user_id}"

    # Generate a unique exercise_id
    while True:
        exercise_id = uuid.uuid4().hex
        sk = f"EXERCISE#{exercise_id}"

        response = table.get_item(Key={"PK": pk, "SK": sk})
        if "Item" not in response:
            break  # SK is unique

    # Use UTC timezone for consistent timestamps
    # in creation and update
    created_at = datetime.now(timezone.utc).isoformat()

    table.put_item(
        Item={
            "PK": pk,
            "SK": sk,
            "ExerciseType": exercise_type.value.upper(),
            "Question": question,
            "CreatedAt": created_at,
            "IsSolved": int(False),  # int, because it is used as LSI
        },
        ReturnValues="NONE",
    )


def update_user_answer_in_exercise(
    user_id: str,
    exercise_id: str,
    user_answer: str,
    is_correct: bool,
) -> dict:
    if not valid_uuid(user_id):
        raise ValueError(f"Invalid user ID: {user_id}")

    pk = f"USER#{user_id}"
    sk = f"EXERCISE#{exercise_id}"

    # Use UTC timezone for consistent timestamps
    # in creation and update
    solved_at = datetime.now(timezone.utc).isoformat()

    try:
        print("trying to update user answer")
        print(f"PK: {pk}, SK: {sk}, UserAnswer: {user_answer}, SolvedAt: {solved_at}, IsCorrect: {is_correct}")
        response = table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression="SET UserAnswer = :ua, SolvedAt = :sa, IsCorrect = :ic, IsSolved = :is",
            ExpressionAttributeValues={
                ":ua": user_answer,
                ":sa": solved_at,
                ":ic": is_correct,
                ":is": int(True),  # int, because it is used as LSI
            },
        )
        print(response)
    except Exception as e:
        # DynamoDB.Client.exceptions.ResourceInUseException
        # DynamoDB.Client.exceptions.ResourceNotFoundException
        # DynamoDB.Client.exceptions.LimitExceededException
        # DynamoDB.Client.exceptions.InternalServerError
        print(f"Error updating user answer in exercise: {e}")
        raise e

    return response


def fetch_exercise(user_id: str, exercise_id: str) -> dict:

    #if not valid_uuid(user_id):
        #raise ValueError(f"Invalid user ID: {user_id}")
    #if not valid_uuid(exercise_id):
        #raise ValueError(f"Invalid exercise ID: {exercise_id}")

    pk = f"USER#{user_id}"
    sk = f"EXERCISE#{exercise_id}"

    print(f"Fetching exercise with PK(userid): {pk} and SK(ex id): {sk}")
    print("Table", table)
    response = table.get_item(Key={"PK": pk, "SK": sk})
    #response = table.query(KeyConditionExpression=Key("PK").eq(pk) & Key("SK").eq(sk))
    #response = table.query(KeyConditionExpression=Key("PK").eq(pk))
    return response.get("Item")


def unsolved_exercises_below_amount(
    user_id: str, amount: Optional[int] = 5
) -> Optional[ExerciseType]:
    if not valid_uuid(user_id):
        raise ValueError(f"Invalid user ID: {user_id}")

    pk = f"USER#{user_id}"

    # Query the table using the LSI and filter by ExerciseType
    response = table.query(
        IndexName="IsSolvedIndex",  # Name of the LSI
        KeyConditionExpression=Key("PK").eq(pk) & Key("IsSolved").eq(0),
        ConsistentRead=True,
    )

    exercise_counts = Counter(item["ExerciseType"] for item in response["Items"])

    # Find the first exercise type below the specified amount
    for exercise_type in ExerciseType:
        if exercise_counts.get(exercise_type.value.upper(), 0) < amount:
            return exercise_type

    return None


def fetch_unsolved_exercise(user_id: str, exercise_type: str):
    if not valid_uuid(user_id):
        raise ValueError(f"Invalid user ID: {user_id}")

    pk = f"USER#{user_id}"

    try:
        response = table.query(
            IndexName="IsSolvedIndex",
            KeyConditionExpression=Key("PK").eq(pk) & Key("IsSolved").eq(0),
            FilterExpression=Attr("ExerciseType").eq(exercise_type),
            ConsistentRead=True,
        )
        items = response.get("Items", [])
        if not items or len(items) == 0:
            print(f"No unsolved exercises found. Debug response: {response}")
            print(f"Table data: {table.scan()}")
            return None
        return json.dumps(decimal_to_float(items[0]))
    except Exception as e:
        print(f"Error fetching unsolved exercise: {e}")


def fetch_all_user_data(user_id: str):
    if not valid_uuid(user_id):
        raise ValueError(f"Invalid user ID: {user_id}")

    pk = f"USER#{user_id}"

    try:
        # Perform a query to fetch all data for the user using their partition key (PK)
        response = table.query(KeyConditionExpression=Key("PK").eq(pk))
        print(response)

        items = response.get("Items", [])
        return items

    except Exception as e:
        print(f"Error fetching all user data: {e}")
        return None

def decimal_to_float(obj):
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(x) for x in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj