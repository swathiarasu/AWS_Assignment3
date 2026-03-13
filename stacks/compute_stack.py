from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    CfnOutput,
)
from constructs import Construct

class ComputeStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        table: dynamodb.ITable,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        layer_arn = self.node.try_get_context("matplotlib_layer_arn")
        matplotlib_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "MatplotlibLayer",
            layer_arn,
        )

        self.bucket = s3.Bucket(
            self,
            "TestBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.size_tracking_fn = _lambda.Function(
            self,
            "SizeTrackingLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="size_tracking_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda/size_tracking"),
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": table.table_name,
            },
        )

        #matplotlib_layer = _lambda.LayerVersion.from_layer_version_arn(self, "MatplotlibLayer","MATPLOTLIB_LAYER_ARN")
        
        self.plotting_fn = _lambda.Function(
            self,
            "PlottingLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="plotting_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda/plotting"),
            layers=[matplotlib_layer],
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                "TABLE_NAME": table.table_name,
                "BUCKET_NAME": self.bucket.bucket_name,
                "PLOT_KEY": "plot.png",
                "LOOKBACK_SECONDS": "10",
                "GSI_MAX_NAME": "gsi_max_size",
            },
        )

        self.driver_fn = _lambda.Function(
            self,
            "DriverLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="driver_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda/driver"),
            timeout=Duration.seconds(60),
            environment={
                "BUCKET_NAME": self.bucket.bucket_name,
                "PLOTTING_FUNCTION_NAME": self.plotting_fn.function_name,
                "SLEEP_SECONDS": "2",
            },
        )

        self.bucket.grant_read(self.size_tracking_fn)
        self.bucket.grant_put(self.plotting_fn)
        self.bucket.grant_read_write(self.driver_fn)

        table.grant_write_data(self.size_tracking_fn)
        table.grant_read_data(self.plotting_fn)

        self.plotting_fn.grant_invoke(self.driver_fn)

        notification_destination = s3n.LambdaDestination(self.size_tracking_fn)
        self.bucket.add_event_notification(s3.EventType.OBJECT_CREATED, notification_destination)
        self.bucket.add_event_notification(s3.EventType.OBJECT_REMOVED, notification_destination)

        CfnOutput(self, "BucketName", value=self.bucket.bucket_name)
        CfnOutput(self, "SizeTrackingFunctionName", value=self.size_tracking_fn.function_name)
        CfnOutput(self, "PlottingFunctionName", value=self.plotting_fn.function_name)
        CfnOutput(self, "DriverFunctionName", value=self.driver_fn.function_name)