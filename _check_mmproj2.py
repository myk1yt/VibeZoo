import sys  
sys.path.insert(0, 'mcp-servers')  
from llama_cpp import Llama  
from bridge.vision.minicpm import _get_model_path, _get_mmproj_path  
mp = str(_get_mmproj_path())  
import os  
print('mmproj path:', mp)  
print('mmproj exists:', os.path.exists(mp))  
print('mmproj size:', os.path.getsize(mp)/1024/1024, 'MB')  
