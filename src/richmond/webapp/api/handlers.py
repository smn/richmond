import re

from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime

class ConversationHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    @throttle(5, 10*60) # allow 5 times in 10 minutes
    @require_mime('yaml')
    def create(self, request):
        return rc.CREATED
    

