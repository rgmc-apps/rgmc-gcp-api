import os
__version__ = os.getenv("API_TAG_VERSION", "0.1.0")
__project_id__ = os.getenv("PROJECT_ID", "RGMC0001")

mssql_server = os.getenv("MSSQL_SERVER", "localhost")
mssql_user = os.getenv("MSSQL_USER", "sa")
mssql_password = os.getenv("MSSQL_PASSWORD", "sqlserver")
mssql_driver = os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server")
mssql_instance = os.getenv("MSSQL_INSTANCE", "") 

bigquery_project_id = os.getenv("BIGQUERY_PROJECT_ID", "default_project")
bigquery_dataset_id = os.getenv("BIGQUERY_DATASET_ID", "default_dataset")

table_version = os.getenv("BQ_TABLE_VERSION", "v1")