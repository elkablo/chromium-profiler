#!/bin/sh

set -e

tag="$(git describe --always --dirty --tags)"
if [[ "${tag:0:1}" == "v" ]]; then
	tag="${tag:1}"
fi

name="chromium-profiler-${tag}"

find . -type d -exec chmod 0755 {} \;
find . -type f -executable -exec chmod 0755 {} \;
find . -type f ! -executable -exec chmod 0644 {} \;

tar --owner=0 --group=0 --mtime=NOW -cf "${name}.tar" --exclude-vcs --transform="s/^\./${name}/" --show-transformed-names .
