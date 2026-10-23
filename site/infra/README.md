# Website hosting (AWS)

This folder deploys `site/www` as a private S3 bucket behind CloudFront (with Origin Access Control). It can also set up a custom domain: an ACM certificate, the apex and `www` records in Route 53, and a redirect from `www` to the apex.

```bash
python3 site/www/_build/build.py                  # regenerate the pages from site/facts.json
cd site/infra && npm install
npx cdk deploy --profile <aws-profile>            # CloudFront URL only
npx cdk deploy --profile <aws-profile> -c domain=sparrowdecider.com -c zoneId=<Route 53 hosted zone id>
```

Before you run the custom-domain deploy, the domain's nameservers at the registrar must point to the Route 53 hosted zone. Otherwise the ACM certificate cannot validate. To redeploy content, run the same deploy command again; it uploads `site/www` and invalidates the CDN cache.
