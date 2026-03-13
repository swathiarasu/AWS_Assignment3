from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    CfnOutput,
)
from constructs import Construct


class ApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        plotting_fn: _lambda.IFunction,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api = apigw.RestApi(
            self,
            "PlottingApi",
            rest_api_name="PlottingApi",
            description="REST API that triggers the plotting lambda",
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        api.root.add_method("GET", apigw.LambdaIntegration(plotting_fn, proxy=True))

        CfnOutput(self, "PlottingApiUrl", value=api.url)
