###################################################################################
#
#    Copyright (c) 2017-2019 MuK IT GmbH.
#
#    This file is part of MuK Documents 
#    (see https://mukit.at).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import http
from odoo.http import request

class OnboardingController(http.Controller):
    
    @http.route('/dms/document_onboarding/directory', auth='user', type='json')
    def document_onboarding_directory(self):
        company = request.env.user.company_id
        closed = company.documents_onboarding_state == 'closed'
        check = request.env.user.has_group('muk_dms.group_dms_manager')
        if check and not closed:
            return {
                'html': request.env.ref('muk_dms.document_onboarding_directory_panel').render({
                    'state': company.get_and_update_documents_onboarding_state(),
                    'company': company,
                })
            }
        return {}   
    
    @http.route('/dms/document_onboarding/file', auth='user', type='json')
    def document_onboarding_file(self):
        company = request.env.user.company_id
        closed = company.documents_onboarding_state == 'closed'
        check = request.env.user.has_group('muk_dms.group_dms_manager')
        if check and not closed:
            return {
                'html': request.env.ref('muk_dms.document_onboarding_file_panel').render({
                    'state': company.get_and_update_documents_onboarding_state(),
                    'company': company,
                })
            }
        return {}   
    
    