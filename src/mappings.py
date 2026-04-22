import os

db_mappings = {
    'sbic' : 'sbic_prod',
    'tradeportal': 'trade_portal_prod',
    'travelandexpense': 'travel_and_expense_prod',
    'creative': 'creative_prod',
    'accounting': 'accounting_prod',
    'production': 'production_prod',
    'masterfile': 'masterfile_prod'
}

table_mappings = {
    'v1': {
        'customerpoulbq': {
            'po_ref_number': 'poRefNumber',
            'po_ref_number_primary': 'poRefNumberPrimary',
            'po_ref_number_count': 'poRefNumberCount',
            'file_name': 'fileName',
            'company_name': 'companyName',
            'customer_name': 'customerName',
            'customer_branch_name' : 'customerBranchName',
            'created_at' : 'createdAt',
            'delivery_date': 'deliveryDate',
            'po_date': 'poDate',
            'cancellation_date': 'cancellationDate',
            'total_discount': 'totalDiscount',
            'total_discount_percent': 'totalDiscountPercent',
            'total_gross_amount': 'totalGrossAmount',
            'total_net_amount': 'totalNetAmount',
            'total_quantity': 'totalQuantity',
            'remark': 'remark',
        },
        'customerpouldetailbq': {
            'po_ref_number': 'poRefNumber',
            'customer_name': 'customerName',
            'customer_branch_name': 'customerBranchName',
            'po_date': 'poDate',
            'delivery_date': 'deliveryDate',
            'line_index': 'lineIndex',
            'customer_sku_code': 'customerSKUCode',
            'customer_sku_desc': 'customerSKUDesc',
            'po_qty': 'poQty',
            'po_qty_pcs': 'poQtyPcs',
            'unit_of_measurement' : 'unitOfMeasurement',
            'unit_price': 'unitPrice',
            'unit_price_pcs': 'unitPricePcs',
            'unit_amount': 'unitAmount',
            'net_amount': 'netAmount',
            'net_price': 'netPrice',
            'net_price_pcs': 'netPricePcs',
            'discount_percent': 'discountPercent',
            'created_at' : 'createdAt',
        },
        'customerrabq': {
            'ra_ref_number': 'raRefNumber',
            'customer_name': 'customerName',
            'payee': 'payee',
            'ra_date': 'raDate',
            'payment_date': 'paymentDate',
            'ra_amount': 'paymentAmount',
            'bank_name': 'bankName',
            'voucher_number': 'voucherNumber',
            'is_multi_page': 'isMultiPage',
            'created_at': 'createdAt',
            'file_name': 'fileName',
        },
        'customerradetailbq': {
            'ra_ref_number': 'raRefNumber',
            'customer_name': 'customerName',
            'payee': 'payee',
            'ra_date': 'raDate',
            'line_index': 'lineIndex',
            'page_index': 'pageIndex',
            'ra_amount_detail': 'raAmountDetail',
            'gross_amount_detail': 'grossAmountDetail',
            'discount_detail': 'discountDetail',
            'source_detail': 'sourceDetail',
            'doc_ref_number_detail': 'docRefNumberDetail',
            'doc_description_detail': 'docDescriptionDetail',
            'apv_number_detail': 'apvNumberDetail',
            'type_code_detail': 'typeCodeDetail',
            'particulars_detail': 'particularDetail',
            'created_at': 'createdAt',
            'file_name': 'fileName',
        }
    }
}

ignore_columns = {
    'v1': {
        'customerpouldetailbq': [
            'file_name',
            'page_index'
        ],
        'customerradetailbq': [
            'md5_hash'
        ]
    }
}

column_defaults = {
    'v1': {
        'customerpoulbq': {
                'po_date': '1900-01-01',
                'delivery_date': '1900-01-01',
                'cancellation_date': '1900-01-01',
                'customer_name': '',
                'customer_branch_name' : '',
                'po_ref_number': '',
                'remark': '',
                'total_gross_amount': 0,
                'total_net_amount': 0,
                'total_discount': 0,
                'total_discount_percent': 0,
                'total_quantity': 0
        },
        'customerpouldetailbq': {
                'po_qty': 0,
                'unit_price': 0,
                'unit_price_pcs': 0,
                'discount_percent': 0,
                'net_price': 0,
                'customer_name': '',
                'customer_sku_desc': '',
                'customer_branch_name': '',
                'customer_sku_code': ''
        },
        'customerrabq': {
                'payee': '',
                'bank_name': '',
                'voucher_number': '',
                'is_multi_page': False,
                'ra_amount': 0,
                'ra_date': '1900-01-01',
                'payment_date': '1900-01-01'
        },
        'customerradetailbq': {
                'ra_ref_number': '',
                'customer_name': '',
                'payee': '',
                'ra_amount_detail': 0,
                'gross_amount_detail': 0,
                'discount_detail': 0,
                'source_detail': '',
                'doc_ref_number_detail': '',
                'doc_description_detail': '',
                'apv_number_detail': '',
                'type_code_detail': '',
                'ra_date': '1900-01-01'
        },
        'onlinesalespo': {
                'poDate': '1900-01-01',
                'customerName': '',
                'customerSKUCode': '',
                'unitPrice': 0,
                'netPrice': 0,
                'unitAmount': 0,
                'netAmount': 0
        }
    }
}

