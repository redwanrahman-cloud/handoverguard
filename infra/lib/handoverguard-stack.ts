import * as path from "path";
import * as cdk from "aws-cdk-lib";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import * as integrations from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as agentcore from "aws-cdk-lib/aws-bedrockagentcore";
import * as bedrock from "aws-cdk-lib/aws-bedrock";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as sources from "aws-cdk-lib/aws-lambda-event-sources";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import * as sns from "aws-cdk-lib/aws-sns";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as tasks from "aws-cdk-lib/aws-stepfunctions-tasks";
import { Construct } from "constructs";

export class HandoverGuardStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const lambdaCode = lambda.Code.fromAsset(path.join(__dirname, "../cloud/lambda"));
    const commonEnvironment: Record<string, string> = {};

    const dataBucket = new s3.Bucket(this, "OperationsData", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      eventBridgeEnabled: true,
      versioned: true,
      lifecycleRules: [{ expiration: cdk.Duration.days(30) }],
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    const operationsTable = new dynamodb.Table(this, "OperationsState", {
      partitionKey: { name: "PK", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "SK", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    commonEnvironment.TABLE_NAME = operationsTable.tableName;
    commonEnvironment.DATA_BUCKET = dataBucket.bucketName;

    const approvalTopic = new sns.Topic(this, "ApprovalNotifications", {
      displayName: "HandoverGuard human approvals",
    });
    commonEnvironment.APPROVAL_TOPIC_ARN = approvalTopic.topicArn;

    const deadLetterQueue = new sqs.Queue(this, "AgentDeadLetterQueue", {
      encryption: sqs.QueueEncryption.SQS_MANAGED,
      retentionPeriod: cdk.Duration.days(14),
    });
    const agentQueue = new sqs.Queue(this, "AgentQueue", {
      encryption: sqs.QueueEncryption.SQS_MANAGED,
      visibilityTimeout: cdk.Duration.minutes(6),
      deadLetterQueue: { queue: deadLetterQueue, maxReceiveCount: 3 },
    });

    const approvalWait = new lambda.Function(this, "ApprovalWaitFunction", {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: "approval_wait.handler",
      code: lambdaCode,
      timeout: cdk.Duration.seconds(20),
      environment: commonEnvironment,
      tracing: lambda.Tracing.ACTIVE,
    });
    operationsTable.grantReadWriteData(approvalWait);
    approvalTopic.grantPublish(approvalWait);

    const waitForHuman = new tasks.LambdaInvoke(this, "WaitForHumanDecision", {
      lambdaFunction: approvalWait,
      integrationPattern: sfn.IntegrationPattern.WAIT_FOR_TASK_TOKEN,
      payload: sfn.TaskInput.fromObject({
        "run_id.$": "$.run_id",
        "issue_id.$": "$.issue_id",
        "reason.$": "$.reason",
        "task_token": sfn.JsonPath.taskToken,
      }),
    });
    const approvalWorkflow = new sfn.StateMachine(this, "HumanApprovalWorkflow", {
      definitionBody: sfn.DefinitionBody.fromChainable(
        waitForHuman.next(new sfn.Succeed(this, "DecisionRecorded")),
      ),
      stateMachineType: sfn.StateMachineType.STANDARD,
      timeout: cdk.Duration.hours(24),
      tracingEnabled: true,
    });
    commonEnvironment.APPROVAL_WORKFLOW_ARN = approvalWorkflow.stateMachineArn;

    const toolFunction = new lambda.Function(this, "OperationsToolFunction", {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: "operations_tools.handler",
      code: lambdaCode,
      timeout: cdk.Duration.seconds(30),
      environment: commonEnvironment,
      tracing: lambda.Tracing.ACTIVE,
    });
    operationsTable.grantReadWriteData(toolFunction);
    dataBucket.grantReadWrite(toolFunction);
    approvalWorkflow.grantStartExecution(toolFunction);

    const gatewayRole = new iam.Role(this, "AgentCoreGatewayRole", {
      assumedBy: new iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
    });
    toolFunction.grantInvoke(gatewayRole);
    const gateway = new agentcore.CfnGateway(this, "OperationsGateway", {
      name: "handoverguard-operations",
      description: "Governed MCP tools for hotel task, approval, trace, and evidence work",
      authorizerType: "NONE",
      protocolType: "MCP",
      roleArn: gatewayRole.roleArn,
    });

    const stringProperty = (description: string): agentcore.CfnGatewayTarget.SchemaDefinitionProperty => ({
      type: "string",
      description,
    });
    const integerProperty = (description: string): agentcore.CfnGatewayTarget.SchemaDefinitionProperty => ({
      type: "integer",
      description,
    });
    const booleanProperty = (description: string): agentcore.CfnGatewayTarget.SchemaDefinitionProperty => ({
      type: "boolean",
      description,
    });
    const tool = (
      name: string,
      description: string,
      properties: Record<string, agentcore.CfnGatewayTarget.SchemaDefinitionProperty>,
      required: string[],
    ): agentcore.CfnGatewayTarget.ToolDefinitionProperty => ({
      name,
      description,
      inputSchema: { type: "object", properties, required },
    });
    const gatewayTarget = new agentcore.CfnGatewayTarget(this, "OperationsGatewayTarget", {
      gatewayIdentifier: gateway.attrGatewayIdentifier,
      name: "hotel-operations",
      description: "Narrow policy-bound hotel operations tools",
      credentialProviderConfigurations: [{ credentialProviderType: "GATEWAY_IAM_ROLE" }],
      targetConfiguration: {
        mcp: {
          lambda: {
            lambdaArn: toolFunction.functionArn,
            toolSchema: {
              inlinePayload: [
                tool("record_trace", "Record a judge-visible AWS execution step", {
                  run_id: stringProperty("Run identifier"),
                  service: stringProperty("AWS service name"),
                  step: stringProperty("Completed operation"),
                  evidence: stringProperty("Short evidence summary"),
                }, ["run_id", "service", "step", "evidence"]),
                tool("route_issue", "Route one extracted issue through deterministic hotel policy", {
                  run_id: stringProperty("Run identifier"),
                  issue_id: stringProperty("Issue identifier"),
                  department: stringProperty("Owning department"),
                  title: stringProperty("Concise operational task title"),
                  category: stringProperty("maintenance, safety, guest_request, billing, or communication"),
                  priority: stringProperty("low, medium, high, or critical"),
                  action: stringProperty("Proposed operational action"),
                  financial_impact_sar: integerProperty("Estimated financial impact in SAR; zero if none"),
                  safety_sensitive: booleanProperty("Whether the issue can affect human safety"),
                }, [
                  "run_id", "issue_id", "department", "title", "category", "priority",
                  "action", "financial_impact_sar", "safety_sensitive",
                ]),
                tool("write_evidence", "Write the final evidence packet to S3", {
                  run_id: stringProperty("Run identifier"),
                  summary: stringProperty("Final verified execution summary"),
                }, ["run_id", "summary"]),
              ],
            },
          },
        },
      },
    });
    gatewayTarget.addResourceDependency(gateway);

    const guardrail = new bedrock.CfnGuardrail(this, "OperationsGuardrail", {
      name: "handoverguard-operations",
      description: "Masks guest identifiers before hotel handovers reach the model",
      blockedInputMessaging: "The handover contains content blocked by hotel safety policy.",
      blockedOutputsMessaging: "The generated output was blocked by hotel safety policy.",
      sensitiveInformationPolicyConfig: {
        piiEntitiesConfig: ["NAME", "EMAIL", "PHONE"].map((type) => ({
          type,
          action: "ANONYMIZE",
          inputAction: "ANONYMIZE",
          outputAction: "ANONYMIZE",
          inputEnabled: true,
          outputEnabled: true,
        })),
      },
    });
    const guardrailVersion = new bedrock.CfnGuardrailVersion(this, "OperationsGuardrailVersion", {
      guardrailIdentifier: guardrail.attrGuardrailId,
      description: "Competition demonstration guardrail",
    });

    const runtimeRole = new iam.Role(this, "AgentCoreRuntimeRole", {
      assumedBy: new iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
    });
    dataBucket.grantReadWrite(runtimeRole);
    operationsTable.grantReadWriteData(runtimeRole);
    runtimeRole.addToPolicy(new iam.PolicyStatement({
      actions: ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      resources: [
        "arn:aws:bedrock:*::foundation-model/*",
        `arn:aws:bedrock:*:${cdk.Aws.ACCOUNT_ID}:inference-profile/*`,
      ],
    }));
    runtimeRole.addToPolicy(new iam.PolicyStatement({
      actions: ["bedrock:ApplyGuardrail"],
      resources: [guardrail.attrGuardrailArn],
    }));
    runtimeRole.addToPolicy(new iam.PolicyStatement({
      actions: ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      resources: ["arn:aws:logs:*:*:*"],
    }));

    const deployAgentCore = new cdk.CfnParameter(this, "DeployAgentCore", {
      type: "String",
      default: "false",
      allowedValues: ["true", "false"],
      description: "Create AgentCore Runtime after agent/runtime.zip has been uploaded",
    });
    const agentArtifactKey = new cdk.CfnParameter(this, "AgentArtifactKey", {
      type: "String",
      default: "agent/runtime.zip",
    });
    const deployRuntimeCondition = new cdk.CfnCondition(this, "DeployAgentCoreCondition", {
      expression: cdk.Fn.conditionEquals(deployAgentCore.valueAsString, "true"),
    });
    const runtime = new agentcore.CfnRuntime(this, "AgentRuntime", {
      agentRuntimeName: "HandoverGuardRuntime",
      description: "Strands supervisor for multilingual hotel handovers",
      roleArn: runtimeRole.roleArn,
      protocolConfiguration: "HTTP",
      networkConfiguration: { networkMode: "PUBLIC" },
      lifecycleConfiguration: { idleRuntimeSessionTimeout: 900, maxLifetime: 28800 },
      agentRuntimeArtifact: {
        codeConfiguration: {
          code: { s3: { bucket: dataBucket.bucketName, prefix: agentArtifactKey.valueAsString } },
          entryPoint: ["main.py"],
          runtime: "PYTHON_3_13",
        },
      },
      environmentVariables: {
        ...commonEnvironment,
        GATEWAY_URL: gateway.attrGatewayUrl,
        GUARDRAIL_ID: guardrail.attrGuardrailId,
        GUARDRAIL_VERSION: guardrailVersion.attrVersion,
        MODEL_ID: "us.amazon.nova-lite-v1:0",
      },
      tags: { Project: "HandoverGuard", Competition: "AgentsForHumans" },
    });
    runtime.cfnOptions.condition = deployRuntimeCondition;
    const endpoint = new agentcore.CfnRuntimeEndpoint(this, "AgentRuntimeEndpoint", {
      agentRuntimeId: runtime.attrAgentRuntimeId,
      agentRuntimeVersion: runtime.attrAgentRuntimeVersion,
      name: "production",
      description: "Judge-facing HandoverGuard runtime endpoint",
    });
    endpoint.cfnOptions.condition = deployRuntimeCondition;

    const dispatcher = new lambda.Function(this, "AgentDispatcherFunction", {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: "dispatcher.handler",
      code: lambdaCode,
      timeout: cdk.Duration.minutes(5),
      environment: {
        ...commonEnvironment,
        AGENT_RUNTIME_ARN: cdk.Fn.conditionIf(
          deployRuntimeCondition.logicalId,
          runtime.attrAgentRuntimeArn,
          "",
        ).toString(),
      },
      tracing: lambda.Tracing.ACTIVE,
    });
    dispatcher.addEventSource(new sources.SqsEventSource(agentQueue, { batchSize: 1 }));
    operationsTable.grantReadWriteData(dispatcher);
    dataBucket.grantRead(dispatcher);
    dispatcher.addToRolePolicy(new iam.PolicyStatement({
      actions: ["bedrock-agentcore:InvokeAgentRuntime"],
      resources: ["*"],
    }));

    const rawUploadRule = new events.Rule(this, "RawHandoverUploaded", {
      description: "Route raw hotel handovers from S3 to the agent queue",
      eventPattern: {
        source: ["aws.s3"],
        detailType: ["Object Created"],
        detail: { bucket: { name: [dataBucket.bucketName] }, object: { key: [{ prefix: "raw/" }] } },
      },
    });
    rawUploadRule.addTarget(new targets.SqsQueue(agentQueue));

    const apiFunction = new lambda.Function(this, "PublicApiFunction", {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: "public_api.handler",
      code: lambdaCode,
      timeout: cdk.Duration.seconds(30),
      environment: commonEnvironment,
      tracing: lambda.Tracing.ACTIVE,
    });
    operationsTable.grantReadWriteData(apiFunction);
    dataBucket.grantPut(apiFunction, "raw/*");
    approvalWorkflow.grantTaskResponse(apiFunction);

    const api = new apigwv2.HttpApi(this, "JudgeApi", {
      apiName: "handoverguard-judge-api",
      description: "Public synthetic-data API for the HandoverGuard judge demo",
      corsPreflight: {
        allowOrigins: ["*"],
        allowHeaders: ["content-type"],
        allowMethods: [apigwv2.CorsHttpMethod.GET, apigwv2.CorsHttpMethod.POST],
      },
    });
    const apiIntegration = new integrations.HttpLambdaIntegration("JudgeApiIntegration", apiFunction);
    api.addRoutes({ path: "/runs", methods: [apigwv2.HttpMethod.POST], integration: apiIntegration });
    api.addRoutes({ path: "/runs/{run_id}", methods: [apigwv2.HttpMethod.GET], integration: apiIntegration });
    api.addRoutes({ path: "/runs/{run_id}/trace", methods: [apigwv2.HttpMethod.GET], integration: apiIntegration });
    api.addRoutes({ path: "/approvals/{approval_id}", methods: [apigwv2.HttpMethod.POST], integration: apiIntegration });
    const publicStage = api.defaultStage?.node.defaultChild as apigwv2.CfnStage | undefined;
    if (publicStage) {
      publicStage.defaultRouteSettings = {
        throttlingBurstLimit: 5,
        throttlingRateLimit: 2,
      };
    }

    const judgeSiteBucket = new s3.Bucket(this, "JudgeSite", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      autoDeleteObjects: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    const judgeDistribution = new cloudfront.Distribution(this, "JudgeDistribution", {
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(judgeSiteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
      },
      defaultRootObject: "index.html",
      errorResponses: [
        { httpStatus: 403, responseHttpStatus: 200, responsePagePath: "/index.html" },
        { httpStatus: 404, responseHttpStatus: 200, responsePagePath: "/index.html" },
      ],
      comment: "Public synthetic-only HandoverGuard judge demonstration",
    });
    new s3deploy.BucketDeployment(this, "JudgeSiteDeployment", {
      destinationBucket: judgeSiteBucket,
      distribution: judgeDistribution,
      distributionPaths: ["/*"],
      sources: [
        s3deploy.Source.asset(path.join(__dirname, "../cloud/web")),
        s3deploy.Source.data("config.json", JSON.stringify({ apiUrl: api.apiEndpoint })),
      ],
    });

    const dashboard = new cloudwatch.Dashboard(this, "CloudOperationsDashboard", {
      dashboardName: "HandoverGuard-Agent-Operations",
    });
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "Judge API and agent dispatch",
        left: [apiFunction.metricInvocations(), dispatcher.metricInvocations()],
        right: [apiFunction.metricErrors(), dispatcher.metricErrors()],
      }),
      new cloudwatch.GraphWidget({
        title: "Agent queue depth and dead letters",
        left: [agentQueue.metricApproximateNumberOfMessagesVisible()],
        right: [deadLetterQueue.metricApproximateNumberOfMessagesVisible()],
      }),
    );

    new cdk.CfnOutput(this, "JudgeApiUrl", { value: api.apiEndpoint });
    new cdk.CfnOutput(this, "JudgeDemoUrl", {
      value: `https://${judgeDistribution.distributionDomainName}`,
    });
    new cdk.CfnOutput(this, "DataBucketName", { value: dataBucket.bucketName });
    new cdk.CfnOutput(this, "OperationsTableName", { value: operationsTable.tableName });
    new cdk.CfnOutput(this, "GatewayUrl", { value: gateway.attrGatewayUrl });
    new cdk.CfnOutput(this, "GuardrailId", { value: guardrail.attrGuardrailId });
    new cdk.CfnOutput(this, "ApprovalWorkflowArn", { value: approvalWorkflow.stateMachineArn });
  }
}
