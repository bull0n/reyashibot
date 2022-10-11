import os
from aws_cdk import (
    Stack,
    Duration,
    aws_dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as api_gw,
    aws_events as events,
    aws_events_targets as targets,
)
from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep
from constructs import Construct

OWNER_REPO = os.environ['OWNER_REPO']

class ReyashibotStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # pipeline = CodePipeline(self, "Pipeline", 
        #     pipeline_name="TeaGlossaryPipeline",
        #         docker_enabled_for_synth=True,
        #         synth=ShellStep("Synth", 
        #         input=CodePipelineSource.git_hub(OWNER_REPO, 'main'),
        #         commands=[
        #             'npm install -g aws-cdk', 
        #             'python -m pip install -r requirements.txt', 
        #             'docker run -v lambda/tea_glossary_insert/layer:/var/task "public.ecr.aws/sam/build-python3.8" /bin/sh -c "pip install -r requirements.txt -t python/lib/python3.8/site-packages/; exit"',
        #             'docker run -v lambda/tea_glossary_search/layer:/var/task "public.ecr.aws/sam/build-python3.8" /bin/sh -c "pip install -r requirements.txt -t python/lib/python3.8/site-packages/; exit"',
        #             'cdk synth',
        #         ]
        #     )
        # )

        lambdaSearchLayer = _lambda.LayerVersion(self, 'SearchLayer',
            code = _lambda.AssetCode('./lambda/tea_glossary_search/layer'),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_8],
        )   

        tea_glossary_search = _lambda.Function(
            self, 'TeaGlossarySearch',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset('./lambda/tea_glossary_search/handler'),
            handler='tea_glossary_search.lambda_handler',
            layers=[lambdaSearchLayer],
            environment={
                'discord_public_key':  os.environ['DISCORD_PUBLIC_KEY'],
            },
        )
        
        api = api_gw.LambdaRestApi(
            self, 
            'TeaGlossarySearchApi',
            handler=tea_glossary_search,
            proxy=False
        )

        items = api.root.add_resource('definitions')
        items.add_method('ANY')

        lambdaInsertLayer = _lambda.LayerVersion(self, 'InsertLayer',
            code = _lambda.AssetCode('./lambda/tea_glossary_insert/layer'),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_8],
        ) 

        tea_glossary_insert = _lambda.Function(
            self, 'TeaGlossaryInsert',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset('./lambda/tea_glossary_insert/handler'),
            handler='tea_glossary_insert.lambda_handler',
            layers=[lambdaInsertLayer],
            environment={
                'google_spreadsheet_api_key': os.environ['GOOGLE_SPREADSHEET_API_KEY'],
                'spreadsheet_id': os.environ['SPREADSHEET_ID'],
            },
            timeout=Duration.minutes(1),
        )
        
        glossary_table = aws_dynamodb.Table(
            self, 'GlossaryTable',
            partition_key=aws_dynamodb.Attribute(
                name='word',
                type=aws_dynamodb.AttributeType.STRING
            )
        )

        tea_glossary_insert.add_environment("TABLE_NAME", glossary_table.table_name)
        tea_glossary_search.add_environment("TABLE_NAME", glossary_table.table_name)

        glossary_table.grant_read_write_data(tea_glossary_insert)
        glossary_table.grant_read_data(tea_glossary_search)

        rule_tea_glossary_insert = events.Rule(
            self, 'TeaGlossaryInsertRule',
            description='Insert glossary entries in database',
            schedule=events.Schedule.rate(Duration.hours(1))
        )
        
        rule_tea_glossary_insert.add_target(targets.LambdaFunction(tea_glossary_insert))
