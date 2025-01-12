import yaml
import html
import sys
import re 
import textwrap
import tempfile
import os

# sys.path.append('/home/rundeck/projects/RulesInterpreter')

from OpExpertOperations import Interactions

class YAMLLanguageInterpreter():
    
    def __init__(self):

        self.interpretedText = (
            "import os\n"
            "import tempfile\n"
            "import yaml\n"
            "from OpExpertOperations import Interactions\n\n"
            "anObject = Interactions()\n"
            "anObject.login()\n\n"
        )
        self.existenceOfElifany = False
        self.trackedReports = set()
        self.recordIterated = []
        self.indices = []
        self.tabsToInclude = 0
        self.dictionaryPattern = r'\b(\w+)\[\'(\w+)\'\]'
        self.isConditionLoop = False
        self.conditionBreak = False
        self.conditionAlias = ""
        self.conditionWithin = False
        self.conditionLength = 1
        self.conditionOriginal = ""
        self.originalPayload = {}
        self.existenceOfLoop = False
        self.conditionalStatementCount = 0
        self.includeBreakStatement = []
        self.existenceOfIfany = False
        self.currentRecord = ""
        self.recordCopied = False
        self.reportGenerated = False
        self.emailArguments = {}
        self.aliases = set()  # Initialize a set to store module aliases
        
        self.anObject = Interactions()
        self.anObject.login()
        
        self.processes = {
            'import': self.__processImport,
            'condition': self.__processCondition, 
            'execute': self.__processExecution,
            'function': self.__processFunction, 
            'integration': self.__processIntegration, 
            'module': self.__processModule,
            'report':  self.__processReport
        }

    def __processImport(self, payload):
        if 'PackageName' in payload:
            interpretedText = "\t" * self.tabsToInclude + f"from {payload.get('ImportName')} import {payload.get('PackageName')}"
        else:
            interpretedText = "\t" * self.tabsToInclude + f"import {payload.get('ImportName')}"
        
        if 'AliasName' in payload:
            interpretedText += f" as {payload.get('AliasName')}\n"
        else:
            interpretedText += "\n"
        
        return interpretedText

    def __processCondition(self, payload):
        
        interpretedText = ""
        condition = payload.get('Condition')
        # print(condition)
        if condition.startswith("}"):
            
            if self.existenceOfIfany:
                interpretedText += "\t" * self.tabsToInclude + f"{self.currentRecord} = {self.currentRecord}Copy[:]\n"
                self.currentRecord = ""
                interpretedText += "\t" * self.tabsToInclude + f"break\n"
                self.existenceOfIfany = False
                self.recordCopied = True
            if self.existenceOfElifany:
                interpretedText += "\t" * self.tabsToInclude + f"{self.currentRecord} = {self.currentRecord}Copy[:]\n"
                self.currentRecord = ""
                interpretedText += "\t" * self.tabsToInclude + f"break\n"
                self.existenceOfElifany = False
                self.recordCopied = True
            self.conditionalStatementCount -= condition.count("}")
            self.tabsToInclude -= 1
            if self.conditionalStatementCount == -1 and self.existenceOfLoop:
                self.existenceOfLoop = False
                self.tabsToInclude = 0
                for d in self.trackedReports:
                    interpretedText += "\t" * self.tabsToInclude + f"{d} = {d}Copy[:]\n"
            interpretedText += "\t" * self.tabsToInclude + "\n"
        recordReferenceOccurrences = re.findall(r'(\b\w+)\.(\w+)(?=(?:[^"]*"[^"]*")*[^"]*$)', condition)
        if condition.startswith("ifany"): #ifany
            condition = condition.replace("ifany", "if")
            if not self.existenceOfLoop:
                interpretedText += "\t" * self.tabsToInclude + f"for {recordReferenceOccurrences[0][0]} in {recordReferenceOccurrences[0][0]}Copy:\n"
                self.existenceOfLoop = True
                self.recordCopied = False
                self.tabsToInclude += 1
                self.currentRecord = recordReferenceOccurrences[0][0]
                self.trackedReports.add(recordReferenceOccurrences[0][0])
                
            newCondition = condition.replace("ifany", "if").replace(" { ", " ")
            newCondition = re.sub(r'(\b\w+)\.(\w+)(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\1[\'\2\']', newCondition,count=3).replace("\\", "")
                        
            interpretedText += "\t" * self.tabsToInclude + f"{newCondition}:\n"
            self.existenceOfIfany = True
            self.conditionalStatementCount += 1
            self.tabsToInclude += 1

        elif condition.startswith("ifall"): #ifall
            condition = condition.replace("ifall", "if")
            if not self.existenceOfLoop:
                interpretedText += "\t" * self.tabsToInclude + f"for {recordReferenceOccurrences[0][0]} in {recordReferenceOccurrences[0][0]}Copy:\n"
                self.existenceOfLoop = True
                self.recordCopied = False
                self.tabsToInclude += 1
                self.currentRecord = recordReferenceOccurrences[0][0]
                self.trackedReports.add(recordReferenceOccurrences[0][0])                
            newCondition = condition.replace("ifall", "if").replace(" { ", " ")
            newCondition = re.sub( r'(\b\w+)\.(\w+)(?=(?:[^"]*"[^"]*")*[^"]*$)',r"\1[\'\2\']",newCondition,count=3).replace("\\", "")
            interpretedText += "\t" * self.tabsToInclude + f"{newCondition}:\n"
            self.conditionalStatementCount += 1
            self.tabsToInclude += 1
        
        elif condition.startswith("elifall"):
            if not self.existenceOfLoop:
                interpretedText += "\t" * self.tabsToInclude + f"for {recordReferenceOccurrences[0][0]} in {recordReferenceOccurrences[0][0]}Copy:\n"
                self.existenceOfLoop = True
                self.recordCopied = False
                self.tabsToInclude += 1
                self.currentRecord = recordReferenceOccurrences[0][0]
                self.trackedReports.add(recordReferenceOccurrences[0][0])
            newCondition = condition.replace("elifall", "elif").replace(" { ", " ")
            newCondition = re.sub(r'(\b\w+)\.(\w+)(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\1[\'\2\']', newCondition,count=3).replace("\\", "")
            # print(newCondition)
            # self.tabsToInclude-=1
            interpretedText += "\t" * self.tabsToInclude + f"{newCondition}:\n"
            self.conditionalStatementCount += 1
            self.tabsToInclude += 1
        
        elif condition.startswith("elifany"):
            if not self.existenceOfLoop:
                interpretedText += "\t" * self.tabsToInclude + f"for {recordReferenceOccurrences[0][0]} in {recordReferenceOccurrences[0][0]}Copy:\n"
                self.existenceOfLoop = True
                self.recordCopied = False
                self.tabsToInclude += 1
                self.currentRecord = recordReferenceOccurrences[0][0]
                self.trackedReports.add(recordReferenceOccurrences[0][0])
            newCondition = condition.replace("elifany", "elif").replace(" { ", " ")
            newCondition = re.sub(r'(\b\w+)\.(\w+)(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\1[\'\2\']', newCondition,count=3).replace("\\", "")
            self.currentRecord = recordReferenceOccurrences[0][0]
            self.existenceOfElifany = True
            interpretedText += "\t" * self.tabsToInclude + f"{newCondition}:\n"
            self.conditionalStatementCount += 1
            self.tabsToInclude += 1

        elif condition.startswith("if"):
                
            newCondition = condition.replace(" { ", " ")
            newCondition = re.sub(r'(\b\w+)\.(\w+)(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\1[\'\2\']', newCondition).replace("\\", "")
                        
            interpretedText += "\t" * (self.tabsToInclude) + f"{html.unescape(newCondition)}:\n"
            self.conditionalStatementCount += 1
            self.tabsToInclude += 1
        
        elif condition.startswith("elif"):
                
            newCondition = condition.replace(" { ", " ")
            newCondition = re.sub(r'(\b\w+)\.(\w+)(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\1[\'\2\']', newCondition).replace("\\", "")
                        
            interpretedText += "\t" * (self.tabsToInclude) + f"{html.unescape(newCondition)}:\n"
            self.conditionalStatementCount += 1
            self.tabsToInclude += 1
        return interpretedText

    def __processExecution(self, payload):
        interpretedText = ""
        parameterList = []
        for parameter in payload.get('params', []):
            if parameter.get('pType') == 'reference':
                parameterList.append(parameter.get('pValue'))
            elif parameter.get('pType') == 'value':
                parameterList.append(f"\"{parameter.get('pValue')}\"")

        function_call = f"{payload.get('fName')}({', '.join(parameterList)})"
        if payload.get('alias'):
            interpretedText += "\t" * self.tabsToInclude + f"{payload.get('alias')} = {function_call}\n"
        else:
            interpretedText += "\t" * self.tabsToInclude + f"{function_call}\n"
        
        return interpretedText

    def __processFunction(self, payload):
        interpretedText = ""
        args = ""
        transformed_inputs = ""
        global_vars = ""
        function_name = payload.get('AliasName')
        
        input_vars = payload.get('InputVars')
        if input_vars:
            transformed_inputs = [f'"{self.transform_value(value)}"' if '.' not in value else self.transform_value(value) for value in input_vars.values()]
            transformed_inputs = ','.join(transformed_inputs)
            args = ", ".join(input_vars.keys())
        
        output_vars = payload.get('OutputVars')
        
        interpretedText += f"\t" * self.tabsToInclude + f"def func_{function_name}({args}):\n"
        self.tabsToInclude += 1
        
        code_snippet = self.anObject.getCodeSnippetWithID(payload.get('FunctionID')).split('\n')
        
        if output_vars:
            output_vars = output_vars.split(',')
            global_vars = ['global ' + function_name + '\n' + ('\t' * self.tabsToInclude) + function_name + ' = {}']
        code_snippet = [line for line in code_snippet if 'return' not in line]
        if output_vars:
            for i in range(len(code_snippet)):
                for var in output_vars:
                    code_snippet[i] = code_snippet[i].replace(var, f'{function_name}[\"{var}\"]')
            code_snippet = global_vars + code_snippet
        else:
            code_snippet = code_snippet
        
        for line in code_snippet:
            line = html.unescape(line)
            interpretedText += "\t" * self.tabsToInclude + line + '\n'
        interpretedText += ('\t' * (self.tabsToInclude-1)) + f"func_{function_name}({transformed_inputs})\n"
        
        self.tabsToInclude -= 1
        return interpretedText

    def __processIntegration(self, payload):
        interpretedText = ""
        alias = payload.get('AliasName')
        record_id = payload.get('IntegrationID')
        params = self.dict_to_string(payload.get('UserInputVars')) if payload.get('UserInputVars') != None else []

        original_data = f"anObject.getIntegrationWithID('{record_id}',f'{params}')"
        interpretedText += "\t" * self.tabsToInclude + f"{alias} = {original_data}\n"
        interpretedText += "\t" * self.tabsToInclude + f"{alias}Copy = {alias}[:]\n"
        return interpretedText

    def __processModule(self, payload):
        interpretedText = ""
        alias = payload.get('AliasName')
        record_id = payload.get('recordID')
        module_name = payload.get('moduleName')
        # fields = payload.get('ModuleVars') not working
        fields = list(payload.get('moduleVars').keys()) if 'moduleVars' in payload else []

        if alias:
            self.aliases.add(alias)  # Store the alias

        interpretedText += "\t" * self.tabsToInclude + f"global {alias}\n"
        if "moduleVars" in payload:
            interpretedText += "\t" * self.tabsToInclude + f"{alias} = anObject.getModuleWithID('{record_id}', '{module_name}', {fields})\n"
        else:
            interpretedText += "\t" * self.tabsToInclude + f"{alias} = anObject.getModuleWithID('{record_id}', '{module_name}')\n"

        return interpretedText

    def __processReport(self, payload):
        interpretedText = ""

        if not isinstance(payload, list):
            raise TypeError("payload must be a list of dictionaries")

        # First, check if any 'screenshot' action requires variable substitution
        needs_variable_substitution = False
        for action in payload:
            if action.get('ReportType') == 'screenshot':
                for key in ['UserName', 'Password']:
                    value = action.get(key)
                    if isinstance(value, str) and '.' in value:
                        prefix, _, suffix = value.partition('.')
                        if prefix in self.aliases:
                            needs_variable_substitution = True
                            break  # No need to check further
                if needs_variable_substitution:
                    break

        # Generate code accordingly
        temp_dir_line = "\t" * self.tabsToInclude + "temp_dir = tempfile.gettempdir()\n"
        report_file_line = "\t" * self.tabsToInclude + "report_yaml_file = os.path.join(temp_dir, f\"report_config_{os.getpid()}.yaml\")\n"

        if needs_variable_substitution:
            # Serialize the payload into a string representation
            payload_str = repr(payload)

            # Generate code to assign the payload
            payload_line = "\t" * self.tabsToInclude + f"payload = {payload_str}\n"

            # Generate code to process the payload during execution using a multi-line string
            process_payload_code = '\t' * self.tabsToInclude + "for action in payload:\n"+ '\t' * self.tabsToInclude +"\tif action.get('ReportType') == 'screenshot':\n"+ '\t' * self.tabsToInclude +"\t\tfor key in ['UserName', 'Password']:\n"+ '\t' * self.tabsToInclude +"\t\t\tvalue = action.get(key)\n"+ '\t' * self.tabsToInclude +"\t\t\tif isinstance(value, str) and '.' in value:\n"+ '\t' * self.tabsToInclude +"\t\t\t\tprefix, _, suffix = value.partition('.')\n"+ '\t' * self.tabsToInclude +"\t\t\t\tif prefix in globals():\n"+ '\t' * self.tabsToInclude +"\t\t\t\t\taction[key] = globals()[prefix].get(suffix, value)\n"+ '\t' * self.tabsToInclude +"\t\t\t\telse:\n"+ '\t' * self.tabsToInclude +"\t\t\t\t\taction[key] = value\n"

            # Generate code to write the YAML file during execution
            write_yaml_code = "\t" * self.tabsToInclude + "with open(report_yaml_file, 'w') as file:\n"
            write_yaml_code += "\t" * (self.tabsToInclude + 1) + "yaml.dump(payload, file)\n\n"

            # Combine all parts
            interpretedText += temp_dir_line + report_file_line + payload_line + process_payload_code + write_yaml_code

        else:
            # No variable substitution needed; write the YAML file now
            # Generate the YAML file during interpretation (before execution)
            temp_dir = tempfile.gettempdir()
            report_yaml_file = os.path.join(temp_dir, f"report_config_{os.getpid()}.yaml")
            with open(report_yaml_file, 'w') as file:
                yaml.dump(payload, file)

            # Since the file is already written, we only need to include the file path in the code
            interpretedText += temp_dir_line + report_file_line

        # Generate code to call getReport
        get_report_line = "\t" * self.tabsToInclude + f"Interactions.getReport(report_yaml_file, {self.emailArguments})\n"

        # Add the getReport call to interpretedText
        interpretedText += get_report_line

        return interpretedText

    def processPayload(self):
        if not self.originalPayload:
            return "ERROR: Invalid or empty payload."

        for action in self.originalPayload:
            if 'Condition' in action:
                self.recordIterated = []
                self.indices = []
                result = self.__processCondition(action)
                if result:
                    self.interpretedText += result
                else:
                    self.interpretedText += f"# No output for action type {action['ActionType']}\n"
            elif action['ActionType'] == 'report' and not self.reportGenerated:
                self.reportGenerated = True
                result = self.__processReport(self.originalPayload)
                self.interpretedText += result
                # self.interpretedText += f"# Action {action['ActionType']} generated\n"
            elif 'ActionType' in action and action['ActionType'] != 'report':
                self.recordIterated = []
                self.indices = []
                process = self.processes.get(action['ActionType'])
                if process:
                    result = process(action)
                    if result:
                        self.interpretedText += result
                    else:
                        self.interpretedText += f"# No output for action type {action['ActionType']}\n"
            elif action['ActionType'] != 'report':
                self.interpretedText += f"# No action type found in {action}\n"
        return self.interpretedText
 
    def executeInterpretedText(self):
        if not self.interpretedText:
            return "ERROR: No script to execute. Please generate a script first."

        try:
            exec(self.interpretedText)
            return "Execution successful."
        except Exception as e:
            return f"ERROR: An error occurred during script execution. {str(e)}"

    def printInterpretedText(self):
        print(self.interpretedText)

    def transform_value(self, value):
        if '.' in value:
            value = value.replace('.', '[\"')
            value = value+'\"]'
        return value

    def dict_to_string(self, data):
        result = '[{{'
        for i, (key, value) in enumerate(data.items()):
            if '.' in value:
                obj, var = value.split('.')
                result += f'"{key}": "{{{obj}["{var}"]}}"'
            else:
                result += f'"{key}": "{value}"'
            if i < len(data) - 1:
                result += ', '
        result += '}}]' 
        return result
    
    def convert_to_dict(self, email_string):
        email_string = email_string.strip("[]")
        pairs = email_string.split(", ")
        email_dict = {}
        
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                if value == 'null':
                    value = None
                email_dict[key] = value
        
        return email_dict
    
