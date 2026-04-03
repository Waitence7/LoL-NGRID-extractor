#이 규모에 이렇게까지 해야하는지는 모르겠지만..
import os
import sys

def get_resource_path(relative_path):
    """ 실행 환경(py/exe)에 상관없이 리소스의 절대 경로를 반환 """
    if getattr(sys, 'frozen', False):
        # .exe 실행 시: 임시 폴더(_MEIPASS) 기준
        base_path = sys._MEIPASS
    else:
        # .py 실행 시: 현재 파일(utils.py)의 부모(src)의 부모(Root) 기준
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)