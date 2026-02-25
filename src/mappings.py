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
        'customerpouldetail': {
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
    }
}

ignore_columns = {
    'v1': {
        'customerpouldetail': [
            'file_name',
            'page_index'
        ]
    }
}

column_defaults = {
    'v1': {
        'customerpoul_v4': {
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
        'customerpouldetail_v4': {
                'po_qty': 0,
                'unit_price': 0,
                'unit_price_pcs': 0,
                'discount_percent': 0,
                'net_price': 0,
                'customer_name': '',
                'customer_sku_desc': '',
                'customer_branch_name': '',
                'customer_sku_code': ''
        }
    }
}

required_columns = {
    'v1': {
        'customerpoul': [
            'po_ref_number',
            'customer_name'
        ],
        'customerpouldetail': [
            'po_ref_number',
            'customer_name', 
            'customer_sku_code'
        ]
    }
}

date_columns = { 
    'v1': {
        'customerpoul_v4': [
            'po_date', 
            'delivery_date', 
            'cancellation_date'
        ]
    }
}

original_columns = {
    'v1': {
        'customerpoul': [
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
        'customerpouldetail': [
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
        'customerpoul': [
                'unit_price',
                'unit_price_pcs',
                'net_price',
                'total_discount',
                'total_discount_percent',
                'total_gross_amount',
                'total_net_amount'
        ],
        'customerpouldetail': [
                'unit_price',
                'unit_price_pcs',
                'unit_amount',
                'net_amount',
                'net_price',
                'net_price_pcs'
        ]
    }
}
