import json
import boto3
import requests

REPO = "REPO_NAME"  # Replace with your GitHub repository name
OWNER = "REPO_OWNER_NAME"  # Replace with your GitHub repository owner name/organization name
PARAMETER_NAME = "PARAMETER_NAME"  # Replace with your SSM parameter name

ssm_client = boto3.client('ssm')

def get_parameter(name):
    try:
        response = ssm_client.get_parameter(Name=name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error fetching SSM parameter '{name}': {str(e)}")
        raise

def get_body(options):
    print("started getbody function")
    try:
        response = requests.request(
            method=options['method'],
            url=options['url'],
            headers=options['headers']
        )
        response.raise_for_status()
        
        if response.text:
            res = response.json()
            print(res)
            return res
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request error: {str(e)}")
        raise

def remove_runner(REPO, instance_id):
    try:
        password = get_parameter(PARAMETER_NAME) 
    except Exception as e:
        print(f"Error fetching SSM parameter: {str(e)}")
        raise
    
    auth = "Bearer " + password
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': auth,
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': OWNER
    }
    
    try:
        result = get_body({
            'method': 'GET',
            'url': f'https://api.github.com/repos/{OWNER}/{REPO}/actions/runners',
            'headers': headers
        })
        
        print(f"Removing GitHub self-hosted runner from EC2 instance {instance_id}")
        print(result, isinstance(result, dict))
        
        off_runners = next((r for r in result['runners'] if r['name'] == instance_id), None)
        print(off_runners, isinstance(off_runners, dict))
        
        if off_runners:
            get_body({
                'method': 'DELETE',
                'url': f'https://api.github.com/repos/{OWNER}/{REPO}/actions/runners/{off_runners["id"]}',
                'headers': headers
            })
            print(f"GitHub self-hosted runner from EC2 instance {instance_id} removed for REPO {REPO}")
        else:
            print(f"No GitHub self-hosted runner for EC2 instance {instance_id}, skipping for REPO {REPO}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

def lambda_handler(event, context):
    print(json.dumps(event))
    
    if event['detail-type'] != 'EC2 Instance Terminate Successful':
        print(f'No action for event type {event["detail-type"]}')
        
    instance_id = event['detail']['EC2InstanceId']
    
    try:
        remove_runner(REPO, instance_id)
    except Exception as e:
        print(f"Error executing Lambda function: {str(e)}")
