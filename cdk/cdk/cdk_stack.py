from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cognito as cognito,
    aws_s3 as s3,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_lambda_event_sources as lambda_events,
)


class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.table = dynamodb.Table(
            self,
            "UserExercisesTable",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,  # Enable stream
            removal_policy=RemovalPolicy.DESTROY,  # Delete table on stack destruction
        )

        # Add the LSI for querying by IsSolved
        self.table.add_local_secondary_index(
            index_name="IsSolvedIndex",
            sort_key=dynamodb.Attribute(
                name="IsSolved",
                type=dynamodb.AttributeType.NUMBER,  # there is no BOOLEAN type
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        self.integration_responses = [
            {
                "statusCode": "200",
                "responseParameters": {
                    "method.response.header.Access-Control-Allow-Origin": "'*'",
                    "method.response.header.Access-Control-Allow-Headers": "'*'",
                    "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,GET,POST,PUT,DELETE'",
                },
            }
        ]

        self.options_integration = apigateway.MockIntegration(
            request_templates={"application/json": '{"statusCode":200}'},
            passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
            integration_responses=self.integration_responses,
        )

        self.method_responses = [
            apigateway.MethodResponse(
                status_code="200",
                response_parameters={
                    "method.response.header.Access-Control-Allow-Headers": True,
                    "method.response.header.Access-Control-Allow-Methods": True,
                    "method.response.header.Access-Control-Allow-Origin": True,
                },
            )
        ]

        self.topics, self.queues = self.create_message_infrastructure()

        self.create_cognito_stack(construct_id)

        self.create_api_gateway()

    def create_message_infrastructure(self):
        # Create queues for different purposes
        generation_queue = sqs.Queue(
            self,
            "exercise_generation_queue",
            visibility_timeout=Duration.seconds(300),
        )

        evaluation_queue = sqs.Queue(
            self,
            "exercise_evaluation_queue",
            visibility_timeout=Duration.seconds(300),
        )

        # Create topics for different exercise types
        topic_addition_gen = sns.Topic(self, "addition_topic_gen")
        topic_multiplication_gen = sns.Topic(self, "multiplication_topic_gen")
        topic_derivatives_gen = sns.Topic(self, "derivatives_topic_gen")
        topic_addition_eval = sns.Topic(self, "addition_topic_eval")
        topic_multiplication_eval = sns.Topic(self, "multiplication_topic_eval")
        topic_derivatives_eval = sns.Topic(self, "derivatives_topic_eval")

        # Subscribe topics to queues
        topic_addition_gen.add_subscription(subs.SqsSubscription(generation_queue))
        topic_multiplication_gen.add_subscription(subs.SqsSubscription(generation_queue))
        topic_derivatives_gen.add_subscription(subs.SqsSubscription(generation_queue))

        topic_addition_eval.add_subscription(subs.SqsSubscription(evaluation_queue))
        topic_multiplication_eval.add_subscription(subs.SqsSubscription(evaluation_queue))
        topic_derivatives_eval.add_subscription(subs.SqsSubscription(evaluation_queue))

        topics_gen = {
            "addition": topic_addition_gen,
            "multiplication": topic_multiplication_gen,
            "derivatives": topic_derivatives_gen
        }

        topics_eval = {
            "addition": topic_addition_eval,
            "multiplication": topic_multiplication_eval,
            "derivatives": topic_derivatives_eval
        }

        queues = {"generation": generation_queue, "evaluation": evaluation_queue}
        topics = {"generation": topics_gen, "evaluation": topics_eval}
        return topics, queues

    def create_cognito_stack(self, construct_id: str) -> None:
        # S3 Bucket for Profile Pictures
        self.profile_picture_bucket = s3.Bucket(
            self,
            "ProfilePictureBucket",
            bucket_name=f"{construct_id.lower()}-profile-pictures",
            removal_policy=RemovalPolicy.DESTROY,  # Automatically delete bucket on stack destruction
            auto_delete_objects=True,  # Automatically delete objects when bucket is removed
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.DELETE,
                    ],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                )
            ],
        )

        # IAM Role for Authenticated Users
        self.authenticated_role = iam.Role(
            self,
            "AuthenticatedUserRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
            ),
        )

        # S3 Permissions for Authenticated Users
        self.profile_picture_bucket.grant_read_write(self.authenticated_role)

        # Cognito User Pool
        user_pool = cognito.UserPool(
            self,
            "AppUserPool",
            user_pool_name=f"{construct_id}-user-pool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True, username=False),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                given_name=cognito.StandardAttribute(required=True, mutable=True),
                family_name=cognito.StandardAttribute(required=True, mutable=True),
                profile_picture=cognito.StandardAttribute(required=False,mutable=True)
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_digits=True,
                require_uppercase=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Cognito User Pool Client
        user_pool_client = user_pool.add_client(
            "AppUserPoolClient",
            auth_flows=cognito.AuthFlow(
                user_password=True, user_srp=True, admin_user_password=True, custom=True
            ),
            o_auth=cognito.OAuthSettings(
                callback_urls=["http://localhost:3000/callback"],
                logout_urls=["http://localhost:3000/logout"],
            ),
        )

        # Output resources
        self.user_pool = user_pool

        # Export User Pool ID and Client ID
        CfnOutput(
            self,
            "UserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID",
        )

        CfnOutput(
            self,
            "UserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID",
        )

        # Export S3 Bucket Name
        CfnOutput(
            self,
            "ProfilePictureBucketName",
            value=self.profile_picture_bucket.bucket_name,
            description="S3 Bucket for Profile Pictures",
        )

    def create_api_gateway(self):
        api = apigateway.RestApi(self, "RestAPI")

        self.create_cognito_endpoint(api)

        self.create_s3_endpoint(api)

        self.create_lambdas(api)

        CfnOutput(self, "APIGateway", value=api.url, description="Rest API Gateway ID")

    def create_cognito_endpoint(self, api: apigateway.RestApi):
        cognito_endpoint = api.root.add_resource("cognito")

        cognito_endpoint.add_method(
            "OPTIONS", self.options_integration, method_responses=self.method_responses
        )

        cognito_integration = apigateway.HttpIntegration(
            url=self.user_pool.user_pool_provider_url, http_method="ANY", proxy=True
        )

        # Add proxy method for non-OPTIONS requests
        cognito_endpoint.add_method(
            "ANY",
            cognito_integration,
            method_responses=self.method_responses,
        )

    def create_s3_endpoint(self, api: apigateway.RestApi):
        s3_endpoint = api.root.add_resource("profile-picture")
        s3_image_endpoint = s3_endpoint.add_resource("{file}")

        s3_put_integration = apigateway.AwsIntegration(
            service="s3",
            integration_http_method="PUT",
            path="{}/{{file}}".format(self.profile_picture_bucket.bucket_name),
            options=apigateway.IntegrationOptions(
                credentials_role=self.authenticated_role,
                request_parameters={
                    "integration.request.path.file": "method.request.path.file"
                },
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Content-Type": "integration.response.header.Content-Type",
                            "method.response.header.Access-Control-Allow-Origin": "'*'",
                            "method.response.header.Access-Control-Allow-Headers": "'*'",
                            "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,GET,POST,PUT,DELETE'",
                        }
                    )
                ]
            )
        )
        
        s3_get_integration = apigateway.AwsIntegration(
            service="s3",
            integration_http_method="GET",
            path="{}/{{file}}".format(self.profile_picture_bucket.bucket_name),
            options=apigateway.IntegrationOptions(
                credentials_role=self.authenticated_role,
                request_parameters={
                    "integration.request.path.file": "method.request.path.file"
                },
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Content-Type": "integration.response.header.Content-Type",
                            "method.response.header.Access-Control-Allow-Origin": "'*'",
                            "method.response.header.Access-Control-Allow-Headers": "'*'",
                            "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,GET,POST,PUT,DELETE'",
                        }
                    )
                ]
            )
        )

        s3_image_endpoint.add_method(
            "PUT",
            s3_put_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    }
                )
            ]
        )

        s3_image_endpoint.add_method(
            "GET",
            s3_get_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    }
                )
            ]
        )

        s3_endpoint.add_method(
            "OPTIONS", self.options_integration, method_responses=self.method_responses
        )

        s3_image_endpoint.add_method(
            "OPTIONS", self.options_integration, method_responses=self.method_responses
        )

    def create_lambdas(self, api: apigateway.RestApi):
        # Create the post-registration Lambda
        post_registration_lambda = _lambda.Function(
            self,
            "PostRegistrationLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="post_registration.handler",
            code=_lambda.Code.from_asset("./lambdas"),
            environment={
                "ADDITION_TOPIC_ARN": self.topics["generation"]["addition"].topic_arn,
                "MULTIPLICATION_TOPIC_ARN": self.topics["generation"]["multiplication"].topic_arn,
                "DERIVATIVES_TOPIC_ARN": self.topics["generation"]["derivatives"].topic_arn,
            },
        )
        self.user_pool.add_trigger(
            cognito.UserPoolOperation.POST_CONFIRMATION, post_registration_lambda
        )

        # Create consumer Lambda for generation queue
        generation_consumer = _lambda.Function(
            self,
            "GenerationConsumerLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="generation_consumer.handler",
            code=_lambda.Code.from_asset("./lambdas"),
            timeout=Duration.seconds(30),
            environment={
                "DYNAMODB_TABLE_NAME": self.table.table_name,
                "ADDITION_TOPIC_ARN": self.topics["generation"]["addition"].topic_arn,
                "MULTIPLICATION_TOPIC_ARN": self.topics["generation"]["multiplication"].topic_arn,
                "DERIVATIVES_TOPIC_ARN": self.topics["generation"]["derivatives"].topic_arn,
            },
        )

        # Create consumer Lambda for evaluation queue
        evaluation_consumer = _lambda.Function(
            self,
            "EvaluationConsumerLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="evaluation_consumer.handler",
            code=_lambda.Code.from_asset("./lambdas"),
            timeout=Duration.seconds(30),
            environment={
                "ADDITION_TOPIC_ARN": self.topics["evaluation"]["addition"].topic_arn,
                "MULTIPLICATION_TOPIC_ARN": self.topics["evaluation"]["multiplication"].topic_arn,
                "DERIVATIVES_TOPIC_ARN": self.topics["evaluation"]["derivatives"].topic_arn,
                "DYNAMODB_TABLE_NAME": self.table.table_name,
            },
        )

        # Create get-exercise Lambda
        get_exercise_lambda = _lambda.Function(
            self,
            "GetExerciseLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="get_exercise.handler",
            code=_lambda.Code.from_asset("./lambdas"),
            environment={
                "DYNAMODB_TABLE_NAME": self.table.table_name,
            },
        )

        # Create post-solution Lambda
        post_solution_lambda = _lambda.Function(
            self,
            "PostSolutionLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="post_solution.handler",
            code=_lambda.Code.from_asset("./lambdas"),
            environment={
                "DYNAMODB_TABLE_NAME": self.table.table_name,
                "EVALUATION_QUEUE_URL": self.queues["evaluation"].queue_url,
                "ADDITION_TOPIC_ARN": self.topics["evaluation"]["addition"].topic_arn,
                "MULTIPLICATION_TOPIC_ARN": self.topics["evaluation"]["multiplication"].topic_arn,
                "DERIVATIVES_TOPIC_ARN": self.topics["evaluation"]["derivatives"].topic_arn,
            },
        )

        # Create DynamoDB Stream Processor Lambda
        dynamo_stream_processor = _lambda.Function(
            self,
            "DynamoStreamProcessor",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="stream_processor.handler",
            code=_lambda.Code.from_asset("./lambdas"),
            timeout=Duration.seconds(30),
            environment={
                "DYNAMODB_TABLE_NAME": self.table.table_name,
                "ADDITION_TOPIC_ARN": self.topics["generation"]["addition"].topic_arn,
                "MULTIPLICATION_TOPIC_ARN": self.topics["generation"]["multiplication"].topic_arn,
                "DERIVATIVES_TOPIC_ARN": self.topics["generation"]["derivatives"].topic_arn,
            },
        )

        # Create Results Lambda
        results_lambda = _lambda.Function(
            self,
            "ResultsLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="results_handler.handler",
            code=_lambda.Code.from_asset("./lambdas"),
            environment={
                "DYNAMODB_TABLE_NAME": self.table.table_name,
            },
        )

        # Add a dependency to ensure the table is created before the Lambda is deployed
        dynamo_stream_processor.node.add_dependency(self.table)

        # Set up permissions and triggers
        self.queues["generation"].grant_consume_messages(generation_consumer)

        self.queues["evaluation"].grant_consume_messages(evaluation_consumer)
        self.queues["evaluation"].grant_send_messages(post_solution_lambda)

        self.table.grant_read_data(post_solution_lambda)
        self.table.grant_read_data(get_exercise_lambda)
        self.table.grant_read_data(dynamo_stream_processor)
        self.table.grant_read_data(results_lambda)

        self.table.grant_stream_read(dynamo_stream_processor)

        self.table.grant_read_write_data(generation_consumer)
        self.table.grant_read_write_data(evaluation_consumer)

        # Grant permissions to publish to SNS topics
        for key in self.topics.keys():
            for topic in self.topics[key].values():
                pass
                #topic.grant_publish(post_registration_lambda)
                #topic.grant_publish(post_solution_lambda)
                #topic.grant_publish(dynamo_stream_processor)
        self.topics["generation"]["addition"].grant_publish(post_registration_lambda)
        self.topics["generation"]["multiplication"].grant_publish(post_registration_lambda)
        self.topics["generation"]["derivatives"].grant_publish(post_registration_lambda)
        self.topics["evaluation"]["addition"].grant_publish(post_solution_lambda)
        self.topics["evaluation"]["multiplication"].grant_publish(post_solution_lambda)
        self.topics["evaluation"]["derivatives"].grant_publish(post_solution_lambda)

        # Add SQS as event source for generation consumer
        generation_consumer.add_event_source(
            lambda_events.SqsEventSource(self.queues["generation"], batch_size=1)
        )

        # Add SQS as event source for evaluation consumer
        evaluation_consumer.add_event_source(
            lambda_events.SqsEventSource(self.queues["evaluation"], batch_size=1)
        )

        # Attach the DynamoDB stream to the Lambda
        dynamo_stream_processor.add_event_source(
            lambda_events.DynamoEventSource(
                self.table,
                starting_position=_lambda.StartingPosition.LATEST,  # Process only new changes
                batch_size=100,  # Adjust as needed
            )
        )

        # Set up API endpoints
        exercise_endpoint = api.root.add_resource("exercise")
        exercise_endpoint.add_method(
            "OPTIONS", self.options_integration, method_responses=self.method_responses
        )
        get_exercise_integration = apigateway.LambdaIntegration(
            get_exercise_lambda, integration_responses=self.integration_responses
        )
        exercise_endpoint.add_method(
            "GET", get_exercise_integration, method_responses=self.method_responses
        )
        
        post_solution_integration = apigateway.LambdaIntegration(
            post_solution_lambda, integration_responses=self.integration_responses
        )
        exercise_endpoint.add_method(
            "POST", post_solution_integration, method_responses=self.method_responses
        )

        results_endpoint = api.root.add_resource("results")
        results_endpoint.add_method(
            "OPTIONS", self.options_integration, method_responses=self.method_responses
        )
        results_integration = apigateway.LambdaIntegration(
            results_lambda, integration_responses=self.integration_responses
        )
        results_endpoint.add_method(
            "GET", results_integration, method_responses=self.method_responses
        )
