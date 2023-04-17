import os
import http.client
import requests
from telegram.ext import Updater,CommandHandler,ConversationHandler,CallbackQueryHandler,MessageHandler,Filters
from telegram import ChatAction,InlineKeyboardMarkup,InlineKeyboardButton
import toDus
import zipfile
from zipfile import ZipFile
import re
from Config import Config
from youtube_dl import YoutubeDL
import multiFile
import math



#S3 Variables
conf = Config()


#Estados
INPUT_TEXT  = 0
TOKEN_TEXT  = 2
INPUT_YOUTUBE  = 3
CHUNK_TEXT  = 4
TELEGRAM_FILE  = 5
TELEGRAM_VID  = 6
TELEGRAM_SOUND  = 7
DOWN_QUERY = 8
DOWN_CHUNK_QUERY = 9
DOWN_CHUNK_FIXED = 22
DOWN_NOZIP_QUERY = 10
CONFIG_TOKEN = 12
CONFIG_CHUNK = 13
DOWN_GALLERY_QUERY = 14


#Opciones
DOWN_TYPE = 1

PROCCECED = False




def text_progres(index,max):
    if max<1:
        max += 1
    porcent = index / max
    porcent *= 100
    porcent = round(porcent)
    make_text = '(' + str(porcent) + '% '
    index_make = 1
    make_text += '100%)'
    make_text += '\n'
    while(index_make<21):
          if porcent >= index_make * 5:
             make_text+='█'
          else:
              make_text+='▒'
          index_make+=1
    make_text += '\n'
    make_text += '(' + str(index) + '/' + str(max) + ')'
    return make_text

def clear_cache():
    try:
        files = os.listdir(os.getcwd())
        for f in files:
            if '.' in f:
                if conf.ExcludeFiles.__contains__(f):
                    print('No Se Permitio la eliminacion de '+f)
                else:
                    os.remove(f)
    except Exception as e:
           print(str(e))


def send_document_to_channel(context,file):
    context.bot.send_document(
        chat_id=conf.BotChannel,
        document=file
        )

def send_message_to_channel(context,msg):
    return context.bot.send_message(
        chat_id=conf.BotChannel,
        text=msg
        )

#Funciones
def upload_to_todus(name,update):
    try:
        todusUtils = toDus.toDus(conf.S3Token)
        file_size = os.stat(name)
        len = file_size.st_size
        req = todusUtils.Get_Upload_URL(file_size.st_size)
        get_link = ''
        if req != 'token error':
           get, put = req[1], req[0]
           h = {
              "Host": "s3.todus.cu",
              "user-agent": "ToDus 0.38.34 HTTP-Upload",
              "authorization": "Bearer "+str(conf.S3Token),
              "content-type": "application/octet-stream",
              "content-length": str(len),
              "accept-encoding": "gzip"
              }
           try :
               file  = open(name,'rb')
               tmp = requests.put(put, data=file.read(), headers=h)
               file.close()
               if tmp.status_code == 200:
                  get_link = get
               else:
                  print('Resubiendo')
                  return upload_to_todus(name,update)
           except Exception as e:
                  update.message.reply_text('(toDus Server) \n' + str(e))
        else:
            update.message.reply_text("Error de Token Actualize Su Token OJO!")
        return get_link
    except Exception as e:
                  print('Resubiendo')
                  return upload_to_todus(name,update)

def create_txt(txt_list,txt_name):
    txt_content = ''
    for e in txt_list:
        txt_content += str(txt_list[e]) + '\t' + str(e) + '\n'
    txt_name = txt_name+'.txt'
    txt_file = open(txt_name,'w')
    try:
       txt_file.write(txt_content)
    except:
        print('Error al escribir el texto ' + str(txt_name))
    txt_file.close();
    return txt_name


def get_url_file_name(url,req):
    name = ''
    try:
        if "Content-Disposition" in req.headers.keys():
            return str(re.findall("filename=(.+)", req.headers["Content-Disposition"])[0])
        else:
            tokens = str(url).split('/');
            return tokens[len(tokens)-1]
    except:
           tokens = str(url).split('/');
           return tokens[len(tokens)-1]
    return name


def get_zip_ext(iter):
    return '.%03d' % iter
