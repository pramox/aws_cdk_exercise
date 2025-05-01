import os
import json
import math
from typing import Optional

from constants import ExerciseType
from dynamo_handler import update_user_answer_in_exercise, fetch_exercise


def handler(event, context):
    print("Received evaluation queue event:", json.dumps(event, indent=2))

    for record in event["Records"]:
        # Parse the SNS message from the SQS event
        body = json.loads(record["body"])
        message = json.loads(body["Message"])

        # Load topic arns
        topic_arn = body["TopicArn"]
        env_add_topic_arn = os.environ.get("ADDITION_TOPIC_ARN")
        env_mul_topic_arn = os.environ.get("MULTIPLICATION_TOPIC_ARN")
        env_der_topic_arn = os.environ.get("DERIVATIVES_TOPIC_ARN")

        # Validate topic arns
        if not all([env_add_topic_arn, env_mul_topic_arn, env_der_topic_arn]):
            raise ValueError(
                f"Missing topic ARNs: ADD:{env_add_topic_arn}, MUL:{env_mul_topic_arn}, DER:{env_der_topic_arn}"
            )

        # For evaluation queue, we currently only handle addition exercises
        try:
            print(f"Check if topic ARN is in any of the known topic ARNs")
            print(f"Topic ARN: {topic_arn}")
            print(f"Known topic ARNs: {env_add_topic_arn}, {env_mul_topic_arn}, {env_der_topic_arn}")

            user_id = message.get("user_id")
            exercise_id = message.get("exercise_id")
            hash_position = user_id.find("#")
            if hash_position != -1:
                user_id = user_id[hash_position + 1:]
            hash_position = exercise_id.find("#")
            if hash_position != -1:
                exercise_id = exercise_id[hash_position + 1:]

            if env_add_topic_arn in topic_arn:
                evaluate_addition_exercise(message, user_id, exercise_id)
            elif env_mul_topic_arn in topic_arn:
                evaluate_multiplication_exercise(message, user_id, exercise_id)
            elif env_der_topic_arn in topic_arn:
                evaluate_derivatives_exercise(message, user_id, exercise_id)
            else:
                print(f"Unknown topic ARN: {topic_arn}")
                raise ValueError(f"Unknown topic ARN: {topic_arn}")
        except Exception as e:
            print(f"Error evaluating exercise: {e}")

    return {"statusCode": 200, "body": json.dumps("Evaluation processed successfully")}


def evaluate_addition_exercise(message, user_id, exercise_id):
    exercise: dict = get_exercise(message)
    print(exercise)
    #validate_type(exercise, ExerciseType.ADDITION)

    question = exercise.get("Question").split(",")
    question_parsed = [int(q) for q in question]
    expected_result = math.fsum(question_parsed)
    user_answer = int(message.get("user_answer"))
    is_correct = expected_result == user_answer

    update_user_answer_in_exercise(
        user_id,
        exercise_id,
        message.get("user_answer"),
        is_correct,
    )


def evaluate_multiplication_exercise(message, user_id, exercise_id):
    exercise: dict = get_exercise(message)
    #validate_type(exercise, ExerciseType.MULTIPLICATION)

    question = exercise.get("Question").split(",")
    question_parsed = [int(q) for q in question]
    expected_result = math.prod(question_parsed)
    user_answer = int(message.get("user_answer"))
    is_correct = expected_result == user_answer
    update_user_answer_in_exercise(
        user_id,
        exercise_id,
        message.get("user_answer"),
        is_correct,
    )


def are_polynomials_equal(expected_result: str, user_answer: str) -> bool:
    if expected_result == "0" or user_answer == "0":
        return expected_result == user_answer

    def to_dict(poly_str):
        return {
            int(deg): int(coef)
            for coef, deg in (term.split(":") for term in poly_str.split(","))
        }

    expected_dict = to_dict(expected_result)
    user_dict = to_dict(user_answer)
    return expected_dict == user_dict


def evaluate_derivatives_exercise(message, user_id, exercise_id):
    exercise: dict = get_exercise(message)
    #validate_type(exercise, ExerciseType.DERIVATIVE)

    question = exercise.get("Question")
    expected_result = derivative(question)
    user_answer = message.get("user_answer")
    is_correct = are_polynomials_equal(expected_result, user_answer)
    update_user_answer_in_exercise(
        user_id,
        exercise_id,
        message.get("user_answer"),
        is_correct,
    )


def get_exercise(message) -> Optional[dict]:
    user_id = message.get("user_id")
    exercise_id = message.get("exercise_id")
    hash_position = user_id.find("#")
    if hash_position != -1:
        user_id = user_id[hash_position + 1:]
    hash_position = exercise_id.find("#")
    if hash_position != -1:
        exercise_id = exercise_id[hash_position + 1:]

    try:
        return fetch_exercise(user_id, exercise_id)
    except Exception as e:
        print(f"Error fetching exercise: {e}")
        print(f"User ID: {user_id}, Exercise ID: {exercise_id}")
        return {}


def validate_type(exercise, expected_type: ExerciseType):
    if not exercise:
        raise ValueError("Exercise not found")

    type = exercise.get("ExerciseType")
    if str(type).upper() != expected_type.value.upper():
        raise ValueError(f"Expected {expected_type}, got {type}")


def derivative(poly_str):
    if poly_str == "0":
        return "0"

    terms = []
    for term in poly_str.split(","):
        coeff, degree = map(int, term.split(":"))
        if degree > 0:  # constants vanish
            new_coeff = coeff * degree
            new_degree = degree - 1
            terms.append(f"{new_coeff}:{new_degree}")

    return "0" if not terms else ",".join(terms)
