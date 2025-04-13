import os
import sys
import yaml
import html
import json
import base64
import jinja2
import pdfkit
import asyncio
import smtplib
import datetime
import uuid
import requests
import pandas as pd
from math import ceil
from PIL import Image
from email import encoders
from pyppeteer import launch
from collections import defaultdict
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from OpExpertOperations import Interactions
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor

os.chdir("/home/rundeck/projects/RulesInterpreterApp02")

def readConfig(filename):
    """
    Reads config file contents.

    :return: contents of config file.
    """
    with open(filename, 'r') as file:
        data = yaml.safe_load(file)
    return data

def getApiReport(data):
    """
    Retrieves report data from an API.

    :param data: Dictionary containing parameters for the API request.
    :return: Response data from the API.
    """
    crm_interaction = Interactions()
    crm_interaction.login()
    report_id = data.get('reportID')

    return crm_interaction.getIntegrationWithID(report_id)
    
def retrieveReports(config):
    """
    Retrieves multiple reports using multithreading.

    :param config: Configuration settings for report retrieval.
    :return: Dictionary containing report data.
    """

    reports = {}

    with ThreadPoolExecutor() as executor:
        future_to_key = {}
        for key in ['printTable', 'printPie', 'printLine', 'printBar', 'printDonut']:
            for i, item in enumerate(config.get(key, [])):
                future = executor.submit(getApiReport, item)
                future_to_key[future] = (key, i)

        for future in future_to_key:
            key, i = future_to_key[future]
            try:
                report_data = future.result()
                reports[(key, i)] = report_data
            except Exception as e:
                print(f"Failed to retrieverundeck report for {key} {i}: {e}")

    return reports

def retrieveHTMLTemplate(templateID):
    """
    Retrieves HTML template data using API.

    Args:
        templateID (str): String containing record ID for HTML template

    Returns:
        result (str): A string containing the API response of HTML template
    """
    
    crm_interaction = Interactions()
    crm_interaction.login()
    result = crm_interaction.getHTMLTemplateWithID(templateID)
    result = html.unescape(result)
    
    return result

def retrieveEmailTemplate(templateID):
    """
    Retrieves Email template data using API.

    Args:
        templateID (str): String containing record ID for Email template

    Returns:
        result (str): A string containing the API response of Email template
    """
    
    crm_interaction = Interactions()
    crm_interaction.login()
    result = crm_interaction.getEmailTemplateWithID(templateID)
    result = html.unescape(result)
    
    return result

def get_vault_token(vault_addr, role_id, secret_id):
    login_url = f"{vault_addr}/v1/auth/approle/login"
    payload = {"role_id": role_id, "secret_id": secret_id}
    
    try:
        response = requests.post(login_url, json=payload)
        response_data = response.json()
        
        if "auth" in response_data and "client_token" in response_data["auth"]:
            return response_data["auth"]["client_token"]
        else:
            print("Authentication failed. No token received.")
            sys.exit(1)
    except requests.RequestException as e:
        print(f"Error during authentication: {e}")
        sys.exit(1)

def get_vault_secret(vault_addr, token, secret_path):
    secret_url = f"{vault_addr}/v1/{secret_path}"
    
    headers = {
        "X-Vault-Token": token
    }
    
    try:
        response = requests.get(secret_url, headers=headers)
        response_data = response.json()

        if "errors" in response_data:
            print(f"Error retrieving the secret: {response_data['errors']}")
            sys.exit(1)
        return response_data
    except requests.RequestException as e:
        print(f"Error retrieving the secret: {e}")
        sys.exit(1)

