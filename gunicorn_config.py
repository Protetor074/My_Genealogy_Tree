import logging
import os

bind = '192.168.1.108:5000'
workers = 10
loglevel = 'info'
# Ustaw odpowiednie ścieżki do plików dziennika
errorlog = os.path.join(os.path.dirname(__file__), 'Logs/error.log')
accesslog = os.path.join(os.path.dirname(__file__), 'Logs/access.log')

