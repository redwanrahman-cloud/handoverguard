#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { HandoverGuardStack } from "../lib/handoverguard-stack";

const app = new cdk.App();

new HandoverGuardStack(app, "HandoverGuardStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? "us-east-1",
  },
  description: "AWS-native Strands and AgentCore hotel handover demonstration",
});
