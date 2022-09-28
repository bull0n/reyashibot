from aws_cdk import (
    Stack,
    Duration,
    aws_dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as api_gw,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct

class ReyashibotStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambdaSearchLayer = _lambda.LayerVersion(self, 'SearchLayer',
            code = _lambda.AssetCode('./lambda/tea_glossary_search/layer'),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_8],
        )   

        tea_glossary_search = _lambda.Function(
            self, "TeaGlossarySearch",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset("./lambda/tea_glossary_search/handler"),
            handler="tea_glossary_search.handler",
            layers=[lambdaSearchLayer],
            environment={
                "discord_public_key": "discord_app_id",
            },
        )
        
        api = api_gw.LambdaRestApi(
            self, 
            'TeaGlossarySearchApi',
            handler=tea_glossary_search,
            proxy=False
        )

        items = api.root.add_resource("items")
        items.add_method("ANY")

        lambdaSearchLayer = _lambda.LayerVersion(self, 'InsertLayer',
            code = _lambda.AssetCode('./lambda/tea_glossary_insert/layer'),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_8],
        ) 

        tea_glossary_insert = _lambda.Function(
            self, "TeaGlossaryInsert",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset("./lambda/tea_glossary_insert/handler"),
            handler="tea_glossary_insert.handler",
            layers=[lambdaSearchLayer],
            environment={
                "google_spreadsheet_api_key": "speradsheet_api_key",
                "spreadsheet_id": "spreadsheet_id",
            },
        )
        
        glossary_table = aws_dynamodb.Table(
            self, "GlossaryTable",
            partition_key=aws_dynamodb.Attribute(
                name="word",
                type=aws_dynamodb.AttributeType.STRING
            )
        )

        glossary_table.grant_read_write_data(tea_glossary_insert)
        glossary_table.grant_read_data(tea_glossary_search)

        rule_tea_glossary_insert = events.Rule(
            self, 'TeaGlossaryInsertRule',
            description='Insert glossary entries in database',
            schedule=events.Schedule.rate(Duration.hours(1))
        )
        
        rule_tea_glossary_insert.add_target(targets.LambdaFunction(tea_glossary_insert))
