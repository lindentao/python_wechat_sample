# coding: UTF-8
import os
import sae
import web
 
from weixinInterface import WeixinInterface
# url处理：第一部分是匹配URL的正则表达式，第二部分是接受请求的类名称
urls = (
'/weixin', 'WeixinInterface'
)
 
app_root = os.path.dirname(__file__)
templates_root = os.path.join(app_root, 'templates')
render = web.template.render(templates_root)
# 创建一个列举url的application
app = web.application(urls, globals()).wsgifunc()        
application = sae.create_wsgi_app(app)