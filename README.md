# jb_data_projects

This Repo is used for data projects as a portfolio of my work.

Ideas:
- Data Quality Framework --> Create UDF that automatically checks: Nulls, duplicates, regex patterns, ranges, foreign keys, date formats, uniqueness and produces a Report (HTML, CSV, JSON)
- Metadata driven ETL Framework --> Use YAML file where someone simply writes: Source, Destination, Table, Validation
                                    Framework would: Extract data, validate it, logs everything, has retries failures, loads data to destination, sends alerts
- Pipeline health Dashboard --> Connect up to ADF, Databricks, Synapse or something similar to see: Pipeline success (%) (Per week/month...), Avg run time, failures, cost, alerts
- Data Dictionary Generator --> Point it to SQL Server, Snowflake... and it automatically generates Excel file with relationships, descriptions and statistics

Contains 3 areas with the src folder
1. intergrations
2. ML Model Projects
3. Scripts

As of 30/06/2026

**Within Integrations**
1. Automated email
Uses Azure Service Principal (OAuth) as the connection keys to sign into Microsoft Graph, then has the ability to send emails with or without an attachment to automate report sending using UDF "send_email". Restirctions are put in place to ensure only emails that are within a specific Azure group, that emails can send from.

2. SharePoint Integration
Successfully integrated to multiple sharepoint sites allowing integrations of SharePoint lists or files including CSV, XLSX, PDF. This uses Microsoft Graph as the authenticator, where configurations have been made to the site to enable permissions to the service principal to allow read, write or whatever permissions are necessary for the use case. Connected up to 4 SharePoint Sites.

3. Web Scraping
Project 1 - Downloads a PDF file based on a file pattern from the href in the source code to match any version in a dynamic URL string
Project 2 - Downloads a XLSX file based on a file pattern from the href in the source code to match on incrementing file version

**Within ML Model Projects**
1. AI - RAG (Retrieval Augmented Generation)
Built an AI RAG model that uses factual information inputted and verified by users/colleagues that is able to be used to support within business use case scnearios. E.g. ChatBots, Colleague onboarding etc... 

2. Image classification - Fruit and Vegetables
Created a CNN (Convolutional Neural Network) model, that identifies fruit and vegetables. Has 36 different classes to choose from and the model will return the classification of the image chosen and its confidence in it's decision making. Uses Tensorflow Keras in this CNN model. 

3. NLP - Topic Modelling
This compares the Topic modelling techniques LDA, LSA, HDP against Covid 19 Tweets. This project was very successful giving 91% in University scoring and the professor recommending this to be submitted as a journal article. Author of Journal Article published on IGI Global - https://www.igi-global.com/gateway/article/292445

4. Predictive - Gas Sites
First "proper" project using ML predictive models, used Linear regression on time series data to predict gas consumption usage for the next 60 days.

5. Predictive - T Shirt Sizing
A home based project where user's would input their height (CM) and weight (KG) and it would output a predicted the T Shirt size for the user. Upon user input, it would save and incrementally learn from the user inputs.

**Within Scripts**
1. UDF: Reading files from Blob storage. Having the ability to connect and read from Azure Data Lake Storage.
