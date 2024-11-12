using Microsoft.Extensions.Logging;
using Microsoft.Data.SqlClient;
using System.Data;
using Dapper;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Extensions.Sql;
using Azure.AI.OpenAI;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace ProductRecommender.RequestHandler;

public class Item 
{
    public required int ProductId { get; set; }

    public override bool Equals(object? obj)
    {
        if (obj is null) return false;
        if (obj is not Item that) return false;         
        return ProductId == that.ProductId;
    }

    public override int GetHashCode()
    {
        return ProductId.GetHashCode();
    }

    public override string ToString()
    {
        return ProductId.ToString();
    }
}

public class Product: Item
{
    public string? ProductName { get; set; }

    public string? Description { get; set; }       
}


public class ChangedItem: Item 
{
    public SqlChangeOperation Operation { get; set; }        
    public required string Payload { get; set; }
}

public class ProductProcessor(OpenAIClient openAIClient, SqlConnection conn, ILogger<ProductProcessor> logger)
{
    private readonly string _openAIDeploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME") ?? "embeddings";

    [Function(nameof(ProductTrigger))]
    public async Task ProductTrigger(
        [SqlTrigger("[dbo].[Products]", "FABRIC_SQL_CONNECTION_STRING")]
        IReadOnlyList<SqlChange<Product>> changes
        )
    {
        var ci = from c in changes 
                    where c.Operation != SqlChangeOperation.Delete 
                    select new ChangedItem() { 
                        ProductId = c.Item.ProductId, 
                        Operation = c.Operation, 
                        Payload = c.Item.ProductName + ' ' + c.Item.Description                       
                    };

        await ProcessChanges(ci, "dbo.Products", "dbo.update_product_embeddings", logger);
    }

    private async Task ProcessChanges(IEnumerable<ChangedItem> changes, string referenceTable, string upsertStoredProcedure, ILogger logger)
    {
        var ct = changes.Count();
        if (ct == 0) {
            logger.LogInformation($"No useful changes detected on {referenceTable} table.");
            return;
        }

        logger.LogInformation($"There are {ct} changes that requires processing on table {referenceTable}.");

        foreach (var change in changes)
        {
            logger.LogInformation($"[{referenceTable}:{change.ProductId}] Processing change for operation: " + change.Operation.ToString());

            var attempts = 0;
            var embeddingsReceived = false;
            while (attempts < 3)
            {
                attempts++;

                logger.LogInformation($"[{referenceTable}:{change.ProductId}] Attempt {attempts}/3 to get embeddings.");

                var response = await openAIClient.GetEmbeddingsAsync(
                    new EmbeddingsOptions(_openAIDeploymentName, [change.Payload])
                );

                var e = response.Value.Data[0].Embedding;
                await conn.ExecuteAsync(
                    upsertStoredProcedure,
                    commandType: CommandType.StoredProcedure,
                    param: new
                    {
                        @id = change.ProductId,
                        @embedding = JsonSerializer.Serialize(e)
                    });
                embeddingsReceived = true;

                logger.LogInformation($"[{referenceTable}:{change.ProductId}] Done.");                

                break;
            }
            if (!embeddingsReceived)
            {
                logger.LogInformation($"[{referenceTable}:{change.ProductId}] Failed to get embeddings.");
            }
        }
    }
}

