# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo import api, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError


class ReportTurnoverCountry(models.AbstractModel):
    _name = "account.report.turnover.country"
    _description = "Turnover by country/partner"
    _inherit = 'account.report'

    def get_columns_name(self, options):
        return [{'name': _('Country')}, {'name': _('Turnover'), 'class': 'number'}]

    @api.model
    def get_lines(self, options, line_id=None):
        lines = []
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        user_type_id = self.env['account.account.type'].search([('type', '=', 'receivable')])
        if where_clause:
            where_clause = 'AND ' + where_clause

        sql_query = """
            SELECT sum(\"account_move_line\".balance) AS balance, c.code, c.id FROM """+tables+"""
                LEFT JOIN res_partner p ON \"account_move_line\".partner_id = p.id
                LEFT JOIN res_country c on p.country_id = c.id
                WHERE \"account_move_line\".invoice_id IS NOT NULL AND \"account_move_line\".user_type_id = %s """+where_clause+"""
                GROUP BY c.code, c.id ORDER BY c.code
        """
        params = [user_type_id.id] + where_params
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.dictfetchall()

        total = 0
        for line in results:
            total += line.get('balance')
            lines.append({
                    'id': line.get('id'),
                    'name': line.get('code'),
                    'level': 2,
                    'unfoldable': False,
                    'columns': [{'name': line.get('balance')}],
                })
        lines.append({
            'id': 'total',
            'name': _('Total'),
            'level': 0,
            'class': 'total',
            'columns': [{'name': total}]
            })

        return lines

    def get_report_name(self):
        return _('Turnover by country/partner')