required_columns = {
    'v1': {
        'customerpoulbq': [
            'po_ref_number',
            'customer_name'
        ],
        'customerpouldetailbq': [
            'po_ref_number',
            'customer_name', 
            'customer_sku_code'
        ],
        'customerra': [
            'ra_ref_number',
            'customer_name'
        ],
        'customerradetailbq': [
            'ra_ref_number',
            'customer_name',
            'doc_ref_number_detail'
        ],
        'onlinesalespo': [
            'poRefNumber',
            'customerName',
            'customerSKUCode'
        ]
    }
}

date_columns = { 
    'v1': {
        'customerpoulbq': [
            'po_date', 
            'delivery_date', 
            'cancellation_date'
        ],
        'onlinesalespo': [
            'poDate'
        ],
    }
}

original_columns = {
    'v1': {
        'customerpoulbq': [
            'po_ref_number',
            'po_ref_number_count',
            'company_name',
            'customer_name',
            'customer_branch_name',
            'created_at',
            'delivery_date',
            'po_date',
            'cancellation_date',
            'customer_sku_code',
            'customer_sku_desc',
            'po_qty',
            'po_qty_pcs',
            'unit_price',
            'unit_price_pcs',
            'net_price',
            'total_discount',
            'total_discount_percent',
            'total_gross_amount',
            'total_net_amount',
            'total_quantity',
            'remark',
        ],
        'customerpouldetailbq': [
            'po_ref_number_primary',
            'customer_name',
            'customer_branch_name',
            'created_at',
            'po_date',
            'delivery_date',
            'line_index',
            'customer_sku_code',
            'customer_sku_desc',
            'po_qty',
            'po_qty_pcs',
            'unit_of_measurement',
            'unit_price',
            'unit_price_pcs',
            'unit_amount',
            'net_amount',
            'net_price',
            'net_price_pcs',
            'discount_percent'
        ]
    }
}

money_columns = {
    'v1': {
        'customerpoulbq': [
                'unit_price',
                'unit_price_pcs',
                'net_price',
                'total_discount',
                'total_discount_percent',
                'total_gross_amount',
                'total_net_amount'
        ],
        'customerpouldetailbq': [
                'unit_price',
                'unit_price_pcs',
                'unit_amount',
                'net_amount',
                'net_price',
                'net_price_pcs'
        ],
        'onlinesalespo': [
                'unitPrice',
                'netPrice',
                'unitAmount',
                'netAmount',
                'netPrice'
        ]
    }
}

variable_mappings = {
    'v1': {
        'customerpoul': {
            'bq_header_name': 'DocumentAIBQ',
            'bq_detail_name': 'DocumentAIDetailBQ',
            'mssql_header_name': 'CustomerPOULBQ',
            'mssql_detail_name': 'CustomerPOULDetailBQ',
            'main_key': 'poRefNumber'
        },
        'customerra': {
            'bq_header_name': 'document_ai_ra',
            'bq_detail_name': 'document_ai_ra_detail',
            'mssql_header_name': 'CustomerRABQ',
            'mssql_detail_name': 'CustomerRADetailBQ',
            'main_key': 'raRefNumber'
        },
        'onlinesalespo': {
            'bq_header_name': 'int_online_sales_data',
            'bq_detail_name': 'int_online_sales_data',
            'mssql_header_name': 'CustomerPOULBQ',
            'mssql_detail_name': 'CustomerPOULDetailBQ',
            'main_key': 'poRefNumber'
        }
    }
}

module_mappings = {
        'customerpoul': 'Customer Purchase Order',
        'customerra': 'Customer Remittance Advice',
        'onlinesalespo': 'Online Sales Purchase Order'
    }

bigquery_dataset_mappings = {
    'v1': {
        'customerpoul': 'sbic_int',
        'customerra': 'sbic_marts',
        'onlinesalespo': 'sbic_int'
    }
}
