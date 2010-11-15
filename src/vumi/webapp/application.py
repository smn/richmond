"""
Application file for running Django with Twisted

twistd -no web --wsgi=richmond.webapp.application

"""
from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()