def get_file_ext(name):
    return '.' + str(name).split('.')[1]
def get_name(file):
    return str(file).split('.')[0]


def get_file_size(req):
    try:
        return int(req.headers['content-length'])
    except:
        return 0

def down_file(url,update,context,ziped=True):
    try:
        multiFile.files.clear()
        clear_cache()
        ret_msg = ''
        txt_list = {}
        chunk_size = (1024 * 1024 * conf.ChunkSize)
        req = requests.get(url, stream = True,allow_redirects=True)
        filesize = get_file_size(req)
        edit_user_message('Procesando...\n'+str(pretty_size(filesize))+text_progres(0,round(filesize/chunk_size)),update,context)
        edit_chanel_message('Procesando...\n'+str(pretty_size(filesize))+text_progres(0,round(filesize/chunk_size)),update,context)
        if filesize <= conf.FileLimit:
            if req.status_code == 200:
                file_name = get_url_file_name(url,req)
                file_name = file_name.replace('"',"")
                file_name = fixed_name(file_name)
                if ziped == True:
                    mult_file =  multiFile.MultiFile(get_name(file_name)+'.7z',chunk_size)
                    zip = ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
                    zip.writestr(file_name,data=req.content)
                    zip.close()
                    mult_file.close()
                    last_msg = 'Trabajando...\nSubiendo\n'+str(pretty_size(filesize))+text_progres(len(txt_list),round(filesize/chunk_size))
                    for file in multiFile.files:
                         get = upload_to_todus(file,update)
                         if get == '':
                             break
                         txt_list[file] = get
                         os.unlink(file)
                         try:
                             current_msg = 'Trabajando...\nSubiendo\n'+str(pretty_size(filesize))+text_progres(len(txt_list),round(filesize/chunk_size))
                             if current_msg != last_msg:
                                 try:
                                     edit_user_message(current_msg,update,context)
                                     edit_chanel_message(current_msg,update,context)
                                 except Exception as e:
                                         print(str(e))
                                 current_msg = last_msg
                         except Exception as e:
                                update.message.reply_text(str(e))
                else:
                    file = open(file_name,'wb')
                    file.write(req.content)
                    file.close()
                    get = upload_to_todus(file_name,update)
                    txt_list[file_name] = get
                    os.unlink(file_name)
                txt_file = create_txt(txt_list,str(file_name).split('.')[0])
                txt = open(txt_file)
                update.message.reply_document(txt)
                update.message.reply_text('Se Publico su Descarga en El Canal!')
                update.message.reply_text(pretty_size(filesize) + ' ' + str(len(txt_list)) + ' Archivos Subidos')
                txt.close()
                os.unlink(txt_file)
        else:
             update.message.reply_text('(down_file) ' + 'Archivo Exedido Limite de ' + str(conf.FileLimit) + 'mb')
    except Exception as e:
            update.message.reply_text(str(e))

def file_exist(path):
    if path in os.listdir():
       return True
    return False

def pretty_size(size):
    kb = 1024
    mb = kb * kb
    gb = mb * mb
    tb = gb * gb
    if size > 0 and size <= kb:
       return str(size) + 'b'
    if size > kb and size <= mb:
       return str(round(size / kb)) + 'kb'
    if size > mb and size <= gb:
       return str(round(size / mb)) + 'mb'
    if size > gb and size <= tb:
       return str(round(size / gb)) + 'gb'
    if size > tb:
       return str(round(size / tb)) + 'tb'
    return size

