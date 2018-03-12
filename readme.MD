# Reaver 

The [DeleteRestApi](https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html#api-gateway-limits) rate limit in API Gateway is [rate limited](https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html#api-gateway-limits) at 2 requests per minute per region. This simple tool can be used to clean up your account.

## Getting Started

Clone this repository to get started. 

### Prerequisites

* [Boto3](https://github.com/boto/boto3)
* [AWS CLI](https://aws.amazon.com/cli) (optional)
 * Installing the AWS CLI is optional, but it makes configuring permissions simple

### Quick Start

This tool can use AWS CLI Credentials for permission. Install the AWS CLI and type ` aws configure ` to configure your key pair and your default region. 

Altenatively, you can manually set up credentials (in e.g. ``~/.aws/credentials``):



    [default]
    aws_access_key_id = YOUR_KEY
    aws_secret_access_key = YOUR_SECRET

Then, set up a default region (in e.g. ``~/.aws/config``):



    [default]
    region=us-east-1

The tool takes a file containing the names of APIs you'd like to delete as input: 

    api_to_delete_01
    api_to_delete_02
    api_to_delete_03
    api_to_delete_04

Run the tool:

    python3 reaver.py apis_to_delete





