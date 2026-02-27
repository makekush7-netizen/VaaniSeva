# VaaniSeva Deploy Script
# Packages Lambda, deploys to AWS, creates API Gateway, updates Twilio webhook
# Run: python scripts/deploy.py

import subprocess
import boto3
import json
import os
import zipfile
import shutil
from dotenv import load_dotenv

load_dotenv()

AWS_REGION      = os.environ["AWS_REGION"]
ACCOUNT_ID      = boto3.client("sts", region_name=AWS_REGION).get_caller_identity()["Account"]
LAMBDA_ROLE     = f"arn:aws:iam::{ACCOUNT_ID}:role/vaaniseva-lambda-role"
LAMBDA_NAME     = "vaaniseva-call-handler"
API_NAME        = "vaaniseva-api"

lambda_client = boto3.client("lambda", region_name=AWS_REGION)
apigw_client  = boto3.client("apigateway", region_name=AWS_REGION)
iam_client    = boto3.client("iam", region_name=AWS_REGION)


def run(cmd):
    print(f"  > {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
    return result.stdout.strip()


def create_lambda_role():
    """Create IAM role for Lambda if it doesn't exist."""
    print("Creating Lambda IAM role...")
    trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    try:
        role = iam_client.create_role(
            RoleName="vaaniseva-lambda-role",
            AssumeRolePolicyDocument=json.dumps(trust),
            Description="VaaniSeva Lambda execution role"
        )
        arn = role["Role"]["Arn"]
        # Attach policies
        for policy in [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
            "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
            "arn:aws:iam::aws:policy/AmazonPollyFullAccess",
            "arn:aws:iam::aws:policy/AmazonTranscribeFullAccess",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess",
        ]:
            iam_client.attach_role_policy(RoleName="vaaniseva-lambda-role", PolicyArn=policy)
        print(f"  ✓ Role created: {arn}")
        print("  Waiting 15s for role to propagate...")
        import time; time.sleep(15)
        return arn
    except iam_client.exceptions.EntityAlreadyExistsException:
        arn = iam_client.get_role(RoleName="vaaniseva-lambda-role")["Role"]["Arn"]
        print(f"  ✓ Role already exists: {arn}")
        return arn


def package_lambda():
    """Zip Lambda code + dependencies."""
    print("Packaging Lambda...")
    pkg_dir = "build/lambda_package"
    shutil.rmtree("build", ignore_errors=True)
    os.makedirs(pkg_dir, exist_ok=True)

    # Install deps into package directory
    run(f"pip install twilio boto3 requests -t {pkg_dir} -q")

    # Copy handler
    shutil.copy("lambdas/call_handler/handler.py", f"{pkg_dir}/handler.py")

    # Zip it
    zip_path = "build/call_handler.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(pkg_dir):
            for file in files:
                filepath = os.path.join(root, file)
                arcname  = os.path.relpath(filepath, pkg_dir)
                zf.write(filepath, arcname)

    print(f"  ✓ Packaged: {zip_path}")
    return zip_path


def deploy_lambda(zip_path, role_arn):
    """Create or update the Lambda function."""
    print("Deploying Lambda...")
    env_vars = {
        "AWS_REGION": AWS_REGION,
        "DYNAMODB_CALLS_TABLE":     os.environ["DYNAMODB_CALLS_TABLE"],
        "DYNAMODB_KNOWLEDGE_TABLE": os.environ["DYNAMODB_KNOWLEDGE_TABLE"],
        "DYNAMODB_VECTORS_TABLE":   os.environ["DYNAMODB_VECTORS_TABLE"],
        "S3_DOCUMENTS_BUCKET":      os.environ["S3_DOCUMENTS_BUCKET"],
        "BEDROCK_MODEL_ID":         os.environ["BEDROCK_MODEL_ID"],
        "BEDROCK_EMBEDDING_MODEL_ID": os.environ["BEDROCK_EMBEDDING_MODEL_ID"],
        "TWILIO_ACCOUNT_SID":       os.environ["TWILIO_ACCOUNT_SID"],
        "TWILIO_AUTH_TOKEN":        os.environ["TWILIO_AUTH_TOKEN"],
        "BHASHINI_USER_ID":         os.environ.get("BHASHINI_USER_ID", ""),
        "BHASHINI_API_KEY":         os.environ.get("BHASHINI_API_KEY", ""),
        "LOG_LEVEL":                "INFO",
    }

    with open(zip_path, "rb") as f:
        zip_bytes = f.read()

    try:
        fn = lambda_client.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime="python3.11",
            Role=role_arn,
            Handler="handler.lambda_handler",
            Code={"ZipFile": zip_bytes},
            Timeout=30,
            MemorySize=512,
            Environment={"Variables": env_vars}
        )
        arn = fn["FunctionArn"]
        print(f"  ✓ Lambda created: {arn}")
    except lambda_client.exceptions.ResourceConflictException:
        lambda_client.update_function_code(FunctionName=LAMBDA_NAME, ZipFile=zip_bytes)
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_NAME,
            Environment={"Variables": env_vars},
            Timeout=30,
            MemorySize=512
        )
        arn = lambda_client.get_function(FunctionName=LAMBDA_NAME)["Configuration"]["FunctionArn"]
        print(f"  ✓ Lambda updated: {arn}")

    return arn


