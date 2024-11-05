import os
from aws_cdk import (
    Stack,
    Duration,
    aws_dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as api_gw,
    aws_events as events,
    aws_events_targets as targets,
    aws_codedeploy as deploy,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_ssm as ssm,
)
from constructs import Construct

class ReyashibotStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        discord_public_key_param = ssm.StringParameter(self, 'DiscordPublicKey', 
            parameter_name='/reyashibot/discord/DiscordPublicKey', 
            string_value=os.environ['DISCORD_PUBLIC_KEY'], 
            tier=ssm.ParameterTier.STANDARD
        )

        lambda_search_layer = _lambda.LayerVersion(self, 'SearchLayer',
            code = _lambda.AssetCode('./lambda/tea_glossary_search/layer'),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_12],
        )

        tea_glossary_search = _lambda.Function(
            self, 'TeaGlossarySearch',
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset('./lambda/tea_glossary_search/handler'),
            handler='tea_glossary_search.lambda_handler',
            layers=[lambda_search_layer],
        )

        discord_public_key_param.grant_read(tea_glossary_search)

        tea_glossary_search_alias = _lambda.Alias(self, 'TeaGlossarySearchAlias', alias_name='live', version=tea_glossary_search.current_version)
        
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
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_12],
        )

        spreadsheet_api_key_param = ssm.StringParameter(self, 'GoogleSpreadsheetApiKey', 
            parameter_name='/reyashibot/spreadhseet/GoogleSpreasheetApiKey', 
            string_value=os.environ['GOOGLE_SPREADSHEET_API_KEY'], 
            tier=ssm.ParameterTier.STANDARD
        )

        spreadsheet_id_param = ssm.StringParameter(self, 'SpreadsheetId', 
            parameter_name='/reyashibot/spreadhseet/SpreadsheetId', 
            string_value=os.environ['SPREADSHEET_ID'], 
            tier=ssm.ParameterTier.STANDARD
        )

        tea_glossary_insert = _lambda.Function(
            self, 'TeaGlossaryInsert',
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset('./lambda/tea_glossary_insert/handler'),
            handler='tea_glossary_insert.lambda_handler',
            layers=[lambdaInsertLayer],
            timeout=Duration.minutes(1),
        )

        spreadsheet_api_key_param.grant_read(tea_glossary_insert)
        spreadsheet_id_param.grant_read(tea_glossary_insert)
        
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

        tea_glossary_search_alarm = cloudwatch.Alarm(
            self, 
            'LambdaTeaGlossarySearchFailure', 
            alarm_description='Lambda search alarm for deployment',
            metric=tea_glossary_search_alias.metric_errors(period=Duration.minutes(2)),
            threshold=1,
            evaluation_periods=1,
        )

        # tea_glossary_search_alarm.add_alarm_action(cloudwatch_actions.Actions.SnsAction(topic));

        tea_glossary_search_deploy_post_hook = _lambda.Function(
            self, 'TeaGlossarySearchDeployPostHook',
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset('./tests/lambda/tea_glossary_search_validate'),
            handler='tea_glossary_search_validate.lambda_handler',
            environment={
                "LAMBDA_NAME": tea_glossary_search.function_name,
            }
        )

        tea_glossary_search.grant_invoke(tea_glossary_search_deploy_post_hook)
    
        deployment_group = deploy.LambdaDeploymentGroup(
            self,
            'TeaGlossarySearchDeploymentGroup',
            alias=tea_glossary_search_alias,
            deployment_config=deploy.LambdaDeploymentConfig.ALL_AT_ONCE,
            alarms=[tea_glossary_search_alarm],
            post_hook=tea_glossary_search_deploy_post_hook,
        )

        tea_glossary_search_deploy_post_hook.grant_invoke(deployment_group)
