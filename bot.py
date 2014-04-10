#-*- coding: utf-8 -*-

import sys
sys.path.insert(0,"lib")
sys.path.insert(0,"basic")

import os
import datetime
import re
import ConfigParser

from irc.bot import SingleServerIRCBot

import basiclex
import basparse
import basinterp

class BotPy(SingleServerIRCBot):

    """ initializer """
    def __init__(self):
        config = ConfigParser.SafeConfigParser()
        config.read("./config.ini")

        self.interpreter = basinterp.BasicInterpreter({})
        self.user_list = []
        src_dir = os.path.join(os.path.dirname(__file__), unicode(config.get("basic", "src_dir")))
        self.interpreter.set_src_dir(src_dir) # default

        server = unicode(config.get("irc", "server"))
        port = int(config.get("irc", "port"))
        nick = unicode(config.get("irc", "nick"))
        SingleServerIRCBot.__init__(self, [(server, port)], nick, nick)
        self.channel = unicode(config.get("irc", "channel"))

    def start(self):
        SingleServerIRCBot.start(self)

    """ ニックネームが被っていたとき """
    def on_nicknameinuse(self, c, e):
        c.nick( c.get_nickname() + "_" )

    """ サーバに接続成功 """
    def on_welcome(self, c, e):
        print "welcome"
        c.join( self.channel )

    """ privmsg受信時 """
    def on_privmsg(self, c, e):
        self.print_log(e)

    """ pubmsg受信時 """
    def on_pubmsg(self, c, e):
        self.print_log(e)
        try:
            user = e.source().nick
            msg = e.arguments()[0]
            if user not in self.user_list :
                msg = e.arguments()[0]
                pattern = re.search(c.get_nickname()+"\s*:\s*(.*)", msg)
                if not pattern: return
                cmd = pattern.group(1).strip()
                print cmd
                if cmd == 'BASIC':
                    self.user_list.append(user)
                    self.notice('enter BASIC mode')
                return
        except Exception as e:
            print >> sys.stderr, "Unexpected error:", e.message
            return

        self.msg_buffer = ''
        try:
            if msg.strip().upper() == 'SYSTEM':
                self.user_list.remove(user)
                self.notice('bye > ' + user)
                return

            sys.stdout = self # 標準出力をフックしてIRCにnoticeで発言
            prog = basparse.parse(msg.strip()+'\n')
            if not prog: return

            keys = list(prog)
            if keys[0] > 0:
                self.interpreter.add_statements(prog)
            else:
                stat = prog[keys[0]]
                if stat[0] == 'RUN':
                    try:
                        self.interpreter.run()
                    except RuntimeError:
                        pass
                elif stat[0] == 'LIST':
                    self.interpreter.list(stat[1])
                elif stat[0] == 'BLANK':
                    self.interpreter.del_line(stat[1])
                elif stat[0] == 'NEW':
                    self.interpreter.new()
                elif stat[0] == 'RENUM':
                    self.interpreter.renum(stat[1])
                elif stat[0] == 'SAVE':
                    self.interpreter.save(stat[1])
                elif stat[0] == 'LOAD':
                    self.interpreter.load(stat[1], stat[2])
            self.notice(self.msg_buffer)
            print >> sys.stderr, self.msg_buffer
        except Exception as e:
            print >> sys.stderr, "Unexpected error:", e.message
        finally:
            sys.stdout = sys.__stdout__
            self.msg_buffer = ''

    on_pubnotice = on_pubmsg

    def print_log(self, e):
        try:
            nick = e.source().nick
            msg = e.arguments()[0]
        except:
            print str(e)
            return
        print "%s: %s" % (nick, msg)

    def on_ping(self, c, e):
        self.connection.pong( self.channel )

    """ チャット発言 """
    def privmsg(self, str):
        self.connection.privmsg( self.channel, unicode(str, "utf8").encode("iso-2022-jp", "ignore") )

    """ 通知発言 """
    def notice(self, str):
        self.connection.notice( self.channel, unicode(str, "utf8").encode("iso-2022-jp", "ignore") )

    def write(self, str):
        self.msg_buffer = self.msg_buffer + str.rstrip('\r\n') + ' '

bot = BotPy()
bot.start()
