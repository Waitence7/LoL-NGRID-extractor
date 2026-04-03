import struct
import zstandard as zstd
import os
import subprocess
import mmap
import sys

def get_default_lol_path():
    """기본적인 롤 설치 경로 반환"""
    return "C:/Riot Games/League of Legends"

def get_full_wad_path(base_dir):
    """베이스 폴더를 받아 실제 Map11.wad.client 전체 경로 반환"""
    target_rel_path = "Game/DATA/FINAL/Maps/Shipping/Map11.wad.client"
    return os.path.join(base_dir, target_rel_path).replace("\\", "/")


def resource_path(relative_path):
    """ PyInstaller의 임시 폴더 또는 프로젝트 루트에서 경로를 찾음 """
    try:
        # 1. 빌드 후 (EXE 실행 시): 모든 파일이 루트(.)에 모임
        base_path = sys._MEIPASS
    except Exception:
        # 2. 개발 중 (uv run src/main.py 실행 시)
        # 현재 파일 위치: .../LoL-NGRID-extractor/src/wad_extractor.py
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        
        if relative_path == "LoLNGRIDConverter.exe":
            # EXE는 src -> extractor -> Ngrid_converter (두 번 위)
            base_path = os.path.join(current_file_dir, "..", "..")
        else:
            # hashes.txt 등은 src -> extractor (한 번 위)
            base_path = os.path.join(current_file_dir, "..")
    
    full_path = os.path.normpath(os.path.join(base_path, relative_path))
    return full_path

def load_data():
    """ hashes.txt 로드 """
    data_map = {}
    # resource_path("hashes.txt")는 빌드 시 루트에서, 개발 시 프로젝트 폴더에서 찾음
    file_path = resource_path("hashes.txt")
    
    if not os.path.exists(file_path):
        print(f"[경고] hashes.txt 없음: {file_path}")
        return {}
        
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                data_map[parts[1]] = parts[0]
    return data_map

def extract_wad(target_hash_hex, wad_path, full_name_path):
    """ 파일 추출 로직 """
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    path_parts = full_name_path.split('/')
    full_file_name = path_parts[-1] 
    pure_name = path_parts[-1].split('.')[0]
    
    final_output_dir = os.path.join(downloads_path, pure_name)
    os.makedirs(final_output_dir, exist_ok=True)

    target_hash_int = int(target_hash_hex, 16)
    target_pattern = struct.pack("<Q", target_hash_int)

    try:
        with open(wad_path, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                pos = mm.find(target_pattern)
                if pos == -1: return False, None

                info_part = mm[pos + 8 : pos + 21]
                offset, csize, usize, ftype = struct.unpack("<IIIB", info_part)
                
                mm.seek(offset)
                raw = mm.read(csize)
                
                if ftype in [2, 3] and csize != usize:
                    dctx = zstd.ZstdDecompressor()
                    result = dctx.decompress(raw, max_output_size=usize if usize > 0 else 10*1024*1024)
                else:
                    result = raw
                
                output_file_path = os.path.join(final_output_dir, full_file_name)
                with open(output_file_path, "wb") as out:
                    out.write(result)
                
                return True, final_output_dir
            
    except Exception as e:
        print(f"추출 에러: {e}")
        return False, None
    
def run_converter(target_dir, file_name):
    # 여기서도 resource_path를 사용하여 내부 포함된 EXE를 찾습니다.
    exe_path = resource_path("LoLNGRIDConverter.exe")
    target_file = os.path.join(target_dir, file_name)

    print(f"[DEBUG] 최종 EXE 경로: {exe_path}")

    if os.path.exists(exe_path) and os.path.exists(target_file):
        try:
            subprocess.run([exe_path, target_file], cwd=target_dir, shell=True)
            return True
        except Exception as e:
            print(f"컨버터 실행 에러: {e}")
            return False
    return False