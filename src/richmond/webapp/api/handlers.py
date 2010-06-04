import yaml, logging
from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime
from piston.utils import Mimer

from richmond.webapp.api.models import URLCallback

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
    allowed_methods = ('PUT',)
    model = URLCallback
    exclude = ('profile','id')
    
    @throttle(60, 60)
    def update(self, request):
        profile = request.user.get_profile()
        name_field = self.model._meta.get_field('name')
        possible_keys = [key for key, value in name_field.choices]
        return [profile.set_callback(key, request.POST.get(key)) \
                                            for key in possible_keys]