# -*- coding: utf-8 -*-
# @Time    : 2023/12/22 下午11:48

def parse_command(command):
    if not command:
        return None, None
    parts = command.split(" ", 1)
    if len(parts) > 1:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], None
    else:
        return None, None
