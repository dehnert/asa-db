#!/bin/bash -e

author="$USER diff_static_data.sh on $(hostname) <asa-db@mit.edu>"

date

cd "$(dirname "$0")/static-data"

../dump_group_perms.py > group-perms.py
git add group-perms.py

../../manage.py dumpdata --format=xml --indent=4 groups.ActivityCategory > groups_initial_data.xml
../../manage.py dumpdata --format=xml --indent=4 forms.FYSMCategory > forms_initial_data.xml
git add {groups,forms}_initial_data.xml

echo
echo Committing current static data:
set +e
git commit -m "Updated static data: $(date +%F)" --author="$author"
commit_result="$?"
set -e

if [ "$commit_result" = "0" ]; then
    echo
    echo Changes in this commit:
    git show
else
    echo "(No changes made.)"
fi

echo
echo
echo Disk usage:
du -h --max-depth=1

echo
echo "gc'ing..."
time git gc
echo "repack'ing..."
time git repack

echo
echo Disk usage:
du -h --max-depth=1

date
