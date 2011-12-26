#!/bin/bash -e

dist_root="$(readlink -f "$(dirname "$0")/../")"
cd "$dist_root"

export KRB5CCNAME="$(mktemp)"
kinit -k -t ../secrets/asa-db.keytab daemon/asa-db.mit.edu@ATHENA.MIT.EDU
pagsh -c 'aklog; util/sync_moira_authz.py' || true
rm "$KRB5CCNAME"
