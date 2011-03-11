
CHARSET = 'utf-8'

def to_str(s, errors='strict'):
    """
    Theoretically http://www.python.org/dev/peps/pep-0263/ for this and 
    # -*- coding: utf-8 -*-
    should help. But it don't .
    """
    
    if not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            return unicode(s).encode(CHARSET, errors)
    elif isinstance(s, unicode):
        return s.encode(CHARSET, errors)
    else:
        return s
    