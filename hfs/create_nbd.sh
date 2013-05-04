#! /bin/sh
# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Pierre Bourdon <pierre.bourdon@prologin.org>
# Copyright (c) 2013 Association Prologin <info@prologin.org>
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

# Format the NBD file and copy the skeleton in it.

filename="$1"
username="$2"
group="$3"
skeleton="$4"

mkfs.ext4 -F -m 0 "$filename"
mnt=$(mktemp -d)
mount -o loop "$filename" "$mnt"
rsync -aHAX "$skeleton" "$mnt"
chown -R "$username:$group" "$mnt"
umount "$mnt"
rmdir "$mnt"
