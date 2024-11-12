CREATE TABLE [dbo].Products (
    [ProductId] INT IDENTITY(1,1) NOT NULL,
    [ProductName] NVARCHAR(100) NOT NULL,
    [Description] NVARCHAR(255) NULL,
    [Price] DECIMAL(18,2) NOT NULL,
    [Category] NVARCHAR(50) NULL,
    [StockQuantity] INT NOT NULL,
    [CreatedDate] DATETIME NOT NULL DEFAULT GETDATE(),
    PRIMARY KEY CLUSTERED ([ProductId] ASC)
);

CREATE TABLE [dbo].ProductEmbeddings (
    [Id] INT IDENTITY(1,1) NOT NULL,
    [ProductId] INT NOT NULL,
    --Embedding] VARBINARY(8000) NOT NULL,
    [Embedding] VECTOR(1536) NOT NULL,
    PRIMARY KEY CLUSTERED ([Id] ASC)
);

-- need a foreign key from the productid to the product table
ALTER TABLE [dbo].ProductEmbeddings
ADD CONSTRAINT FK_ProductEmbeddings_ProductId
FOREIGN KEY (ProductId)
REFERENCES [dbo].Products (ProductId);

ALTER TABLE [dbo].[Products] ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = OFF);
GO



