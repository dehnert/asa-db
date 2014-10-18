#!/bin/sh

set -euf

settings=$(dirname "$0")
base="$settings/.."

echo Creating config files...
secret=$(python -c "import random; print(''.join([random.choice('abcdefghijklmnopqrstuvwxyz0123456789@#%&-_=+') for i in range(50)]))")
secret_re="s/^#SECRET_KEY = something$/SECRET_KEY = '$secret'/"
sed -e "$secret_re" < "$settings/local_settings.dev-template.py" > "$settings/local.py"
touch "$settings/local_after.py"

echo
echo Creating database and doing basic sync...
$base/manage.py syncdb && $base/manage.py migrate

echo; echo
echo Done!
echo 'Run the server with "./manage.py runserver 8003" or similar.'
