from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
import os
from django.conf import settings

# Get the path to Unity WebGL build files
UNITY_BUILD_PATH = os.path.join(settings.BASE_DIR.parent, 'raggey.app', 'web')

@cache_control(no_cache=True)
def unity_index(request):
    '''Serve Unity WebGL index.html'''
    try:
        with open(os.path.join(UNITY_BUILD_PATH, 'index.html'), 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse('Unity build files not found.', status=404)

@cache_control(max_age=3600)
def serve_unity_build(request, filename):
    '''Serve Unity build files'''
    file_path = os.path.join(UNITY_BUILD_PATH, 'Build', filename)
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        content_type = get_content_type(filename)
        return HttpResponse(content, content_type=content_type)
    except FileNotFoundError:
        return HttpResponse(f'Build file not found: {filename}', status=404)

@cache_control(max_age=3600)
def serve_unity_template_data(request, filename):
    '''Serve Unity template data files'''
    file_path = os.path.join(UNITY_BUILD_PATH, 'TemplateData', filename)
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        content_type = get_content_type(filename)
        return HttpResponse(content, content_type=content_type)
    except FileNotFoundError:
        return HttpResponse(f'Template file not found: {filename}', status=404)

def get_content_type(filename):
    '''Determine content type based on file extension'''
    if filename.endswith('.js'):
        return 'application/javascript'
    elif filename.endswith('.wasm'):
        return 'application/wasm'
    elif filename.endswith('.data'):
        return 'application/octet-stream'
    elif filename.endswith('.css'):
        return 'text/css'
    elif filename.endswith('.png'):
        return 'image/png'
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        return 'image/jpeg'
    elif filename.endswith('.svg'):
        return 'image/svg+xml'
    elif filename.endswith('.ico'):
        return 'image/x-icon'
    else:
        return 'application/octet-stream'
