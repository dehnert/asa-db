#!/bin/bash -e

author="$USER warehouse-refresh.sh on $(hostname) <asa-db@mit.edu>"

date

cd saved-data

mysqldump --skip-extended-insert asa+forms > data.sql

echo
echo Committing previous DB:
git commit data.sql -m "Previous ASA database: $(date +%F)" --allow-empty --author="$author"

echo
echo Changes in this commit:
git show

echo
echo
echo Performing replacement
echo "TRUNCATE TABLE groups_group" | mysql asa+forms
../import_db.py < ../warehouse-dump.csv > /dev/null
mysqldump --skip-extended-insert asa+forms > data.sql

echo
echo Committing new DB:
git commit data.sql -m "New ASA database: $(date +%F)" --allow-empty --author="$author"

echo
echo Changes in this commit:
git show

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