def down_chunked(url,update,context):
    try:
        multiFile.files.clear()
        clear_cache()
        ret_msg = ''
        txt_list = {}
        chunk_size = 1024 * 1024 * conf.ChunkSize
        req = requests.get(url, stream = True,allow_redirects=True)
        filesize = get_file_size(req)
        edit_user_message('Trabajando...\n'+str(pretty_size(filesize))+text_progres(0,round(filesize/chunk_size)),update,context)
        edit_chanel_message('Trabajando...\n'+str(pretty_size(filesize))+text_progres(0,round(filesize/chunk_size)),update,context)
        if req.status_code == 200:
            file_name = get_url_file_name(url,req)
            file_name = file_name.replace('"',"")
            file_name = fixed_name(file_name)
            mult_file =  multiFile.MultiFile(get_name(file_name)+'.7z',chunk_size)
            zip = ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
            iterator = 1
            for chunk in req.iter_content(chunk_size = chunk_size):
                if chunk:
                    chunk_name = file_name + get_zip_ext(iterator)
                    zip.writestr(chunk_name,data=chunk)
                    current_file = get_name(file_name) + '.7z' + get_zip_ext(iterator-1)
					#END ZIP FILE ERROR
                    last_msg = 'Trabajando...\nSubiendo\n'+str(pretty_size(filesize))+text_progres(len(txt_list),round(filesize/chunk_size))
                    if file_exist(current_file) == True:
                        print('Subiendo '+current_file)
                        get = upload_to_todus(current_file,update)
                        if get == '':
                             break
                        txt_list[current_file] = get
                        os.unlink(current_file)
                        if current_file in multiFile.files:
                            multiFile.files.remove(current_file)
                        try:
                             current_msg = 'Trabajando...\n'+str(pretty_size(filesize))+text_progres(len(txt_list),round(filesize/chunk_size))
                             if current_msg != last_msg:
                                 try:
                                     edit_user_message(current_msg,update,context)
                                     edit_chanel_message(current_msg,update,context)
                                 except Exception as e:
                                        print(str(e))
                                 current_msg = last_msg
                        except Exception as e:
                                update.message.reply_text(str(e))
                    iterator+=1
            
            zip.close()
            mult_file.close()
            for f in multiFile.files:
                    print('Subiendo '+f)
                    get = upload_to_todus(f,update)
                    if get == '':
                        break
                    txt_list[f] = get
                    os.unlink(f)
                    try:
                        current_msg = 'Trabajando...\nSubiendo '+f+'\n'+str(pretty_size(filesize))+text_progres(len(txt_list),round(filesize/chunk_size))
                        edit_user_message(current_msg,update,context)
                        edit_chanel_message(current_msg,update,context)
                    except Exception as e:
                                print(str(e))
            txt_file = create_txt(txt_list,get_name(file_name))
            txt = open(txt_file)
            update.message.reply_document(txt)
            update.message.reply_text(pretty_size(filesize) + ' ' + str(len(txt_list)) + ' Archivos Subidos')
            txt.close()
            os.unlink(txt_file)
    except Exception as e:
            update.message.reply_text('(down_chunked) ' + str(e))
            print(str(e))


def down_chunked_fixed(url,update,context):
    try:
        multiFile.files.clear()
        clear_cache()
        ret_msg = ''
        txt_list = {}
        chunk_size = 1024 * 1024 * conf.ChunkSize
        req = requests.get(url, stream = True,allow_redirects=True)
        filesize = get_file_size(req)
        edit_user_message('Trabajando...\n'+str(pretty_size(filesize))+text_progres(0,round(filesize/chunk_size)),update,context)
        edit_chanel_message('Trabajando...\n'+str(pretty_size(filesize))+text_progres(0,round(filesize/chunk_size)),update,context)
        if req.status_code == 200:
            file_name = get_url_file_name(url,req)
            file_name = file_name.replace('"',"")
            file_name = fixed_name(file_name)
            mult_file =  multiFile.MultiFile(get_name(file_name)+'.7z',chunk_size)
            zip = ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
            iterator = 1
            file_wr = open(file_name,'wb')
            print('Descargando...')
            for chunk in req.iter_content(chunk_size = 1024 * 1024 * conf.ChunkFixed):
                if chunk:
                    file_wr.write(chunk)
            file_wr.close()
            print('Comprimiendo...')
            zip.write(file_name)
            zip.close()
            mult_file.close()
            os.unlink(file_name)
            for f in multiFile.files:
                    print('Subiendo '+f)
                    get = upload_to_todus(f,update)
                    if get == '':
                        break
                    txt_list[f] = get
                    os.unlink(f)
                    try:
                        current_msg = 'Trabajando...\nSubiendo '+f+'\n'+str(pretty_size(filesize))+text_progres(len(txt_list),round(filesize/chunk_size))
                        edit_user_message(current_msg,update,context)
                        edit_chanel_message(current_msg,update,context)
                    except Exception as e:
                                print(str(e))
            txt_file = create_txt(txt_list,get_name(file_name))
            txt = open(txt_file)
            update.message.reply_document(txt)
            update.message.reply_text(pretty_size(filesize) + ' ' + str(len(txt_list)) + ' Archivos Subidos')
            txt.close()
            os.unlink(txt_file)
    except Exception as e:
            update.message.reply_text('(down_chunked) ' + str(e))
            print(str(e))



