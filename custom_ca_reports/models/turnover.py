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
        # When unfolding, only fetch sum for the country we are unfolding and
        # fetch all partners for that country
        if line_id != None:
            where_clause = 'AND c.id = %s ' + where_clause
            where_params = [line_id] + where_params
            unfold_query = """
                SELECT sum(\"account_move_line\".balance) AS balance, p.name, p.id, c.id AS country_id FROM """+tables+"""
                    LEFT JOIN res_partner p ON \"account_move_line\".partner_id = p.id
                    LEFT JOIN res_country c on p.country_id = c.id
                    WHERE \"account_move_line\".invoice_id IS NOT NULL AND \"account_move_line\".user_type_id = %s """+where_clause+"""
                    GROUP BY p.name, p.id, c.id ORDER BY p.name
            """


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
                    'unfoldable': True,
                    'unfolded': line_id == line.get('id') and True or False,
                    'columns': [{'name': line.get('balance')}],
                })
        # Adding partners lines
        if line_id:
            self.env.cr.execute(unfold_query, params)
            results = self.env.cr.dictfetchall()
            for child_line in results:
                lines.append({
                        'id': '%s_%s' % (child_line.get('id'), child_line.get('name')),
                        'name': child_line.get('name'),
                        'level': 4,
                        'parent_id': line_id,
                        'columns': [{'name': child_line.get('balance')}]
                    })
            # Sum of all the partner lines
            lines.append({
                    'id': 'total_%s' % (line_id,),
                    'class': 'o_account_reports_domain_total',
                    'name': _('Total '),
                    'parent_id': line_id,
                    'columns': [{'name': total}]
                })

        # Don't display level 0 total line in case we are unfolding
        if total and not line_id:
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