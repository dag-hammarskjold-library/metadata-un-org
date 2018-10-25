from flask import request

def get_preferred_language(request, return_kwargs):
    lang = request.args.get('lang','en')
    return_kwargs['lang'] = lang
    return return_kwargs