def fixed_name(name):
    return str(name).replace('%20',' ')


def download_gallery(list,update,context):
     try:
       name_split = str(list[0]).split('/')
       txt_name = name_split[len(name_split)-2]
       txt_name = fixed_name(txt_name)
       txt_list = {}
       for url in list:
           if url == '':
                continue
           req = requests.get(url,allow_redirects=True)
           file_name = get_url_file_name(url,req)
           current_msg = 'Descargando Galeria...\n'+file_name+'\n'+text_progres(len(txt_list),len(list))
           edit_user_message(current_msg,update,context)
           edit_chanel_message(current_msg,update,context)
           f = open(file_name,'wb')
           f.write(req.content)
           f.close()
           get = upload_to_todus(file_name,update)
           if get == '':
              break
           txt_list[file_name] = get
           os.unlink(file_name)
       txt_file = create_txt(txt_list,txt_name)
       txt = open(txt_file)
       update.message.reply_document(txt)
       txt.close()
       os.unlink(txt_file)
     except Exception as e:
            update.message.reply_text(str(e))



def process_link(url,update,context):
    if 'nozip@' in str(url):
           link = str(url).split('@')[1]
           down_file(link,update,context,False)
    elif 'chunked@' in str(url):
           link = str(url).split('@')[1]
           down_chunked(link,update,context)
    elif 'chunkedf@' in str(url):
           link = str(url).split('@')[1]
           down_chunked_fixed(link,update,context)
    else:
           down_file(url,update,context,True)



def edit_user_message(msg,update,context,nose=''):
    try:
        try:
            context.bot.edit_message_text(text = msg,
                                              chat_id = update.message.chat.id,
                                              message_id = conf.current_user_msg.message_id
                                              )
        except:
            conf.current_user_msg = update.message.reply_text(msg)
    except Exception as e:
            print(str(e))

def edit_chanel_message(msg,update,context,nose=''):
    pass

def download(url,update,context,type):
    edit_user_message('Trabajando...',update,context)
    edit_chanel_message('Trabajando...',update,context)
    if type == 1:
           if ';' in url:
               list = str(url).split(';')
               for l in list:
                   process_link(l,update,context)
           else:
               process_link(url,update,context)
    edit_user_message('Aprebecha Locos Q Estoy Libre\n[--------------------]',update,context)
    edit_chanel_message('Aprebechen Locos Q Estoy Libre\n[--------------------]',update,context)


def is_accesble(update,context):
    if update.message.chat.username in conf.AdminUsers:
        return True
    return False

def start(update,context):
    if is_accesble(update,context):
         update.message.reply_text('Bienvenido Usted Ya Tiene Acceso Al Bot!\nUse /help - Para Saber Los Comandos Existentes')

def down_query_handler(update,context):
    if is_accesble(update,context):
        update.message.reply_text('Envie La Url De Descarga...')
        return DOWN_QUERY

def down_url(update,context):
    link = update.message.text
    download(link,update,context,1)
    return -1

def down_chunked_query_handler(update,context):
     if is_accesble(update,context):
        update.message.reply_text('Envie La Url De Descarga...')
        return DOWN_CHUNK_QUERY

def down_chunked_url(update,context):
    link = update.message.text
    download('chunked@'+link,update,context,1)
    return -1

def down_chunked_fixed_handler(update,context):
     if is_accesble(update,context):
        update.message.reply_text('Envie La Url De Descarga...')
        return DOWN_CHUNK_FIXED

def down_chunked_fixed_url(update,context):
    link = update.message.text
    download('chunkedf@'+link,update,context,1)
    return -1


def down_nozip_query_handler(update,context):
     if is_accesble(update,context):
        update.message.reply_text('Envie La Url De Descarga...')
        return DOWN_NOZIP_QUERY

