### 策略1

您好，接下來要請您行一些資料統計上的任務，分析的檔案是「/home/ubuntu/Nextplace/nextplace/miner/ml/strategies/data_analytics/nextplace_training_data.csv」。

該資料包含所有詳細的房產資料，重要的是包含「listing_price」、「listing_date」、「sale_price」、「sale_date」，我希望您能幫我建置一個 Python 程式，幫我對這些資料進行分析，主要是分析各種變因對於「價格差異率」，價格變異率定義為 (sale_price - listing_price) / listing_price，意思就是真實售價與掛牌價格的差異率。
分析1：各個 market 的價格變異率（幫我統計分析排名各 market 的價格變異率）
分析2：各 sqft 範圍的價格變異率（幫我統計各範圍 sqft 的價格變異率）
分析3：各個 property_type 的價格變異率（幫我統計排名各 property_type 的價格變異率）
分析4：各 year_built 的價格變異率（幫我統計各範圍 year_built 的價格變異率）

也請您將分析的程式全部放置於「/home/ubuntu/Nextplace/nextplace/miner/ml/strategies/data_analytics」這個 Folder 當中。
並用非常清晰的表達方式，讓我能夠馬上了解這些數據。