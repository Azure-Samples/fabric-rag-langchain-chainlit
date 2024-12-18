# SQL Database in Microsoft Fabric, Langchain and Chainlit

This repository contains code that demonstrates a Sample RAG pattern using SQL Database in Microsoft Fabric, Langchain and Chainlit.

## Architecture

![Architecture](./_assets/architecture.png)

## Solution

The solution works locally and in Azure. The solution is composed of three main Azure components:

- [Fabric SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/database/sql-database-paas-overview?view=azuresql): The database that stores the data.
- [Azure Open AI](https://learn.microsoft.com/azure/ai-services/openai/): The language model that generates the text and the embeddings.
- [Azure Functions](https://learn.microsoft.com/azure/azure-functions/functions-overview?pivots=programming-language-csharp): The serverless function to automate the process of generating the embeddings (this is optional for this sample)


### Azure Open AI

Make sure to have two models deployed, one for generating embeddings (*text-embedding-3-small* model recommended) and one for handling the chat (*gpt-4 turbo* recommended). You can use the Azure OpenAI service to deploy the models. Make sure to have the endpoint and the API key ready. The two models are assumed to be deployed with the following names:

- Embedding model: `text-embedding-3-small`
- Chat model: `gpt-4`


### Database

### Database
Create a Fabric SQL Database in your workspace.

![Create Fabric SQL](./_assets/create_fabric_sql.png)

Copy the connection string information as shown below, use  `Data Source` for `Server` and `Initial Catalog` for `Database` while creating your connection string

![Connection String](./_assets/fabric_sql_conn.png)

To deploy the database, you can either use the provided .NET 8 Core console application or deploy it manually.

To use .NET 8 Core console application move into the `/database` and then make sure to create a `.env` file in the `/database` folder starting from the `.env.example` file:

- `MSSQL`: the connection string to the Fabric SQL database where you want to deploy the database objects and sample data
- `OPENAI_URL`: specify the URL of your Azure OpenAI endpoint, eg: 'https://my-open-ai.openai.azure.com/'
- `OPENAI_KEY`: specify the API key of your Azure OpenAI endpoint
- `OPENAI_MODEL`: specify the deployment name of your Azure OpenAI embedding endpoint, eg: 'text-embedding-3-small'

After setting up the configuration in `.env` file, execute the following command to build and run the database project.

 ```PowerShell
    dotnet build .\Database.Deploy.csproj 
    dotnet run
```

If you want to deploy the database manually, make sure to execute the script in the `/database/sql` folder in the order specifed by the number in the file name. Some files (`020-security.sql` and `060-get_embedding.sql`) with have placeholders that you have to replace with your own values:

- `$OPENAI_URL$`: replace with the URL of your Azure OpenAI endpoint, eg: 'https://my-open-ai.openai.azure.com/'
- `$OPENAI_KEY$`: replace with the API key of your Azure OpenAI endpoint
- `$OPENAI_MODEL$`: replace with the deployment name of your Azure OpenAI embedding endpoint, eg: 'text-embedding-3-small'

### Chainlit

Chainlit solution is in `chainlit` folder. Move into the folder, create a virtual environment and install the requirements:

> [!Note]  
> This Chainlit app works best with Python 3.12, While Python 3.13 is supported, additional tool installation may be required to build NumPy from source. Refer to the NumPy documentation for detailed instructions.
https://numpy.org/doc/stable/building/index.html#building-from-source

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

or, on Windows: 

```PowerShell
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```


Then make sure to create a `.env` file in the `/chainlit` folder starting from the `.env.example` file and it with your own values, then run the chainlit solution:

```bash
chainlit run app.py
```

Once the application is running, you'll be able to ask question about your data and get the answer from the Azure OpenAI model. For example you can ask question on the data you have in the database:

```
Looking for a wireless charger any recommendation ?
```

You'll see that Langchain will call the function `get_relevant_products` that behind the scenes connects to the database and exceute the stored procedure `dbo.find_relevant_products` which perform vector search on database data.

#### SQL DB Connection Error

Occasionally, you may encounter a SQL authentication error. In this case, you will need to configure your `.env` file to use a connection token configuration `CONN_TOKEN` for authentication. To generate the token value follow these steps :

Open a terminal window and execute the following `azure cli` command,

```bash
az login
```
Select the subscription and then execute the following command to generate a token,

```bash
az account get-access-token --resource https://database.windows.net
```

> [!Note]                         
> The token expires one hour after it is obtained and must be regenerated.

The RAG process is defined using Langchain's LCEL [Langchain Expression Language](https://python.langchain.com/v0.1/docs/expression_language/) that can be easily extended to include more complex logic, even including complex agent actions with the aid of [LangGraph](https://langchain-ai.github.io/langgraph/), where the function calling the stored procedure will be a [tool](https://langchain-ai.github.io/langgraph/how-tos/tool-calling/?h=tool) available to the agent.


### Azure Functions (optional)

> [!NOTE]  
> Azure functions will operate on existing rows, treating them as `new rows` to generate embeddings.To avoid redundant processing, delete the file `070-update_product_emebddings.sql` during database deployment.

In order to automate the process of generating the embeddings, you can use the Azure Functions. Thanks to [Azure SQL Trigger Binding](https://learn.microsoft.com/azure/azure-functions/functions-bindings-azure-sql-trigger), it is  possible to have tables monitored for changes and then react to those changes by executing some code in the Azure Function itself. As a result it is possible to automate the process of generating the embeddings and storing them in the database.

In a perfect microservices architecture, the Azure Functions are written in C#, but you can easily create the same solutoin using Python, Node.js or any other supported language.

The Azure Functions solution is in the `azure-functions` folder. Move into the folder, then create a `local.settings.json` starting from the provided `local.settings.json.example` file and fill it with your own values. Then execute the following commands to build and run the Azure Function locally (make sure to have the [Azure Function core tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local) installed):

```bash
dotnet build .\FunctionTrigger.csproj
func start
```

the Azure Function will monitor the configured tables for changes and automatically call the Azure OpenAI endpoint to generate the embeddings for the new or updated data.