def down_nozip_url(update,context):
    link = update.message.text
    download('nozip@'+link,update,context,1)
    return -1

def down_gallery_query_handler(update,context):
     if is_accesble(update,context):
         update.message.reply_text('Envie el txt de la galleria...')
         return DOWN_GALLERY_QUERY

def down_gallery_url(update,context):
    try:
        file = context.bot.get_file(update.message.document.file_id)
        req = requests.get(file.file_path)
        f = open('gallery.txt','wb')
        f.write(req.content)
        f.close()
        list = str(open('gallery.txt','r').read()).replace('\n','').split(';')
        download_gallery(list,update,context)
    except Exception as e:
            update.message.reply_text('(down_chunked) ' + str(e))
    edit_user_message('Aprebecha Locos Q Estoy Libre\n[--------------------]',update,context)
    edit_chanel_message('Aprebechen Locos Q Estoy Libre\n[--------------------]',update,context)
    return -1


def set_token(update,context):
     if is_accesble(update,context):
        update.message.reply_text('Cual es Su Token?')
        return CONFIG_TOKEN

def set_token_text(update,context):
    conf.setS3Token(update.message.text)
    update.message.reply_text('Se a configurado!')
    return -1

def set_chunk(update,context):
     if is_accesble(update,context):
          update.message.reply_text('DALE DIME SIZE')
          return CONFIG_CHUNK

def set_chunk_text(update,context):
    conf.setChunkSize(int(update.message.text))
    update.message.reply_text('Se a configurado!')
    return -1

def get_conf(update,context):
     if is_accesble(update,context):
        update.message.reply_text(conf.toStr())


def help(update,context):
    if is_accesble(update,context):
        update.message.reply_text('/start - Iniciar el Bot\n/d - Descarga Normal Maximo (200mb)\n/dnz - Descarga Sin Compresion\n/dc - Descara Mediante Chunks (Sin Limite)\n/dcf - Descarga Mediante Chunks (Sin Limite Arreglado)\n/dg - Descargar Galeria (Lioner) XD...\n/st - Cambiar El Token S3\n/sc - Cambiar El Tamaño de los Chunks (Partes Compresas)\n/gc - Obtener La configuracion del Bot')


def onMSG(update,conte):
    print(update)

#Inicio del Bot
def init():
     try:
        updater = Updater(token=conf.BotToken,use_context=True) #conectarse con el telegrambot

        dp = updater.dispatcher # extraer el dispersador de mensages
    
        #dp.add_handler(MessageHandler(filters=Filters.text,callback=onMSG))

        dp.add_handler(ConversationHandler(
        entry_points=[
           CommandHandler('help',help),
           CommandHandler('start',start),
           CommandHandler(command='dc',callback=down_chunked_query_handler),
           CommandHandler(command='dcf',callback=down_chunked_fixed_handler),
           CommandHandler(command='dnz',callback=down_nozip_query_handler),
           CommandHandler(command='dg',callback=down_gallery_query_handler),
           CommandHandler(command='d',callback=down_query_handler),


           CommandHandler(command='st',callback=set_token),
           CommandHandler(command='sc',callback=set_chunk),
           CommandHandler(command='gc',callback=get_conf)
        ],
        states={
            DOWN_QUERY      : [MessageHandler(Filters.text,down_url)],
            DOWN_CHUNK_QUERY: [MessageHandler(Filters.text,down_chunked_url)],
            DOWN_NOZIP_QUERY: [MessageHandler(Filters.text,down_nozip_url)],

            CONFIG_TOKEN    : [MessageHandler(Filters.text,set_token_text)],
            CONFIG_CHUNK    : [MessageHandler(Filters.text,set_chunk_text)],
            DOWN_GALLERY_QUERY : [MessageHandler(Filters.document,down_gallery_url)],
            DOWN_CHUNK_FIXED  : [MessageHandler(Filters.text,down_chunked_fixed_url)]
        },
        fallbacks=[]
        ))

        updater.start_polling() #iniciar escucha del bot
        updater.idle() #bucle de espera del bot
     except Exception as e:
         print(str(e))
         init()

#Metodo de Entrada del Programa
if __name__ == '__main__':
   init()



