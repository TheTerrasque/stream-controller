#!/bin/bash
python manage.py migrate
supervisord -c supervisord.conf