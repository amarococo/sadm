#! /usr/bin/env bash
# This file is part of Prologin-SADM.
#
# Copyright (c) 2013-2014 Antoine Pietri <antoine.pietri@prologin.org>
# Copyright (c) 2011 Pierre Bourdon <pierre.bourdon@prologin.org>
# Copyright (c) 2011-2014 Association Prologin <info@prologin.org>
#
# Prologin-SADM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prologin-SADM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prologin-SADM.  If not, see <http://www.gnu.org/licenses/>.

if [ "$#" -ne 2 ]; then
    echo >&2 "Usage: $0 <stechec-root> <champion-dir>"
    exit 1
fi

player_env_dir=$1
champion_dir=$2

compil_dir=`mktemp -d /tmp/stechec_compil_XXXXXX`
champion_tarball=$champion_dir/champion.tgz
lang_file=_lang

# Signal the makefiles to use wildcards to find the champion sources
export STECHEC_SERVER=1

(
    # We should not preempt the contestant tasks
    renice 5 $$ &>/dev/null

    if ! test -f "$champion_tarball"; then
        echo >&2 "*** Unable to locate the champion.tgz file. Upload failed?"
        exit 2
    fi
    echo "Champion tarball found. Extracting to $compil_dir."

    cd "$compil_dir"
    echo "Files contained in the tarball:"
    tar xzvf "$champion_tarball" 2>&1 | sed 's/^.*$/- &/'

    if test "${PIPESTATUS[0]}" -ne 0; then
        echo >&2 "*** Extraction failed. Corrupted tarball?"
        exit 1
    fi

    lang="$( cat ${lang_file} )"
    makefile_path="$lang/Makefile-$lang"

    echo "Compiling the champion (detected language: $lang)."
    make -f "$player_env_dir/$makefile_path" all 2>&1 | sed 's/^.*$/    &/'
    res=${PIPESTATUS[0]}
    echo

    if test "$res" -ne 0; then
        echo >&2 "*** Compilation failed. Try again :)"
        echo >&2 "*** If this compiles on your side, contact an organizer"
        exit 1
    fi

    echo "Checking the compilation result:"
    if [ ! -f "champion.so" ]; then
        echo >&2 "*** Champion library not found. This should not happen."
        exit 1
    fi
    ls -gGlah champion.so 2>&1 | sed 's/^.*$/    &/'
    echo

    echo "Copying the champion files."
    mkdir "$champion_dir/champion-compiled"
    for f in *; do
        if [ "$f" != "champion-compiled" ]; then
            cp -v "$f" "$champion_dir/champion-compiled/$f"
        fi
    done 2>&1 | sed 's/^.*$/    &/'
    echo "Making tarball."
    tar czvf "$champion_dir"/champion-compiled.tar.gz \
        -C "$champion_dir"/champion-compiled/ . \
        | sed 's/^.*$/    &/'

    rm -rf "$champion_dir/champion-compiled/"
    echo 'Success!'
) 2>&1

res=${PIPESTATUS[0]}
rm -rf "$compil_dir"
exit $res
