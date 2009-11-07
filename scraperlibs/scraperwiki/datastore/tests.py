import unittest
import save
import connection

class testConnection(unittest.TestCase):

  def testConfig(self):
    config = connection.load_config()
    assert config
    
  def testConnect(self):
     connection.connect()


if __name__ == '__main__':
  unittest.main()