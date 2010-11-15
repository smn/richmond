import yaml, logging
from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime
from piston.utils import Mimer, FormValidationError, rc

from vumi.webapp.api.models import URLCallback
from vumi.webapp.api.forms import URLCallbackForm

from alexandria.loader.base import YAMLLoader
from alexandria.dsl.utils import dump_menu

# Complete reset, clear defaults - they're hard to debug
Mimer.TYPES = {}
# Specify the default Mime loader for YAML, Piston's YAML loader by default 
# tries to wrap the loaded YAML data in a dict, which for our conversation 
# YAML documents doesn't work.
Mimer.register(yaml.safe_load, ('application/x-yaml',))
# Do nothing with incoming XML, leave the parsing for the handler
Mimer.register(lambda *a: None, ('text/xml','application/xml'))
# Do nothing with plain text, leave the parsing for the handler
Mimer.register(lambda *a: None, ('text/plain; charset=utf-8',))


class ConversationHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    @throttle(5, 10*60) # allow 5 times in 10 minutes
    @require_mime('yaml')
    def create(self, request):
        menu = YAMLLoader().load_from_string(request.raw_post_data)
        dump = dump_menu(menu) # debug
        logging.debug("Received a new conversation script with %s items "
                        "but not doing anything with it yet." % len(dump))
        return rc.CREATED
    

class URLCallbackHandler(BaseHandler):
    allowed_methods = ('POST', 'PUT', 'GET', 'DELETE')
    exclude = ('profile','id')
    
    @throttle(60, 60)
    def update(self, request, callback_id=None):
        profile = request.user.get_profile()
        callback = profile.urlcallback_set.get(pk=callback_id)
        kwargs = request.POST.copy()
        kwargs.update({
            'profile': profile.pk
        })
        form = URLCallbackForm(kwargs, instance=callback)
        if not form.is_valid():
            raise FormValidationError(form)
        return form.save()
    
    @throttle(60, 60)
    def create(self, request):
        kwargs = request.POST.copy()
        kwargs.update({
            'profile': request.user.get_profile().pk
        })
        form = URLCallbackForm(kwargs)
        if not form.is_valid():
            raise FormValidationError(form)
        return form.save()
    
    @throttle(60, 60)
    def read(self, request, callback_id=None):
        profile = request.user.get_profile()
        if callback_id:
            return profile.urlcallback_set.get(pk=callback_id)
        return profile.urlcallback_set.all()
    
    @throttle(60, 60)
    def delete(self, request, callback_id):
        profile = request.user.get_profile()
        callback = profile.urlcallback_set.get(pk=callback_id)
        callback.delete()
        return rc.DELETED