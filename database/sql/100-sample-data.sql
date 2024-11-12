declare @t as nvarchar(max), @e as vector(1536), @p as int, @n as nvarchar(255), @d as nvarchar(max) 
-- need to loop through all the products and get the embeddings for the ones that don't have it
declare c cursor for select ProductId, ProductName, Description from dbo.Products p WHERE NOT EXISTS (SELECT 1 FROM dbo.ProductEmbeddings WHERE ProductId = p.ProductId)
open c
fetch next from c into @p, @n, @d
while @@fetch_status = 0
begin
    set @t = @n + ' ' + @d
    exec dbo.get_embedding @t, @e output
    insert into dbo.ProductEmbeddings (ProductId, Embedding) select @p, @e
    fetch next from c into @p, @n, @d
end