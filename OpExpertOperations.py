from hashlib import md5
from json import dumps, loads
import requests
import sys
from requests import Session
from urllib.parse import unquote
import os
import base64

class Interactions:
    
    def __init__(self):
        
        VAULT_ADDR = "http://vault.opexpert.io"
        ROLE_ID = "9a88b01d-a49d-2d31-6ba5-4e431a8d7530"
        SECRET_ID = "1d5bb023-2dc4-6261-127b-22b3a1d06e29"
        SECRET_PATH = "user_abdallah/data/rules"

        try:
            auth_response = requests.post(
                f"{VAULT_ADDR}/v1/auth/approle/login",
                json={"role_id": ROLE_ID, "secret_id": SECRET_ID}
            )

            if auth_response.status_code != 200:
                print(f"Authentication failed: {auth_response.text}")
                sys.exit(1)

            auth_data = auth_response.json()
            token = auth_data.get("auth", {}).get("client_token")

            if not token:
                print("Authentication failed. No token received.")
                sys.exit(1)

            secret_response = requests.get(
                f"{VAULT_ADDR}/v1/{SECRET_PATH}",
                headers={"X-Vault-Token": token}
            )

            if secret_response.status_code != 200:
                print(f"Error retrieving the secret: {secret_response.text}")
                sys.exit(1)

            secret_data = secret_response.json()
            self.username = secret_data.get("data", {}).get("data", {}).get("username")
            self.password = secret_data.get("data", {}).get("data", {}).get("password")

            if not self.username or not self.password:
                print("Error: Secret data is incomplete.")
                sys.exit(1)

        except requests.RequestException as e:
            print(f"Error communicating with Vault: {e}")
            sys.exit(1)
        
        self.CRMURL = 'https://app02.opexpert.com/custom/service/v4_1_custom/rest.php'
        self.sessionID = False

    def login(self):
        
        data = {
            'user_auth': {
                'user_name': self.username, 
                'password': md5(self.password.encode()).hexdigest()
            }
        }
        
        response = self.__call('login', data)
        self.sessionID = response.get('id') 

    def __call(self, method, data, URL = False):
        
        curlRequest = Session()
        
        payload = {
            'method': method, 
            'input_type': 'JSON', 
            'response_type': 'JSON', 
            'rest_data': dumps(data), 
            'script_command': True
        }
        
        response = curlRequest.post(URL if URL else self.CRMURL, data = payload)
        curlRequest.close()
        result = loads(response.text)

        return result

    def getIntegrationWithID(self, reportID = '', params=''):
        if self.sessionID:
            
            data = {
                'session': self.sessionID, 
                'report_id': reportID, 
                'UserInputParams': base64.b64encode(params.encode()).decode() 
            }
            try:
                return self.__call('getAPIReportResponse', data)
            except:
                return "An error occurred. Please try again after verifying your session ID and report ID."
            
        else:
            return "You cannot proceed with this action without initializing a session."

    def getModuleWithID(self, reportID = '', moduleName = '', fields = []):
        
        if self.sessionID:
            
            data = {
                'session': self.sessionID, 
                'module_name': moduleName, 
                'query': f"{moduleName.lower()}.id = \'{reportID}\'", 
                'order_by': '', 
                'offset': 0, 
                'deleted': False
            }
            
            try:
                module = self.__call('get_entry_list', data)['entry_list']
                if len(fields) == 0:
                    return module
                elif len(fields) == 1:
                    return module[0]['name_value_list'][fields[0]]['value']
                else:
                    requiredFields = {}
                    for field in fields:
                        requiredFields[field] = module[0]['name_value_list'][field]['value']
                    return requiredFields
            except:
                return "An error occurred. Please try again after verifying your session ID and report ID."
            
        else:
            return "You cannot proceed with this action without initializing a session."

    def getCodeSnippetWithID(self, reportID = ''):
        
        if self.sessionID:
            
            data = {
                'session': self.sessionID, 
                'module_name': 'bc_api_methods', 
                'query': f"{'bc_api_methods'.lower()}.id = \'{reportID}\'", 
                'order_by': '', 
                'offset': 0, 
                'deleted': False
            }
            
            try:
                code = unquote(self.__call('get_entry_list', data)['entry_list'][0]['name_value_list']['description']['value'])
                return code if code else 'return None'
            except:
                return "An error occurred. Please try again after verifying your session ID and report ID."
            
        else:
            return "You cannot proceed with this action without initializing a session."
        
    def getHTMLTemplateWithID(self, reportID = ''):
        
        if self.sessionID:
            
            data = {
                'session': self.sessionID, 
                'module_name': 'bc_html_writer', 
                'query': f"{'bc_html_writer'.lower()}.id = \'{reportID}\'", 
                'order_by': '', 
                'offset': 0, 
                'deleted': False
            }
            
            try:
                code = unquote(self.__call('get_entry_list',data)['entry_list'][0]['name_value_list']['html_body']['value'])
                return code if code else 'return None'
            except:
                return "An error occurred. Please try again after verifying your session ID and report ID."
            
        else:
            return "You cannot proceed with this action without initializing a session."
        
    def getEmailTemplateWithID(self, reportID = ''):
        
        if self.sessionID:
            
            data = {
                'session': self.sessionID, 
                'module_name': "EmailTemplates", 
                'query': f"email_templates.id = '{reportID}'", 
                'order_by': '', 
                'offset': 0, 
                'deleted': False
            }
            
            try:
                code = self.__call('get_entry_list',data)['entry_list'][0]['name_value_list']['body_html']['value']
                return code if code else 'return None'
            except:
                return "An error occurred. Please try again after verifying your session ID and report ID."
            
        else:
            return "You cannot proceed with this action without initializing a session."
        
    def getReport(yamlFile,emailConfig): 
        command = f"python3 /home/rundeck/projects/RulesInterpreterApp02/getAPIReport.py {yamlFile} \"{emailConfig}\""
        os.system(command)
        
