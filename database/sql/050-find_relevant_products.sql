create or alter procedure [dbo].[find_relevant_products]
@text nvarchar(max),
@top int = 10,
@min_similarity decimal(19,16) = 0.30
as
if (@text is null) return;


declare @retval int, @qv vector(1536);
--declare @retval int, @qv varbinary(8000);

exec @retval = dbo.get_embedding @text, @qv output;

if (@retval != 0) return;

with cteSimilarEmbeddings as 
(
    select top(@top)
        pe.ProductId as product_id, 
        vector_distance('cosine', pe.[embedding], @qv) as distance
    from 
        dbo.ProductEmbeddings pe
    order by
        distance 
)
select top(@top)
    p.*,
    1-distance as cosine_similarity
from 
    cteSimilarEmbeddings se
inner join 
    dbo.Products p on se.product_id = p.ProductId
where   
    (1-distance) > @min_similarity
order by    
    distance asc;

