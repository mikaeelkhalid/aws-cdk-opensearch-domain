from aws_cdk import (
    aws_iam as iam,
    aws_sns_subscriptions as subs,
    core,
    aws_iot as iot,
    aws_opensearchservice as opensearch
)


class OpensearchStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # 1 create a openserch domain
        prod_domain = opensearch.Domain(self, "CdkDomainOpenSearch",
            version=opensearch.EngineVersion.OPENSEARCH_1_0,
            enforce_https=True,
            node_to_node_encryption=True,
            use_unsigned_basic_auth=True,
            capacity=opensearch.CapacityConfig(
                data_nodes=2,
                data_node_instance_type="t3.small.search"
            ),
            ebs=opensearch.EbsOptions(
                volume_size=10
            ),
            zone_awareness=opensearch.ZoneAwarenessConfig(
                availability_zone_count=2,
                enabled=False,
            ),
            encryption_at_rest=opensearch.EncryptionAtRestOptions(
                enabled=True
            ),
            fine_grained_access_control=opensearch.AdvancedSecurityOptions(
                master_user_name="master user name",
            )
        )

        # 2 create an IAM role to have permission to dump data into openserch
        cdk_role = iam.Role(self, "CdkRoleOpenSearch",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"))
        cdk_role.add_to_policy(iam.PolicyStatement(
            actions=["es:ESHttpPut"],
            resources=[prod_domain.domain_arn + "/*"]
        ))
        
        # 3 defines an IoT Rule to send data to opensearch
        cfn_topic_rule = iot.CfnTopicRule(self, "CdkTopicRuleOpenSearch",
         topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SQL statement to IoT topic",
                actions=[iot.CfnTopicRule.ActionProperty(
                open_search=iot.CfnTopicRule.OpenSearchActionProperty(
                endpoint="https://"+prod_domain.domain_endpoint,
                id="id",
                index="index",
                role_arn=cdk_role.role_arn,
                type="_doc"
             ),
            )]
         ))