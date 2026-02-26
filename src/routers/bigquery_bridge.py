"""BigQuery to MSSQL Bridge Router."""
import pandas
import pandas_gbq
import re
import src.mappings as mappings
import src.config as config
import src.services.send_mail as send_mail
from sqlalchemy.exc import IntegrityError
from src.db.dbconn import DbConn
from datetime import timedelta, datetime
from sqlalchemy import text


class BigqueryBridge(object):
    def __init__(self, logger, method="manual"):
        self.__dbconn = DbConn(logger, 'sbic')
        self.__mssql_engine = self.__dbconn.main()
        self.__logger = logger
        self.__last_run_timestamp = None
        self.__last_run_timestamp_detail = None
        self.__table_version = config.table_version
        self.__log_body = "BigQuery Bridge Execution Log: {}".format(datetime.now().isoformat())
    
    def __log(self, message, level="info"):
        if level == "info":
            self.__logger.info(message)
        elif level == "error":
            self.__logger.error(message)
        elif level == "warning":
            self.__logger.warning(message)
        self.__log_body += "\n{}: {}".format(level.upper(), message)
        
    def __get_last_run_timestamp(self):
        """Get the last run timestamp from MSSQL table."""
        try:
            with self.__mssql_engine.connect() as connection:
                result = connection.execute(
                    text("SELECT MAX(createdAt) FROM CustomerPOULBQ")
                )
                self.__last_run_timestamp = result.scalar()
                if self.__last_run_timestamp:
                    self.__last_run_timestamp = self.__last_run_timestamp + timedelta(seconds=1)  # Add 1 second to avoid fetching the last record again
                self.__log(f"Last run timestamp (in UTC): {self.__last_run_timestamp}", level="info")
                
                result = connection.execute(
                    text("SELECT MAX(createdAt) FROM CustomerPOULDetailBQ")
                )
                self.__last_run_timestamp_detail = result.scalar()
                if self.__last_run_timestamp_detail:
                    self.__last_run_timestamp_detail = self.__last_run_timestamp_detail + timedelta(seconds=1)
            
        except Exception as e:
            self.__log(f"Error fetching last run timestamp: {e}", level="error")
            send_mail.send_mail(self.__log_body, category="ERROR")
            return {"status": "error", "message": str(e)}
        
    def __get_bigquery_data(self, table_name):
        """Get data from BigQuery based on the last run timestamp."""
        try:
            if table_name == 'DocumentAIBQ':
                query = "SELECT * FROM `{}.int_document_ai`".format(config.bigquery_dataset_id)
                
                if self.__last_run_timestamp:
                    query += f" WHERE created_at  > '{self.__last_run_timestamp}'"
                
                df = pandas_gbq.read_gbq(
                    query,
                    project_id=config.bigquery_project_id,
                    dialect='standard',
                )
                self.__log(f"Fetched {len(df)} records from BigQuery.", level="info")
                return df
            elif table_name == 'DocumentAIDetailBQ':
                query = "SELECT * FROM `{}.int_document_ai_detail`".format(config.bigquery_dataset_id)

                if self.__last_run_timestamp_detail:
                    query += f" WHERE created_at  > '{self.__last_run_timestamp_detail}'"
                
                df = pandas_gbq.read_gbq(
                    query,
                    project_id=config.bigquery_project_id,
                    dialect='standard',
                )
                self.__log(f"Fetched {len(df)} records from BigQuery.", level="info")
                return df
        except Exception as e:
            self.__log(f"Error fetching data from BigQuery: {e}", level="error")
            send_mail.send_mail(self.__log_body, category="ERROR")
            return {"status": "error", "message": str(e)}
    
    def __rename_columns(self, table_name, df):
        """Rename columns based on the mapping."""
        column_mapping = mappings.table_mappings[self.__table_version].get(table_name, {})
        ignore_cols = mappings.ignore_columns.get(self.__table_version, {}).get(table_name, [])
        column_defaults = mappings.column_defaults.get(self.__table_version, {}).get(table_name, {})
        requirements_cols = mappings.required_columns.get(self.__table_version, {}).get(table_name, [])
        date_cols = mappings.date_columns.get(self.__table_version, {}).get(table_name, [])
        money_cols = mappings.money_columns.get(self.__table_version, {}).get(table_name, [])

        if not column_mapping:
            self.__log(f"No column mapping found for table: {table_name}", level="warning")
            return df
        
        if ignore_cols:
            df.drop(columns=ignore_cols, inplace=True)
            self.__log(f"Removed Columns for {table_name}", level="info")

        if requirements_cols:
            len_before = len(df)
            self.__log('Removing Duplicates for table: {}'.format(table_name), level="info")
            df.drop_duplicates(requirements_cols, keep='first', inplace=True)
            self.__log('Removed {} duplicate rows for table: {}'.format(len_before - len(df), table_name), level="info")

        for key, val in column_defaults.items():
            df[key] = df[key].mask(df[key].isnull(), val)
        
        df['customer_name'] = df['customer_name'].astype(str).str.encode('utf-8')

        for money_col in money_cols:
            if money_col in df.columns:
                df[money_col] = pandas.to_numeric(df[money_col], errors='coerce').fillna(0)

        for date_col in date_cols:
            if date_col in df.columns:
                df[date_col] = pandas.to_datetime(df[date_col], 
                                                  errors="coerce", 
                                                  format='mixed', 
                                                  yearfirst=True, 
                                                  dayfirst=True, 
                                                  utc=True)
                df[date_col] = df[date_col].dt.strftime("%Y-%m-%d")

        return df.rename(columns=column_mapping)
    
    def __extract_duplicate_key(self, error_message: str):
        """
        Extracts the duplicate key value from a SQL IntegrityError message.
        
        Returns:
            tuple: (key1, key2, ...) if found
            None: if no duplicate key found
        """
        pattern = r"The duplicate key value is \((.*?)\)"
        match = re.search(pattern, error_message)

        if not match:
            return None

        # Split values by comma but preserve spacing properly
        values = [v.strip() for v in match.group(1).split(",")]

        return values
    
    def main(self):
        """Bigquery Bridge Main Function."""
        self.__log("BigQuery to MSSQL Bridge initialized.", level="info")
        self.__get_last_run_timestamp()
        self.__log(f"Last run timestamp obtained: {self.__last_run_timestamp}", level="info")
        
        self.__log("Fetching data from BigQuery...", level="info")
        customer_po_ul_bq = self.__get_bigquery_data('DocumentAIBQ')
        customer_po_ul_detail_bq = self.__get_bigquery_data('DocumentAIDetailBQ')

        self.__log("Renaming columns to match MSSQL schema...", level="info")
        customer_po_ul_bq = self.__rename_columns('customerpoulbq', customer_po_ul_bq)
        customer_po_ul_detail_bq = self.__rename_columns('customerpouldetailbq', customer_po_ul_detail_bq)

        bq_inserted = False
        continue_execution = True
        while continue_execution:
            try:
                self.__log("Attempting to insert data into MSSQL. Total Records - CustomerPOULBQ: {}, CustomerPOULDetailBQ: {}".format(len(customer_po_ul_bq), len(customer_po_ul_detail_bq)), level="info")
                with self.__mssql_engine.connect() as connection:
                    ul_bq = customer_po_ul_bq.to_sql(
                        name='CustomerPOULBQ',
                        con=connection,
                        if_exists='append',
                        schema='dbo',
                        index=False,
                        chunksize=100,
                        method='multi'
                    )
                    bq_inserted = True
                    
                    uldetail_bq = customer_po_ul_detail_bq.to_sql(
                        name='CustomerPOULDetailBQ',
                        con=connection,
                        if_exists='append',
                        index=False
                    )

                continue_execution = False
                self.__log("Data inserted successfully into MSSQL.", level="info")
                self.__log("Inserted Records - CustomerPOULBQ: {}, CustomerPOULDetailBQ: {}".format(ul_bq, uldetail_bq), level="info")
            except IntegrityError as ie:
                duplicate_keys = self.__extract_duplicate_key(str(ie))
                if duplicate_keys:
                    if not bq_inserted:
                        requirements_cols = mappings.required_columns[self.__table_version].get('customerpoulbq', [])
                        self.__log(f"Duplicate entries found in CustomerPOULBQ ({requirements_cols}): {duplicate_keys}. Skipping insertion for these records.", level="warning")
                        customer_po_ul_bq = customer_po_ul_bq[customer_po_ul_bq['poRefNumber'] != duplicate_keys[0]]
                    else:
                        requirements_cols = mappings.required_columns[self.__table_version].get('customerpouldetailbq', [])
                        self.__log(f"Duplicate entries found in CustomerPOULDetailBQ ({requirements_cols}): {duplicate_keys}. Skipping insertion for these records.", level="warning")
                        customer_po_ul_detail_bq = customer_po_ul_detail_bq[customer_po_ul_detail_bq['poRefNumber'] != duplicate_keys[0]]
                else:
                    self.__log(f"IntegrityError encountered: {ie}", level="error")
                    send_mail.send_mail(self.__log_body, category="ERROR")
                    return {"status": "error", "message": str(ie)}
            except Exception as e:
                self.__log(f"Error inserting data into MSSQL: {e}", level="error")
                send_mail.send_mail(self.__log_body, category="ERROR")
                return {"status": "error", "message": str(e)}
        
        send_mail.send_mail(self.__log_body, category="INFO")
        return {
            "status": "success", 
            "message": "Data transfer from BigQuery to MSSQL completed successfully.", 
            "details": {"customerpoulbq_records": len(customer_po_ul_bq), 
                        "customerpouldetailbq_records": len(customer_po_ul_detail_bq)}}