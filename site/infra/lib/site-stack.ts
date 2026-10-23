import * as cdk from "aws-cdk-lib";
import * as acm from "aws-cdk-lib/aws-certificatemanager";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as route53 from "aws-cdk-lib/aws-route53";
import * as targets from "aws-cdk-lib/aws-route53-targets";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import { Construct } from "constructs";
import * as path from "path";

export interface SiteStackProps extends cdk.StackProps {
  /** e.g. "sparrowdecider.com"; leave undefined to serve on the CloudFront domain only. */
  domainName?: string;
  /** Route 53 hosted zone ID for domainName (required with domainName). */
  hostedZoneId?: string;
}

/** Static website: private S3 bucket + CloudFront (OAC), optional apex + www domain with ACM. */
export class SiteStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: SiteStackProps) {
    super(scope, id, props);

    const bucket = new s3.Bucket(this, "SiteBucket", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    let zone: route53.IHostedZone | undefined;
    let certificate: acm.ICertificate | undefined;
    const names: string[] = [];
    if (props.domainName && props.hostedZoneId) {
      zone = route53.HostedZone.fromHostedZoneAttributes(this, "Zone", {
        hostedZoneId: props.hostedZoneId,
        zoneName: props.domainName,
      });
      names.push(props.domainName, `www.${props.domainName}`);
      certificate = new acm.Certificate(this, "Cert", {
        domainName: props.domainName,
        subjectAlternativeNames: [`www.${props.domainName}`],
        validation: acm.CertificateValidation.fromDns(zone),
      });
    }

    // Folder URLs (/models/ -> /models/index.html) and www -> apex redirect.
    const rewrite = new cloudfront.Function(this, "Rewrite", {
      runtime: cloudfront.FunctionRuntime.JS_2_0,
      code: cloudfront.FunctionCode.fromInline(`
function handler(event) {
  var req = event.request;
  var host = req.headers.host ? req.headers.host.value : "";
  ${props.domainName ? `if (host === "www.${props.domainName}") {
    return { statusCode: 301, statusDescription: "Moved Permanently",
             headers: { location: { value: "https://${props.domainName}" + req.uri } } };
  }` : ""}
  if (req.uri.endsWith("/")) { req.uri += "index.html"; }
  else if (!req.uri.split("/").pop().includes(".")) { req.uri += "/index.html"; }
  return req;
}`),
    });

    const headers = new cloudfront.ResponseHeadersPolicy(this, "Headers", {
      securityHeadersBehavior: {
        contentTypeOptions: { override: true },
        frameOptions: { frameOption: cloudfront.HeadersFrameOption.DENY, override: true },
        referrerPolicy: { referrerPolicy: cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN, override: true },
        strictTransportSecurity: { accessControlMaxAge: cdk.Duration.days(365), includeSubdomains: true, override: true },
      },
    });

    const dist = new cloudfront.Distribution(this, "Cdn", {
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(bucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        responseHeadersPolicy: headers,
        compress: true,
        functionAssociations: [{ function: rewrite, eventType: cloudfront.FunctionEventType.VIEWER_REQUEST }],
      },
      defaultRootObject: "index.html",
      domainNames: names.length ? names : undefined,
      certificate,
      errorResponses: [
        { httpStatus: 403, responseHttpStatus: 404, responsePagePath: "/404.html", ttl: cdk.Duration.minutes(5) },
        { httpStatus: 404, responseHttpStatus: 404, responsePagePath: "/404.html", ttl: cdk.Duration.minutes(5) },
      ],
      priceClass: cloudfront.PriceClass.PRICE_CLASS_ALL,
      minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
    });

    new s3deploy.BucketDeployment(this, "Deploy", {
      sources: [s3deploy.Source.asset(path.join(__dirname, "..", "..", "www"), { exclude: ["_shots", "_shots/*", "_build", "_build/*"] })],
      destinationBucket: bucket,
      distribution: dist,
      distributionPaths: ["/*"],
      memoryLimit: 512,
    });

    if (zone && props.domainName) {
      for (const [rid, name] of [["Apex", props.domainName], ["Www", `www.${props.domainName}`]]) {
        new route53.ARecord(this, `${rid}A`, { zone, recordName: name, target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(dist)) });
        new route53.AaaaRecord(this, `${rid}AAAA`, { zone, recordName: name, target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(dist)) });
      }
    }

    new cdk.CfnOutput(this, "CloudFrontUrl", { value: `https://${dist.distributionDomainName}` });
    new cdk.CfnOutput(this, "DistributionId", { value: dist.distributionId });
    if (props.domainName) new cdk.CfnOutput(this, "SiteUrl", { value: `https://${props.domainName}` });
  }
}
