#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { SiteStack } from "../lib/site-stack";

// cdk deploy                                   -> CloudFront URL only
// cdk deploy -c domain=sparrowdecider.com -c zoneId=Z...   -> plus apex + www with HTTPS
const app = new cdk.App();
new SiteStack(app, "SparrowDeciderSite", {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: "us-east-1" }, // CloudFront certs live in us-east-1
  domainName: app.node.tryGetContext("domain"),
  hostedZoneId: app.node.tryGetContext("zoneId"),
  description: "Sparrow Decider website (S3 + CloudFront)",
});