def sendEmail(emailArguments, reportName, attachment_path):
    """
    Sends an email with an attachment.

    Args:
        emailArguments (dict): A dictionary containing email arguments, including the recipient's email address.
        reportName (str): The name of the report.
        attachment_path (str): The file path of the attachment.

    Returns:
        None
    """
    VAULT_ADDR = "https://vault.broadbits.com"
    ROLE_ID = "d999f7e8-b9ad-e2df-08c2-0b66fadeb1d8"
    SECRET_ID = "f683fa30-d8f5-0557-a30d-2dd5271f23d8"
    SECRET_PATH = "rules_engine/data/support"
    token = get_vault_token(VAULT_ADDR, ROLE_ID, SECRET_ID)
    secret_response = get_vault_secret(VAULT_ADDR, token, SECRET_PATH)
    username = secret_response['data']['data'].get('username')
    password = secret_response['data']['data'].get('password')
    smtp_server = secret_response['data']['data'].get('smtp_server')
    port = secret_response['data']['data'].get('port')
    receiver_email = emailArguments['to'].split(',')
    receiver_cc = emailArguments['cc'].split(',')
    receiver_bcc = emailArguments['bcc'].split(',')
    all_recipients = receiver_email + receiver_cc + receiver_bcc
    reportName = ''.join(reportName.split('_')[1:])
    if 'emailTemplateID' in emailArguments and emailArguments['emailTemplateID'] != "":
        email_ID = emailArguments['emailTemplateID']
        email_content = retrieveEmailTemplate(email_ID)
    else:
        # Set default email content if 'emailTemplateID' is not in emailArguments
        email_content = "Dear User, \n\nPlease find the attached report. Let us know if you have any questions.\n\nBest Regards,\nOpExpert Team"
    print(f"\tSending  email to {', '.join(receiver_email)}")
    message = MIMEMultipart()
    message['From'] = f'OpExpert Notifications <{username}>'
    message['To'] = ', '.join(receiver_email)
    message['Cc'] = ', '.join(receiver_cc)
    message['Bcc'] = ', '.join(receiver_bcc)
    message['Subject'] = f'Automated Report Generation - {reportName}'
    if 'emailTemplateID' in emailArguments and emailArguments['emailTemplateID'] != "":
        message.attach(MIMEText(email_content, 'html'))
    else:
        message.attach(MIMEText(email_content, 'plain'))

    with open(attachment_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename={reportName}.pdf")
    message.attach(part)

    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(username, password)
    server.sendmail(username,all_recipients, message.as_string())
    server.quit()

def convert_yaml(data):
    """
    Convert YAML data to a specific format for generating reports.

    Args:
        input_yaml (str): YAML data containing report configuration.

    Returns:
        str: YAML data in the desired format for generating reports.
    """

    result = defaultdict(list)
    main_config = {}

    for item in data:
        if item.get('ActionType') == 'report':
            report_type = item['ReportType']

            if report_type == 'config':
                main_config = {
                    'reportName': item.get('ReportName', 'Report-{{yy-mm-dd}}'),
                    'orientation': item.get('Orientation', 'Landscape'),
                    'pageSize': item.get('PageSize', 'Letter'),
                }
            elif report_type == 'coverpage':
                result['printCoverPage'] = {
                    'title': item.get('Title'),
                    'description': item.get('Description', 'This is a test'),
                    'date': item.get('Date', '01/01/2024'),
                    'template': item.get('TemplateId')
                    # 'template': 'defaultCoverPage'
                }
            elif report_type == 'index':
                result['printIndex'] = {
                    'template': item.get('TemplateId','16e000a5-e417-4be6-f5a9-66c2e0744402')
                    # 'template': 'defaultIndex'
                }
            elif report_type == 'table':
                result['printTable'].append({
                    'reportID': item.get('IntegrationID'),
                    'tableName': item.get('AliasName'),
                    'tableTitle': item.get('IntegrationName'),
                    'template': item.get('TemplateId','378e309a-97f3-068e-e9a1-66c2e0a59228'),
                    # 'template': 'defaultTable',
                    'includeRowNumbers': True
                })
            elif report_type == 'pie':
                result['printPie'].append({
                    'reportID': item.get('IntegrationID'),
                    'tableName': item.get('AliasName'),
                    'tableTitle': item.get('IntegrationName'),
                    'template': item.get('TemplateId','ef967964-dfcd-ac49-a207-66c2d972eb34')
                    # 'template': 'defaultPie'
                })
            elif report_type == 'line':
                result['printLine'].append({
                    'reportID': item.get('IntegrationID'),
                    'tableName': item.get('AliasName'),
                    'tableTitle': item.get('IntegrationName'),
                    'template': item.get('TemplateId','5b0d2dac-d106-bcd1-7328-66c2e03c683a'),
                    # 'template': 'defaultLine',
                    'grid': True
                })
            elif report_type == 'bar':
                result['printBar'].append({
                    'reportID': item.get('IntegrationID'),
                    'tableName': item.get('AliasName'),
                    'tableTitle': item.get('IntegrationName'),
                    'template': item.get('TemplateId','31fef628-e312-854a-d418-66ac5f7d9f2f'),
                    # 'template': 'defaultBar',
                    'grid': False
                })
            elif report_type == 'donut':
                result['printDonut'].append({
                    'reportID': item.get('IntegrationID'),
                    'tableName': item.get('AliasName'),
                    'tableTitle': item.get('IntegrationName'),
                    'template': item.get('TemplateId','c08ed299-f282-ba3d-f394-66c8452589bb'),
                    # 'template': 'defaultDonut',
                })
            elif report_type == 'screenshot':
                result['printScreenshot'].append({
                    'loginURL': item.get('URL'),
                    'username': item.get('UserName'),
                    'password': item.get('Password'),
                    'targetURL': item.get('UserVal'),
                    'tableName': item.get('PassVal'),
                    'template': 'a57000ba-cca7-b074-3198-66ceef65c189'
                })
            elif report_type == 'close':
                result['printClose'] = {
                    'template': item.get('TemplateId')
                    # 'template': 'defaultClose'
                }

    result['mainConfig'] = main_config
    return dict(result)

async def capture_screenshot(image_path, html_path, chart_type):
    """
    Capture a screenshot of a web page and save it to the specified image path.

    Args:
        image_path (str): The path where the screenshot image will be saved.
        html_path (str): The path of the HTML file to capture the screenshot of.

    Returns:
        None
    """

    browser = await launch(headless=True, args=['--no-sandbox', '--headless', '--disable-gpu'])
    page = await browser.newPage()

    absolute_path = os.path.abspath(html_path)
    local_html_file_url = f'file:///{absolute_path}'

    try:
        await page.goto(local_html_file_url)
        await page.waitForFunction("document.querySelector('#container').innerHTML.includes('highcharts-series-group')",{'timeout': 20000})
        await page.setViewport({'width': 1600, 'height': 800})
        await page.screenshot({'path': image_path})  
        # if pageOrientation == 'Portrait':
        #     crop_screenshot(image_path, 100)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.close()

async def insert_data_into_HTML(data, chart_type, title):
    """
    Inserts data into an HTML template and saves it as a file based on the specified chart type.

    Args:
        data (list): The data to be inserted into the HTML template.
        chart_type (str): The type of chart to be generated ('pie', 'donut', 'bar', or 'line').
        title (str): The title of the chart.

    Returns:
        None
    """
    data_json = json.dumps(data)
    chart_options = {
        "pie": f"""
        const firstItem = columns[0];
        const descriptionKey = Object.keys(firstItem)[0];
        const countKey = Object.keys(firstItem)[1];

        function parseValue(value) {{
            if (!isNaN(value)) {{
                return parseFloat(value);
            }}
            return value;
        }}

        const descriptionCounts = {{}};
        columns.forEach((item) => {{
            const description = item[descriptionKey];
            const count = parseValue(item[countKey]);
            descriptionCounts[description] = (descriptionCounts[description] || 0) + count;
        }});

        const pieData = Object.entries(descriptionCounts).map(([description, count]) => ({{
            name: description,
            y: count
        }}));

        Highcharts.chart('container', {{
            chart: {{
                type: 'pie',
                animation: false
            }},
            title: {{
                text: '{title}'
            }},
            credits: {{
                enabled: false
            }},
            series: [{{
                name: 'Description',
                data: pieData,
                animation: false,
                dataLabels: [{{
                    enabled: true,
                    format: '{{point.name}}: {{point.y}}',
                    distance: 30,
                    style: {{
                        fontSize: '15px',
                        fontWeight: 'bold',
                        color: '#555',
                        textOutline: 'none',
                    }}
                }}, {{
                    enabled: true,
                    format: '{{point.percentage:.1f}} %',
                    distance: -50,
                    style: {{
                        fontSize: '15px',
                        fontWeight: 'bold',
                        color: 'white',
                        textOutline: 'none',
                    }},
                    filter: {{
                        operator: '>',
                        property: 'percentage',
                        value: 5
                    }}
                }}]
            }}],
            plotOptions: {{
                pie: {{
                    showInLegend: true
                }}
            }}
        }});
        """,
        "bar": f"""
        const firstItem = columns[0];
        const descriptionKey = Object.keys(firstItem)[0];
        const countKey = Object.keys(firstItem)[1];

        function parseValue(value) {{
            if (!isNaN(value)) {{
                return parseFloat(value);
            }}
            return value;
        }}

        const descriptionCounts = {{}};
        columns.forEach((item) => {{
            const description = item[descriptionKey];
            const count = parseValue(item[countKey]);
            descriptionCounts[description] = (descriptionCounts[description] || 0) + count;
        }});

        const categories = Object.keys(descriptionCounts);
        const data = Object.values(descriptionCounts);

        Highcharts.chart('container', {{
            chart: {{
                type: 'column',
                animation: false
            }},
            title: {{
                text: '{title}'
            }},
            credits: {{
                enabled: false
            }},
            xAxis: {{
                categories: categories,
                title: {{
                    text: 'Description'
                }}
            }},
            yAxis: {{
                min: 0,
                title: {{
                    text: 'Count',
                    align: 'high'
                }},
                labels: {{
                    overflow: 'justify'
                }}
            }},
            series: [{{
                name: 'Count',
                data: data,
                animation: false
            }}]
        }});
        """,
        "line": f"""
        const firstItem = columns[0];
        const xKey = Object.keys(firstItem)[0];
        const yKey = Object.keys(firstItem)[1];
        
        const xValues = columns.map(item => item[xKey]);
        const yValues = columns.map(item => item[yKey]);

        Highcharts.chart('container', {{
            chart: {{
                type: 'line',
                animation: false
            }},
            title: {{
                text: '{title}'
            }},
            credits: {{
                enabled: false
            }},
            xAxis: {{
                categories: xValues,
                title: {{
                    text: xKey
                }},
                labels: {{
                    rotation: -45,
                    align: 'right'
                }}
            }},
            yAxis: {{
                title: {{
                    text: yKey
                }}
            }},
            series: [{{
                name: yKey,
                data: yValues,
                animation: false
            }}]
        }});
        """,
        "donut": f"""
        const firstItem = columns[0];
        const descriptionKey = Object.keys(firstItem)[0];
        const countKey = Object.keys(firstItem)[1];

        function parseValue(value) {{
            if (!isNaN(value)) {{
                return parseFloat(value);
            }}
            return value;
        }}

        const descriptionCounts = {{}};
        columns.forEach((item) => {{
            const description = item[descriptionKey];
            const count = parseValue(item[countKey]);
            descriptionCounts[description] = (descriptionCounts[description] || 0) + count;
        }});

        const pieData = Object.entries(descriptionCounts).map(([description, count]) => ({{
            name: description,
            y: count
        }}));

        Highcharts.chart('container', {{
            chart: {{
                type: 'pie',
                animation: false
            }},
            title: {{
                text: '{title}'
            }},
            credits: {{
                enabled: false
            }},
            series: [{{
                name: 'Description',
                data: pieData,
                innerSize: '50%',
                animation: false,
                dataLabels: [{{
                    enabled: true,
                    format: '{{point.name}}: {{point.y}}',
                    distance: 30,
                    style: {{
                        fontSize: '15px',
                        fontWeight: 'bold',
                        color: '#555',
                        textOutline: 'none',
                    }}
                }}, {{
                    enabled: true,
                    format: '{{point.percentage:.1f}} %',
                    distance: -50,
                    style: {{
                        fontSize: '15px',
                        fontWeight: 'bold',
                        color: 'white',
                        textOutline: 'none',
                    }},
                    filter: {{
                        operator: '>',
                        property: 'percentage',
                        value: 5
                    }}
                }}]
            }}],
            plotOptions: {{
                pie: {{
                    showInLegend: true
                }}
            }}
        }});
        """
    }
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://code.highcharts.com/highcharts.js"></script>
        <title>Highcharts {chart_type.capitalize()} Chart</title>
    </head>
    <body>
        <div id="container" style="width: 1600px; height: 800px;"></div>
        <script>
            const input_response = {data_json};
            const columns = input_response;

            {chart_options[chart_type]}
        </script>
    </body>
    </html>
    """

    file_name = f'templates/{chart_type}_chart.html'
    with open(file_name, 'w') as file:
        file.write(html_template)
    # print(f'{file_name} saved')

def crop_screenshot(image_path, crop_amount):
    """
    Crop the specified image using the provided crop area.

    Parameters:
    - image_path (str): The path to the image file.
    - crop_area (tuple): The coordinates of the crop area in the format (left, upper, right, lower).
                        Default is (0, 0, 700, 400).

    Returns:
    None

    Raises:
    - Exception: If there is an error while cropping the image.
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            left = crop_amount
            upper = 0  # No cropping from the top
            right = width - crop_amount
            lower = height  # No cropping from the bottom

            crop_area = (left, upper, right, lower)
            cropped_img = img.crop(crop_area)

            cropped_img.save(image_path)
            # print(f"Cropped image saved successfully as '{image_path}'.")
    except Exception as e:
        print(f"Failed to crop image: {e}")

def printCoverPage(config):
    """
    Generates the cover page HTML content.

    :param config: Configuration settings for the cover page.
    :return: HTML content for the cover page.
    """
    title = config['title'] if 'title' in config else 'Null'
    description = config['description'] if 'description' in config else 'Null'
    date = datetime.datetime.now().strftime("%d/%b/%Y")
    coverTemplate = config['template'] if 'template' in config and config['template'] != None else '5dad0c10-4f06-bec2-e52d-66c2dffd135c'

    with open('images/coverImage.png', 'rb') as img_file:
        coverImage = base64.b64encode(img_file.read()).decode('utf-8')

    context = {'title': title, 'description': description, 'date': date, 'cover_image': coverImage}

    # template_loader = jinja2.FileSystemLoader('./')
    # template_env = jinja2.Environment(loader=template_loader)
    # html_template = 'templates/defaultCoverPage.html'
    # template = template_env.get_template(html_template)
    
    env = Environment()
    templateContent = retrieveHTMLTemplate(coverTemplate).replace(
                'id="coverImage"', 'src="data:image/png;base64,{{cover_image}}"'
            ).replace('NEWLINE','&nbsp;')
    template = env.from_string(templateContent)
    
    output_text = template.render(context)

    return output_text

def printTable(data, config, start_page):
    """
    Generates HTML content for a table.

    :param data: Data for the table.
    :param config: Configuration settings for the table.
    :param start_page: Starting page number for the table.
    :return: HTML content for the table.
    """
    df = pd.DataFrame(data)
    include_row_numbers = config['includeRowNumbers'] if 'includeRowNumbers' in config else False

    if pageOrientation == 'Landscape':
        rows_per_page = 25
    elif pageOrientation == 'Portrait':
        rows_per_page = 40 
        
    num_pages = max(1, -(-len(df) // rows_per_page))  

    # template_name = config['template'] if 'template' in config else 'defaultTable'
    # template_loader = FileSystemLoader('./')
    # template_env = Environment(loader=template_loader)
    # template = template_env.get_template('templates/portraitTable.html')
    env = Environment()
    templateContent = retrieveHTMLTemplate(config['template']).replace(
                'id="icon"', 'src="file:///home/rundeck/projects/RulesInterpreterApp02/images/logoFull.png"'
            )
    template = env.from_string(templateContent)

    html_content = ""
    current_page = start_page
    for page in range(num_pages):
        start_index = page * rows_per_page
        end_index = start_index + rows_per_page
        page_df = df.iloc[start_index:end_index]

        if include_row_numbers:
            table_html = page_df.to_html(classes='my_table_class', index=False, border=0)
        else:
            table_html = page_df.to_html(classes='my_table_class', index=False, border=0)

        rendered_html = template.render(table=table_html, page_number=current_page, heading=config['tableName'], include_row_numbers=include_row_numbers)
        html_content += rendered_html
        current_page += 1 

    return html_content, current_page 

async def printPie(response, config, start_page):
    """
    Generate a pie chart, capture a screenshot, and return the rendered HTML.

    Args:
        response: The response data.
        config: The configuration data.
        start_page: The starting page number.

    Returns:
        A tuple containing the rendered HTML and the next page number.
    """

    # Generate chart.html with data
    await insert_data_into_HTML(response, 'pie', config['tableTitle'])
    unique_id = str(uuid.uuid4())[:8]
    chart_path = f'/var/tmp/piechart_{unique_id}.png'
    # Capture screenshot
    await capture_screenshot(chart_path, 'templates/pie_chart.html', "pie")

    pageNumber = start_page

    # env = Environment(loader=FileSystemLoader('.'))
    # template_name = config['template'] if 'template' in config else 'defaultLine'
    # template = env.get_template('templates/defaultPie.html')
    
    env = Environment()
    templateContent = retrieveHTMLTemplate(config['template']).replace(
                "id=\"icon\"", "src=\"file:///home/rundeck/projects/RulesInterpreterApp02/images/logoFull.png\""
            ).replace(
                'id="graph"', f'src="file://{chart_path}"'
            )
            
    if pageSize == 'Letter':
        templateContent = templateContent.replace('PAGESIZE', '690px')
        templateContent = templateContent.replace('PORTSIZE', '800px')
    elif pageSize == 'A4':
        templateContent = templateContent.replace('PAGESIZE', '660px')
        templateContent = templateContent.replace('PORTSIZE', '980px')
        
    template = env.from_string(templateContent)
    
    rendered_html = template.render(page_number=pageNumber, heading=config['tableName'])

    return rendered_html, start_page + 1

async def printLine(response, config, start_page):
    """
    Generate a line chart, capture a screenshot, and render the chart into an HTML template.

    Args:
        response: The response object.
        config: A dictionary containing configuration options.
        start_page: The starting page number.

    Returns:
        A tuple containing the rendered HTML and the updated start page number.
    """

    chart_type = 'line'
    unique_id = str(uuid.uuid4())[:8]
    chart_path = f'/var/tmp/linechart_{unique_id}.png'
    # Generate chart.html with data
    await insert_data_into_HTML(response, chart_type, config['tableTitle'])

    # Capture screenshot
    await capture_screenshot(chart_path, 'templates/line_chart.html', "line")

    pageNumber = start_page

    # env = Environment(loader=FileSystemLoader('.'))
    # template_name = config['template'] if 'template' in config else 'defaultLine'
    # template = env.get_template('templates/' + template_name + '.html')
    
    env = Environment()
    templateContent = retrieveHTMLTemplate(config['template']).replace(
                'id="icon"', 'src="file:///home/rundeck/projects/RulesInterpreterApp02/images/logoFull.png"'
            ).replace(
                'id="graph"', f'src="file://{chart_path}"'
            )
            
    if pageSize == 'Letter':
        templateContent = templateContent.replace('PAGESIZE', '690px')
        templateContent = templateContent.replace('PORTSIZE', '800px')
    elif pageSize == 'A4':
        templateContent = templateContent.replace('PAGESIZE', '660px')
        templateContent = templateContent.replace('PORTSIZE', '980px')
        
    template = env.from_string(templateContent)
    
    rendered_html = template.render(page_number=pageNumber, heading=config['tableName'])

    return rendered_html, start_page + 1

async def printBar(response, config, start_page):
    """
    Generate a bar chart, capture a screenshot, and return the rendered HTML.

    Args:
        response: The response object.
        config: A dictionary containing configuration options.
        start_page: The starting page number.

    Returns:
        A tuple containing the rendered HTML and the next page number.
    """

    chart_type = 'bar'
    # Generate chart.html with data
    unique_id = str(uuid.uuid4())[:8]
    chart_path = f'/var/tmp/barchart_{unique_id}.png'

    await insert_data_into_HTML(response, chart_type, config['tableTitle'])

    # Capture screenshot
    await capture_screenshot(chart_path, 'templates/bar_chart.html', "bar")

    pageNumber = start_page

    # env = Environment(loader=FileSystemLoader('.'))
    # template_name = config['template'] if 'template' in config else 'defaultBar'
    # template = env.get_template('templates/' + template_name + '.html')
    
    env = Environment()
    templateContent = retrieveHTMLTemplate(config['template']).replace(
                'id="icon"', 'src="file:///home/rundeck/projects/RulesInterpreterApp02/images/logoFull.png"'
            ).replace(
                'id="graph"', f'src="file://{chart_path}"'
            )
            
    if pageSize == 'Letter':
        templateContent = templateContent.replace('PAGESIZE', '690px')
        templateContent = templateContent.replace('PORTSIZE', '800px')
    elif pageSize == 'A4':
        templateContent = templateContent.replace('PAGESIZE', '660px')
        templateContent = templateContent.replace('PORTSIZE', '980px')

    template = env.from_string(templateContent)
    
    rendered_html = template.render(page_number=pageNumber, heading=config['tableName'])

    return rendered_html, start_page + 1

async def printDonut(response, config, start_page):
    """
    Generate a donut chart, capture a screenshot, and return the rendered HTML.

    Args:
        response: The response data.
        config: The configuration data.
        start_page: The starting page number.

    Returns:
        A tuple containing the rendered HTML and the next page number.
    """

    chart_type = 'donut'
    # Generate chart.html with data, uuid for giving the chart's unique id to distinguish from the same ones
    unique_id = str(uuid.uuid4())[:8]                           
    chart_path = f'/var/tmp/donutchart_{unique_id}.png'
    await insert_data_into_HTML(response, chart_type, config['tableTitle'])

    # Capture screenshot
    await capture_screenshot(chart_path, 'templates/donut_chart.html', "donut")

    pageNumber = start_page

    # env = Environment(loader=FileSystemLoader('.'))
    # template_name = config['template'] if 'template' in config else 'defaultDonut'
    # template = env.get_template('templates/' + template_name + '.html')
    
    env = Environment()
    templateContent = retrieveHTMLTemplate(config['template']).replace(
                'id="icon"', 'src="file:///home/rundeck/projects/RulesInterpreterApp02/images/logoFull.png"'
            ).replace(
                'id="graph"', f'src="file://{chart_path}"'
            )
            
    if pageSize == 'Letter':
        templateContent = templateContent.replace('PAGESIZE', '690px')
        templateContent = templateContent.replace('PORTSIZE', '800px')
    elif pageSize == 'A4':
        templateContent = templateContent.replace('PAGESIZE', '660px')
        templateContent = templateContent.replace('PORTSIZE', '980px')
        
    template = env.from_string(templateContent)
    
    rendered_html = template.render(page_number=pageNumber, heading=config['tableName'])

    return rendered_html, start_page + 1

async def printScreenshot(config, start_page):
    """
    Generate a screenshot page, process it, and return the rendered HTML along with the next page number.
    """
    browser = await launch(headless=True, args=['--no-sandbox', '--headless', '--disable-gpu'])

    try:
        page = await browser.newPage()
        await page.setViewport({'width': 1920, 'height': 1080})
        unique_id = str(uuid.uuid4())[:8]

        # If 'loginURL' is provided, attempt login.
        if 'loginURL' in config and config['loginURL']:
            print("\t\tOpening the login page")
            await page.goto(config['loginURL'], timeout=600000, waitUntil='networkidle0')

            # Attempt to locate username field.
            username_field_appeared = False
            for selector in [
                'input[type="email"]',
                'input[name="user"]',
                'input[type="text"][id*="username"]',
                'input[type="text"][name*="username"]',
                'input[type="text"][id*="email"]',
                'input[type="text"][name*="email"]',
                'input[type="text"][id*="login"]',
                'input[type="text"][name*="login"]',
                'input[type="text"][id*="user"]',
                'input[type="text"][name*="user"]',
                'input[type="text"][id*="userid"]',
                'input[type="text"][name*="userid"]',
                'input[type="text"][id*="usr"]',
                'input[type="text"][name*="usr"]',
                'input[type="text"][id*="uname"]',
                'input[type="text"][name*="uname"]',
                'input[type="text"][id*="loginid"]',
                'input[type="text"][name*="loginid"]',
                'input[type="text"][id*="name"]',
                'input[type="text"][name*="name"]'
            ]:
                try:
                    await page.waitForSelector(selector, timeout=20000)
                    username_field_appeared = True
                    break
                except Exception:
                    continue

            if not username_field_appeared:
                button_selector = 'button[data-test-subj="loginCard-basic/cloud-basic"]'
                button = await page.querySelector(button_selector)
                if button:
                    await button.click()
                else:
                    print("Username field did not appear.")

            # Attempt to fill password field.
            password_field_appeared = False
            for selector in [
                'input[type="password"]',
                'input[name="password"]',
                'input[type="password"][id*="password"]',
                'input[type="password"][name*="password"]',
                'input[type="password"][id*="pass"]',
                'input[type="password"][name*="pass"]',
                'input[type="password"][id*="pwd"]',
                'input[type="password"][name*="pwd"]',
                'input[type="password"][id*="secret"]',
                'input[type="password"][name*="secret"]',
                'input[type="password"][id*="passwd"]',
                'input[type="password"][name*="passwd"]'
            ]:
                try:
                    await page.waitForSelector(selector, timeout=20000)
                    password_field_appeared = True
                    break
                except Exception:
                    continue

            if not password_field_appeared:
                print("Password field did not appear.")

            # Helper functions to fill in the username and password fields.
            async def fill_field(selectors, value, field_name):
                for selector in selectors:
                    try:
                        element = await page.querySelector(selector)
                        if element:
                            await page.type(selector, value, {'delay': 50})
                            return True
                    except Exception:
                        continue
                print(f"{field_name} field not found.")
                return False

            username_selectors = [
                'input[type="email"]',
                'input[name="user"]',
                'input[type="text"][id*="username"]',
                'input[type="text"][name*="username"]',
                'input[type="text"][id*="email"]',
                'input[type="text"][name*="email"]',
                'input[type="text"][id*="login"]',
                'input[type="text"][name*="login"]',
                'input[type="text"][id*="user"]',
                'input[type="text"][name*="user"]',
                'input[type="text"][id*="userid"]',
                'input[type="text"][name*="userid"]',
                'input[type="text"][id*="usr"]',
                'input[type="text"][name*="usr"]',
                'input[type="text"][id*="uname"]',
                'input[type="text"][name*="uname"]',
                'input[type="text"][id*="loginid"]',
                'input[type="text"][name*="loginid"]',
                'input[type="text"][id*="name"]',
                'input[type="text"][name*="name"]'
            ]
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[type="password"][id*="password"]',
                'input[type="password"][name*="password"]',
                'input[type="password"][id*="pass"]',
                'input[type="password"][name*="pass"]',
                'input[type="password"][id*="pwd"]',
                'input[type="password"][name*="pwd"]',
                'input[type="password"][id*="secret"]',
                'input[type="password"][name*="secret"]',
                'input[type="password"][id*="passwd"]',
                'input[type="password"][name*="passwd"]'
            ]
            username_filled = await fill_field(username_selectors, config['username'], "Username")
            password_filled = await fill_field(password_selectors, config['password'], "Password")

            if username_filled and password_filled:
                try:
                    login_buttons = await page.xpath(
                        "//button["
                        "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login') or "
                        "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in') or "
                        "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'signin') or "
                        "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')"
                        "]"
                    )
                    if login_buttons:
                        await login_buttons[0].click()
                        print("\t\tLogged in successfully")
                        print("\t\tWaiting for page load...")
                        await page.waitForNavigation(timeout=120000, waitUntil='networkidle0')
                    else:
                        print("Login button not found.")
                except Exception:
                    print("Login took too long to respond. Please check the login credentials.")
            else:
                print("Could not fill all required fields.")

        else:
            print("\t\tNo login URL provided. Skipping login step.")

        url = config['targetURL']
        print(f"\t\tNavigating to {url}...")
        await page.goto(url, timeout=900000)

        try:
            await page.waitForSelector('body', timeout=600000)
        except Exception:
            print("Main content did not load in time.")

        # Define a unique screenshot file path.
        screenshot_path = f'/var/tmp/{config["tableName"]}_screenshot{unique_id}.png'

        # Find the largest scrollable element.
        largest_scrollable_element = await page.evaluate('''() => {
            function getScrollableElement() {
                let maxVisibleHeight = 0;
                let largestElement = document.body;

                function checkScrollable(node) {
                    const rect = node.getBoundingClientRect();
                    if (rect.height > 0 && node.scrollHeight > node.clientHeight) {
                        const visibleHeight = rect.height;
                        if (visibleHeight > maxVisibleHeight) {
                            maxVisibleHeight = visibleHeight;
                            largestElement = node;
                        }
                    }
                }

                function walkDOM(node) {
                    checkScrollable(node);
                    for (let i = 0; i < node.children.length; i++) {
                        walkDOM(node.children[i]);
                    }
                }

                walkDOM(document.body);
                return largestElement;
            }

            const scrollableElement = getScrollableElement();
            const rect = scrollableElement.getBoundingClientRect();
            return {
                tag: scrollableElement.tagName,
                scrollHeight: scrollableElement.scrollHeight,
                width: rect.width,
                height: rect.height,
                selector: scrollableElement.tagName.toLowerCase() +
                          (scrollableElement.id ? "#" + scrollableElement.id : "") +
                          (scrollableElement.className ? "." + scrollableElement.className.replace(/ /g, ".") : "")
            };
        }''')

        scroll_height = largest_scrollable_element['scrollHeight']
        print(f"\t\tDetected largest scrollable element: {largest_scrollable_element['selector']}, scrollHeight: {scroll_height}")

        FULL_PAGE_HEIGHT = 1500  # Adjust as needed.
        if scroll_height < FULL_PAGE_HEIGHT:
            scroll_height = FULL_PAGE_HEIGHT

        await page.setViewport({'width': 1920, 'height': scroll_height})
        # Allow some extra time for the adjustments.
        await asyncio.sleep(2)

        # Capture a screenshot using the dynamically adjusted viewport.
        await page.screenshot({
            'path': screenshot_path,
            'fullPage': False
        })
        print(f"\t\tTook a screenshot of {url}")

        # Close the browser after processing the screenshot.
        # Image processing: crop and split into pages.
        if pageOrientation == 'Portrait':
            PAGE_HEIGHT = 1700
        elif pageOrientation == 'Landscape':
            PAGE_HEIGHT = 1700

        from math import ceil
        with Image.open(screenshot_path) as img:
            width, height = img.size
            num_pages = ceil(height / PAGE_HEIGHT)
            print(f"\t\tScreenshot height: {height}px, splitting into {num_pages} page(s).")
            
            html_pages = ""
            page_number = start_page

            for i in range(num_pages):
                upper = i * PAGE_HEIGHT
                lower = (i + 1) * PAGE_HEIGHT
                if lower > height:
                    lower = height

                bbox = (0, upper, width, lower)
                cropped_img = img.crop(bbox)

                temp_image_path = f'/var/tmp/{config["tableName"]}_screenshot_part{i+1}{unique_id}.png'
                cropped_img.save(temp_image_path)

                # Choose the template depending on orientation.
                if pageOrientation == 'Landscape':
                    templateID = 'a57000ba-cca7-b074-3198-66ceef65c189'
                elif pageOrientation == 'Portrait':
                    templateID = '695c88c1-efe2-0750-9b38-66fb79f45eaa'

                env = Environment()
                templateContent = retrieveHTMLTemplate(templateID).replace(
                    'id="icon"', f'src="file://{os.getcwd()}/images/logoFull.png"'
                ).replace(
                    'id="graph"', f'src="file://{temp_image_path}"'
                )
                
                if pageSize == 'Letter':
                    templateContent = templateContent.replace('PAGESIZE', '880px').replace('PORTSIZE', '1550px')
                elif pageSize == 'A4':
                    templateContent = templateContent.replace('PAGESIZE', '850px').replace('PORTSIZE', '1730px')
                    
                template = env.from_string(templateContent)
                rendered_html = template.render(page_number=page_number, heading=config['tableName'])
                html_pages += rendered_html
                page_number += 1

        return html_pages, page_number

    except Exception as e:
        print(f"Error in printScreenshot: {e}")
        return "", start_page  # Return an empty string and unchanged page number on error.
    
    finally:
        await browser.close()
        print("\t\tBrowser closed")

def printIndex(index_content, config):
    """
    Generates the index page HTML content.

    :param index_content: A list of tuples containing section titles and their start page numbers.
    :return: HTML content for the index page.
    """
    tables_list = [[title, f"Page {start}" if start == end else f"Pages {start} - {end}"] for title, (start, end) in index_content.items()]
    indexTemplate = config['template'] if 'template' in config and config['template'] != None else '16e000a5-e417-4be6-f5a9-66c2e0744402'

    with open('images/logoFull.png', 'rb') as logo_file:
        logo = base64.b64encode(logo_file.read()).decode('utf-8')

    # templateName = config['template'] if 'template' in config else 'defaultIndex'
    # template_loader = FileSystemLoader('./')
    # template_env = Environment(loader=template_loader)
    # template = template_env.get_template('templates/'+templateName+'.html')
    
    env = Environment()
    templateContent = retrieveHTMLTemplate(indexTemplate).replace(
                'id="icon"', 'src="data:image/png;base64,{{ icon }}"'
            ).replace(
                '<tr id="startFor"></tr>', '{% for table in tables %}'
            ).replace(
                '<tr id="endFor"></tr>', '{% endfor %}'
            )
    template = env.from_string(templateContent)
    
    rendered_html = template.render(tables=tables_list, page_number=2, icon=logo)

    return rendered_html

def printClose(config):
    """
    Generates HTML content for the closing page.

    :param config: Configuration settings for the closing page.
    :return: HTML content for the closing page.
    """
    template_loader = jinja2.FileSystemLoader('./')
    template_env = jinja2.Environment(loader=template_loader)
    indexTemplate = config['template'] if 'template' in config and config['template'] != None else '69624102-595c-f08f-6b86-66c2df2a615f'

    with open('images/logoFull.png', 'rb') as logo_file:
        logo = base64.b64encode(logo_file.read()).decode('utf-8')

    # templateName = config['template'] if 'template' in config else 'defaultClose'
    # html_template = 'templates/portrait.html'

    # template = template_env.get_template(html_template)
    
    env = Environment()
    templateContent = retrieveHTMLTemplate(indexTemplate).replace(
                'id="icon"', 'src="file:///home/rundeck/projects/RulesInterpreterApp02/images/logoFull.png"'
            )
    template = env.from_string(templateContent)
    
    output_text = template.render()

    return output_text

async def main(filename, emailArguments):
    """
    Main function to execute the report generation process.

    :param filename: The filename directory for the config file.
    :type filename: str
    :param emailArguments: The email arguments for sending the generated report.
    :type emailArguments: str
    """
    config = readConfig(filename)
    
    config = convert_yaml(config) 
    
    reportName = config['mainConfig']['reportName'] if 'reportName' in config['mainConfig'] else 'Report-{{yy-mm-dd}}'
    current_date = datetime.datetime.now().strftime("%y-%m-%d")
    formattedReportName = reportName.replace('{{yy-mm-dd}}', current_date)
    formattedReportName = str(datetime.datetime.now())+"_"+formattedReportName
    global pageOrientation,pageSize
    pageOrientation = config['mainConfig']['orientation'] if 'orientation' in config['mainConfig'] else 'Landscape'
    pageSize = config['mainConfig'].get('pageSize', 'Letter')
    if not pageSize:
        pageSize = 'Letter'
    # pageOrientation = 'Portrait'
    # pageSize = 'Letter'
    cover_page_html = ""
    subsequent_content = ""
    index_html = ""
    close_html = ""
    current_page = 3  
    index_content = {}
    
    if pageOrientation != 'Portrait' and pageOrientation != 'Landscape':
        print("Invalid page orientation. Defaulting to Landscape.")
        pageOrientation = 'Landscape'
        
    print("Retrieving data from the database...")
    reports = retrieveReports(config)
    print("\tData retrieved.")
    
    print("Generating report pages...")
    for key, data in reports.items():
        if key[0] == 'printTable':
            print("\tGenerating Table:",config['printTable'][key[1]]['tableTitle'])
            table_html, next_page = printTable(data, config['printTable'][key[1]], current_page)
            subsequent_content += table_html
            index_content[config['printTable'][key[1]]['tableName']] = (current_page, next_page - 1)
            current_page = next_page
        elif key[0] == 'printPie':
            print("\tGenerating Pie Chart:",config['printPie'][key[1]]['tableTitle'])
            pie_html, next_page = await printPie(data, config['printPie'][key[1]], current_page)
            subsequent_content += pie_html
            index_content[config['printPie'][key[1]]['tableName']] = (current_page, next_page - 1)
            current_page = next_page
        elif key[0] == 'printLine':
            print("\tGenerating Line Chart:",config['printLine'][key[1]]['tableTitle'])
            line_html, next_page = await printLine(data, config['printLine'][key[1]], current_page)
            subsequent_content += line_html
            index_content[config['printLine'][key[1]]['tableName']] = (current_page, next_page - 1)
            current_page = next_page
        elif key[0] == 'printBar':
            print("\tGenerating Bar Chart:",config['printBar'][key[1]]['tableTitle'])
            bar_html, next_page = await printBar(data, config['printBar'][key[1]], current_page)
            subsequent_content += bar_html
            index_content[config['printBar'][key[1]]['tableName']] = (current_page, next_page - 1)
            current_page = next_page
        elif key[0] == 'printDonut':
            print("\tGenerating Donut Chart:",config['printDonut'][key[1]]['tableTitle'])
            donut_html, next_page = await printDonut(data, config['printDonut'][key[1]], current_page)
            subsequent_content += donut_html
            index_content[config['printDonut'][key[1]]['tableName']] = (current_page, next_page - 1)
            current_page = next_page
            
    for key, data in config.items():
        if key == "printScreenshot":
            for conf in data:
                print("\tGenerating Screenshot Page:",conf['tableName'])
                screenshot_html, next_page = await printScreenshot(conf, current_page)
                subsequent_content += screenshot_html
                index_content[conf['tableName']] = (current_page, next_page - 1)
                current_page = next_page

    if 'printCoverPage' in config:
        cover_page_html = printCoverPage(config['printCoverPage'])
    else:
        cover_page_html = printCoverPage({})
    if 'printIndex' in config:
        index_html = printIndex(index_content, config['printIndex'])
    else:
        index_html = printIndex(index_content,{})
    if 'printClose' in config:
        close_html = printClose(config['printClose'])
    else:
        close_html = printClose({})
    
    all_html_content = cover_page_html + index_html + subsequent_content + close_html
    all_html_content = all_html_content.replace('<!DOCTYPE html>','').replace('<html>','').replace('<head>','').replace('<body>','').replace('</head>','').replace('</body>','').replace('</html>','').replace('BLANK','')
    print("\tDone Generating.")

    print("Converting to PDF...")
    options = {'page-size': pageSize, 'orientation': pageOrientation, 'enable-local-file-access': ''}
    # pdf_config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
    pdfkit.from_string(all_html_content, '/var/tmp/'+formattedReportName+'.pdf', options=options)
    # pdfkit.from_string(all_html_content, formattedReportName+'.pdf', options=options)
    print("\tPDF Created.")

    emailArguments = emailArguments.replace("'", '"').replace("None", "null")
    emailArguments = json.loads(emailArguments)
    emailArguments['to'] = emailArguments['to'].strip(',') 
    if emailArguments['to'] != "":
        print("Sending email...")
        sendEmail(emailArguments,formattedReportName,'/var/tmp/'+formattedReportName+'.pdf')
        print("\tEmail Sent.")

if __name__ == "__main__":
    filename = sys.argv[1]
    emailArguments = sys.argv[2]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main(filename, emailArguments))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
# vijay