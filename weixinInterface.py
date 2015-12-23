# -*- coding: utf-8 -*-
import hashlib
import web
import lxml
import time
import os
import urllib2,json, random, pylibmc
from lxml import etree

def simsimi(ask):
    ask = ask.encode('UTF-8')
    enask = urllib2.quote(ask)
    baseurl = r'http://www.simsimi.com/requestChat?lc=zh&ft=1.0&req='
    url = baseurl + enask + '&uid=18005764&did=0'
    req = urllib2.Request(url)
    resp = urllib2.urlopen(req)
    reson = json.loads(resp.read())
    return reson

def translate(data):
    qword = urllib2.quote(data)
    baseurl = r'http://fanyi.youdao.com/openapi.do?keyfrom=linden&key=1102672932&type=data&doctype=json&version=1.1&q='
    url = baseurl+qword
    resp = urllib2.urlopen(url)
    fanyi = json.loads(resp.read())
    if fanyi['errorCode'] == 0:
        if 'basic' in fanyi.keys():
            trans = u'%s:\n%s\n%s\n网络释义：\n%s'%(fanyi['query'], ''.join(fanyi['translation']), ' '.join(fanyi['basic']['explains']), ''.join(fanyi['web'][0]['value']))
            return trans
        else:
            trans =u'%s:\n基本翻译:%s\n'%(fanyi['query'], ''.join(fanyi['translation']))
            return trans
    elif fanyi['errorCode'] == 20:
        return u'对不起，要翻译的文本过长'
    elif fanyi['errorCode'] == 30:
        return u'对不起，无法进行有效的翻译'
    elif fanyi['errorCode'] == 40:
        return u'对不起，不支持的语言类型'
    else:
        return u'对不起，您输入的单词%s无法翻译,请检查拼写'% data

class WeixinInterface:
 
    def __init__(self):
        self.app_root = os.path.dirname(__file__)
        self.templates_root = os.path.join(self.app_root, 'templates')
        self.render = web.template.render(self.templates_root)
    def GET(self):
        #获取输入参数
        data = web.input()
        signature = data.signature
        timestamp = data.timestamp
        nonce = data.nonce
        echostr = data.echostr
        #自己的token
        token = "linden" #这里改写你在微信公众平台里输入的token
        #字典序排序
        list = [token, timestamp, nonce]
        list.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, list)
        hashcode=sha1.hexdigest()
        #sha1加密算法        
 
        #如果是来自微信的请求，则回复echostr
        if hashcode == signature:
            return echostr
    def POST(self):        
        str_xml = web.data()
        xml = etree.fromstring(str_xml)
        # xml = urllib.unquote(xml)
        msg_type = xml.find("MsgType").text
        fromUser = xml.find("FromUserName").text
        toUser = xml.find("ToUserName").text
        # 初始化一个memcache实例用来保存用户的操作
        mc = pylibmc.Client()

        # 下面创建一个欢迎消息，通过判断Event类型
        if msg_type == "event":
            msg_content = xml.find("Event").text
            if msg_content == "subscribe":
                replay_text = u'''欢迎关注本微信，这个微信是本人业余爱好所建立，现在还没有什么功能，你们有什么好的想法欢迎反馈给我,我会不定期的进行添加，输入help查看操作指令...'''
                return self.render.reply_text(fromUser, toUser, int(time.time()), replay_text)
            if msg_content == "unsubscribe":
                replay_text = u'我现在功能还很简单，知道满足不了您的需求，但是我会慢慢改进，欢迎您以后再来！'
                return self.render.reply_text(fromUser, toUser, int(time.time()), replay_text)
        elif msg_type == 'text':
            msg_content = xml.find("Content").text

            if msg_content.lower() == 'bye':
                mc.delete(fromUser+'_xhj')
                return self.render.reply_text(fromUser, toUser, int(time.time()), u'您已经跳出了聊天的交谈中，输入help来显示操作指令')
            elif msg_content.lower() == 'chat':
                mc.set(fromUser+'_xhj', 'chat')
                return self.render.reply_text(fromUser, toUser, int(time.time()), u'您已经进入聊天中...\n输入bye结束聊天...')
            elif msg_content.lower() == 'music':
                musicList = [
                    [r'http://other.web.re01.sycdn.kuwo.cn/resource/n2/69/33/1625071345.mp3', '喜欢你', u'G.E.M.邓紫棋'],
                    [r'http://other.web.rg01.sycdn.kuwo.cn/resource/n2/37/30/3252857194.mp3', u'一次就好-(电影《夏洛特烦恼》暖水曲)', u'杨宗纬'],
                    [r'http://other.web.rh01.sycdn.kuwo.cn/resource/n1/29/85/1922529202.mp3', u'我们不该这样的', u'张赫宣']
                             ]
                music = random.choice(musicList)
                musicurl = music[0]
                musictitle = music[1]
                musicdes = music[2]
                return self.render.reply_music(fromUser, toUser, int(time.time()), musictitle, musicdes, musicurl)

            #读取memcache中的缓存数据
            mcdata = mc.get(fromUser+'_xhj')

            if mcdata == 'chat':
                res = simsimi(msg_content)
                reply_text = res['res']['msg']
                if u'微信' in reply_text or u'微 信' in reply_text:
                    reply_text = u"请换个问题啦，么么哒-_-~"
                return self.render.reply_text(fromUser, toUser, int(time.time()), reply_text)

            if msg_content.lower() == 'help':
                reply_text = u'''1.默认中英翻译工具\n2.输入"chat"可进入聊天模式\n3.输入"music"可随机听一首音乐'''
                return self.render.reply_text(fromUser, toUser, int(time.time()), reply_text)
            elif type(msg_content).__name__ == "unicode":
                msg_content = msg_content.encode('UTF-8')
            translate_content = translate(msg_content)
            return self.render.reply_text(fromUser, toUser, int(time.time()), translate_content)