def main(arguments):
    interpreter = YAMLLanguageInterpreter()
    
    arguments = ["path", """    
Rules:
  -
    Step: 1
    ActionType: integration
    IntegrationID: 677a1508-a5bc-45e5-3c34-673d91571327
    IntegrationName: 'Jazeera Inactive Hosts Count'
    AliasName: report
    UserInput: false
    UserInputVars: null
  -
    Step: 2
    Condition: 'ifany {  report.unavailable_count == 4'
  -
    Step: 3
    ActionType: report
    ReportType: config
    ReportName: Test
    Orientation: Portrait
    PageSize: A4
  -
    Step: 4
    ActionType: report
    ReportType: index
    TemplateId: afe3b001-eb10-9603-5698-66fb77ac69ce
    TemplateName: 'Default Index Portrait'
  -
    Step: 5
    ActionType: report
    ReportType: table
    IntegrationID: 14c91c44-7375-99e0-eec7-673d989e46ac
    IntegrationName: 'Jazeera Inactive Hosts Details'
    AliasName: report2
    UserInput: false
    UserInputVars: {  }
    TemplateId: 93503d18-2182-5339-489f-66fb798b92d2
    TemplateName: 'Default Table Portrait'
  -
    Step: 6
    Condition: '}'
  -
    Step: 7
    Condition: 'elifany {  report.unavailable_count == 3'
  -
    Step: 8
    ActionType: integration
    IntegrationID: 6a867ddf-9f0e-43e5-4325-6735985652c4
    IntegrationName: 'Telegram Alert'
    AliasName: alert
    UserInput: false
    UserInputVars: {  }
  -
    Step: 9
    Condition: '}'
""","[to:\"\", cc:, bcc:, emailTemplateID:\"b7e5f922-fdbf-d83f-f9a5-65a3b3b4fa45\", emailTemplateName:null]"]
    
    interpreter.emailArguments = interpreter.convert_to_dict(arguments[2])
    
    arguments[1] = arguments[1].replace("Rules:", "")

    interpreter.originalPayload = yaml.safe_load(arguments[1])
    
    interpreted_text = interpreter.processPayload()

    print("Generated Python Code:")
    print(interpreted_text)

    execution_result = interpreter.executeInterpretedText()
    print("Execution Result:", execution_result)

if __name__ == '__main__':
    import time
    start_time = time.time()
    arguments = sys.argv
    main(arguments)
    end_time = time.time()
    execution_time = end_time - start_time

    print("Execution time:", execution_time, "seconds")