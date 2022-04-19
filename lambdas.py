from constants import *

def admin_command(c):
    return c.from_user.id == creator

def pm_command(c):
    return c.chat.type == 'private'