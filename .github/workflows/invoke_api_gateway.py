import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import json

def get_credentials():
    """Get credentials from EC2 instance profile"""
    session = boto3.Session()
    credentials = session.get_credentials()
    return credentials

def sign_request(method, url, region, service='execute-api'):
    """Sign the request with SigV4"""
    credentials = get_credentials()
    
    request = AWSRequest(
        method=method,
        url=url,
        data=''
    )

    SigV4Auth(credentials, service, region).add_auth(request)
    return dict(request.headers)

def invoke_api(api_endpoint, region):
    """Invoke API Gateway endpoint through VPC endpoint"""
    try:
        # Get signed headers
        headers = sign_request('GET', api_endpoint, region)
        
        # Make the request
        response = requests.get(
            api_endpoint,
            headers=headers,
            verify=True  # Enable SSL verification
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        return {
            'statusCode': response.status_code,
            'body': response.text,
            'headers': dict(response.headers)
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        return {
            'statusCode': 500,
            'body': str(e)
        }

def main():
    # Hardcoded configuration
    API_ENDPOINT = "https://vpce-xxxxx.execute-api.us-east-1.vpce.amazonaws.com/prod/your-endpoint"
    REGION = "us-gov-west-1"  # Replace with your region
    
    # Invoke API and get response
    result = invoke_api(API_ENDPOINT, REGION)
    
    # Print results
    print("Response Status Code:", result['statusCode'])
    print("Response Headers:", json.dumps(result.get('headers', {}), indent=2))
    print("Response Body:", result.get('body'))

if __name__ == "__main__":
    main()
