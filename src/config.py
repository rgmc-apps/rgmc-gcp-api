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
mail_recipient = os.getenv("MAIL_RECIPIENT", "it.arellanoerwin@gmail.com")
mail_sender = os.getenv("MAIL_SENDER", "rgmc.apps@gmail.com")
mail_password = os.getenv("MAIL_PASSWORD", "password")
mail_port = int(os.getenv("MAIL_PORT", "587"))
mail_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")

pass_key = os.getenv("PASS_KEY", "default_pass_key")
revision_code = os.environ.get('K_REVISION', '00001')

BC_CLIENT_ID = os.getenv("BC_CLIENT_ID", "1dbc90f8-3822-4c1b-b4f6-5156971b7212")
BC_CLIENT_SECRET = os.getenv("BC_CLIENT_SECRET", "ifQ8Q~swYV~L9iStzebwMwgx3Y8w_lwv9cpWtaCZ")
BC_TENANT_ID = os.getenv("BC_TENANT_ID", "ca3ca144-09d9-42dd-920a-c72aedd54dd6")    
BC_SCOPE = os.getenv("BC_SCOPE", "https://api.businesscentral.dynamics.com/.default")
BC_AUTH_URL = os.getenv("BC_AUTH_URL", f"https://login.microsoftonline.com/{BC_TENANT_ID}/oauth2/v2.0/token")

BC_ENVIRONMENT = os.getenv("BC_ENVIRONMENT", "UAT")
BC_COMPANY = os.getenv("BC_COMPANY", "CGI")

developer_email = os.getenv("DEVELOPER_EMAIL", "")
smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
smtp_user = os.getenv("SMTP_USER", "")
smtp_password = os.getenv("SMTP_PASSWORD", "")
