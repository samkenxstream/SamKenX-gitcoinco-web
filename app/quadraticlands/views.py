# -*- coding: utf-8 -*-
"""Define the quadraticlands views.

Copyright (C) 2020 Gitcoin Core

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

"""

import json
import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import Http404
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from quadraticlands.helpers import (
    get_FAQ, get_initial_dist, get_mission_status
)
from ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)

def index(request):
    '''render template for base index page'''
    context, game_status = get_initial_dist(request), get_mission_status(request)
    context.update(game_status)
    return TemplateResponse(request, 'quadraticlands/index.html', context)

def base(request, base):
    '''render templates for /quadraticlands/'''
    context, game_status = get_initial_dist(request), get_mission_status(request)
    context.update(game_status)
    if base == 'faq':
        context.update(get_FAQ(request))
    return TemplateResponse(request, f'quadraticlands/{base}.html', context)

def mission_index(request):
    '''render quadraticlands/mission/index.html'''
    context, game_status = get_initial_dist(request), get_mission_status(request)
    context.update(game_status)
    return TemplateResponse(request, 'quadraticlands/mission/index.html', context)  

def test_index(request):
    '''render quadraticlands/mission/index.html'''
    context, game_status = get_initial_dist(request), get_mission_status(request)
    context.update(game_status)
    return TemplateResponse(request, 'quadraticlands/test.html', context) 


def mission_base(request, mission_name):
    '''used to handle quadraticlands/<mission_name>'''
    context, game_status = get_initial_dist(request), get_mission_status(request)
    context.update(game_status)
    if not request.user.is_authenticated and mission_name == 'receive': 
        return redirect('/quadraticlands/mission', context)
    return TemplateResponse(request, f'quadraticlands/mission/{mission_name}/index.html', context)

def dashboard_index(request):
    '''render quadraticlands/dashboard/index.html'''
    if not request.user.is_authenticated:
        return redirect('/login/github/?next=' + request.get_full_path())
    context, game_status = get_initial_dist(request), get_mission_status(request)
    context.update(game_status)
    return TemplateResponse(request, 'quadraticlands/dashboard/index.html', context)  

def mission_state(request, mission_name, mission_state):
    '''quadraticlands/<mission_name>/<mission_state>'''
    if not request.user.is_authenticated:
        return redirect('/login/github/?next=' + request.get_full_path())
    context, game_status = get_initial_dist(request), get_mission_status(request)
    context.update(game_status)
    if not request.user.is_authenticated and mission_state == 'claim': # probably can remove this but leaving in case we want/need it
         return redirect('quadraticlands/mission/index.html')
    return TemplateResponse(request, f'quadraticlands/mission/{mission_name}/{mission_state}.html', context)


def mission_question(request, mission_name, question_num):
    '''Used to handle quadraticlands/<mission_name>/<mission_state>/<question_num>'''
    if not request.user.is_authenticated:
        return redirect('/login/github/?next=' + request.get_full_path())
    context, game_status = get_initial_dist(request), get_mission_status(request)
    context.update(game_status)
    return TemplateResponse(request, f'quadraticlands/mission/{mission_name}/question_{question_num}.html', context)


def mission_postcard(request):
    '''Used to handle quadraticlands/<mission_name>/<mission_state>/<question_num>'''
    if not request.user.is_authenticated:
        return redirect('/login/github/?next=' + request.get_full_path())
    attrs = {
        'front_frame': ['1', '2'],
        'front_background': ['a', 'b'],
        'back_background': ['a', 'b'],
    }
    context = {
        'attrs': attrs,
    }
    return TemplateResponse(request, f'quadraticlands/mission/postcard/postcard.html', context)

def mission_postcard_svg(request):
    import xml.etree.ElementTree as ET
    from django.http import HttpResponse

    width = 100
    height = 100
    viewBox = ''
    tags = ['{http://www.w3.org/2000/svg}style']
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    prepend = f'''<?xml version="1.0" encoding="utf-8"?>
<svg width="{width}%" height="{height}%" viewBox="{viewBox}" version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
'''
    postpend = '''
</svg>
'''

    package = request.GET.dict()
    file = 'assets/v2/images/quadraticlands/postcard.svg'
    with open(file) as file:
        elements = []
        tree = ET.parse(file)
        for item in tree.getroot():
            output = ET.tostring(item).decode('utf-8')

            _id = item.attrib.get('id')
            include_item = None
            if _id == 'text':
                include_item = True
                output = output.replace('POSTCARD_TEXT_GOES_HERE', package.get('text'))
            if _id:
                val = _id.split(":")[-1]
                key = _id.split(":")[0]
                print(key, val, package)
                if val == package.get(key):
                    include_item = True
            if include_item:
                elements.append(output)
        output = prepend + "".join(elements) + postpend

        response = HttpResponse(output, content_type='image/svg+xml')
        return response

def mission_answer(request, mission_name, question_num, answer):
    '''Used to handle quadraticlands/<mission_name>/<mission_state>/<question_num>/<answer>'''
    if not request.user.is_authenticated:
        return redirect('/login/github/?next=' + request.get_full_path())
    context, game_status = get_initial_dist(request), get_mission_status(request)
    context.update(game_status)
    return TemplateResponse(request, f'quadraticlands/mission/{mission_name}/question_{question_num}_{answer}.html', context)