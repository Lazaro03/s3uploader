class Config(object):
      def __init__(self):
          self.BotToken     = '6626336774:AAE-B9in4SXtazI3hStFNhrZ70ZoadIataQ'
          self.S3Token      = 'Todus S3 Token Auth'
          self.ChunkSize    = 10
          self.ChunkFixed   = 150
          self.FileLimit    = 1024 * 1024 * 200
          self.ExcludeFiles = ['bot.py','Config.py','multiFile.py','toDus.py','requirements.txt','Procfile','__pycache__','.git','.profile.d','.heroku']
          self.ChunkedFileLimit = 1024 * 1024 * 1024
          self.InProcces = False
          self.BotChannel = '-1001807928266'
          self.AdminUsers = ['Michel1203']
          self.current_user_msg = ''
          self.current_chanel_msg = ''


      def setS3Token(self,token : str):
          self.S3Token = token

      def setBotToken(self,token : str):
          self.BotToken = token

      def setChunkSize(self,chunk : int):
          self.ChunkSize = chunk

      def toStr(self):
          return '[Chunk Size]\n' + str(self.ChunkSize) + '\n\n[Token]\n' + self.S3Token
