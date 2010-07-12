"""

Start the celery daemon from the Django management command.

"""
from django.core.management.base import AppCommand
from optparse import make_option, OptionParser
from richmond import daemonize


class Command(AppCommand):
    help = 'Run commands in the background'
    
    def handle_app(self, app, **options):
        """
        Perform the command's actions for ``app``, which will be the
        Python module corresponding to an application name given on
        the command line.
        """
        print app, '-> ', options