def create_api_gateway(lambda_arn):
    """Create REST API Gateway with /voice routes."""
    print("Creating API Gateway...")

    # Check if it exists
    apis = apigw_client.get_rest_apis()["items"]
    existing = next((a for a in apis if a["name"] == API_NAME), None)
    if existing:
        api_id = existing["id"]
        print(f"  ✓ API already exists: {api_id}")
    else:
        api = apigw_client.create_rest_api(name=API_NAME, description="VaaniSeva Voice API")
        api_id = api["id"]
        print(f"  ✓ API created: {api_id}")

    # Get root resource
    resources = apigw_client.get_resources(restApiId=api_id)["items"]
    root_id   = next(r["id"] for r in resources if r["path"] == "/")

    def get_or_create_resource(parent_id, path_part):
        existing_res = next((r for r in resources if r.get("pathPart") == path_part
                             and r.get("parentId") == parent_id), None)
        if existing_res:
            return existing_res["id"]
        res = apigw_client.create_resource(restApiId=api_id, parentId=parent_id, pathPart=path_part)
        resources.append(res)
        return res["id"]

    def add_post_method(resource_id, path):
        try:
            apigw_client.put_method(
                restApiId=api_id, resourceId=resource_id,
                httpMethod="POST", authorizationType="NONE"
            )
        except apigw_client.exceptions.ConflictException:
            pass
        apigw_client.put_integration(
            restApiId=api_id, resourceId=resource_id, httpMethod="POST",
            type="AWS_PROXY",
            integrationHttpMethod="POST",
            uri=f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        )
        print(f"    ✓ POST {path}")

    # Create /voice → /voice/incoming, /voice/language, /voice/gather
    voice_id    = get_or_create_resource(root_id, "voice")
    incoming_id = get_or_create_resource(voice_id, "incoming")
    language_id = get_or_create_resource(voice_id, "language")
    gather_id   = get_or_create_resource(voice_id, "gather")

    add_post_method(incoming_id, "/voice/incoming")
    add_post_method(language_id, "/voice/language")
    add_post_method(gather_id,   "/voice/gather")

    # Grant API Gateway permission to invoke Lambda
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId="apigateway-invoke",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{AWS_REGION}:{ACCOUNT_ID}:{api_id}/*/*"
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass

    # Deploy
    apigw_client.create_deployment(restApiId=api_id, stageName="prod")
    base_url = f"https://{api_id}.execute-api.{AWS_REGION}.amazonaws.com/prod"
    print(f"  ✓ Deployed API: {base_url}")
    return base_url


def update_twilio_webhook(base_url):
    """Update Twilio phone number webhook to point to our API."""
    from twilio.rest import Client
    client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])

    numbers = client.incoming_phone_numbers.list()
    target  = os.environ["TWILIO_PHONE_NUMBER"]
    number  = next((n for n in numbers if n.phone_number == target), None)

    if number:
        number.update(voice_url=f"{base_url}/voice/incoming", voice_method="POST")
        print(f"  ✓ Twilio webhook updated: {base_url}/voice/incoming")
    else:
        print(f"  ! Could not find Twilio number {target}. Update webhook manually to: {base_url}/voice/incoming")


def main():
    print("=" * 50)
    print("VaaniSeva Deployment")
    print("=" * 50)

    role_arn   = create_lambda_role()
    zip_path   = package_lambda()
    lambda_arn = deploy_lambda(zip_path, role_arn)
    base_url   = create_api_gateway(lambda_arn)
    update_twilio_webhook(base_url)

    print("\n" + "=" * 50)
    print("DEPLOYMENT COMPLETE")
    print(f"API Base URL : {base_url}")
    print(f"Twilio calls : {os.environ['TWILIO_PHONE_NUMBER']}")
    print(f"\nNext: Run seed script:")
    print(f"  python scripts/seed_knowledge.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
