"""BigQuery to MSSQL Bridge Router."""
import pandas
import pandas_gbq
import re
import src.mappings as mappings
import src.config as config
import src.services.send_mail as send_mail
from src.db.dbconn import DbConn

from sqlalchemy.exc import IntegrityError
from datetime import timedelta, datetime
from sqlalchemy import text


class BigqueryBridge(object):
    def __init__(self, logger, method="manual", group_code='customerpoul'):
        self.__dbconn = DbConn(logger, 'sbic')
        self.__mssql_engine = self.__dbconn.main()
        self.__logger = logger
        self.__last_run_timestamp = None
        self.__last_run_timestamp_detail = None
        self.__table_version = config.table_version
        self.__method = method
        self.__log_body = "BigQuery Bridge Execution Log ({} Run): {}".format(self.__method, datetime.now().isoformat())
        self.__group_code = group_code
        self.__dataset_id = "{}.{}".format(config.bigquery_project_id,
            mappings.bigquery_dataset_mappings[self.__table_version].get(group_code, 'sbic_int'))
        
    
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
                if self.__group_code == 'customerpoul':
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
                elif self.__group_code == 'customerra':
                    result = connection.execute(
                        text("SELECT MAX(createdAt) FROM CustomerRABQ")
                    )
                    self.__last_run_timestamp = result.scalar()

                    if self.__last_run_timestamp:
                        self.__last_run_timestamp = self.__last_run_timestamp + timedelta(seconds=1)
                    self.__log(f"Last run timestamp for CustomerRA (in UTC): {self.__last_run_timestamp}", level="info")\
                    
                    result = connection.execute(
                        text("SELECT MAX(createdAt) FROM customerRADetailBQ")
                    )
                    self.__last_run_timestamp_detail = result.scalar()

                    if self.__last_run_timestamp_detail:
                        self.__last_run_timestamp_detail = self.__last_run_timestamp_detail + timedelta(seconds=1)
            
        except Exception as e:
            self.__log(f"Error fetching last run timestamp: {e}", level="error")
            send_mail.send_mail(self.__log_body, category="ERROR", method=self.__method, module=self.__group_code)
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
                
            elif table_name == 'document_ai_ra':
                query = "SELECT * FROM `{}.marts_document_ai_ra`".format(self.__dataset_id)

                if self.__last_run_timestamp:
                    query += f" WHERE created_at  > '{self.__last_run_timestamp}'"

                df = pandas_gbq.read_gbq(
                    query,
                    project_id=config.bigquery_project_id,
                    dialect='standard',
                )
                self.__log(f"Fetched {len(df)} records from BigQuery.", level="info")
                return df
            elif table_name == 'document_ai_ra_detail':
                query = "SELECT * FROM `{}.marts_document_ai_ra_detail`".format(self.__dataset_id)

                if self.__last_run_timestamp_detail:
                    query += f" WHERE created_at  > '{self.__last_run_timestamp_detail}'"

                df = pandas_gbq.read_gbq(
                    query,
                    project_id=config.bigquery_project_id,
                    dialect='standard',
                )
                self.__log(f"Fetched {len(df)} records from BigQuery.", level="info")
                return df
            elif table_name == 'int_online_sales_data':
                query = "SELECT * FROM `{}.int_online_sales_data`".format(self.__dataset_id)

                if self.__last_run_timestamp:
                    query += f" WHERE createdAt  > '{self.__last_run_timestamp}'"

                df = pandas_gbq.read_gbq(
                    query,
                    project_id=config.bigquery_project_id,
                    dialect='standard',
                )
                self.__log(f"Fetched {len(df)} records from BigQuery.", level="info")
                return df
        except Exception as e:
            self.__log(f"Error fetching data from BigQuery: {e}", level="error")
            send_mail.send_mail(self.__log_body, category="ERROR", method=self.__method, module=self.__group_code)
            return {"status": "error", "message": str(e)}     
    
    def __rename_columns(self, table_name, df):
        """Rename columns based on the mapping."""
        table_name = table_name.lower()
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
    
    def __format_onlinesalespo_data(self, df):
        """Format Online Sales PO data to match MSSQL schema."""
        detail_dict = df.to_dict(orient='records')
        porefnumber_list = []
        header_list = []
        detail_list = []
        lineindex = 0

        for record in detail_dict:
            porefnumber = record.get('poRefNumber')
            if porefnumber and porefnumber not in porefnumber_list:
                temp_header_dict = {
                    'po_ref_number': record.get('poRefNumber'),
                    'customer_name': record.get('customerName'),
                    'customer_branch_name': record.get('customerBranchName', ''),
                    'company_name': record.get('companyName', ''),
                    'created_at': record.get('createdAt', '{}'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])),
                    'po_date': record.get('poDate', '1900-01-01'),
                    'delivery_date': record.get('deliveryDate', '1900-01-01'),
                    'cancellation_date': record.get('cancellationDate', '1900-01-01'),
                    'total_gross_amount': record.get('totalGrossAmount', 0),
                    'total_discount': record.get('totalDiscount', 0),
                    'total_discount_percent': record.get('totalDiscountPercent', 0),
                    'file_name': record.get('fileName', ''),
                    'total_net_amount': record.get('totalNetAmount', 0),
                    'total_quantity': record.get('totalQuantity', 0),
                    'remark': record.get('remark'),
                    'poStatus': record.get('poStatus', 'NEW'),
                    'poRefNumberPrimary': record.get('poRefNumberPrimary', ''),
                    'poRefNumberCount': record.get('poRefNumberCount', ''),
                    'customerSKUCode': '',
                    'customerSKUDesc': '',
                    'poQty': record.get('poQty', 0),
                    'poQtyPcs': record.get('poQtyPcs', 0),
                    'unitPrice': record.get('unitPrice', 0),
                    'unitPricePcs': record.get('unitPricePcs', 0),
                    'netPrice': record.get('netPrice', 0),
                }
                porefnumber_list.append(porefnumber)
                header_list.append(temp_header_dict)
                lineindex = 0

            temp_detail_dict = {
                'po_ref_number': record.get('poRefNumber'),
                'customer_name': record.get('customerName'),
                'customer_branch_name': record.get('customerBranchName', ''),
                'customer_sku_code': record.get('customerSKUCode'),
                'customer_sku_desc': record.get('customerSKUDesc'),
                'created_at': record.get('createdAt', '{}'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])),
                'po_date': record.get('poDate', '1900-01-01'),
                'delivery_date': record.get('deliveryDate', '1900-01-01'),
                'po_qty': record.get('poQty', 0),
                'unit_price': record.get('unitPrice', 0),
                'unit_amount': record.get('unitAmount', 0),
                'net_price': record.get('netPrice', 0),
                'line_index': lineindex,
                'unit_price_pcs': record.get('unitPricePcs', 0),
                'net_price_pcs': record.get('netPricePcs', 0),
                'po_qty_pcs': record.get('poQtyPcs', 0),
                'unit_of_measurement': record.get('unitOfMeasurement', ''),
                'discount_percent': record.get('discountPercent', 0),
                'file_name': record.get('fileName', ''),
                'page_index': record.get('pageIndex', 0),
                'netAmount': record.get('netAmount', 0),
            }
            detail_list.append(temp_detail_dict)
            lineindex += 1

        header_df = pandas.DataFrame(header_list)
        detail_df = pandas.DataFrame(detail_list)

        return header_df, detail_df
    
    def main(self):
        """Bigquery Bridge Main Function."""
        self.__log("BigQuery to MSSQL Bridge initialized.", level="info")
        self.__get_last_run_timestamp()
        self.__log(f"Last run timestamp obtained: {self.__last_run_timestamp}", level="info")
        
        self.__log("Fetching data from BigQuery...", level="info")
        variable_mapping = mappings.variable_mappings[self.__table_version].get(self.__group_code, {})
        bq_header_table_name = variable_mapping.get('bq_header_name', 'DocumentAIBQ')
        bq_detail_table_name = variable_mapping.get('bq_detail_name', 'DocumentAIDetailBQ')
        mssql_header_table_name = variable_mapping.get('mssql_header_name', 'CustomerPOULBQ')
        mssql_detail_table_name = variable_mapping.get('mssql_detail_name', 'CustomerPOULDetailBQ')
        main_key = variable_mapping.get('main_key', 'poRefNumber')

        if self.__group_code in ('customerpoul', 'customerra'):
            header_table = self.__get_bigquery_data(bq_header_table_name)
            detail_table = self.__get_bigquery_data(bq_detail_table_name)

        elif self.__group_code == 'onlinesalespo':
            self.__log("Processing data from online sales bigquery table...", level="info")
            bq_table = self.__get_bigquery_data('int_online_sales_data')
            header_table, detail_table = self.__format_onlinesalespo_data(bq_table)

        self.__log("Renaming columns to match MSSQL schema...", level="info")
        header_table = self.__rename_columns(mssql_header_table_name.lower(), header_table)
        detail_table = self.__rename_columns(mssql_detail_table_name.lower(), detail_table)

        continue_execution = True
        while continue_execution:
            try:
                bq_inserted = False
                self.__log("Attempting to insert data into MSSQL. Total Records - {}: {}, {}: {}".format(mssql_header_table_name,
                                                                                                         len(header_table), 
                                                                                                         mssql_detail_table_name, 
                                                                                                         len(detail_table)), 
                                                                                                         level="info")
                with self.__mssql_engine.connect() as connection:
                    uldetail_bq = detail_table.to_sql(
                        name=mssql_detail_table_name,
                        con=connection,
                        if_exists='append',
                        index=False
                    )
                    bq_inserted = True
                    ul_bq = header_table.to_sql(
                        name=mssql_header_table_name,
                        con=connection,
                        if_exists='append',
                        schema='dbo',
                        index=False,
                        chunksize=100,
                        method='multi'
                    )
                continue_execution = False
                self.__log("Data inserted successfully into MSSQL.", level="info")
                self.__log("Inserted Records - {}: {}, {}: {}".format(mssql_header_table_name, 
                                                                      ul_bq, 
                                                                      mssql_detail_table_name, 
                                                                      uldetail_bq), 
                                                                      level="info")
            except IntegrityError as ie:
                duplicate_keys = self.__extract_duplicate_key(str(ie))
                if duplicate_keys:
                    if not bq_inserted:
                        requirements_cols = mappings.required_columns[self.__table_version].get(mssql_detail_table_name.lower(), [])
                        self.__log(f"Duplicate entries found in {mssql_detail_table_name} ({requirements_cols}): {duplicate_keys}. Skipping insertion for these records.", level="warning")
                        detail_table = detail_table[detail_table[main_key] != duplicate_keys[0]]
                    else:
                        requirements_cols = mappings.required_columns[self.__table_version].get(mssql_header_table_name.lower(), [])
                        self.__log(f"Duplicate entries found in {mssql_header_table_name} ({requirements_cols}): {duplicate_keys}. Skipping insertion for these records.", level="warning")
                        header_table = header_table[header_table[main_key] != duplicate_keys[0]]
                else:
                    self.__log(f"IntegrityError encountered: {ie}", level="error")
                    send_mail.send_mail(self.__log_body, category="ERROR", method=self.__method, module=self.__group_code)
                    return {"status": "error", "message": str(ie)}
            except Exception as e:
                self.__log(f"Error inserting data into MSSQL: {e}", level="error")
                send_mail.send_mail(self.__log_body, category="ERROR", method=self.__method, module=self.__group_code)
                return {"status": "error", "message": str(e)}
        
        send_mail.send_mail(self.__log_body, category="INFO", method=self.__method, module=self.__group_code)
        return {
            "status": "success", 
            "message": "Data transfer from BigQuery to MSSQL completed successfully.", 
            "details": {"header_records": len(header_table), 
                        "detail_records": len(detail_table)}}

if __name__ == "__main__":
    # For local testing
    import logging
    from src.test_logger import LogHandler
    LogHandler('BigQueryBridge')
    logger = logging.getLogger('BigQueryBridge')
    bridge = BigqueryBridge(logger, method='manual', group_code='customerra')
    result = bridge.main()
    print(result)