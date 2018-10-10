import unittest

if __name__ == "__main__":
    modules = ['test', 'test_codec']
    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromNames(modules))
