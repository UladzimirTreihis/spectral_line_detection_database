#!/bin/sh
. ../protected/.venv/bin/activate
cd ../protected
exec flask run
