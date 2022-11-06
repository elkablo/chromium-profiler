#!/bin/sh

set -e

cd web-page-records

for replay in *.wprgo; do
	sha256sum "${replay}" >"${replay}.sha256sum"
	echo "$replay"
done
