import json
import os
import random
from dynamo_handler import store_exercise
from constants import ExerciseType


def handler(event, context):
    print("Received generation queue event:", json.dumps(event, indent=2))

    for record in event["Records"]:
        # Parse the SNS message from the SQS event
        body = json.loads(record["body"])
        message = json.loads(body["Message"])

        # Determine which topic this message came from
        topic_arn = body["TopicArn"]

        print(f"User ID: {message.get('user_id')}")
        print(f"Email: {message.get('email')}")

        # Load topic arns
        env_add_topic_arn = os.environ.get("ADDITION_TOPIC_ARN")
        env_mul_topic_arn = os.environ.get("MULTIPLICATION_TOPIC_ARN")
        env_der_topic_arn = os.environ.get("DERIVATIVES_TOPIC_ARN")

        # Validate topic arns
        if not all([env_add_topic_arn, env_mul_topic_arn, env_der_topic_arn]):
            raise ValueError(
                f"Missing topic ARNs: ADD:{env_add_topic_arn}, MUL:{env_mul_topic_arn}, DER:{env_der_topic_arn}"
            )

        print(f"Check if {topic_arn} in any of {env_add_topic_arn}, {env_mul_topic_arn}, {env_der_topic_arn}")
        # Generate exercise based on type
        if env_add_topic_arn in topic_arn:
            generate_addition_exercise(message)
        elif env_mul_topic_arn in topic_arn:
            generate_multiplication_exercise(message)
        elif env_der_topic_arn in topic_arn:
            generate_derivatives_exercise(message)
        else:
            raise ValueError(f"Unknown topic ARN: {topic_arn}")

    return {"statusCode": 200, "body": json.dumps("Exercises generated successfully")}


def generate_addition_exercise(message):
    print(f"Generating addition exercises for {message.get('email')}")
    tasks = 10 if message.get("is_initial") else 1
    for _ in range(tasks):
        question = str(random.randint(0, 99))
        for summands in range(random.randint(0, 4), -1, -1):
            question += "," + str(random.randint(0, 99))
        print(f"Generating addition exercise: {question}")
        store_exercise(message.get("user_id"), ExerciseType.ADDITION, question)


def generate_multiplication_exercise(message):
    print(f"Generating multiplication exercises for {message.get('email')}")
    tasks = 10 if message.get("is_initial") else 1
    for _ in range(tasks):
        question = str(random.randint(0, 99)) + "," + str(random.randint(0, 99))
        print(f"Generating multiplication exercise: {question}")
        store_exercise(message.get("user_id"), ExerciseType.MULTIPLICATION, question)


def generate_derivatives_exercise(message):
    print(f"Generating derivative exercises for {message.get('email')}")
    tasks = 10 if message.get("is_initial") else 1
    for _ in range(tasks):
        terms = []
        for degree in range(4, -1, -1):
            if random.randint(0, 4) != 0:
                coefficient = random.randint(1, 9)
                terms.append(f"{coefficient}:{degree}")

        question = "0" if not terms else ",".join(terms)
        print(f"Generating derivatives exercise: {question}")
        store_exercise(message.get("user_id"), ExerciseType.DERIVATIVE, question)
