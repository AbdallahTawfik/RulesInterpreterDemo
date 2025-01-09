# Rule Builder Documentation

## Table of Contents

- [Actions](#-actions)
    - [Function](#-function)
    - [Integration](#-integration)
    - [Module](#-module)
    - [Import](#-import)
    - [Report](#-report)
        - [Config](#-config)
        - [CoverPage](#-coverpage)
        - [Index](#-index)
        - [Table](#-table)
        - [Pie](#-pie)
        - [Donut](#-donut)
        - [Line](#-line)
        - [Bar](#-bar)
        - [Close](#-close)
        - [Screenshot](#-screenshot)
        - [Other](#-other)
- [Conditions](#-conditions)
    - [If](#-if)
    - [Ifany](#-ifany)
    - [Ifall](#-ifall)

# Actions

<!-- ============================================================= -->

## Function

#### Click [here](https://app02.opexpert.com/index.php?module=bc_rule_builder&offset=7&stamp=1726651071049355600&return_module=bc_rule_builder&action=EditView&record=5bfd5556-19e2-613b-5d85-66c8535abd25) for Use Case link

### Inputs

- **Alias:** This is a required parameter to store the function name under an alias to refer to later.
- **Select API Function:** Allows the selection of readily made python functions, within the OpExpert database, to ease automation.
- **Input Dropdown:** If the selected function requires input then you can select the input(s) through the dropdown. If not then leave blank.
    > [!NOTE]
    > Input dropdown is not currently working with this Rule Builder version. Please refer to the [Known Issues](#known-issues) section below
- **Output Field:** Provides the list of outputs expected for the selected function. If output is `null` then no output will be returned from the selected function

### Creating a function

#### To create a function click [here](https://app02.opexpert.com/index.php?module=bc_api_methods&action=EditView&return_module=bc_api_methods&return_action=DetailView)

#### Arguments needed to create a function:
- **Name:** As expected, the name of the function being created
    > [!NOTE]
    > Do not add any single quotes `'` or double-quotes `"` to the function name.
- **Used Variables (Function Inputs):** Enter `null` if the function being written does not require any inputs. If it does then enter input name(s) and separate them using a comma if multiple inputs are required.
- **Function Alias (Function Outputs):** Enter `null` if the function being written does not require any outputs. If it does then enter output name(s) and separate them using a comma if multiple outputs are required.
    > [!NOTE]
    > If the function has an output, add a `return` statement within the code snippet that has the required outputs (naming should be the same as how it was written in the `Function Outputs` section)
- **Code Snippet:** Type python code as it would be written within a function

### Known Issues

- If a function contains input arguments then create a new `Key/Val` and define it as such: 
    - `Key` should be `InputVars`
    - `Value` should be written in dictionary style format, for example `{ input_date: 06/01/2024 }` or `{ input_date: a.yesterday_str }` for addressing predefined outputs. Please refer to the [Use Case](https://app02.opexpert.com/index.php?module=bc_rule_builder&offset=7&stamp=1726651071049355600&return_module=bc_rule_builder&action=EditView&record=5bfd5556-19e2-613b-5d85-66c8535abd25) for further clarification.
    > [!IMPORTANT]
    > Make sure to remove the single quotes `'` from the YAML Editor Panel surrounding the defined inputs. Any updates made to the rule builder will override this change, so make sure to remove the single quotes `'` after everything is done.

<!-- ============================================================= -->

## Integration

#### Click [here](https://app02.opexpert.com/index.php?module=bc_rule_builder&offset=6&stamp=1726651071049355600&return_module=bc_rule_builder&action=EditView&record=c9ee9261-0ea2-ad4f-6f68-66c9aea690ff) for Use Case link

### Inputs

- **Alias:** This is a required parameter to store the integration name under an alias to refer to later.
- **Select Integration:** Allows the selection of readily made reports, within the OpExpert database.
> [!NOTE]
> Some integrations require parameters

If so, then select `Add Parameters` button and enter all required parameters.<br><br>
For custom input parameters create a new `Key/Val` and define it as such: 
- `Key` should be `UserInputVars`
- `Value` should be written in dictionary style format, for example `{ $from: "06/01/2024" }` or `{ $from: a.yesterday_str }` for addressing predefined outputs. Please refer to step 4 in the [Use Case](https://app02.opexpert.com/index.php?module=bc_rule_builder&offset=6&stamp=1726651071049355600&return_module=bc_rule_builder&action=EditView&record=c9ee9261-0ea2-ad4f-6f68-66c9aea690ff) for further clarification.<br>

    > [!IMPORTANT]
    > Make sure to remove the single quotes `'` from the YAML Editor Panel surrounding the defined inputs. Any updates made to the rule builder will override this change, so make sure to remove the single quotes `'` after everything is done.

<!-- ============================================================= -->

## Module

#### Click [here](https://app02.opexpert.com/index.php?module=bc_rule_builder&offset=5&stamp=1726651071049355600&return_module=bc_rule_builder&action=EditView&record=5b2bad0a-65fe-3b19-97e9-66c9afb38787) for Use Case link

### Inputs

- **Select Module Dropdown:** Allows the selection of modules within the OpExpert database.
- **Alias:** This is a required parameter to store the module name under an alias to refer to later.
- **Select Value Dropdown:** Allows the selection of module value within the OpExpert database.
- **Select Attribute(s) Dropdown:** Allows the selection of attributes that are assigned to the value.

<!-- ============================================================= -->

## Import

#### Click [here](https://app02.opexpert.com/index.php?module=bc_rule_builder&offset=4&stamp=1726651071049355600&return_module=bc_rule_builder&action=EditView&record=17919ecd-e8d7-840f-4d45-66c9b2442e99) for Use Case link

`import` actions can be placed anywhere within the rule. However, it's recommended to include them at the beginning of the rules to ensure their scope availability throughout. This operation exclusively supports **Python packages.**

### Inputs

- **Import Name (import):** Enter the python package name that is being imported. Similarly to `import pi`
- **Package Name (from):** Enter the specific functions, classes, or variables directly from a module. Similarly to `from math import pi` 
- **Alias (as):** Enter a custom name to the given import. Similarly to `from math import pi as p`

<!-- ============================================================= -->

## Report

#### Click [here](https://app02.opexpert.com/index.php?module=bc_rule_builder&offset=8&stamp=1726719475088919300&return_module=bc_rule_builder&action=EditView&record=1b1d074f-6b53-8e82-8063-66c2e19eed93) for Use Case link

### Config

**Inputs**

- **Report Name:** Enter a report name. To include the date that the report was generated on include this `{{yy-mm-dd}}` exact string within the report name, for example: `Report-{{yy-mm-dd}}`
- **Orientation:** Either `Portrait` or `Landscape`
    > [!NOTE]
    > Currently only `Landscape` is supported.
- **PageSize:** Enter `Letter/A4/etc.`
    > [!NOTE]
    > Currently only `Letter` is supported.
---
### CoverPage

**Inputs**

- **Title:** Enter a report title. It will revert to `null` if the title was not provided.
- **Description:** Enter a report description. It will revert to `null` if the description was not provided.
- **Template:** Select a template for the CoverPage.
    > [!NOTE]
    > Currently only `Default Cover Page` is supported.
---
### Index

**Inputs**

- **Template:** Select a template for the Index page.
    > [!NOTE]
    > Currently only `Default Index` is supported.

---
### Table

**Inputs**

- **Alias (Title):** Enter a title for the table.
- **Integration Report:** Select an integration report to be displayed as a table.
- **Template:** Select a template for the table.
    > [!NOTE]
    > Currently only `Default Table` is supported.
---
### Pie

**Inputs**

- **Alias (Title):** Enter a title for the pie chart.
- **Integration Report:** Select an integration report to be displayed as a pie chart.
- **Template:** Select a template for the pie chart.
    > [!NOTE]
    > Currently only `Default Pie Chart` is supported.
---
### Donut

**Inputs**

- **Alias (Title):** Enter a title for the donut chart.
- **Integration Report:** Select an integration report to be displayed as a donut chart.
- **Template:** Select a template for the donut chart.
    > [!NOTE]
    > Currently only `Default Donut Chart` is supported.
---
### Line

**Inputs**

- **Alias (Title):** Enter a title for the line chart.
- **Integration Report:** Select an integration report to be displayed as a line chart.
- **Template:** Select a template for the line chart.
    > [!NOTE]
    > Currently only `Default Line` is supported.
---
### Bar

**Inputs**

- **Alias (Title):** Enter a title for the bar chart.
- **Integration Report:** Select an integration report to be displayed as a bar chart.
- **Template:** Select a template for the bar chart.
    > [!NOTE]
    > Currently only `Default Bar Chart` is supported.
---
### Close

**Inputs**

- **Template:** Select a template for the Close page.
    > [!NOTE]
    > Currently only `Default Close` is supported.
---
### Screenshot

**Inputs**

- **URL (Login URL):** Enter the login URL. Leave blank if login is not needed.
    > [!NOTE]
    > Only websites that have the username and password fields on the same page are supported for now.
- **Username:** Enter the username credential.
- **Password:** Enter the password credential.
- **User Val (Target URL):** Enter the target URL for the screenshot to be taken.
- **Pass Val (Title):** Enter a title for the screenshot page.
- **Submit:** Leave blank
> [!NOTE]
> Default template will be applied. There is no option to select a template at the moment.
---
### Other

> [!NOTE]
> This is currently not in use.
---

<!-- ============================================================= -->

# Conditions

> [!IMPORTANT]
> It is required to close the conditional statement with the `}` after inserting all the necessary steps

<!-- ============================================================= -->

## If

#### Click [here](https://app02.opexpert.com/index.php?module=bc_rule_builder&offset=1&stamp=1726651071049355600&return_module=bc_rule_builder&action=EditView&record=86c23c63-2d15-ace7-b1ab-66c9b853f95b) for Use Case link

This functions as a normal `if` statement in python. It requires a conditional statement with two values and a comparator in the middle, such like `if sizeX > sizeY`.

### Inputs

- **Type of Condition (1st input):** Select `if`
- **Type of Braces (2nd input):** Select `{`
- **First Comparison Value Dropdown (4th input):** Select from a list of outputs provided by previous actions
- **Type of Operator Dropdown (5th input):** Select from a list of operators provided
- **Second Comparison Value (6th input):** Manually enter a value. Enter `ruleAlias.output` to select an output from a previous action or `anyText` for a string

> [!NOTE]
> - To enter custom comparison values in both fields then edit the YAML Editor Panel with the custom fields
> - To add `and/or/not` do the same <br>

Place all the rule steps that are needed within the condition after this condition step.<br>  
After placing them create a new condition step and select `}` (only select this) from the 2nd input options

<!-- ============================================================= -->

## Ifany

#### Click [here](https://app02.opexpert.com/index.php?module=bc_rule_builder&offset=3&stamp=1726651071049355600&return_module=bc_rule_builder&action=EditView&record=d6ab90a4-2ad6-c7bd-5c0f-66c9b7c6f5e4) for Use Case link

This functions as a normal `if` statement in python but is placed within a breakable loop that breaks once the condition is met. Usually used to compare values within an integration for every row stored. For example:
```python
for row in integrationAlias:
    if integrationAlias.rowColumn == "someValue:
        ...
        break
```
It requires a conditional statement with two values and a comparator in the middle, such like `if sizeX > sizeY`.

### Inputs

- **Type of Condition (1st input):** Select `ifany`
- **Type of Braces (2nd input):** Select `{`
- **First Comparison Value Dropdown (4th input):** Select from a list of outputs provided by previous actions
- **Type of Operator Dropdown (5th input):** Select from a list of operators provided
- **Second Comparison Value (6th input):** Manually enter a value. Enter `ruleAlias.output` to select an output from a previous action or `anyText` for a string

> [!NOTE]
> - To enter custom comparison values in both fields then edit the YAML Editor Panel with the custom fields
> - To add `and/or/not` do the same <br>

Place all the rule steps that are needed within the condition after this condition step.<br> 
After placing them create a new condition step and select `}` (only select this) from the 2nd input options

<!-- ============================================================= -->

## Ifall

#### Click [here](https://app02.opexpert.com/index.php?module=bc_rule_builder&offset=2&stamp=1726651071049355600&return_module=bc_rule_builder&action=EditView&record=18005a45-b71f-3bfc-b8c3-66c9b8299cc8) for Use Case link

This functions as a normal `if` statement in python but is placed within a loop that does something every time the condition is met. Usually used to compare values within an integration for every row stored. For example:
```python
for row in integrationAlias:
    if integrationAlias.rowColumn == "someValue:
        ...
```
It requires a conditional statement with two values and a comparator in the middle, such like `if sizeX > sizeY`.

### Inputs

- **Type of Condition (1st input):** Select `ifall`
- **Type of Braces (2nd input):** Select `{`
- **First Comparison Value Dropdown (4th input):** Select from a list of outputs provided by previous actions
- **Type of Operator Dropdown (5th input):** Select from a list of operators provided
- **Second Comparison Value (6th input):** Manually enter a value. Enter `ruleAlias.output` to select an output from a previous action or `anyText` for a string

> [!NOTE]
> - To enter custom comparison values in both fields then edit the YAML Editor Panel with the custom fields
> - To add `and/or/not` do the same <br>

Place all the rule steps that are needed within the condition after this condition step.<br> 
After placing them create a new condition step and select `}` (only select this) from the 2nd input options