from setuptools import setup

__author__  = 'Mike Asker'
__doc__     = 'MPY development tool - UART'
__version__ = '0.0.1'

setup(
    name         = 'MpyUart',
    version      = __version__,
    description  = __doc__,
    author       = __author__,
    author_email = 'mike.asker@gmail.com',
    license      = 'wxWindows',
    packages     = ['mpyuart'],
    entry_points = '''
    [Editra.plugins]
    MpyUart = mpyuart:MpyUart
    '''
    )