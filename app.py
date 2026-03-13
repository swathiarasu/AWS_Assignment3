#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.data_stack import DataStack
from stacks.compute_stack import ComputeStack
from stacks.api_stack import ApiStack

app = cdk.App()

data_stack = DataStack(app, "DataStack")

compute_stack = ComputeStack(
    app,
    "ComputeStack",
    table=data_stack.table,
)

api_stack = ApiStack(
    app,
    "ApiStack",
    plotting_fn=compute_stack.plotting_fn,
)

compute_stack.add_dependency(data_stack)
api_stack.add_dependency(compute_stack)

app.synth()