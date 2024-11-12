create or alter procedure [dbo].[update_product_embeddings]
@id int,
@embedding nvarchar(max)
as
begin
    merge dbo.ProductEmbeddings as target
    using (select @id as ProductId, cast(@embedding as vector(1536)) as embedding) as source
    on (target.ProductId = source.ProductId)
    when matched then
        update set embedding = source.embedding
    when not matched then
        insert (ProductId, embedding)
        values (source.ProductId, source.embedding);
end
GO