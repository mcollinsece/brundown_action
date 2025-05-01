import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import json

def get_credentials():
    """Get credentials from EC2 instance profile"""
    session = boto3.Session(region_name='us-gov-west-1')  # Explicitly set GovCloud region
    credentials = session.get_credentials()
    if not credentials:
        raise Exception("No credentials found")
    return credentials

def sign_request(method, url, region, service='execute-api'):
    """Sign the request with SigV4"""
    credentials = get_credentials()
    
    # Create headers with host
    host = url.replace('https://', '').split('/')[0]
    headers = {
        'host': host,
        'x-amz-date': None,  # Will be set by SigV4Auth
        'x-amz-security-token': credentials.token if credentials.token else None
    }
    
    request = AWSRequest(
        method=method,
        url=url,
        headers=headers,
        data=''
    )

    SigV4Auth(credentials, service, region).add_auth(request)
    return dict(request.headers)

def invoke_api(api_endpoint, region):
    """Invoke API Gateway endpoint through VPC endpoint"""
    try:
        # Get signed headers
        headers = sign_request('GET', api_endpoint, region)
        
        print("Debug - Request Headers:", json.dumps(headers, indent=2))
        
        # Make the request
        response = requests.get(
            api_endpoint,
            headers=headers,
            verify=True
        )
        
        # Print detailed debug information
        print(f"Debug - Response Status: {response.status_code}")
        print(f"Debug - Response Headers: {dict(response.headers)}")
        print(f"Debug - Response Body: {response.text}")
        
        # Check if request was successful
        response.raise_for_status()
        
        return {
            'statusCode': response.status_code,
            'body': response.text,
            'headers': dict(response.headers)
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Error response body: {e.response.text}")
            print(f"Error response headers: {dict(e.response.headers)}")
        return {
            'statusCode': getattr(e.response, 'status_code', 500),
            'body': str(e)
        }

def main():
    # Hardcoded configuration
    API_ENDPOINT = "https://vpce-xxxxx.execute-api.us-gov-west-1.vpce.amazonaws.com/prod/your-endpoint"  # Update with GovCloud endpoint
    REGION = "us-gov-west-1"
    
    try:
        # Print debug info
        print(f"Using API Endpoint: {API_ENDPOINT}")
        print(f"Using Region: {REGION}")
        
        # Invoke API and get response
        result = invoke_api(API_ENDPOINT, REGION)
        
        # Print results
        print("Response Status Code:", result['statusCode'])
        print("Response Headers:", json.dumps(result.get('headers', {}), indent=2))
        print("Response Body:", result.get('body'))
        
    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()
