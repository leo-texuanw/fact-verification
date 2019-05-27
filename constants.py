class Const():
    """ Store all constants used in the project """
    class ConstError(TypeError):
        pass

    class ConstCaseError(ConstError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError("Can't change const.%s" % name)
        if not name.isupper():
            raise self.ConstCaseError('const name "%s" is not all supercase' % name)

        self.__dict__[name] = value


Args = Const()
Args.OBJECTS = './objects'
Args.TITLES = 'xapian_titles_dict'

Args.DB_PATH = './xdb/wiki.db'

Args.LOG_MISSING_DOCS = False
