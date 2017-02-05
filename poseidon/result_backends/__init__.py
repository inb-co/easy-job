__author__ = 'Apollo'



class BaseResultBackend(object):
    def store(self, *args, **kwargs):
        raise NotImplementedError("BaseResultBackend should not be used")
