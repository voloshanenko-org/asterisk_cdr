from __future__ import print_function
import os
import portainer_api
from portainer_api.rest import ApiException
from pprint import pprint
import requests
import json
import subprocess
import sys

portainer_env_variables = ["PORTAINER_HOST", "PORTAINER_USERNAME", "PORTAINER_PASSWORD", "PORTAINER_STACK_NAME"]

for env_variable in portainer_env_variables:
    if env_variable not in os.environ:
        print("ENV variable '" + env_variable + "' required but not SET")
        print("Exit...")
        exit(1)

portainer_host = os.environ.get('PORTAINER_HOST') or 'http://10.100.101.201:9000/api'
portainer_username = os.environ.get('PORTAINER_USERNAME') or 'admin'
portainer_password = os.environ.get('PORTAINER_PASSWORD') or 'Qazwsx!@#123'
portainer_stack_name = os.environ.get('PORTAINER_STACK_NAME') or 'asteriskcdr'

def main():
    portainer_config = portainer_api.Configuration()
    portainer_config.host = portainer_host

    api_client_credentials = portainer_api.AuthApi(portainer_api.ApiClient(portainer_config))
    portainer_auth = portainer_api.AuthenticateUserRequest(username=portainer_username, password=portainer_password)

    try:
        # Authenticate a user
        print("Retrieve portainer JWT token...")
        jwt_token = api_client_credentials.authenticate_user(portainer_auth).jwt

        # Create API client with JWT token auth
        api_client = portainer_api.ApiClient(configuration=portainer_config, header_name="Authorization", header_value=jwt_token)

        # Get stacks list
        print("Retrieve current portainer stacks list...")
        stacks_api = portainer_api.StacksApi(api_client=api_client)
        stacks_list = stacks_api.stack_list()

        current_stack = [stack for stack in stacks_list if stack['Name'] == portainer_stack_name]
        if current_stack:
            print("...Found stack: '" + portainer_stack_name + "'")
            endpoint_id = current_stack[0]['EndpointId']
            stack_id = current_stack[0]['Id']
            stack_containers, containers_images = containers_list(endpoint_id=endpoint_id, stack_name=portainer_stack_name, jwt_token=jwt_token)
            if stack_containers:
                for container in stack_containers:
                    print("......Found container: '" + container + "'")
                    print("......Delete container: '" + container + "'")
                    delete_container(endpoint_id=endpoint_id, container_name=container, jwt_token=jwt_token)

            if containers_images:
                for image in containers_images:
                    print("......Found container image: '" + image + "'")
                    print("......Delete image: '" + image + "'")
                    delete_container_image(endpoint_id=endpoint_id, image_name=image, jwt_token=jwt_token)

            print("...Remove stack: '" + portainer_stack_name + "'")
            stacks_api.stack_delete(id=stack_id, endpoint_id=endpoint_id)
        else:
            print("...Stack '" + portainer_stack_name + "' not found on portainer side...")
            endpoint_id=1
            print("...Set EndpointId='" + str(endpoint_id) + "'")

        print("...Create stack from git repo")
        repo_dir = sys.path[0]
        git_url = subprocess.check_output("cd " + repo_dir + " && git config --get remote.origin.url", shell=True).decode('utf-8').strip()
        print("......Repo URL: '" + git_url + "'")


        stack_env_variables = ["DB_HOST", "DB_NAME_CDR", "DB_NAME_USERS", "DB_USERNAME", "DB_PASSWORD",
                               "VIRTUAL_HOST", "VIRTUAL_PORT", "LETSENCRYPT_HOST", "LETSENCRYPT_EMAIL",
                               "ASTERISK_HOST", "ASTERISK_AMI_USERNAME", "ASTERISK_AMI_PASSWORD"]
        stack_env_dict = []

        for env_variable in stack_env_variables:
            if env_variable in os.environ:
                print("......Stack ENV variable '" + env_variable + "' found...")
                stack_env_dict.append({ "name": env_variable, "value": os.environ.get(env_variable)})

        print(stack_env_dict)

        stack_create_request = portainer_api.StackCreateRequest(
            name=portainer_stack_name,
            repository_url=git_url,
            compose_file_path_in_repository="docker-compose.yml",
            env=stack_env_dict if stack_env_dict else ""
        )
        stacks_api.stack_create(type=2, method='repository', body=stack_create_request, endpoint_id=endpoint_id)


    except ApiException as e:
        print("Exception when calling AuthApi->authenticate_user: %s\n" % e)

def containers_list(endpoint_id=None, stack_name=None, jwt_token=None):
    url = portainer_host + '/endpoints/' + str(endpoint_id)  + '/docker/containers/json'
    headers ={'Authorization': jwt_token}
    payload = {
        'all': '1',
        'filters': '{"label":["com.docker.compose.project=' + stack_name + '"]}'
    }

    r = requests.get(url, headers=headers, params=payload)
    r_data = json.loads(r.text)

    containers = [con['Names'][0].replace("/","") for con in r_data]
    images = [con['Image'] for con in r_data]

    return containers, images


def delete_container(endpoint_id=None, container_name=None, jwt_token=None):
    url = portainer_host + '/endpoints/' + str(endpoint_id)  + '/docker/containers/' + container_name
    headers ={'Authorization': jwt_token}
    payload = {
        'force': True,
        'v': True
    }
    r = requests.delete(url, headers=headers, params=payload)

def delete_container_image(endpoint_id=None, image_name=None, jwt_token=None):
    url = portainer_host + '/endpoints/' + str(endpoint_id)  + '/docker/images/' + image_name
    headers ={'Authorization': jwt_token}
    payload = {
        'force': True
    }
    r = requests.delete(url, headers=headers, params=payload)


if __name__ == '__main__':
    main()
