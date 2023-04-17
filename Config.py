class Config(object):
      def __init__(self):
          self.BotToken     = '1710625956:AAHBoGPuifwjkuvEd7BcB7UnFZ0wF1Dr5No'
          self.S3Token      = 'Todus S3 Token Auth'
          self.ChunkSize    = 10
          self.ChunkFixed   = 150
          self.FileLimit    = 1024 * 1024 * 200
          self.ExcludeFiles = ['bot.py','Config.py','multiFile.py','toDus.py','requirements.txt','Procfile','__pycache__','.git','.profile.d','.heroku']
          self.ChunkedFileLimit = 1024 * 1024 * 1024
          self.InProcces = False
          self.BotChannel = '-1001432878672'
          self.AdminUsers = ['Genoskuncyborg']
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